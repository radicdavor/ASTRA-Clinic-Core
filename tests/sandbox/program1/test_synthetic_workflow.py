"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import unittest

from sandbox.program1.models import (
    SAFETY_BANNER,
    SyntheticDataError,
    SyntheticPatient,
)
from sandbox.program1.sample_data import build_sample_workflow
from sandbox.program1.workflow import build_workflow_summary


class SyntheticWorkflowTests(unittest.TestCase):
    def test_sample_workflow_is_synthetic_and_sandbox_only(self):
        patient, encounter, findings, review = build_sample_workflow()
        summary = build_workflow_summary(review)

        self.assertIn(SAFETY_BANNER, summary["safety_banner"])
        self.assertEqual(patient.synthetic_patient_id, "SYNTHETIC_PATIENT_ALPHA")
        self.assertEqual(encounter.encounter_id, "SYNTHETIC_ENCOUNTER_ALPHA")
        self.assertEqual(len(findings), 2)
        self.assertTrue(review.note.startswith("DEMO_REVIEW_NOTE_SYNTHETIC_ONLY"))
        self.assertIs(summary["sandbox_only"], True)
        self.assertIs(summary["clinical_use_authorized"], False)
        self.assertIs(summary["real_patient_data_allowed"], False)
        self.assertIs(summary["phi_pii_allowed"], False)
        self.assertIs(summary["external_integrations_enabled"], False)
        self.assertIs(summary["appointment_mutation_enabled"], False)
        self.assertIs(summary["patient_messaging_enabled"], False)
        self.assertIs(summary["approval_override_enabled"], False)

    def test_real_identifier_like_values_are_rejected(self):
        with self.assertRaises(SyntheticDataError):
            SyntheticPatient(
                synthetic_patient_id="SYNTHETIC_PATIENT_12345678901",
                display_label="DEMO_ONLY_PATIENT_ALPHA",
            )

    def test_values_must_be_marked_as_synthetic_or_demo_or_example(self):
        with self.assertRaises(SyntheticDataError):
            SyntheticPatient(
                synthetic_patient_id="PATIENT_ALPHA",
                display_label="DEMO_ONLY_PATIENT_ALPHA",
            )


if __name__ == "__main__":
    unittest.main()
