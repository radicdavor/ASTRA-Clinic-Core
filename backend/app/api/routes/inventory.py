from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.audit.service import audit, snapshot
from app.auth.dependencies import Actor, require_permission
from app.core.database import get_db
from app.models.domain import (
    Appointment,
    InventoryBatch,
    InventoryItem,
    Invoice,
    InvoiceLine,
    PaymentTransaction,
    PurchaseOrder,
    PurchaseOrderLine,
    ServiceMaterialTemplate,
    StockLocation,
    StockMovement,
    StockMovementType,
    Supplier,
)
from app.schemas.common import (
    AppointmentMaterialConsumptionRequest,
    InventoryBatchCreate,
    InventoryBatchOut,
    InventoryItemCreate,
    InventoryItemOut,
    InvoiceCreate,
    InvoiceLineCreate,
    InvoiceIssueOut,
    InvoiceLineOut,
    InvoiceLineUpdate,
    InvoiceOut,
    PaymentTransactionCreate,
    PaymentTransactionOut,
    PurchaseOrderCreate,
    PurchaseOrderLineCreate,
    PurchaseOrderLineOut,
    PurchaseOrderLineUpdate,
    PurchaseOrderOut,
    PurchaseOrderReceiveRequest,
    ServiceMaterialCreate,
    StockMovementCreate,
    StockMovementOut,
    SupplierCreate,
    SupplierOut,
)
from app.services.inventory import (
    ensure_batch_available,
    ensure_positive,
    expiring_batches,
    recalculate_all_stock,
    recalculate_stock,
    transfer_batch,
)
from app.services.appointment_materials import consume_appointment_materials
from app.services.billing import (
    add_invoice_line,
    delete_invoice_line as delete_invoice_line_service,
    draft_invoice_number,
    draft_invoice_from_appointment as draft_invoice_from_appointment_service,
    issue_invoice,
    load_invoice,
    mark_invoice_paid,
    record_payment,
    update_invoice_line as update_invoice_line_service,
)
from app.services.procurement import (
    receive_purchase_order as receive_purchase_order_service,
    recalculate_purchase_order_total,
)

router = APIRouter(prefix="/api", tags=["inventory"])


def update_from_payload(obj, payload) -> None:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)


def audit_actor(db: Session, action: str, entity_type: str, entity_id: int | None, summary: str, actor: Actor, request: Request, before=None, after=None) -> None:
    audit(db, action, entity_type, entity_id, summary, actor.user_id, actor.actor_type, actor.api_key_id, before, after, request)


@router.get("/inventory/items", response_model=list[InventoryItemOut])
def inventory_items(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.read"))):
    return db.scalars(select(InventoryItem).order_by(InventoryItem.name)).all()


@router.post("/inventory/items", response_model=InventoryItemOut)
def create_inventory_item(payload: InventoryItemCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.write"))):
    item = InventoryItem(**payload.model_dump())
    db.add(item)
    db.flush()
    audit_actor(db, "create", "InventoryItem", item.id, item.name, actor, request, None, snapshot(item))
    db.commit()
    db.refresh(item)
    return item


@router.get("/inventory/items/{item_id}", response_model=InventoryItemOut)
def get_inventory_item(item_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.read"))):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, detail="Artikl nije pronaden")
    return item


@router.patch("/inventory/items/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(item_id: int, payload: InventoryItemCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.write"))):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, detail="Artikl nije pronaden")
    before = snapshot(item)
    update_from_payload(item, payload)
    db.flush()
    audit_actor(db, "update", "InventoryItem", item.id, item.name, actor, request, before, snapshot(item))
    db.commit()
    db.refresh(item)
    return item


