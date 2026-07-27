import pytest

from app.services.dashboard_operational_status import resolve_dashboard_operational_status


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ({"workflow_stage": "booked"}, ("waiting_arrival", "neutral")),
        ({"workflow_stage": "arrived"}, ("arrived", "active")),
        ({"workflow_stage": "in_encounter", "activity_statuses": ["in_progress"]}, ("in_encounter", "active")),
        ({"workflow_stage": "ready_for_clinician", "has_reception_warning": True}, ("problem", "critical")),
        ({"workflow_stage": "completed", "payment_status": "unpaid", "activity_statuses": ["completed"]}, ("completed_unpaid", "warning")),
        ({"workflow_stage": "completed", "payment_status": "partially_paid", "activity_statuses": ["completed"]}, ("completed_unpaid", "warning")),
        ({"workflow_stage": "completed", "payment_status": "paid", "activity_statuses": ["completed"]}, ("completed_paid", "success")),
        ({"workflow_stage": "procedure_completed"}, ("awaiting_consumables", "warning")),
        ({"workflow_stage": "awaiting_billing"}, ("awaiting_billing", "warning")),
        ({"workflow_stage": "awaiting_payment", "payment_status": "partially_paid"}, ("awaiting_payment", "warning")),
        ({"workflow_stage": "cancelled"}, ("cancelled", "neutral")),
        ({"workflow_stage": "no_show"}, ("no_show", "neutral")),
    ],
)
def test_dashboard_operational_status_cases(case, expected):
    payload = {
        "workflow_stage": "booked",
        "payment_status": "not_due",
        "billing_status": "not_ready",
        "consumables_status": "not_ready",
        "activity_statuses": ["ready"],
        "has_open_blocker": False,
        "has_reception_warning": False,
        **case,
    }

    projection = resolve_dashboard_operational_status(**payload)

    assert (projection.status, projection.severity) == expected
    assert projection.label
    assert projection.reasons


def test_red_problem_has_priority_over_unpaid_warning():
    projection = resolve_dashboard_operational_status(
        workflow_stage="completed",
        payment_status="unpaid",
        billing_status="invoice_created",
        consumables_status="confirmed",
        activity_statuses=["completed"],
        has_open_blocker=True,
        has_reception_warning=False,
    )

    assert projection.status == "problem"
    assert projection.severity == "critical"
    assert projection.reasons[0].code == "open_blocker"


def test_payment_alone_does_not_make_unfinished_visit_success():
    projection = resolve_dashboard_operational_status(
        workflow_stage="in_encounter",
        payment_status="paid",
        billing_status="closed",
        consumables_status="confirmed",
        activity_statuses=["in_progress"],
        has_open_blocker=False,
        has_reception_warning=False,
    )

    assert projection.severity == "active"
    assert projection.status == "in_encounter"
