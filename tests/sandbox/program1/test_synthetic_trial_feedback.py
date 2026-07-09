"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import io
import unittest
from contextlib import redirect_stdout

from sandbox.program1.cli import main
from sandbox.program1.feedback import build_feedback_template, validate_feedback
from sandbox.program1.models import SAFETY_BANNER, SyntheticDataError
from sandbox.program1.trial import build_trial_packet, render_trial_packet


class SyntheticTrialFeedbackTests(unittest.TestCase):
    def test_trial_output_includes_synthetic_warning_and_prompts(self):
        packet = build_trial_packet("alpha")
        rendered = render_trial_packet(packet)

        self.assertIn(SAFETY_BANNER, rendered)
        self.assertIn("No clinical use is authorized.", rendered)
        self.assertIn("Clinician trial checklist:", rendered)
        self.assertIn("Note missing workflow steps", rendered)
        self.assertIn("Feedback template fields:", rendered)
        self.assertIn("Clinical use: not authorized", rendered)

    def test_trial_cli_prints_packet(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["trial", "--scenario", "beta"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn(SAFETY_BANNER, text)
        self.assertIn("Scenario: Beta", text)
        self.assertIn("Synthetic patient B", text)
        self.assertIn("No clinical use is authorized.", text)

    def test_trial_output_avoids_internal_placeholder_labels(self):
        rendered = render_trial_packet(build_trial_packet("alpha"))

        for placeholder in (
            "DEMO_CHECKLIST_NOTE_MISSING_WORKFLOW_STEPS",
            "DEMO_FINDING_CONTEXT_REVIEW",
            "DEMO_ONLY_PATIENT_ALPHA",
            "DEMO_REVIEW_NOTE_SYNTHETIC_ONLY",
        ):
            self.assertNotIn(placeholder, rendered)

    def test_review_note_remains_non_clinical(self):
        rendered = render_trial_packet(build_trial_packet("alpha"))

        self.assertIn("does not recommend diagnosis", rendered)
        self.assertIn("does not recommend", rendered)
        self.assertNotIn("Start medication", rendered)
        self.assertNotIn("Send patient instruction", rendered)
        self.assertNotIn("Change appointment", rendered)

    def test_feedback_template_requires_synthetic_only_confirmation(self):
        payload = build_feedback_template()
        payload["synthetic_only_confirmation"] = False

        with self.assertRaises(SyntheticDataError):
            validate_feedback(payload)

    def test_feedback_validation_rejects_real_identifier_like_text(self):
        payload = build_feedback_template()
        payload["missing_information"] = "EXAMPLE_NOTE_12345678901"

        with self.assertRaises(SyntheticDataError):
            validate_feedback(payload)

    def test_feedback_template_validates_without_persistence(self):
        payload = build_feedback_template("SYNTHETIC_SCENARIO_ALPHA")
        feedback = validate_feedback(payload)

        self.assertEqual(feedback.scenario_id, "SYNTHETIC_SCENARIO_ALPHA")
        self.assertTrue(feedback.synthetic_only_confirmation)


if __name__ == "__main__":
    unittest.main()
