"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

from dataclasses import dataclass

from .models import SyntheticDataError, require_synthetic_text


@dataclass(frozen=True)
class SyntheticIterationQueueItem:
    """Local-only sandbox iteration queue item."""

    item_id: str
    source_feedback_id: str
    theme: str
    proposed_change: str
    priority: str
    safety_boundary: str
    allowed_in_sandbox: bool
    prohibited_escalation: str
    status: str

    def __post_init__(self) -> None:
        for field_name in (
            "item_id",
            "source_feedback_id",
            "theme",
            "proposed_change",
            "priority",
            "safety_boundary",
            "prohibited_escalation",
            "status",
        ):
            object.__setattr__(
                self,
                field_name,
                require_synthetic_text(getattr(self, field_name), field_name),
            )
        if self.allowed_in_sandbox is not True:
            raise SyntheticDataError("allowed_in_sandbox must be true for local queue items.")


def build_iteration_queue(feedback_items: list[dict[str, object]]) -> list[SyntheticIterationQueueItem]:
    """Create a local-only sandbox iteration queue from validated synthetic feedback."""

    queue: list[SyntheticIterationQueueItem] = []
    for index, feedback in enumerate(feedback_items, start=1):
        scenario = require_synthetic_text(str(feedback["scenario_id"]), "scenario_id")
        clarity_score = int(feedback["workflow_clarity_score"])
        if clarity_score <= 3:
            theme = "DEMO_THEME_WORKFLOW_CLARITY"
            proposed_change = "EXAMPLE_CHANGE_CLARIFY_SYNTHETIC_SUMMARY_OUTPUT"
            priority = "DEMO_PRIORITY_MEDIUM"
        else:
            theme = "DEMO_THEME_USEFULNESS_REVIEW"
            proposed_change = "EXAMPLE_CHANGE_KEEP_SANDBOX_BOUNDARY_VISIBLE"
            priority = "DEMO_PRIORITY_LOW"
        queue.append(
            SyntheticIterationQueueItem(
                item_id=f"SYNTHETIC_QUEUE_ITEM_{index}",
                source_feedback_id=scenario,
                theme=theme,
                proposed_change=proposed_change,
                priority=priority,
                safety_boundary="DEMO_BOUNDARY_SYNTHETIC_LOCAL_ONLY",
                allowed_in_sandbox=True,
                prohibited_escalation="DEMO_PROHIBIT_PRODUCTION_CLINICAL_REAL_DATA_ESCALATION",
                status="DEMO_STATUS_PROPOSED_FOR_FUTURE_SANDBOX_REVIEW",
            )
        )
    return queue
