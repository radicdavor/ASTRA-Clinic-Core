"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

from __future__ import annotations

import argparse
import json

from .models import SAFETY_BANNER
from .scenarios import SCENARIOS, build_scenario
from .trial import build_trial_packet, render_trial_packet
from .workflow import build_workflow_summary


def render_summary(summary: dict[str, object]) -> str:
    """Render a local-only synthetic workflow summary for console display."""

    lines = [
        SAFETY_BANNER,
        "",
        f"Patient: {summary['patient']}",
        f"Encounter: {summary['encounter']}",
        "Findings:",
    ]
    lines.extend(f"- {finding}" for finding in summary["findings"])
    lines.extend(
        [
            f"Review note: {summary['review_note']}",
            "",
            "Safety flags:",
            f"- sandbox_only: {summary['sandbox_only']}",
            f"- clinical_use_authorized: {summary['clinical_use_authorized']}",
            f"- real_patient_data_allowed: {summary['real_patient_data_allowed']}",
            f"- phi_pii_allowed: {summary['phi_pii_allowed']}",
            f"- external_integrations_enabled: {summary['external_integrations_enabled']}",
            f"- appointment_mutation_enabled: {summary['appointment_mutation_enabled']}",
            f"- patient_messaging_enabled: {summary['patient_messaging_enabled']}",
            f"- approval_override_enabled: {summary['approval_override_enabled']}",
        ]
    )
    return "\n".join(lines)


def run_scenario(name: str = "alpha") -> dict[str, object]:
    """Run a local synthetic scenario and return the summary dictionary."""

    _patient, _encounter, _findings, review = build_scenario(name)
    return build_workflow_summary(review)


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
    args = parser.parse_args(argv)
    command = args.command or "summary"
    if command == "trial":
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
