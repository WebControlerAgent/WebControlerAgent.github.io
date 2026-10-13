"""Tests for deterministic patch scope/risk validation."""
import unittest

from controller.patch_review import validate_patch


class PatchReviewTests(unittest.TestCase):
    def setUp(self):
        self.task = {"allowed_paths": ["index.html"]}

    def test_allowed_patch_passes_but_still_requires_review(self):
        patch = (
            "diff --git a/index.html b/index.html\n"
            "index 1111111..2222222 100644\n"
            "--- a/index.html\n"
            "+++ b/index.html\n"
            "@@ -1 +1 @@\n"
            "-<title>Old</title>\n"
            "+<title>New</title>\n"
        )
        result = validate_patch(self.task, patch)
        self.assertTrue(result["passed"])
        self.assertEqual(result["state"], "READY_FOR_CAPTAIN_REVIEW")
        self.assertTrue(result["human_or_ai_code_review_still_required"])
        self.assertFalse(result["automatic_merge"])

    def test_out_of_scope_path_is_blocked(self):
        patch = "diff --git a/index.html b/admin.js\n--- a/index.html\n+++ b/admin.js\n"
        result = validate_patch(self.task, patch)
        self.assertFalse(result["passed"])
        self.assertEqual(result["state"], "BLOCKED")

    def test_secret_pattern_requires_human_review(self):
        patch = (
            "diff --git a/index.html b/index.html\n"
            "--- a/index.html\n+++ b/index.html\n"
            "+const token = \"ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890\";\n"
        )
        result = validate_patch(self.task, patch)
        self.assertFalse(result["passed"])
        self.assertEqual(result["state"], "NEEDS_HUMAN_REVIEW")


if __name__ == "__main__":
    unittest.main()
