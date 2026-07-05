from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import audit
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.domain import (
    Appointment,
    InventoryBatch,
    InventoryItem,
    Invoice,
    PurchaseOrder,
    ServiceMaterialTemplate,
    StockLocation,
    StockMovement,
    StockMovementType,
    Supplier,
    User,
)
from app.schemas.common import (
    InventoryBatchCreate,
    InventoryItemCreate,
    InvoiceCreate,
    PurchaseOrderCreate,
    ServiceMaterialCreate,
    StockMovementCreate,
    SupplierCreate,
)
from app.services.inventory import consume_fefo, ensure_batch_available, ensure_positive, expiring_batches, recalculate_stock, transfer_batch

router = APIRouter(prefix="/api", tags=["inventory"])


def update_from_payload(obj, payload) -> None:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)


@router.get("/inventory/items")
def inventory_items(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(InventoryItem).order_by(InventoryItem.name)).all()


@router.post("/inventory/items")
def create_inventory_item(payload: InventoryItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = InventoryItem(**payload.model_dump())
    db.add(item)
    db.flush()
    audit(db, "create", "InventoryItem", item.id, item.name, user.id)
    db.commit()
    db.refresh(item)
    return item


@router.get("/inventory/items/{item_id}")
def get_inventory_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, detail="Artikl nije pronađen")
    return item


@router.patch("/inventory/items/{item_id}")
def update_inventory_item(item_id: int, payload: InventoryItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, detail="Artikl nije pronađen")
    update_from_payload(item, payload)
    audit(db, "update", "InventoryItem", item.id, item.name, user.id)
    db.commit()
    db.refresh(item)
    return item


@router.get("/inventory/low-stock")
def low_stock(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(InventoryItem).where(InventoryItem.current_stock <= InventoryItem.reorder_point).order_by(InventoryItem.current_stock)).all()


@router.get("/inventory/expiring")
def expiring(days: int = 30, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return expiring_batches(db, days)


@router.get("/inventory/batches")
def batches(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(InventoryBatch).options(joinedload(InventoryBatch.item), joinedload(InventoryBatch.location)).order_by(InventoryBatch.expiration_date)).all()


@router.post("/inventory/batches")
def create_batch(payload: InventoryBatchCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    batch = InventoryBatch(**payload.model_dump())
    db.add(batch)
    db.flush()
    movement = StockMovement(inventory_item_id=batch.inventory_item_id, batch_id=batch.id, to_location_id=batch.location_id, quantity=batch.quantity, movement_type="purchase_receipt", reason="Ulaz robe", created_by=user.id)
    db.add(movement)
    recalculate_stock(db, batch.inventory_item_id)
    audit(db, "create", "InventoryBatch", batch.id, "Nova serija zalihe", user.id)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/inventory/stock-locations")
def stock_locations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(StockLocation).order_by(StockLocation.name)).all()


@router.get("/inventory/stock-movements")
def stock_movements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(StockMovement).options(joinedload(StockMovement.item)).order_by(StockMovement.created_at.desc()).limit(200)).all()


@router.post("/inventory/stock-movements")
def create_stock_movement(payload: StockMovementCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.movement_type not in {movement_type.value for movement_type in StockMovementType}:
        raise HTTPException(422, detail="Neispravan tip skladišnog kretanja")
    ensure_positive(payload.quantity)
    if payload.movement_type in {StockMovementType.adjustment.value, StockMovementType.write_off.value} and not payload.reason:
        raise HTTPException(422, detail="Adjustment i otpis moraju imati razlog")
    movement = StockMovement(**payload.model_dump(), created_by=user.id)
    db.add(movement)
    if payload.batch_id:
        batch = db.get(InventoryBatch, payload.batch_id)
        if not batch:
            raise HTTPException(404, detail="Serija nije pronađena")
        if payload.movement_type in {"consumption", "write_off"}:
            ensure_batch_available(batch, payload.quantity)
            batch.quantity -= payload.quantity
        elif payload.movement_type in {"adjustment", "purchase_receipt"}:
            batch.quantity += payload.quantity
        recalculate_stock(db, payload.inventory_item_id)
    audit(db, "create", "StockMovement", payload.inventory_item_id, payload.movement_type, user.id)
    db.commit()
    db.refresh(movement)
    return movement


@router.post("/inventory/transfer")
def transfer(payload: StockMovementCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not payload.batch_id or not payload.to_location_id:
        raise HTTPException(422, detail="Transfer zahtijeva batch_id i to_location_id")
    batch = db.get(InventoryBatch, payload.batch_id)
    if not batch:
        raise HTTPException(404, detail="Serija nije pronađena")
    movements = transfer_batch(db, batch, payload.to_location_id, payload.quantity, payload.reason, user.id)
    audit(db, "create", "StockMovement", payload.inventory_item_id, "Transfer zalihe", user.id)
    db.commit()
    return {"movements": movements}


@router.post("/inventory/write-off")
def write_off(payload: StockMovementCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload.movement_type = "write_off"
    return create_stock_movement(payload, db, user)


@router.post("/inventory/adjustment")
def adjustment(payload: StockMovementCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payload.movement_type = "adjustment"
    return create_stock_movement(payload, db, user)


@router.get("/suppliers")
def suppliers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Supplier).order_by(Supplier.name)).all()


@router.post("/suppliers")
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.flush()
    audit(db, "create", "Supplier", supplier.id, supplier.name, user.id)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(404, detail="Dobavljač nije pronađen")
    return supplier


@router.patch("/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, payload: SupplierCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(404, detail="Dobavljač nije pronađen")
    update_from_payload(supplier, payload)
    audit(db, "update", "Supplier", supplier.id, supplier.name, user.id)
    db.commit()
    return supplier


@router.get("/purchase-orders")
def purchase_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(PurchaseOrder).options(joinedload(PurchaseOrder.supplier)).order_by(PurchaseOrder.order_date.desc())).all()


@router.post("/purchase-orders")
def create_purchase_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = PurchaseOrder(**payload.model_dump(exclude_none=True))
    db.add(order)
    db.flush()
    audit(db, "create", "PurchaseOrder", order.id, "Nova narudžbenica", user.id)
    db.commit()
    return order


@router.get("/purchase-orders/{order_id}")
def purchase_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, detail="Narudžbenica nije pronađena")
    return order


@router.patch("/purchase-orders/{order_id}")
def update_purchase_order(order_id: int, payload: PurchaseOrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, detail="Narudžbenica nije pronađena")
    update_from_payload(order, payload)
    audit(db, "update", "PurchaseOrder", order.id, "Ažurirana narudžbenica", user.id)
    db.commit()
    return order


@router.post("/purchase-orders/{order_id}/receive")
def receive_purchase_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, detail="Narudžbenica nije pronađena")
    order.status = "received"
    audit(db, "update", "PurchaseOrder", order.id, "Zaprimljena narudžbenica", user.id)
    db.commit()
    return order


