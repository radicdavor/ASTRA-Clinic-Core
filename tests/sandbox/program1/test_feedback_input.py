"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from sandbox.program1.cli import main
from sandbox.program1.feedback_input import (
    build_feedback_input_preview,
    render_feedback_input_preview,
)
from sandbox.program1.models import SAFETY_BANNER


class FeedbackInputTests(unittest.TestCase):
    def test_feedback_input_with_text_renders_local_preview(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "feedback-input",
                    "--text",
                    "The review note is easier to understand now.",
                ]
            )

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("Program 1 Synthetic Sandbox Feedback Preview", text)
        self.assertIn(SAFETY_BANNER, text)
        self.assertIn("Local synthetic design feedback", text)
        self.assertIn("The review note is easier to understand now.", text)
        self.assertIn("Persisted: no", text)
        self.assertIn("Sent externally: no", text)
        self.assertIn("Clinical task created: no", text)
        self.assertIn("Patient message created: no", text)
        self.assertIn("Appointment changed: no", text)
        self.assertIn("Workflow enforced: no", text)
        self.assertIn("Clinical writeback performed: no", text)
        self.assertIn("Approval/override created: no", text)

    def test_feedback_input_with_empty_text_handles_safely(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["feedback-input", "--text", ""])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("No feedback text was entered", text)
        self.assertIn("No data was stored or transmitted", text)

    def test_feedback_input_json_retains_safety_flags(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "feedback-input",
                    "--text",
                    "The review note is easier to understand now.",
                    "--json",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(output.getvalue())
        self.assertTrue(payload["synthetic_only"])
        self.assertTrue(payload["non_production"])
        self.assertFalse(payload["clinical_use_authorized"])
        self.assertFalse(payload["real_patient_data_allowed"])
        self.assertFalse(payload["phi_pii_allowed"])
        self.assertFalse(payload["persisted"])
        self.assertFalse(payload["sent_externally"])
        self.assertFalse(payload["clinical_task_created"])
        self.assertFalse(payload["patient_message_created"])
        self.assertFalse(payload["appointment_mutation_performed"])
        self.assertFalse(payload["workflow_enforced"])
        self.assertFalse(payload["clinical_writeback_performed"])
        self.assertFalse(payload["approval_override_created"])
        self.assertFalse(payload["go_live_authorized"])

    def test_interactive_mode_only_prompts_when_explicit(self):
        output = io.StringIO()
        with patch("builtins.input", return_value="Synthetic design comment."):
            with redirect_stdout(output):
                exit_code = main(["feedback-input", "--interactive"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("Synthetic-only local feedback input", text)
        self.assertIn("Synthetic design comment.", text)

    def test_feedback_input_identifier_like_text_warns_without_persistence(self):
        preview = build_feedback_input_preview("Synthetic note with test@example.invalid")
        rendered = render_feedback_input_preview(preview)

        self.assertTrue(preview["identifier_warning"])
        self.assertIn("identifier-like pattern", rendered)
        self.assertFalse(preview["persisted"])
        self.assertFalse(preview["sent_externally"])


if __name__ == "__main__":
    unittest.main()
