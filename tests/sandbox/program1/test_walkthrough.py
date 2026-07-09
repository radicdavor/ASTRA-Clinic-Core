"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import io
import unittest
from contextlib import redirect_stdout

from sandbox.program1.cli import main
from sandbox.program1.models import SAFETY_BANNER
from sandbox.program1.walkthrough import build_walkthrough_packet, render_walkthrough


class WalkthroughTests(unittest.TestCase):
    def test_walkthrough_output_includes_synthetic_warning(self):
        packet = build_walkthrough_packet()
        rendered = render_walkthrough(packet)

        self.assertIn(SAFETY_BANNER, rendered)
        self.assertIn("Local sandbox only. Non-production. Not for clinical use.", rendered)

    def test_walkthrough_lists_core_local_commands(self):
        rendered = render_walkthrough(build_walkthrough_packet())

        self.assertIn("python -m sandbox.program1.cli summary --scenario alpha", rendered)
        self.assertIn("python -m sandbox.program1.cli trial --scenario alpha", rendered)
        self.assertIn("python -m sandbox.program1.cli review-feedback", rendered)

    def test_walkthrough_does_not_imply_readiness(self):
        packet = build_walkthrough_packet()

        self.assertFalse(packet["clinical_use_authorized"])
        self.assertFalse(packet["real_patient_data_allowed"])
        self.assertFalse(packet["phi_pii_allowed"])
        self.assertFalse(packet["cloud_ready"])
        self.assertFalse(packet["network_or_database_used"])
        self.assertFalse(packet["external_integrations_enabled"])
        self.assertFalse(packet["go_live_authorized"])

    def test_cli_walkthrough_prints_local_pack(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["walkthrough"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn(SAFETY_BANNER, text)
        self.assertIn("Available synthetic scenarios:", text)
        self.assertIn("Safety confirmations:", text)


if __name__ == "__main__":
    unittest.main()