@router.get("/inventory/low-stock", response_model=list[InventoryItemOut])
def low_stock(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.read"))):
    return db.scalars(select(InventoryItem).where(InventoryItem.current_stock <= InventoryItem.reorder_point).order_by(InventoryItem.current_stock)).all()


@router.get("/inventory/expiring", response_model=list[InventoryBatchOut])
def expiring(days: int = 30, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.read"))):
    return expiring_batches(db, days)


@router.get("/inventory/batches", response_model=list[InventoryBatchOut])
def batches(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.read"))):
    return db.scalars(select(InventoryBatch).options(joinedload(InventoryBatch.item), joinedload(InventoryBatch.location)).order_by(InventoryBatch.expiration_date)).all()


@router.post("/inventory/batches", response_model=InventoryBatchOut)
def create_batch(payload: InventoryBatchCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.write"))):
    ensure_positive(payload.quantity)
    item = db.get(InventoryItem, payload.inventory_item_id)
    if not item:
        raise HTTPException(404, detail="Artikl nije pronaden")
    if item.lot_tracking_enabled and not payload.lot_number:
        raise HTTPException(422, detail="LOT broj je obavezan za ovaj artikl")
    if item.expiration_tracking_enabled and not payload.expiration_date:
        raise HTTPException(422, detail="Rok trajanja je obavezan za ovaj artikl")
    batch = InventoryBatch(**payload.model_dump())
    db.add(batch)
    db.flush()
    movement = StockMovement(inventory_item_id=batch.inventory_item_id, batch_id=batch.id, to_location_id=batch.location_id, quantity=batch.quantity, movement_type=StockMovementType.purchase_receipt.value, reason="Ulaz robe", created_by=actor.user_id)
    db.add(movement)
    recalculate_stock(db, batch.inventory_item_id)
    db.flush()
    audit_actor(db, "create", "InventoryBatch", batch.id, "Nova serija zalihe", actor, request, None, snapshot(batch))
    audit_actor(db, "create", "StockMovement", movement.id, "Ulaz robe", actor, request, None, snapshot(movement))
    db.commit()
    db.refresh(batch)
    return batch


@router.post("/inventory/recalculate-stock")
def recalculate_stock_endpoint(request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.adjust"))):
    recalculate_all_stock(db)
    audit_actor(db, "update", "InventoryItem", None, "Recalculate stock cache", actor, request)
    db.commit()
    return {"ok": True}


@router.get("/inventory/stock-locations")
def stock_locations(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.read"))):
    return db.scalars(select(StockLocation).order_by(StockLocation.name)).all()


@router.get("/inventory/stock-movements", response_model=list[StockMovementOut])
def stock_movements(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.read"))):
    return db.scalars(select(StockMovement).options(joinedload(StockMovement.item)).order_by(StockMovement.created_at.desc()).limit(200)).all()


@router.post("/inventory/stock-movements", response_model=StockMovementOut)
def create_stock_movement(payload: StockMovementCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.adjust"))):
    if payload.movement_type not in {movement_type.value for movement_type in StockMovementType}:
        raise HTTPException(422, detail="Neispravan tip skladisnog kretanja")
    if payload.movement_type == StockMovementType.write_off.value and "inventory.write_off" not in actor.permissions:
        raise HTTPException(403, detail="Nedostaje dozvola: inventory.write_off")
    if payload.movement_type == StockMovementType.transfer_out.value and "inventory.transfer" not in actor.permissions:
        raise HTTPException(403, detail="Nedostaje dozvola: inventory.transfer")
    ensure_positive(payload.quantity)
    if payload.movement_type in {StockMovementType.adjustment.value, StockMovementType.write_off.value} and not payload.reason:
        raise HTTPException(422, detail="Korekcija i otpis moraju imati razlog")
    movement = StockMovement(**payload.model_dump(), created_by=actor.user_id)
    db.add(movement)
    if payload.batch_id:
        batch = db.get(InventoryBatch, payload.batch_id)
        if not batch:
            raise HTTPException(404, detail="Serija nije pronadena")
        if batch.inventory_item_id != payload.inventory_item_id:
            raise HTTPException(422, detail="Serija ne pripada artiklu")
        before = snapshot(batch)
        if payload.movement_type in {StockMovementType.consumption.value, StockMovementType.write_off.value}:
            ensure_batch_available(batch, payload.quantity)
            batch.quantity -= payload.quantity
        elif payload.movement_type in {StockMovementType.adjustment.value, StockMovementType.purchase_receipt.value}:
            batch.quantity += payload.quantity
        else:
            raise HTTPException(422, detail="Za transfer koristite /api/inventory/transfer")
        recalculate_stock(db, payload.inventory_item_id)
        db.flush()
        audit_actor(db, "update", "InventoryBatch", batch.id, payload.movement_type, actor, request, before, snapshot(batch))
    db.flush()
    audit_actor(db, "create", "StockMovement", movement.id, payload.movement_type, actor, request, None, snapshot(movement))
    db.commit()
    db.refresh(movement)
    return movement


@router.post("/inventory/transfer")
def transfer(payload: StockMovementCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.transfer"))):
    if not payload.batch_id or not payload.to_location_id:
        raise HTTPException(422, detail="Transfer zahtijeva batch_id i to_location_id")
    batch = db.get(InventoryBatch, payload.batch_id)
    if not batch:
        raise HTTPException(404, detail="Serija nije pronadena")
    before = snapshot(batch)
    movements = transfer_batch(db, batch, payload.to_location_id, payload.quantity, payload.reason, actor.user_id)
    db.flush()
    audit_actor(db, "update", "InventoryBatch", batch.id, "Transfer zalihe", actor, request, before, snapshot(batch))
    for movement in movements:
        audit_actor(db, "create", "StockMovement", movement.id, "Transfer zalihe", actor, request, None, snapshot(movement))
    db.commit()
    return {"movements": movements}


@router.post("/inventory/write-off", response_model=StockMovementOut)
def write_off(payload: StockMovementCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.write_off"))):
    payload.movement_type = StockMovementType.write_off.value
    return create_stock_movement(payload, request, db, actor)


@router.post("/inventory/adjustment", response_model=StockMovementOut)
def adjustment(payload: StockMovementCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.adjust"))):
    payload.movement_type = StockMovementType.adjustment.value
    return create_stock_movement(payload, request, db, actor)


@router.get("/suppliers", response_model=list[SupplierOut])
def suppliers(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.read"))):
    return db.scalars(select(Supplier).order_by(Supplier.name)).all()


@router.post("/suppliers", response_model=SupplierOut)
def create_supplier(payload: SupplierCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.write"))):
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.flush()
    audit_actor(db, "create", "Supplier", supplier.id, supplier.name, actor, request, None, snapshot(supplier))
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers/{supplier_id}", response_model=SupplierOut)
def get_supplier(supplier_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.read"))):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(404, detail="Dobavljac nije pronaden")
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, payload: SupplierCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.write"))):
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(404, detail="Dobavljac nije pronaden")
    before = snapshot(supplier)
    update_from_payload(supplier, payload)
    db.flush()
    audit_actor(db, "update", "Supplier", supplier.id, supplier.name, actor, request, before, snapshot(supplier))
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/purchase-orders", response_model=list[PurchaseOrderOut])
def purchase_orders(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.read"))):
    return db.scalars(select(PurchaseOrder).options(selectinload(PurchaseOrder.lines), joinedload(PurchaseOrder.supplier)).order_by(PurchaseOrder.order_date.desc())).all()


@router.post("/purchase-orders", response_model=PurchaseOrderOut)
def create_purchase_order(payload: PurchaseOrderCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.write"))):
    order = PurchaseOrder(**payload.model_dump(exclude_none=True))
    db.add(order)
    db.flush()
    audit_actor(db, "create", "PurchaseOrder", order.id, "Nova narudzbenica", actor, request, None, snapshot(order))
    db.commit()
    return order


@router.get("/purchase-orders/{order_id}", response_model=PurchaseOrderOut)
def purchase_order(order_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.read"))):
    order = db.scalar(select(PurchaseOrder).options(selectinload(PurchaseOrder.lines)).where(PurchaseOrder.id == order_id))
    if not order:
        raise HTTPException(404, detail="Narudzbenica nije pronadena")
    return order


@router.patch("/purchase-orders/{order_id}", response_model=PurchaseOrderOut)
def update_purchase_order(order_id: int, payload: PurchaseOrderCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.write"))):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, detail="Narudzbenica nije pronadena")
    before = snapshot(order)
    update_from_payload(order, payload)
    db.flush()
    audit_actor(db, "update", "PurchaseOrder", order.id, "Azurirana narudzbenica", actor, request, before, snapshot(order))
    db.commit()
    return order


@router.get("/purchase-orders/{order_id}/lines", response_model=list[PurchaseOrderLineOut])
def purchase_order_lines(order_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.read"))):
    return db.scalars(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == order_id).order_by(PurchaseOrderLine.id)).all()


@router.post("/purchase-orders/{order_id}/lines", response_model=PurchaseOrderLineOut)
def create_purchase_order_line(order_id: int, payload: PurchaseOrderLineCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.write"))):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, detail="Narudzbenica nije pronadena")
    ensure_positive(payload.quantity_ordered)
    line = PurchaseOrderLine(purchase_order_id=order_id, **payload.model_dump())
    db.add(line)
    db.flush()
    recalculate_purchase_order_total(order)
    audit_actor(db, "create", "PurchaseOrderLine", line.id, "Dodana stavka narudzbenice", actor, request, None, snapshot(line))
    db.commit()
    return line


@router.patch("/purchase-orders/{order_id}/lines/{line_id}", response_model=PurchaseOrderLineOut)
def update_purchase_order_line(order_id: int, line_id: int, payload: PurchaseOrderLineUpdate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.write"))):
    line = db.get(PurchaseOrderLine, line_id)
    if not line or line.purchase_order_id != order_id:
        raise HTTPException(404, detail="Stavka narudzbenice nije pronadena")
    before = snapshot(line)
    update_from_payload(line, payload)
    ensure_positive(line.quantity_ordered)
    order = db.get(PurchaseOrder, order_id)
    recalculate_purchase_order_total(order)
    db.flush()
    audit_actor(db, "update", "PurchaseOrderLine", line.id, "Azurirana stavka narudzbenice", actor, request, before, snapshot(line))
    db.commit()
    return line


@router.delete("/purchase-orders/{order_id}/lines/{line_id}")
def delete_purchase_order_line(order_id: int, line_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.write"))):
    line = db.get(PurchaseOrderLine, line_id)
    if not line or line.purchase_order_id != order_id:
        raise HTTPException(404, detail="Stavka narudzbenice nije pronadena")
    if line.quantity_received > 0:
        raise HTTPException(409, detail="Zaprimljena stavka se ne moze obrisati")
    before = snapshot(line)
    order = db.get(PurchaseOrder, order_id)
    db.delete(line)
    db.flush()
    recalculate_purchase_order_total(order)
    audit_actor(db, "delete", "PurchaseOrderLine", line_id, "Obrisana stavka narudzbenice", actor, request, before, None)
    db.commit()
    return {"ok": True}


@router.post("/purchase-orders/{order_id}/receive", response_model=PurchaseOrderOut)
def receive_purchase_order(order_id: int, payload: PurchaseOrderReceiveRequest, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.write"))):
    order = db.scalar(select(PurchaseOrder).options(selectinload(PurchaseOrder.lines)).where(PurchaseOrder.id == order_id))
    if not order:
        raise HTTPException(404, detail="Narudzbenica nije pronadena")
    before_order = snapshot(order)
    before_lines: dict[int, dict] = {}
    for receive_line in payload.lines:
        line = db.get(PurchaseOrderLine, receive_line.purchase_order_line_id)
        if line:
            before_lines[line.id] = snapshot(line)
    received = receive_purchase_order_service(db, order, payload, actor.user_id)
    db.flush()
    for line, batch, movement in received:
        before_line = snapshot(line)
        audit_actor(db, "update", "PurchaseOrderLine", line.id, "Zaprimljena stavka narudzbenice", actor, request, before_lines.get(line.id, before_line), snapshot(line))
        audit_actor(db, "create", "InventoryBatch", batch.id, "Zaprimanje narudzbenice", actor, request, None, snapshot(batch))
        audit_actor(db, "create", "StockMovement", movement.id, "Zaprimanje narudzbenice", actor, request, None, snapshot(movement))
    db.flush()
    audit_actor(db, "update", "PurchaseOrder", order.id, "Zaprimljena narudzbenica", actor, request, before_order, snapshot(order))
    db.commit()
    db.refresh(order)
    return order


@router.get("/procurement/reorder-suggestions")
def reorder_suggestions(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("procurement.read"))):
    items = db.scalars(select(InventoryItem).where(InventoryItem.current_stock <= InventoryItem.reorder_point)).all()
    return [{"item": item, "suggested_quantity": max(item.minimum_stock * 2 - item.current_stock, Decimal("1")), "reason": "Zaliha je ispod tocke ponovne narudzbe"} for item in items]


@router.get("/invoices", response_model=list[InvoiceOut])
def invoices(db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.read"))):
    return db.scalars(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).order_by(Invoice.invoice_date.desc())).all()


@router.post("/invoices", response_model=InvoiceOut)
def create_invoice(payload: InvoiceCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.write"))):
    data = payload.model_dump(exclude_none=True)
    data["invoice_number"] = draft_invoice_number()
    invoice = Invoice(**data)
    db.add(invoice)
    db.flush()
    audit_actor(db, "create", "Invoice", invoice.id, invoice.invoice_number, actor, request, None, snapshot(invoice))
    db.commit()
    return invoice


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def invoice(invoice_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.read"))):
    invoice_obj = db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    if not invoice_obj:
        raise HTTPException(404, detail="Racun nije pronaden")
    return invoice_obj


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
def update_invoice(invoice_id: int, payload: InvoiceCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.write"))):
    invoice_obj = db.get(Invoice, invoice_id)
    if not invoice_obj:
        raise HTTPException(404, detail="Racun nije pronaden")
    if invoice_obj.status != "draft":
        allowed = {"notes", "operator", "business_unit", "register_id", "vat_id", "fiscalization_status", "fiscalization_reference"}
        requested = set(payload.model_dump(exclude_unset=True).keys())
        if requested - allowed:
            raise HTTPException(409, detail="Izdani, placeni ili stornirani racun ne dopusta izmjenu zasticenih polja")
    before = snapshot(invoice_obj)
    update_from_payload(invoice_obj, payload)
    db.flush()
    audit_actor(db, "update", "Invoice", invoice_obj.id, invoice_obj.invoice_number, actor, request, before, snapshot(invoice_obj))
    db.commit()
    return invoice_obj


@router.post("/appointments/{appointment_id}/draft-invoice", response_model=InvoiceOut)
def draft_invoice_from_appointment(appointment_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.write"))):
    invoice_obj, line, created = draft_invoice_from_appointment_service(db, appointment_id)
    if not created:
        return invoice_obj
    audit_actor(db, "create", "Invoice", invoice_obj.id, "Nacrt racuna iz termina", actor, request, None, snapshot(invoice_obj))
    if line:
        audit_actor(db, "create", "InvoiceLine", line.id, "Stavka usluge iz termina", actor, request, None, snapshot(line))
    db.commit()
    return db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_obj.id))


@router.post("/invoices/{invoice_id}/issue", response_model=InvoiceIssueOut)
def issue_invoice_endpoint(invoice_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.write"))):
    invoice_obj = load_invoice(db, invoice_id)
    if not invoice_obj:
        raise HTTPException(404, detail="Racun nije pronaden")
    before = snapshot(invoice_obj)
    issue_invoice(db, invoice_obj)
    db.flush()
    audit_actor(db, "update", "Invoice", invoice_obj.id, "Izdan racun", actor, request, before, snapshot(invoice_obj))
    db.commit()
    return load_invoice(db, invoice_id)


@router.get("/invoices/{invoice_id}/lines", response_model=list[InvoiceLineOut])
def invoice_lines(invoice_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.read"))):
    return db.scalars(select(InvoiceLine).where(InvoiceLine.invoice_id == invoice_id).order_by(InvoiceLine.id)).all()


@router.post("/invoices/{invoice_id}/lines", response_model=InvoiceLineOut)
def create_invoice_line(invoice_id: int, payload: InvoiceLineCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.write"))):
    invoice_obj = db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    if not invoice_obj:
        raise HTTPException(404, detail="Racun nije pronaden")
    before = snapshot(invoice_obj)
    line = add_invoice_line(invoice_obj, payload)
    db.add(line)
    db.flush()
    audit_actor(db, "create", "InvoiceLine", line.id, "Dodana stavka racuna", actor, request, None, snapshot(line))
    audit_actor(db, "update", "Invoice", invoice_obj.id, "Preracunat racun", actor, request, before, snapshot(invoice_obj))
    db.commit()
    return line


@router.patch("/invoices/{invoice_id}/lines/{line_id}", response_model=InvoiceLineOut)
def update_invoice_line(invoice_id: int, line_id: int, payload: InvoiceLineUpdate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.write"))):
    invoice_obj = db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    line = db.get(InvoiceLine, line_id)
    if not invoice_obj or not line or line.invoice_id != invoice_id:
        raise HTTPException(404, detail="Stavka racuna nije pronadena")
    before = snapshot(line)
    before_invoice = snapshot(invoice_obj)
    update_invoice_line_service(invoice_obj, line, payload)
    db.flush()
    audit_actor(db, "update", "InvoiceLine", line.id, "Azurirana stavka racuna", actor, request, before, snapshot(line))
    audit_actor(db, "update", "Invoice", invoice_obj.id, "Preracunat racun", actor, request, before_invoice, snapshot(invoice_obj))
    db.commit()
    return line


@router.delete("/invoices/{invoice_id}/lines/{line_id}")
def delete_invoice_line(invoice_id: int, line_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.write"))):
    invoice_obj = db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    line = db.get(InvoiceLine, line_id)
    if not invoice_obj or not line or line.invoice_id != invoice_id:
        raise HTTPException(404, detail="Stavka racuna nije pronadena")
    before = snapshot(line)
    before_invoice = snapshot(invoice_obj)
    delete_invoice_line_service(invoice_obj, line)
    db.delete(line)
    db.flush()
    audit_actor(db, "delete", "InvoiceLine", line_id, "Obrisana stavka racuna", actor, request, before, None)
    audit_actor(db, "update", "Invoice", invoice_obj.id, "Preracunat racun", actor, request, before_invoice, snapshot(invoice_obj))
    db.commit()
    return {"ok": True}


@router.post("/invoices/{invoice_id}/payments", response_model=PaymentTransactionOut)
def create_payment(invoice_id: int, payload: PaymentTransactionCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.mark_paid"))):
    invoice_obj = db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    if not invoice_obj:
        raise HTTPException(404, detail="Racun nije pronaden")
    before = snapshot(invoice_obj)
    payment = record_payment(invoice_obj, payload, actor.user_id)
    db.add(payment)
    db.flush()
    audit_actor(db, "create", "PaymentTransaction", payment.id, "Evidentirano placanje", actor, request, None, snapshot(payment))
    audit_actor(db, "update", "Invoice", invoice_obj.id, "Azuriran status placanja", actor, request, before, snapshot(invoice_obj))
    db.commit()
    return payment


@router.get("/invoices/{invoice_id}/payments", response_model=list[PaymentTransactionOut])
def invoice_payments(invoice_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.read"))):
    return db.scalars(select(PaymentTransaction).where(PaymentTransaction.invoice_id == invoice_id).order_by(PaymentTransaction.paid_at)).all()


@router.post("/invoices/{invoice_id}/mark-paid", response_model=InvoiceOut)
def mark_paid(invoice_id: int, request: Request, payment_method: str | None = None, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("billing.mark_paid"))):
    invoice_obj = db.scalar(select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.payments)).where(Invoice.id == invoice_id))
    if not invoice_obj:
        raise HTTPException(404, detail="Racun nije pronaden")
    before = snapshot(invoice_obj)
    payment = mark_invoice_paid(invoice_obj, payment_method, actor.user_id)
    if payment:
        db.add(payment)
        db.flush()
        audit_actor(db, "create", "PaymentTransaction", payment.id, "Evidentirano placanje", actor, request, None, snapshot(payment))
    audit_actor(db, "update", "Invoice", invoice_obj.id, "Oznaceno kao placeno", actor, request, before, snapshot(invoice_obj))
    db.commit()
    return load_invoice(db, invoice_id)


@router.get("/services/{service_id}/materials")
def service_materials(service_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.read"))):
    return db.scalars(select(ServiceMaterialTemplate).options(joinedload(ServiceMaterialTemplate.item)).where(ServiceMaterialTemplate.service_id == service_id)).all()


@router.post("/services/{service_id}/materials")
def create_service_material(service_id: int, payload: ServiceMaterialCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.write"))):
    template = ServiceMaterialTemplate(service_id=service_id, **payload.model_dump())
    db.add(template)
    db.flush()
    audit_actor(db, "create", "ServiceMaterialTemplate", template.id, "Predlozak materijala", actor, request, None, snapshot(template))
    db.commit()
    return template


@router.patch("/services/{service_id}/materials/{template_id}")
def update_service_material(service_id: int, template_id: int, payload: ServiceMaterialCreate, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.write"))):
    template = db.get(ServiceMaterialTemplate, template_id)
    if not template or template.service_id != service_id:
        raise HTTPException(404, detail="Predlozak nije pronaden")
    before = snapshot(template)
    update_from_payload(template, payload)
    db.flush()
    audit_actor(db, "update", "ServiceMaterialTemplate", template.id, "Azuriran predlozak materijala", actor, request, before, snapshot(template))
    db.commit()
    return template


@router.delete("/services/{service_id}/materials/{template_id}")
def delete_service_material(service_id: int, template_id: int, request: Request, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("services.write"))):
    template = db.get(ServiceMaterialTemplate, template_id)
    if not template or template.service_id != service_id:
        raise HTTPException(404, detail="Predlozak nije pronaden")
    before = snapshot(template)
    db.delete(template)
    audit_actor(db, "delete", "ServiceMaterialTemplate", template_id, "Obrisan predlozak materijala", actor, request, before, None)
    db.commit()
    return {"ok": True}


@router.get("/appointments/{appointment_id}/suggest-material-consumption")
def suggest_material_consumption(appointment_id: int, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.read"))):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronaden")
    templates = db.scalars(select(ServiceMaterialTemplate).options(joinedload(ServiceMaterialTemplate.item)).where(ServiceMaterialTemplate.service_id == appointment.service_id)).all()
    result = []
    for template in templates:
        available = sum(batch.quantity for batch in db.scalars(select(InventoryBatch).where(InventoryBatch.inventory_item_id == template.inventory_item_id)))
        result.append({
            "template_id": template.id,
            "item": template.item,
            "quantity": template.default_quantity,
            "required": template.required,
            "variable_quantity_allowed": template.variable_quantity_allowed,
            "auto_consumable": template.required and not template.variable_quantity_allowed,
            "requires_user_quantity": template.required and template.variable_quantity_allowed,
            "optional": not template.required,
            "available_stock": available,
            "warning": "Nedovoljna zaliha" if template.required and available < template.default_quantity else None,
            "warnings": ["Nedovoljna zaliha"] if template.required and available < template.default_quantity else [],
        })
    return result


@router.post("/appointments/{appointment_id}/consume-materials")
def consume_materials(appointment_id: int, request: Request, payload: AppointmentMaterialConsumptionRequest | None = None, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("inventory.write"))):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronaden")
    movements = consume_appointment_materials(db, appointment, payload, actor, request)
    db.commit()
    return {"movements": movements}


@router.post("/appointments/{appointment_id}/complete-with-consumption")
def complete_with_consumption(appointment_id: int, request: Request, payload: AppointmentMaterialConsumptionRequest | None = None, db: Session = Depends(get_db), actor: Actor = Depends(require_permission("appointments.write"))):
    if "inventory.write" not in actor.permissions:
        raise HTTPException(403, detail="Nedostaje dozvola: inventory.write")
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(404, detail="Termin nije pronaden")
    before = snapshot(appointment)
    consume_appointment_materials(db, appointment, payload, actor, request)
    appointment.status = "completed"
    db.flush()
    audit_actor(db, "update", "Appointment", appointment.id, "Zavrsen termin s potrosnjom materijala", actor, request, before, snapshot(appointment))
    db.commit()
    return appointment
