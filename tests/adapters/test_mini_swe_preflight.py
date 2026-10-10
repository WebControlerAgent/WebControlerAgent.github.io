"""Security regression tests for the mini-SWE patch gate."""
import tempfile
import unittest
from pathlib import Path

from agents.adapters.mini_swe_preflight import inspect_patch, _path_block_reason


class PatchGateTests(unittest.TestCase):
    def inspect(self, patch_text: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.patch"
            path.write_text(patch_text, encoding="utf-8")
            return inspect_patch(str(path))

    def test_allows_scoped_patch_but_requires_human_review(self):
        result = self.inspect(
            "diff --git a/controller/example.py b/controller/example.py\n"
            "--- a/controller/example.py\n+++ b/controller/example.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        )
        self.assertEqual(result["review_state"], "PATCH_PRESENT_REQUIRES_HUMAN_REVIEW")
        self.assertFalse(result["automatic_merge"])
        self.assertFalse(result["automatic_deploy"])

    def test_blocks_workflow_changes(self):
        result = self.inspect(
            "diff --git a/.github/workflows/deploy.yml b/.github/workflows/deploy.yml\n"
            "--- a/.github/workflows/deploy.yml\n+++ b/.github/workflows/deploy.yml\n"
        )
        self.assertEqual(result["review_state"], "BLOCKED")

    def test_blocks_renamed_secret_even_if_new_path_is_allowed(self):
        result = self.inspect(
            "diff --git a/.env b/agents/harmless.py\n"
            "--- a/.env\n+++ b/agents/harmless.py\n"
        )
        self.assertEqual(result["review_state"], "BLOCKED")
        self.assertIn(".env", [p["path"] for p in result["blocked_paths"]])

    def test_blocks_path_traversal_and_backslashes(self):
        self.assertIsNotNone(_path_block_reason("agents/../../secret.txt"))
        self.assertIsNotNone(_path_block_reason("agents\\..\\secret.txt"))

    def test_rejects_non_diff_text(self):
        result = self.inspect("hello world")
        self.assertEqual(result["review_state"], "INVALID_PATCH")


if __name__ == "__main__":
    unittest.main()
