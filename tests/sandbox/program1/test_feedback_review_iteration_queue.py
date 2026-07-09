"""Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use."""

import io
import unittest
from contextlib import redirect_stdout

from sandbox.program1.cli import main
from sandbox.program1.feedback_review import (
    build_synthetic_feedback_examples,
    render_feedback_review,
    review_feedback,
)
from sandbox.program1.iteration_queue import build_iteration_queue
from sandbox.program1.models import SAFETY_BANNER


class FeedbackReviewIterationQueueTests(unittest.TestCase):
    def test_feedback_review_output_includes_safety_warning(self):
        review = review_feedback()
        rendered = render_feedback_review(review)

        self.assertIn(SAFETY_BANNER, rendered)
        self.assertIn("Local sandbox only. Not for clinical use.", rendered)
        self.assertIn("Network/database behavior: disabled", rendered)
        self.assertIn("External integrations: disabled", rendered)
        self.assertIn("Real patient data: not allowed", rendered)
        self.assertIn("PHI/PII: not allowed", rendered)

    def test_synthetic_feedback_examples_validate(self):
        review = review_feedback(build_synthetic_feedback_examples())

        self.assertEqual(review["feedback_count"], 2)
        self.assertTrue(review["local_only"])
        self.assertFalse(review["network_or_database_used"])

    def test_iteration_queue_items_preserve_sandbox_only_boundary(self):
        queue = build_iteration_queue(build_synthetic_feedback_examples())

        self.assertGreaterEqual(len(queue), 2)
        for item in queue:
            self.assertTrue(item.allowed_in_sandbox)
            self.assertEqual(item.safety_boundary, "DEMO_BOUNDARY_SYNTHETIC_LOCAL_ONLY")
            self.assertEqual(
                item.prohibited_escalation,
                "DEMO_PROHIBIT_PRODUCTION_CLINICAL_REAL_DATA_ESCALATION",
            )

    def test_cli_review_feedback_prints_local_summary(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["review-feedback"])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn(SAFETY_BANNER, text)
        self.assertIn("Design iteration queue:", text)
        self.assertIn("Clinical use: not authorized", text)

    def test_feedback_review_output_uses_readable_queue_text(self):
        rendered = render_feedback_review(review_feedback())

        self.assertIn("Design iteration queue item 1", rendered)
        self.assertIn("Workflow clarity", rendered)
        self.assertIn("does not create a clinical task", rendered)
        self.assertNotIn("SYNTHETIC_QUEUE_ITEM_1", rendered)
        self.assertNotIn("DEMO_THEME_WORKFLOW_CLARITY", rendered)


if __name__ == "__main__":
    unittest.main()
