"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import io
import unittest
from contextlib import redirect_stdout

from sandbox.program1.cli import main
from sandbox.program1.models import SAFETY_BANNER
from sandbox.program1.scenarios import SCENARIOS


EXPANDED_SCENARIOS = ("alpha", "beta", "gamma", "delta", "epsilon")
NEW_SCENARIOS = ("gamma", "delta", "epsilon")


class ScenarioExpansionTests(unittest.TestCase):
    def _run_cli(self, args):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(args)
        self.assertEqual(exit_code, 0)
        return output.getvalue()

    def test_registry_contains_expanded_synthetic_scenarios(self):
        self.assertEqual(sorted(SCENARIOS), sorted(EXPANDED_SCENARIOS))

    def test_summary_trial_and_session_recap_work_for_new_scenarios(self):
        for scenario in NEW_SCENARIOS:
            with self.subTest(command="summary", scenario=scenario):
                self.assertIn(SAFETY_BANNER, self._run_cli(["summary", "--scenario", scenario]))
            with self.subTest(command="trial", scenario=scenario):
                self.assertIn(SAFETY_BANNER, self._run_cli(["trial", "--scenario", scenario]))
            with self.subTest(command="session-recap", scenario=scenario):
                self.assertIn(
                    SAFETY_BANNER,
                    self._run_cli(["session-recap", "--scenario", scenario]),
                )

    def test_new_scenarios_use_clinician_readable_labels(self):
        expected_labels = {
            "gamma": (
                "Scenario: Gamma",
                "Synthetic patient C",
                "Incomplete documentation review visit",
                "Missing source document context",
                "Missing prior review reference",
            ),
            "delta": (
                "Scenario: Delta",
                "Synthetic patient D",
                "Conflicting information review visit",
                "Conflicting synthetic note context",
                "Follow-up clarification placeholder",
            ),
            "epsilon": (
                "Scenario: Epsilon",
                "Synthetic patient E",
                "Safety-boundary stress review visit",
                "Patient-facing action remains disabled",
                "Clinical workflow action remains disabled",
            ),
        }
        for scenario, labels in expected_labels.items():
            text = self._run_cli(["summary", "--scenario", scenario])
            for label in labels:
                self.assertIn(label, text)

    def test_new_scenario_output_avoids_internal_placeholder_labels(self):
        for scenario in NEW_SCENARIOS:
            text = self._run_cli(["summary", "--scenario", scenario])
            for placeholder in (
                "DEMO_ONLY_PATIENT_",
                "DEMO_ENCOUNTER_",
                "DEMO_FINDING_",
                "EXAMPLE_FINDING_",
                "SYNTHETIC_PATIENT_",
            ):
                self.assertNotIn(placeholder, text)

    def test_walkthrough_lists_new_scenarios(self):
        text = self._run_cli(["walkthrough"])

        self.assertIn("Gamma: Synthetic patient C", text)
        self.assertIn("Delta: Synthetic patient D", text)
        self.assertIn("Epsilon: Synthetic patient E", text)

    def test_compare_scenarios_includes_expanded_scenarios(self):
        text = self._run_cli(["compare-scenarios"])

        for scenario in ("Scenario Gamma:", "Scenario Delta:", "Scenario Epsilon:"):
            self.assertIn(scenario, text)
        self.assertIn("incomplete documentation context", text)
        self.assertIn("conflicting synthetic information", text)
        self.assertIn("disabled action boundaries", text)

    def test_safety_boundaries_remain_visible_for_new_scenarios(self):
        for scenario in NEW_SCENARIOS:
            text = self._run_cli(["session-recap", "--scenario", scenario])
            self.assertIn("Real patient data: not allowed", text)
            self.assertIn("PHI/PII: not allowed", text)
            self.assertIn("Clinical use: not authorized", text)
            self.assertIn("Patient messaging: disabled", text)
            self.assertIn("Appointment mutation: disabled", text)
            self.assertIn("Workflow enforcement: disabled", text)
            self.assertIn("Clinical writeback: disabled", text)
            self.assertIn("Clinical task creation: disabled", text)
            self.assertIn("Approval/override capability: disabled", text)
            self.assertIn("Go-live authorization: disabled", text)
            self.assertIn("No diagnosis, treatment, triage", text)


if __name__ == "__main__":
    unittest.main()
