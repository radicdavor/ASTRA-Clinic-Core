from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


OperationalSeverity = Literal["neutral", "info", "active", "warning", "critical", "success"]


@dataclass(frozen=True)
class OperationalStatusReason:
    code: str
    label: str


@dataclass(frozen=True)
class OperationalStatusProjection:
    status: str
    label: str
    severity: OperationalSeverity
    reasons: list[OperationalStatusReason] = field(default_factory=list)


PAYMENT_RESOLVED = {"paid", "not_due", "cancelled"}


def resolve_dashboard_operational_status(
    *,
    workflow_stage: str,
    payment_status: str,
    billing_status: str,
    consumables_status: str,
    activity_statuses: list[str],
    has_open_blocker: bool,
    has_reception_warning: bool,
) -> OperationalStatusProjection:
    if has_open_blocker or has_reception_warning:
        reasons = []
        if has_open_blocker:
            reasons.append(OperationalStatusReason("open_blocker", "Postoji otvoreni blokator"))
        if has_reception_warning:
            reasons.append(OperationalStatusReason("reception_red_flag", "Postoji prijemna crvena napomena"))
        label = "Čeka pregled/pretragu" if workflow_stage in {"ready_for_clinician", "in_encounter"} else "Crvena napomena"
        return OperationalStatusProjection("problem", label, "critical", reasons)

    if workflow_stage in {"cancelled", "no_show"}:
        return OperationalStatusProjection(
            workflow_stage,
            "Otkazano" if workflow_stage == "cancelled" else "Nije došao/la",
            "neutral",
            [OperationalStatusReason(workflow_stage, "Termin nije aktivan operativni dolazak")],
        )

    unresolved_activities = [status for status in activity_statuses if status not in {"completed", "not_performed", "cancelled"}]
    if workflow_stage == "completed":
        if payment_status in PAYMENT_RESOLVED and not unresolved_activities:
            return OperationalStatusProjection("completed_paid", "Završeno", "success", [OperationalStatusReason("payment_resolved", "Plaćanje je riješeno")])
        return OperationalStatusProjection(
            "completed_unpaid",
            "Čeka plaćanje",
            "warning",
            [OperationalStatusReason("invoice_balance_due", "Klinički dio je završen, ali plaćanje nije riješeno")],
        )

    if workflow_stage == "procedure_completed":
        return OperationalStatusProjection("awaiting_consumables", "Čeka materijal", "warning", [OperationalStatusReason("consumables_pending", "Treba potvrditi korišteni materijal")])

    if workflow_stage == "awaiting_billing":
        return OperationalStatusProjection("awaiting_billing", "Čeka račun", "warning", [OperationalStatusReason("invoice_not_ready", "Račun treba izraditi")])

    if workflow_stage == "awaiting_payment":
        if payment_status == "partially_paid":
            reason = OperationalStatusReason("invoice_partially_paid", "Račun je djelomično plaćen")
        else:
            reason = OperationalStatusReason("invoice_balance_due", "Račun je izrađen i čeka plaćanje")
        return OperationalStatusProjection("awaiting_payment", "Čeka plaćanje", "warning", [reason])

    if billing_status in {"invoice_created", "adjustment_required"} or payment_status in {"unpaid", "partially_paid"}:
        return OperationalStatusProjection("billing_attention", "Čeka naplatu", "warning", [OperationalStatusReason("billing_or_payment_pending", "Račun ili plaćanje nije riješeno")])

    if workflow_stage in {"ready_for_clinician", "in_encounter"}:
        return OperationalStatusProjection(
            workflow_stage,
            "Pregled u tijeku" if workflow_stage == "in_encounter" else "Čeka pregled/pretragu",
            "active",
            [OperationalStatusReason("clinical_step_active", "Pacijent je nakon prijema u kliničkom dijelu procesa")],
        )

    if workflow_stage in {"arrived", "check_in_review"}:
        return OperationalStatusProjection("arrived", "Stigao", "active", [OperationalStatusReason("patient_arrived", "Pacijent je stigao i treba prijemnu provjeru")])

    if workflow_stage in {"requested", "booked", "awaiting_forms", "awaiting_documents", "preparation_in_progress", "ready_for_arrival"}:
        return OperationalStatusProjection("waiting_arrival", "Čeka dolazak", "neutral", [OperationalStatusReason("patient_not_arrived", "Pacijent je naručen i još se nije javio na prijem")])

    return OperationalStatusProjection("not_started", "Nije započeto", "neutral", [OperationalStatusReason("unknown_stage", "Nema trenutne operativne radnje")])
