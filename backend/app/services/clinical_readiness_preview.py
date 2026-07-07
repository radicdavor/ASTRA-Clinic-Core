from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.domain import Appointment
from app.schemas.common import ClinicalReadinessPreviewItem, ClinicalReadinessPreviewResponse
from app.services.clinical_readiness_templates import ClinicalReadinessTemplateItem, select_clinical_readiness_template
from app.services.patient_knowledge import official_patient_documents_statement, summary_record_from_documents


DEMO_LIMITATION = "Ovo je demo/pilot read-only preview i nije produkcijska odluka."
PREVIEW_SUMMARY = "Klinicka spremnost prikazana je kao read-only preview. Ne blokira termin i ne predstavlja klinicku odluku."
TEMPLATE_LIMITATION = "Clinical readiness template je demo/pilot staticna definicija, nije produkcijsko pravilo."
GENERIC_TEMPLATE_LIMITATION = "Nema specificnog clinical readiness templatea za ovu uslugu; koristi se genericki preview."
NO_REVIEWED_DOCUMENTS_LIMITATION = "Nema pregledanih klinickih dokumenata za ovog pacijenta."


def aggregate_status(items: list[ClinicalReadinessPreviewItem]) -> str:
    if any(item.blocking for item in items):
        return "blocked"
    if any(item.status == "needs_physician_review" for item in items):
        return "needs_physician_review"
    if any(item.severity == "warning" or item.status == "ready_with_warning" for item in items):
        return "ready_with_warning"
    return "ready"


def template_item_to_preview_item(
    template_item: ClinicalReadinessTemplateItem,
    *,
    service_id: int,
    service_name: str,
) -> ClinicalReadinessPreviewItem:
    return ClinicalReadinessPreviewItem(
        key=f"template_{template_item.key}",
        label=template_item.label,
        category=template_item.category,
        status=template_item.default_status,
        severity=template_item.severity,
        responsible_role=template_item.responsible_role,
        source_type=template_item.source_type,
        source_ref=f"Service:{service_id}",
        source_label=service_name,
        suggested_action=template_item.suggested_action,
        blocking=False,
        override_allowed=False,
        override_role=None,
        override_reason_required=False,
        audit_required=False,
    )


def build_clinical_readiness_preview(db: Session, appointment: Appointment) -> ClinicalReadinessPreviewResponse:
    items: list[ClinicalReadinessPreviewItem] = []
    limitations = [DEMO_LIMITATION]
    source_warnings: list[str] = []
    template_key: str | None = None
    template_label: str | None = None
    template_binding_status = "unbound"
    template_binding_warning: str | None = None

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
        service_name = appointment.service.name if appointment.service else f"Usluga #{appointment.service_id}"
        template_selection = select_clinical_readiness_template(service_name)
        template = template_selection.template
        template_key = template.key
        template_label = template.name
        template_binding_status = template_selection.binding_status
        template_binding_warning = template_selection.binding_warning
        limitations.append(TEMPLATE_LIMITATION)
        if template.specific:
            limitations.append(f"Koristi se demo/pilot template: {template.name}.")
        else:
            limitations.append(GENERIC_TEMPLATE_LIMITATION)
        items.extend(
            template_item_to_preview_item(template_item, service_id=appointment.service_id, service_name=service_name)
            for template_item in template.items
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
        template_key=template_key,
        template_label=template_label,
        template_binding_status=template_binding_status,
        template_binding_warning=template_binding_warning,
        status=aggregate_status(items),
        is_preview=True,
        generated_at=datetime.now(UTC),
        summary=PREVIEW_SUMMARY,
        items=items,
        source_warnings=source_warnings,
        limitations=limitations,
    )
