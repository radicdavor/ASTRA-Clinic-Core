"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import io
import json
import unittest
from contextlib import redirect_stdout

from sandbox.program1.cli import main
from sandbox.program1.models import SAFETY_BANNER
from sandbox.program1.session_recap import build_session_recap, render_session_recap


class SessionRecapTests(unittest.TestCase):
    def test_session_recap_alpha_renders_clinician_readable_recap(self):
        rendered = render_session_recap(build_session_recap("alpha"))

        self.assertIn("Program 1 Synthetic Sandbox Session Recap", rendered)
        self.assertIn(SAFETY_BANNER, rendered)
        self.assertIn("Synthetic patient A", rendered)
        self.assertIn("Example review visit", rendered)
        self.assertIn("Missing context in uploaded record", rendered)
        self.assertIn("Follow-up context placeholder", rendered)
        self.assertIn("No diagnosis, treatment, triage", rendered)

    def test_session_recap_beta_renders_clinician_readable_recap(self):
        rendered = render_session_recap(build_session_recap("beta"))

        self.assertIn("Synthetic patient B", rendered)
        self.assertIn("Boundary review visit", rendered)
        self.assertIn("Visibility of safety boundary", rendered)

    def test_session_recap_with_feedback_includes_local_preview(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "session-recap",
                    "--scenario",
                    "alpha",
                    "--feedback",
                    "The review note is easier to understand now.",
                ]
            )

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("Synthetic feedback preview:", text)
        self.assertIn("The review note is easier to understand now.", text)
        self.assertIn("not stored, not transmitted", text)
        self.assertIn("not converted into a clinical task", text)

    def test_session_recap_without_feedback_handles_safely(self):
        rendered = render_session_recap(build_session_recap("alpha"))

        self.assertIn("No feedback text was entered", rendered)
        self.assertIn("No data was stored or transmitted", rendered)

    def test_session_recap_confirms_no_side_effects(self):
        rendered = render_session_recap(build_session_recap("alpha"))

        self.assertIn("Persistence: disabled", rendered)
        self.assertIn("Transmission: disabled", rendered)
        self.assertIn("Network/database: disabled", rendered)
        self.assertIn("Patient messaging: disabled", rendered)
        self.assertIn("Appointment mutation: disabled", rendered)
        self.assertIn("Workflow enforcement: disabled", rendered)
        self.assertIn("Clinical writeback: disabled", rendered)
        self.assertIn("Clinical task creation: disabled", rendered)
        self.assertIn("Approval/override capability: disabled", rendered)

    def test_session_recap_json_retains_safety_flags(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "session-recap",
                    "--scenario",
                    "alpha",
                    "--feedback",
                    "The review note is easier to understand now.",
                    "--json",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["scenario"], "alpha")
        self.assertTrue(payload["feedback_entered"])
        self.assertTrue(payload["synthetic_only"])
        self.assertTrue(payload["non_production"])
        self.assertFalse(payload["clinical_use_authorized"])
        self.assertFalse(payload["real_patient_data_allowed"])
        self.assertFalse(payload["phi_pii_allowed"])
        self.assertFalse(payload["persisted"])
        self.assertFalse(payload["sent_externally"])
        self.assertFalse(payload["network_or_database_used"])
        self.assertFalse(payload["patient_message_created"])
        self.assertFalse(payload["appointment_mutation_performed"])
        self.assertFalse(payload["workflow_enforced"])
        self.assertFalse(payload["clinical_writeback_performed"])
        self.assertFalse(payload["clinical_task_created"])
        self.assertFalse(payload["approval_override_created"])
        self.assertFalse(payload["go_live_authorized"])

    def test_session_recap_default_output_avoids_internal_placeholder_labels(self):
        rendered = render_session_recap(build_session_recap("alpha"))

        for placeholder in (
            "DEMO_FINDING_CONTEXT_REVIEW",
            "DEMO_ONLY_PATIENT_ALPHA",
            "SYNTHETIC_QUEUE_ITEM_1",
            "EXAMPLE_FINDING_SUMMARY_FOR_SYNTHETIC_WORKFLOW_ONLY",
        ):
            self.assertNotIn(placeholder, rendered)


if __name__ == "__main__":
    unittest.main()
