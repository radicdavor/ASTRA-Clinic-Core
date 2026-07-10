"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

import argparse
import json

from .display import (
    HUMAN_REVIEW_NOTE,
    humanize_label,
    render_allowed_state,
    render_authorized_state,
    render_enabled_state,
    render_safety_banner,
)
from .feedback_input import build_feedback_input_preview, render_feedback_input_preview
from .feedback_review import render_feedback_review, review_feedback
from .models import SAFETY_BANNER
from .scenario_comparison import build_scenario_comparison, render_scenario_comparison
from .scenarios import SCENARIOS, build_scenario
from .session_recap import build_session_recap, render_session_recap
from .trial import build_trial_packet, render_trial_packet
from .walkthrough import build_walkthrough_packet, render_walkthrough
from .workflow import build_workflow_summary


def render_summary(summary: dict[str, object]) -> str:
    """Render a local-only synthetic workflow summary for console display."""

    lines = [
        render_safety_banner(),
        "",
        f"Scenario: {str(summary.get('scenario', 'alpha')).title()}",
        "",
        "Patient:",
        humanize_label(summary["patient"]),
        "",
        "Encounter:",
        humanize_label(summary["encounter"]),
        "",
        "Findings:",
    ]
    lines.extend(f"- {humanize_label(finding)}" for finding in summary["findings"])
    lines.extend(
        [
            "",
            "Clinician review note:",
            HUMAN_REVIEW_NOTE,
            "",
            "Safety confirmations:",
            f"- Real patient data: {render_allowed_state(summary['real_patient_data_allowed'])}",
            f"- PHI/PII: {render_allowed_state(summary['phi_pii_allowed'])}",
            f"- Clinical use: {render_authorized_state(summary['clinical_use_authorized'])}",
            f"- Patient messaging: {render_enabled_state(summary['patient_messaging_enabled'])}",
            f"- Appointment mutation: {render_enabled_state(summary['appointment_mutation_enabled'])}",
            "- Clinical writeback: disabled",
            f"- Approval/override capability: {render_enabled_state(summary['approval_override_enabled'])}",
        ]
    )
    return "\n".join(lines)


def run_scenario(name: str = "alpha") -> dict[str, object]:
    """Run a local synthetic scenario and return the summary dictionary."""

    _patient, _encounter, _findings, review = build_scenario(name)
    summary = build_workflow_summary(review)
    summary["scenario"] = name
    return summary


def main(argv: list[str] | None = None) -> int:
    """Local-only CLI entry point for the synthetic sandbox."""

    if argv and argv[0] in {"--scenario", "--json"}:
        argv = ["summary", *argv]
    parser = argparse.ArgumentParser(
        description="Run a Program 1 synthetic-only local sandbox scenario."
    )
    subparsers = parser.add_subparsers(dest="command")
    summary_parser = subparsers.add_parser("summary", help="Print a synthetic summary.")
    summary_parser.add_argument(
        "--scenario",
        default="alpha",
        choices=sorted(SCENARIOS),
        help="Synthetic-only scenario to render.",
    )
    summary_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the synthetic summary as JSON.",
    )
    trial_parser = subparsers.add_parser("trial", help="Print a local clinician trial packet.")
    trial_parser.add_argument(
        "--scenario",
        default="alpha",
        choices=sorted(SCENARIOS),
        help="Synthetic-only scenario to use for the trial packet.",
    )
    trial_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the synthetic trial packet as JSON.",
    )
    review_parser = subparsers.add_parser(
        "review-feedback",
        help="Print local synthetic feedback themes and iteration queue.",
    )
    review_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the local synthetic feedback review as JSON.",
    )
    walkthrough_parser = subparsers.add_parser(
        "walkthrough",
        help="Print the local synthetic clinician walkthrough pack.",
    )
    walkthrough_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the local synthetic walkthrough as JSON.",
    )
    feedback_input_parser = subparsers.add_parser(
        "feedback-input",
        help="Preview local synthetic design feedback without storing or sending it.",
    )
    feedback_input_parser.add_argument(
        "--text",
        nargs="?",
        const="",
        default=None,
        help="Synthetic design-feedback text to preview locally.",
    )
    feedback_input_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for synthetic design-feedback text locally.",
    )
    feedback_input_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the local synthetic feedback preview as JSON.",
    )
    recap_parser = subparsers.add_parser(
        "session-recap",
        help="Print a local synthetic sandbox session recap.",
    )
    recap_parser.add_argument(
        "--scenario",
        default="alpha",
        choices=sorted(SCENARIOS),
        help="Synthetic-only scenario to recap.",
    )
    recap_parser.add_argument(
        "--feedback",
        default=None,
        help="Optional synthetic design-feedback text to include as a local preview.",
    )
    recap_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the local synthetic session recap as JSON.",
    )
    compare_parser = subparsers.add_parser(
        "compare-scenarios",
        help="Print a local synthetic alpha/beta scenario comparison.",
    )
    compare_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the local synthetic scenario comparison as JSON.",
    )
    args = parser.parse_args(argv)
    command = args.command or "summary"
    if command == "walkthrough":
        packet = build_walkthrough_packet()
        if args.json:
            print(json.dumps(packet, indent=2, sort_keys=True))
        else:
            print(render_walkthrough(packet))
    elif command == "review-feedback":
        review = review_feedback()
        if args.json:
            print(json.dumps(review, indent=2, sort_keys=True))
        else:
            print(render_feedback_review(review))
    elif command == "feedback-input":
        text = args.text
        if args.interactive:
            print("Synthetic-only local feedback input. Do not enter real patient data or PHI/PII.")
            text = input("Enter synthetic design feedback: ")
        preview = build_feedback_input_preview(text)
        if args.json:
            print(json.dumps(preview, indent=2, sort_keys=True))
        else:
            print(render_feedback_input_preview(preview))
    elif command == "session-recap":
        recap = build_session_recap(args.scenario, args.feedback)
        if args.json:
            print(json.dumps(recap, indent=2, sort_keys=True))
        else:
            print(render_session_recap(recap))
    elif command == "compare-scenarios":
        comparison = build_scenario_comparison()
        if args.json:
            print(json.dumps(comparison, indent=2, sort_keys=True))
        else:
            print(render_scenario_comparison(comparison))
    elif command == "trial":
        packet = build_trial_packet(args.scenario)
        if args.json:
            print(json.dumps(packet, indent=2, sort_keys=True))
        else:
            print(render_trial_packet(packet))
    else:
        summary = run_scenario(args.scenario)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            print(render_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
