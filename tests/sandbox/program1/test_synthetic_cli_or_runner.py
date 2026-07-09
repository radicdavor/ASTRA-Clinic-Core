"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import io
import unittest
from contextlib import redirect_stdout

from sandbox.program1.cli import main, render_summary, run_scenario
from sandbox.program1.models import SAFETY_BANNER
from sandbox.program1.scenarios import SCENARIOS, build_scenario


class SyntheticCliOrRunnerTests(unittest.TestCase):
    def test_beta_scenario_is_available_and_synthetic(self):
        self.assertIn("beta", SCENARIOS)
        patient, encounter, findings, review = build_scenario("beta")

        self.assertEqual(patient.synthetic_patient_id, "SYNTHETIC_PATIENT_BETA")
        self.assertEqual(encounter.encounter_id, "SYNTHETIC_ENCOUNTER_BETA")
        self.assertEqual(len(findings), 1)
        self.assertTrue(review.note.startswith("DEMO_REVIEW_NOTE_SYNTHETIC_ONLY"))

    def test_runner_summary_contains_safety_flags(self):
        summary = run_scenario("beta")
        rendered = render_summary(summary)

        self.assertIn(SAFETY_BANNER, rendered)
        self.assertIn("Synthetic-only", rendered)
        self.assertIn("Clinical use: not authorized", rendered)
        self.assertIn("Real patient data: not allowed", rendered)
        self.assertIn("PHI/PII: not allowed", rendered)
        self.assertIn("Appointment mutation: disabled", rendered)
        self.assertIn("Patient messaging: disabled", rendered)
        self.assertIn("Approval/override capability: disabled", rendered)

    def test_cli_prints_local_sandbox_summary(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--scenario", "alpha"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn(SAFETY_BANNER, text)
        self.assertIn("Synthetic patient A", text)
        self.assertIn("Missing context in uploaded record", text)
        self.assertIn("Not for clinical use", text)

    def test_default_summary_avoids_internal_placeholder_labels(self):
        text = render_summary(run_scenario("alpha"))

        for placeholder in (
            "DEMO_FINDING_CONTEXT_REVIEW",
            "DEMO_ONLY_PATIENT_ALPHA",
            "EXAMPLE_FINDING_SUMMARY_FOR_SYNTHETIC_WORKFLOW_ONLY",
            "DEMO_REVIEW_NOTE_SYNTHETIC_ONLY",
        ):
            self.assertNotIn(placeholder, text)


if __name__ == "__main__":
    unittest.main()
