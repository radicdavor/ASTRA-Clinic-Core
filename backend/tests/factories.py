from datetime import date, time
from decimal import Decimal

from app.models.domain import Appointment, ClinicalDocument, ClinicalEpisode, ClinicalPlan, InventoryBatch, InventoryItem, Patient, Provider, Room, Service, StockLocation


def patient(db, first_name="Test", last_name="Patient"):
    obj = Patient(first_name=first_name, last_name=last_name)
    db.add(obj)
    db.flush()
    return obj


def provider(db, name="dr. Test"):
    obj = Provider(full_name=name, specialty="Test")
    db.add(obj)
    db.flush()
    return obj


def room(db, name="Room 1"):
    obj = Room(name=name, type="test")
    db.add(obj)
    db.flush()
    return obj


def service(db, name="Service", price=Decimal("100")):
    obj = Service(name=name, duration_minutes=30, price=price)
    db.add(obj)
    db.flush()
    return obj


def appointment(db, patient_obj=None, provider_obj=None, room_obj=None, service_obj=None, status="scheduled"):
    patient_obj = patient_obj or patient(db)
    provider_obj = provider_obj or provider(db)
    room_obj = room_obj or room(db)
    service_obj = service_obj or service(db)
    obj = Appointment(
        patient_id=patient_obj.id,
        provider_id=provider_obj.id,
        room_id=room_obj.id,
        service_id=service_obj.id,
        date=date(2026, 7, 5),
        start_time=time(9, 0),
        end_time=time(9, 30),
        duration_minutes=30,
        status=status,
    )
    db.add(obj)
    db.flush()
    return obj


def episode(db, patient_obj=None, provider_obj=None, title="Test episode"):
    patient_obj = patient_obj or patient(db)
    provider_obj = provider_obj or provider(db)
    obj = ClinicalEpisode(
        patient_id=patient_obj.id,
        title=title,
        episode_type="general",
        status="active",
        priority="routine",
        start_date=date(2026, 7, 5),
        owner_provider_id=provider_obj.id,
    )
    db.add(obj)
    db.flush()
    return obj


def clinical_plan(db, episode_obj=None, status="draft", physician_confirmed=False):
    episode_obj = episode_obj or episode(db)
    obj = ClinicalPlan(
        episode_id=episode_obj.id,
        source="ai_suggestion",
        status=status,
        proposed_episode_status="waiting",
        next_action="wait_for_pathology",
        due_date=date(2026, 7, 20),
        priority="important",
        rationale="Test plan",
        suggested_follow_up="Test follow up",
        physician_conclusion="Test physician conclusion",
        ai_confidence=Decimal("0.91"),
        physician_confirmed=physician_confirmed,
    )
    db.add(obj)
    db.flush()
    return obj


def clinical_document(db, patient_obj=None, physician_reviewed=True):
    patient_obj = patient_obj or patient(db)
    obj = ClinicalDocument(
        patient_id=patient_obj.id,
        source_type="external",
        document_type="gastroscopy",
        origin="Test institution",
        document_date=date(2026, 7, 5),
        title="Test gastroscopy",
        raw_text="GERB refluks. H. pylori negativan. Esomeprazol terapija.",
        ai_summary="Reviewed test summary",
        key_findings=["GERB/refluks naveden u dokumentu", "H. pylori status naveden u dokumentu"],
        recommendations=["Kontrola prema odluci lijecnika"],
        physician_reviewed=physician_reviewed,
    )
    db.add(obj)
    db.flush()
    return obj


def stock_item_with_batch(db, sku="ITEM", quantity=Decimal("5"), lot_tracking=False, expiration_tracking=False):
    item = InventoryItem(sku=sku, name=sku, lot_tracking_enabled=lot_tracking, expiration_tracking_enabled=expiration_tracking)
    location = StockLocation(name=f"{sku} location", type="test")
    db.add_all([item, location])
    db.flush()
    batch = InventoryBatch(inventory_item_id=item.id, quantity=quantity, location_id=location.id, lot_number="LOT" if lot_tracking else None)
    db.add(batch)
    db.flush()
    return item, batch, location
