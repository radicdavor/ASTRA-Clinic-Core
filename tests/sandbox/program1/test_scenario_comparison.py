"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import io
import json
import unittest
from contextlib import redirect_stdout

from sandbox.program1.cli import main
from sandbox.program1.models import SAFETY_BANNER
from sandbox.program1.scenario_comparison import (
    build_scenario_comparison,
    render_scenario_comparison,
)


class ScenarioComparisonTests(unittest.TestCase):
    def test_compare_scenarios_renders_clinician_readable_comparison(self):
        rendered = render_scenario_comparison(build_scenario_comparison())

        self.assertIn("Program 1 Synthetic Sandbox Scenario Comparison", rendered)
        self.assertIn(SAFETY_BANNER, rendered)
        self.assertIn("Comparison purpose:", rendered)
        self.assertIn("Scenario Alpha:", rendered)
        self.assertIn("Synthetic patient A", rendered)
        self.assertIn("Example review visit", rendered)
        self.assertIn("Missing context in uploaded record", rendered)
        self.assertIn("Scenario Beta:", rendered)
        self.assertIn("Synthetic patient B", rendered)
        self.assertIn("Boundary review visit", rendered)
        self.assertIn("Visibility of safety boundary", rendered)

    def test_compare_scenarios_confirms_no_side_effects(self):
        rendered = render_scenario_comparison(build_scenario_comparison())

        self.assertIn("Persistence: disabled", rendered)
        self.assertIn("Export: disabled", rendered)
        self.assertIn("Transmission: disabled", rendered)
        self.assertIn("Network/database: disabled", rendered)
        self.assertIn("Patient messaging: disabled", rendered)
        self.assertIn("Appointment mutation: disabled", rendered)
        self.assertIn("Workflow enforcement: disabled", rendered)
        self.assertIn("Clinical writeback: disabled", rendered)
        self.assertIn("Clinical task creation: disabled", rendered)
        self.assertIn("Approval/override capability: disabled", rendered)

    def test_compare_scenarios_default_output_avoids_internal_placeholder_labels(self):
        rendered = render_scenario_comparison(build_scenario_comparison())

        for placeholder in (
            "DEMO_FINDING_CONTEXT_REVIEW",
            "DEMO_ONLY_PATIENT_ALPHA",
            "DEMO_ONLY_PATIENT_BETA",
            "SYNTHETIC_QUEUE_ITEM_1",
            "EXAMPLE_FINDING_SUMMARY_FOR_SYNTHETIC_WORKFLOW_ONLY",
        ):
            self.assertNotIn(placeholder, rendered)

    def test_compare_scenarios_cli_prints_comparison(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["compare-scenarios"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("Scenario Alpha:", text)
        self.assertIn("Scenario Beta:", text)
        self.assertIn("does not support clinical decision-making", text)

    def test_compare_scenarios_uses_intended_demo_order(self):
        rendered = render_scenario_comparison(build_scenario_comparison())

        scenario_markers = (
            "Scenario Alpha:",
            "Scenario Beta:",
            "Scenario Gamma:",
            "Scenario Delta:",
            "Scenario Epsilon:",
        )
        positions = [rendered.index(marker) for marker in scenario_markers]
        self.assertEqual(positions, sorted(positions))

    def test_compare_scenarios_summary_uses_intended_demo_order(self):
        rendered = render_scenario_comparison(build_scenario_comparison())

        summary_markers = (
            "Alpha demonstrates",
            "Beta demonstrates",
            "Gamma demonstrates",
            "Delta demonstrates",
            "Epsilon demonstrates",
        )
        positions = [rendered.index(marker) for marker in summary_markers]
        self.assertEqual(positions, sorted(positions))

    def test_compare_scenarios_json_uses_intended_demo_order(self):
        payload = build_scenario_comparison()

        self.assertEqual(
            list(payload["scenarios"]),
            ["alpha", "beta", "gamma", "delta", "epsilon"],
        )

    def test_compare_scenarios_cli_json_uses_intended_demo_order(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["compare-scenarios", "--json"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        positions = [
            text.index(f'"{scenario}":')
            for scenario in ("alpha", "beta", "gamma", "delta", "epsilon")
        ]
        self.assertEqual(positions, sorted(positions))

    def test_compare_scenarios_json_retains_safety_flags(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["compare-scenarios", "--json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(output.getvalue())
        self.assertIn("alpha", payload["scenarios"])
        self.assertIn("beta", payload["scenarios"])
        self.assertTrue(payload["synthetic_only"])
        self.assertTrue(payload["non_production"])
        self.assertFalse(payload["clinical_use_authorized"])
        self.assertFalse(payload["real_patient_data_allowed"])
        self.assertFalse(payload["phi_pii_allowed"])
        self.assertFalse(payload["persisted"])
        self.assertFalse(payload["exported"])
        self.assertFalse(payload["sent_externally"])
        self.assertFalse(payload["network_or_database_used"])
        self.assertFalse(payload["patient_message_created"])
        self.assertFalse(payload["appointment_mutation_performed"])
        self.assertFalse(payload["workflow_enforced"])
        self.assertFalse(payload["clinical_writeback_performed"])
        self.assertFalse(payload["clinical_task_created"])
        self.assertFalse(payload["approval_override_created"])
        self.assertFalse(payload["go_live_authorized"])


if __name__ == "__main__":
    unittest.main()
