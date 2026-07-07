from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.domain import Appointment
from app.schemas.common import ClinicalReadinessPreviewItem, ClinicalReadinessPreviewResponse
from app.services.patient_knowledge import official_patient_documents_statement, summary_record_from_documents


DEMO_LIMITATION = "Ovo je demo/pilot read-only preview i nije produkcijska odluka."
PREVIEW_SUMMARY = "Klinicka spremnost prikazana je kao read-only preview. Ne blokira termin i ne predstavlja klinicku odluku."
NO_TEMPLATE_LIMITATION = "Nema definiranog clinical readiness templatea za ovu uslugu."
NO_REVIEWED_DOCUMENTS_LIMITATION = "Nema pregledanih klinickih dokumenata za ovog pacijenta."


def aggregate_status(items: list[ClinicalReadinessPreviewItem]) -> str:
    if any(item.blocking for item in items):
        return "blocked"
    if any(item.status == "needs_physician_review" for item in items):
        return "needs_physician_review"
    if any(item.severity == "warning" or item.status == "ready_with_warning" for item in items):
        return "ready_with_warning"
    return "ready"


def build_clinical_readiness_preview(db: Session, appointment: Appointment) -> ClinicalReadinessPreviewResponse:
    items: list[ClinicalReadinessPreviewItem] = []
    limitations = [DEMO_LIMITATION]
    source_warnings: list[str] = []

    if not appointment.patient_id:
        items.append(
            ClinicalReadinessPreviewItem(
                key="missing_patient",
                label="Pacijent nije povezan s terminom",
                category="identity",
                status="not_ready",
                severity="blocking",
                responsible_role="admin",
                source_type="system_record",
                source_ref=None,
                source_label=None,
                suggested_action="Povezati pacijenta s terminom.",
                blocking=True,
                override_allowed=False,
                override_role=None,
                override_reason_required=False,
                audit_required=False,
            )
        )

    if not appointment.service_id:
        items.append(
            ClinicalReadinessPreviewItem(
                key="missing_service",
                label="Usluga nije povezana s terminom",
                category="service",
                status="not_ready",
                severity="blocking",
                responsible_role="admin",
                source_type="system_record",
                source_ref=None,
                source_label=None,
                suggested_action="Povezati uslugu s terminom.",
                blocking=True,
                override_allowed=False,
                override_role=None,
                override_reason_required=False,
                audit_required=False,
            )
        )
    else:
        limitations.append(NO_TEMPLATE_LIMITATION)
        items.append(
            ClinicalReadinessPreviewItem(
                key="service_template_missing",
                label="Clinical readiness template nije definiran za ovu uslugu",
                category="service",
                status="ready_with_warning",
                severity="warning",
                responsible_role="admin",
                source_type="system_record",
                source_ref=f"Service:{appointment.service_id}",
                source_label=appointment.service.name if appointment.service else f"Usluga #{appointment.service_id}",
                suggested_action="Nastaviti samo kao preview; template treba definirati u buducem B4 tasku.",
                blocking=False,
                override_allowed=False,
                override_role=None,
                override_reason_required=False,
                audit_required=False,
            )
        )

    reviewed_documents = []
    if appointment.patient_id:
        reviewed_documents = db.scalars(official_patient_documents_statement(appointment.patient_id)).all()
        if not reviewed_documents:
            limitations.append(NO_REVIEWED_DOCUMENTS_LIMITATION)
            items.append(
                ClinicalReadinessPreviewItem(
                    key="no_reviewed_clinical_documents",
                    label="Nema pregledanih klinickih dokumenata",
                    category="reviewed_evidence",
                    status="ready_with_warning",
                    severity="warning",
                    responsible_role="physician",
                    source_type="missing_evidence",
                    source_ref=None,
                    source_label=None,
                    suggested_action="Ako je klinicki potrebno, pregledati dostupne dokumente prije postupka.",
                    blocking=False,
                    override_allowed=False,
                    override_role=None,
                    override_reason_required=False,
                    audit_required=False,
                )
            )
        else:
            summary_data = summary_record_from_documents(appointment.patient_id, reviewed_documents)
            for index, text in enumerate(summary_data.get("open_items") or [], start=1):
                source_document = reviewed_documents[0]
                items.append(
                    ClinicalReadinessPreviewItem(
                        key=f"open_question_{index}",
                        label=text,
                        category="open_question",
                        status="needs_physician_review",
                        severity="warning",
                        responsible_role="physician",
                        source_type="reviewed_clinical_source",
                        source_ref=f"ClinicalDocument:{source_document.id}",
                        source_label=source_document.title,
                        suggested_action="Pregledati otvoreno pitanje i izvorni dokument. Ovo nije zadatak niti automatski blocker.",
                        blocking=False,
                        override_allowed=False,
                        override_role=None,
                        override_reason_required=False,
                        audit_required=False,
                    )
                )
            if summary_data.get("open_items"):
                source_warnings.append("Open Questions su prikazana kao upozorenja za lijecnicki pregled, ne kao zadaci ili automatski blockeri.")

    return ClinicalReadinessPreviewResponse(
        appointment_id=appointment.id,
        patient_id=appointment.patient_id,
        service_id=appointment.service_id,
        status=aggregate_status(items),
        is_preview=True,
        generated_at=datetime.now(UTC),
        summary=PREVIEW_SUMMARY,
        items=items,
        source_warnings=source_warnings,
        limitations=limitations,
    )

