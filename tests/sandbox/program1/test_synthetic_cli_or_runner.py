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
        self.assertIn("clinical_use_authorized: False", rendered)
        self.assertIn("real_patient_data_allowed: False", rendered)
        self.assertIn("phi_pii_allowed: False", rendered)
        self.assertIn("external_integrations_enabled: False", rendered)
        self.assertIn("appointment_mutation_enabled: False", rendered)
        self.assertIn("patient_messaging_enabled: False", rendered)
        self.assertIn("approval_override_enabled: False", rendered)

    def test_cli_prints_local_sandbox_summary(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--scenario", "alpha"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn(SAFETY_BANNER, text)
        self.assertIn("Patient: DEMO_ONLY_PATIENT_ALPHA", text)
        self.assertIn("Not for clinical use", text)


if __name__ == "__main__":
    unittest.main()
