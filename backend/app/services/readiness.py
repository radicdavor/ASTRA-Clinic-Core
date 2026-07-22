from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.domain import ApiKey, Appointment, AuditLog, ClinicalDocument, ClinicalEpisode, Institution, InventoryBatch, InventoryItem, Invoice, Module, Patient, PatientClinicalSummaryRecord, Provider, Room, Service, room_services
from app.schemas.common import ReadinessCheck
from app.services.patient_knowledge import DOCUMENT_REVIEW_AWAITING_STATUSES, official_patient_documents_statement


def scalar_count(db: Session, stmt) -> int:
    return int(db.scalar(stmt) or 0)


def build_operational_readiness(db: Session) -> dict:
    settings = get_settings()
    today = date.today()
    critical = "critical"
    warning = "warning"
    ok = "ok"

    patient_count = scalar_count(db, select(func.count(Patient.id)))
    provider_count = scalar_count(db, select(func.count(Provider.id)).where(Provider.active.is_(True)))
    room_count = scalar_count(db, select(func.count(Room.id)).where(Room.active.is_(True)))
    service_count = scalar_count(db, select(func.count(Service.id)).where(Service.active.is_(True)))
    module_count = scalar_count(db, select(func.count(Module.id)).where(Module.enabled.is_(True)))
    audit_count = scalar_count(db, select(func.count(AuditLog.id)))
    active_api_keys = scalar_count(db, select(func.count(ApiKey.id)).where(ApiKey.active.is_(True)))
    low_stock_count = scalar_count(db, select(func.count(InventoryItem.id)).where(InventoryItem.active.is_(True), InventoryItem.current_stock <= InventoryItem.reorder_point))
    expiring_count = scalar_count(db, select(func.count(InventoryBatch.id)).where(InventoryBatch.quantity > 0, InventoryBatch.expiration_date.is_not(None), InventoryBatch.expiration_date <= today + timedelta(days=30)))
    draft_invoice_count = scalar_count(db, select(func.count(Invoice.id)).where(Invoice.status == "draft"))
    unpaid_invoice_count = scalar_count(db, select(func.count(Invoice.id)).where(Invoice.status != "draft", Invoice.payment_status != "paid"))
    episode_count = scalar_count(db, select(func.count(ClinicalEpisode.id)))
    appointments_without_episode = scalar_count(db, select(func.count(Appointment.id)).where(Appointment.episode_id.is_(None)))
    documents_awaiting_review = scalar_count(
        db,
        select(func.count(ClinicalDocument.id)).where(
            ClinicalDocument.institution_id.is_not(None),
            ClinicalDocument.review_status.in_(DOCUMENT_REVIEW_AWAITING_STATUSES),
        ),
    )
    rooms_without_services = scalar_count(db, select(func.count(Room.id)).where(Room.active.is_(True), ~Room.id.in_(select(room_services.c.room_id))))
    services_without_rooms = scalar_count(db, select(func.count(Service.id)).where(Service.active.is_(True), ~Service.id.in_(select(room_services.c.service_id))))
    providers_without_clinic = scalar_count(db, select(func.count(Provider.id)).where(Provider.active.is_(True), Provider.clinic_id.is_(None)))
    today_incomplete_appointments = scalar_count(db, select(func.count(Appointment.id)).where(Appointment.date == today, or_(Appointment.provider_id.is_(None), Appointment.room_id.is_(None), Appointment.service_id.is_(None))))
    institution_ids = set(db.scalars(select(Institution.id).where(Institution.active.is_(True))).all())
    reviewed_documents = db.scalars(official_patient_documents_statement(institution_ids)).all()
    reviewed_summaries = db.scalars(
        select(PatientClinicalSummaryRecord)
        .where(PatientClinicalSummaryRecord.status == "reviewed")
        .order_by(PatientClinicalSummaryRecord.patient_id, PatientClinicalSummaryRecord.updated_at.desc(), PatientClinicalSummaryRecord.id.desc())
    ).all()
    reviewed_summaries_by_patient: dict[int, list[PatientClinicalSummaryRecord]] = {}
    for summary in reviewed_summaries:
        reviewed_summaries_by_patient.setdefault(summary.patient_id, []).append(summary)
    stale_summary_patients = {
        document.patient_id
        for document in reviewed_documents
        if not any(
            document.id in {
                source_id
                for source_id in (summary.source_document_ids or [])
                if isinstance(source_id, int) and not isinstance(source_id, bool)
            }
            and (document.updated_at is None or (summary.updated_at is not None and summary.updated_at >= document.updated_at))
            for summary in reviewed_summaries_by_patient.get(document.patient_id, [])
        )
    }

    checks = [
        ReadinessCheck(
            key="demo_guardrail",
            label="Demo sigurnost",
            status=ok if settings.demo_mode and not settings.real_data_allowed else critical,
            message="Demo nacin je ukljucen i stvarni podaci nisu dopusteni." if settings.demo_mode and not settings.real_data_allowed else "Provjerite postavke demo/real-data zastite prije nastavka.",
            action="Ne unositi stvarne podatke pacijenata dok real-data readiness nije odobren.",
            target_path="/readiness",
            target_label="Otvori spremnost",
            decision_impact="none" if settings.demo_mode and not settings.real_data_allowed else "blocks_demo",
            severity_reason="Realni podaci moraju ostati blokirani u demo/pilot okruzenju.",
        ),
        ReadinessCheck(
            key="fiscalization",
            label="Fiskalizacija",
            status=warning if settings.fiscalization_mode == "noop" else ok,
            message="Aktivna je demo/noop fiskalizacija." if settings.fiscalization_mode == "noop" else "Fiskalizacijski provider nije noop.",
            action="Ne koristiti za stvarnu hrvatsku fiskalizaciju dok provider nije odobren." if settings.fiscalization_mode == "noop" else None,
            target_path="/invoices",
            target_label="Otvori racune",
            decision_impact="review" if settings.fiscalization_mode == "noop" else "none",
            severity_reason="Noop fiskalizacija je prihvatljiva za demo samo ako je jasno oznacena.",
        ),
        ReadinessCheck(key="patients", label="Pacijenti", status=ok if patient_count > 0 else warning, message="Demo pacijenti su dostupni." if patient_count > 0 else "Nema pacijenata za pilot prolaz.", count=patient_count, target_path="/patients", target_label="Otvori pacijente", decision_impact="review" if patient_count == 0 else "none", severity_reason="Pilot treba barem jednog demo pacijenta za prolaz kroz workspace." if patient_count == 0 else None),
        ReadinessCheck(key="providers", label="Lijecnici", status=ok if provider_count > 0 else critical, message="Aktivan lijecnik je dostupan." if provider_count > 0 else "Nema aktivnog lijecnika za termine.", count=provider_count, target_path="/appointments/new", target_label="Otvori termin", decision_impact="blocks_demo" if provider_count == 0 else "none", severity_reason="Termin se ne moze sigurno kreirati bez aktivnog lijecnika." if provider_count == 0 else None),
        ReadinessCheck(key="rooms", label="Sobe", status=ok if room_count > 0 else critical, message="Aktivna soba je dostupna." if room_count > 0 else "Nema aktivne sobe za termine.", count=room_count, target_path="/appointments/new", target_label="Otvori termin", decision_impact="blocks_demo" if room_count == 0 else "none", severity_reason="Termin se ne moze sigurno kreirati bez aktivne sobe." if room_count == 0 else None),
        ReadinessCheck(key="services", label="Usluge", status=ok if service_count > 0 else critical, message="Aktivne usluge su dostupne." if service_count > 0 else "Nema aktivnih usluga.", count=service_count, target_path="/services", target_label="Otvori usluge", decision_impact="blocks_demo" if service_count == 0 else "none", severity_reason="Termin i racun trebaju aktivnu uslugu." if service_count == 0 else None),
        ReadinessCheck(key="modules", label="Moduli", status=ok if module_count > 0 else warning, message="Modularni katalog je inicijaliziran." if module_count > 0 else "Nema aktivnih modula.", count=module_count, target_path="/modules", target_label="Otvori module", decision_impact="review" if module_count == 0 else "none"),
        ReadinessCheck(key="audit", label="Audit", status=ok if audit_count > 0 else warning, message="Audit log sadrzi zapise." if audit_count > 0 else "Audit log jos nema zapisa.", count=audit_count, target_path="/audit-log", target_label="Otvori audit", decision_impact="review" if audit_count == 0 else "none", severity_reason="Audit je dokaz operativnog toka; prazan audit treba provjeriti prije release odluke." if audit_count == 0 else None),
        ReadinessCheck(key="inventory_low_stock", label="Niska zaliha", status=warning if low_stock_count > 0 else ok, message="Postoje artikli na ili ispod reorder razine." if low_stock_count > 0 else "Nema artikala ispod reorder razine.", count=low_stock_count, action="Provjeriti inventar i nabavu." if low_stock_count > 0 else None, target_path="/inventory", target_label="Otvori inventar", decision_impact="review" if low_stock_count > 0 else "none", severity_reason="Niska zaliha ne mora blokirati demo, ali moze utjecati na materijalni workflow." if low_stock_count > 0 else None),
        ReadinessCheck(key="inventory_expiring", label="Rokovi zalihe", status=warning if expiring_count > 0 else ok, message="Postoje serije kojima uskoro istjece rok." if expiring_count > 0 else "Nema serija s rokom unutar 30 dana.", count=expiring_count, action="Provjeriti artikle s rokom trajanja." if expiring_count > 0 else None, target_path="/inventory", target_label="Otvori inventar", decision_impact="review" if expiring_count > 0 else "none"),
        ReadinessCheck(key="draft_invoices", label="Draft racuni", status=warning if draft_invoice_count > 0 else ok, message="Postoje neizdani draft racuni." if draft_invoice_count > 0 else "Nema neizdanih draft racuna.", count=draft_invoice_count, target_path="/invoices", target_label="Otvori racune", decision_impact="review" if draft_invoice_count > 0 else "none"),
        ReadinessCheck(key="unpaid_invoices", label="Neplaceni racuni", status=warning if unpaid_invoice_count > 0 else ok, message="Postoje izdani racuni koji nisu placeni." if unpaid_invoice_count > 0 else "Nema otvorenih uplata.", count=unpaid_invoice_count, target_path="/invoices", target_label="Otvori racune", decision_impact="review" if unpaid_invoice_count > 0 else "none"),
        ReadinessCheck(key="api_keys", label="API kljucevi", status=warning if active_api_keys > 0 else ok, message="Postoje aktivni API kljucevi." if active_api_keys > 0 else "Nema aktivnih API kljuceva.", count=active_api_keys, action="Provjeriti scopeove i deaktivirati nepotrebne kljuceve." if active_api_keys > 0 else None, target_path="/api-keys", target_label="Otvori API kljuceve", decision_impact="review" if active_api_keys > 0 else "none", severity_reason="Aktivni kljucevi su sigurnosno osjetljivi i trebaju provjeru scopeova." if active_api_keys > 0 else None),
        ReadinessCheck(
            key="clinical_episodes",
            label="Kliničke epizode (deferred)",
            status=ok,
            message=f"Episode Engine je eksperimentalno/deferred. Termini bez epizode ({appointments_without_episode}) nisu problem i ne blokiraju rad.",
            count=episode_count,
            action="Primarni klinicki smjer je Patient Clinical Knowledge Layer.",
            target_path="/clinical-documents",
            target_label="Otvori dokumente",
            decision_impact="none",
            severity_reason=None,
        ),
        ReadinessCheck(
            key="clinical_documents_review",
            label="Klinicki dokumenti",
            status=warning if documents_awaiting_review > 0 else ok,
            message=f"Postoje dokumenti koji cekaju lijecnicki pregled ({documents_awaiting_review})." if documents_awaiting_review > 0 else "Nema klinickih dokumenata koji cekaju pregled.",
            count=documents_awaiting_review,
            action="Pregledati dokumente i potvrditi samo provjerene sazetke." if documents_awaiting_review > 0 else None,
            target_path="/clinical-documents?review_status=needs_physician_review",
            target_label="Pregledaj dokumente",
            decision_impact="review" if documents_awaiting_review > 0 else "none",
            severity_reason="Dokumenti bez pregleda ne ulaze u sluzbeni sazetak pacijenta." if documents_awaiting_review > 0 else None,
        ),
        ReadinessCheck(
            key="patient_summary_stale",
            label="Sazetak pacijenta",
            status=warning if stale_summary_patients else ok,
            message=f"Postoje pacijenti s pregledanim dokumentima nakon zadnjeg potvrdjenog sazetka ({len(stale_summary_patients)})." if stale_summary_patients else "Potvrdjeni sazetci pacijenata su uskladjeni s pregledanim dokumentima.",
            count=len(stale_summary_patients),
            action="Generirati draft i lijecnicki potvrditi sazetak pacijenta." if stale_summary_patients else None,
            target_path="/patients",
            target_label="Otvori pacijente",
            decision_impact="review" if stale_summary_patients else "none",
            severity_reason="Sazetak je operativna pomoc i ne smije zamijeniti pregled izvora." if stale_summary_patients else None,
        ),
        ReadinessCheck(
            key="room_service_compatibility",
            label="Sobe i usluge",
            status=warning if rooms_without_services or services_without_rooms else ok,
            message=f"Sobe bez dopustenih usluga: {rooms_without_services}; usluge bez soba: {services_without_rooms}." if rooms_without_services or services_without_rooms else "Sve aktivne sobe i usluge imaju osnovnu kompatibilnost.",
            count=rooms_without_services + services_without_rooms,
            action="Provjeriti pravila soba/usluga prije recepcijskog narucivanja." if rooms_without_services or services_without_rooms else None,
            target_path="/reception",
            target_label="Otvori prijem",
            decision_impact="review" if rooms_without_services or services_without_rooms else "none",
            severity_reason="Recepcija treba znati u kojoj sobi se usluga smije izvesti." if rooms_without_services or services_without_rooms else None,
        ),
        ReadinessCheck(
            key="provider_clinic_assignments",
            label="Osoblje i klinike",
            status=warning if providers_without_clinic else ok,
            message=f"Postoje aktivni djelatnici bez klinike ({providers_without_clinic})." if providers_without_clinic else "Aktivni djelatnici imaju klinicki kontekst.",
            count=providers_without_clinic,
            action="Dodijeliti kliniku djelatnicima za resursno narucivanje." if providers_without_clinic else None,
            target_path="/reception",
            target_label="Otvori prijem",
            decision_impact="review" if providers_without_clinic else "none",
        ),
        ReadinessCheck(
            key="today_appointments_resource_context",
            label="Danasnji termini",
            status=critical if today_incomplete_appointments else ok,
            message=f"Danas postoje termini bez sobe, lijecnika ili usluge ({today_incomplete_appointments})." if today_incomplete_appointments else "Danasnji termini imaju osnovne resurse.",
            count=today_incomplete_appointments,
            action="Popuniti sobu, lijecnika i uslugu prije prijema pacijenta." if today_incomplete_appointments else None,
            target_path="/reception",
            target_label="Otvori prijem",
            decision_impact="blocks_demo" if today_incomplete_appointments else "none",
        ),
        ReadinessCheck(
            key="human_pilot_evidence",
            label="Human pilot evidence",
            status=warning,
            message="Provjerite docs/pilot_sessions prije v0.1-pilot taga.",
            action="Azurirati human pilot report, triage, ADR i Go/No-Go matrix.",
            target_path="/readiness",
            target_label="Otvori spremnost",
            decision_impact="blocks_release",
            severity_reason="Human pilot evidence ostaje release gate i ne zamjenjuje se readiness cockpitom.",
        ),
    ]

    summary = {
        "ok": sum(1 for check in checks if check.status == ok),
        "warning": sum(1 for check in checks if check.status == warning),
        "critical": sum(1 for check in checks if check.status == critical),
    }
    status = "blocked" if summary["critical"] else "attention_needed" if summary["warning"] else "ready_for_demo"
    return {
        "status": status,
        "demo_mode": settings.demo_mode,
        "real_data_allowed": settings.real_data_allowed,
        "fiscalization_mode": settings.fiscalization_mode,
        "summary": summary,
        "checks": checks,
    }