@router.get("/procurement/reorder-suggestions")
def reorder_suggestions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.scalars(select(InventoryItem).where(InventoryItem.current_stock <= InventoryItem.reorder_point)).all()
    return [{"item": item, "suggested_quantity": max(item.minimum_stock * 2 - item.current_stock, Decimal("1")), "reason": "Zaliha je ispod točke ponovne narudžbe"} for item in items]


@router.get("/invoices")
def invoices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Invoice).order_by(Invoice.invoice_date.desc())).all()


@router.post("/invoices")
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    invoice = Invoice(**payload.model_dump(exclude_none=True))
    db.add(invoice)
    db.flush()
    audit(db, "create", "Invoice", invoice.id, invoice.invoice_number, user.id)
    db.commit()
    return invoice


@router.get("/invoices/{invoice_id}")
def invoice(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(404, detail="Račun nije pronađen")
    return invoice


@router.patch("/invoices/{invoice_id}")
def update_invoice(invoice_id: int, payload: InvoiceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(404, detail="Račun nije pronađen")
    update_from_payload(invoice, payload)
    audit(db, "update", "Invoice", invoice.id, invoice.invoice_number, user.id)
    db.commit()
    return invoice


@router.post("/invoices/{invoice_id}/mark-paid")
def mark_paid(invoice_id: int, payment_method: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(404, detail="Račun nije pronađen")
    invoice.payment_status = "paid"
    invoice.payment_method = payment_method
    audit(db, "update", "Invoice", invoice.id, "Označeno kao plaćeno", user.id)
    db.commit()
    return invoice


@router.get("/services/{service_id}/materials")
def service_materials(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(ServiceMaterialTemplate).options(joinedload(ServiceMaterialTemplate.item)).where(ServiceMaterialTemplate.service_id == service_id)).all()


@router.post("/services/{service_id}/materials")
def create_service_material(service_id: int, payload: ServiceMaterialCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    template = ServiceMaterialTemplate(service_id=service_id, **payload.model_dump())
    db.add(template)
    db.flush()
    audit(db, "create", "ServiceMaterialTemplate", template.id, "Predložak materijala", user.id)
    db.commit()
    return template


@router.patch("/services/{service_id}/materials/{template_id}")
def update_service_material(service_id: int, template_id: int, payload: ServiceMaterialCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    template = db.get(ServiceMaterialTemplate, template_id)
    if not template or template.service_id != service_id:
        raise HTTPException(404, detail="Predložak nije pronađen")
    update_from_payload(template, payload)
    audit(db, "update", "ServiceMaterialTemplate", template.id, "Ažuriran predložak materijala", user.id)
    db.commit()
    return template


@router.delete("/services/{service_id}/materials/{template_id}")
def delete_service_material(service_id: int, template_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    template = db.get(ServiceMaterialTemplate, template_id)
    if not template or template.service_id != service_id:
        raise HTTPException(404, detail="Predložak nije pronađen")
    db.delete(template)
    audit(db, "delete", "ServiceMaterialTemplate", template_id, "Obrisan predložak materijala", user.id)
    db.commit()
    return {"ok": True}


@router.get("/appointments/{appointment_id}/suggest-material-consumption")
def suggest_material_consumption(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    templates = db.scalars(select(ServiceMaterialTemplate).options(joinedload(ServiceMaterialTemplate.item)).where(ServiceMaterialTemplate.service_id == appointment.service_id)).all()
    return [{"template_id": t.id, "item": t.item, "quantity": t.default_quantity, "required": t.required, "variable_quantity_allowed": t.variable_quantity_allowed} for t in templates]


@router.post("/appointments/{appointment_id}/consume-materials")
def consume_materials(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    templates = db.scalars(select(ServiceMaterialTemplate).where(ServiceMaterialTemplate.service_id == appointment.service_id)).all()
    movements = []
    for template in templates:
        if template.required:
            movements.extend(consume_fefo(db, template.inventory_item_id, template.default_quantity, appointment_id))
    audit(db, "create", "StockMovement", appointment_id, "Automatska potrošnja po terminu", user.id)
    db.commit()
    return {"movements": movements}


@router.post("/appointments/{appointment_id}/complete-with-consumption")
def complete_with_consumption(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronađen")
    consume_materials(appointment_id, db, user)
    appointment.status = "completed"
    audit(db, "update", "Appointment", appointment.id, "Završen termin s potrošnjom materijala", user.id)
    db.commit()
    return appointment
