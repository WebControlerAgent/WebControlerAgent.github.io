"""Contract tests for the bounded code-change proposal worker."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from controller.code_change_worker import (
    CodeChangeError, check_proposal, prepare_proposal,
)

SITES = {"sites": [{
    "id": "demo", "repository": "owner/site",
    "enabled": True, "authorized": True,
}]}


def task(**updates):
    result = {
        "task_id": "change-001",
        "site": "demo",
        "repository": "owner/site",
        "task_type": "code_change_proposal",
        "objective": "Add a small example module",
        "allowed_paths": ["src/example.py"],
        "changes": [{"path": "src/example.py", "content": "VALUE = 1\n"}],
    }
    result.update(updates)
    return result


class CodeChangeWorkerTests(unittest.TestCase):
    def test_prepares_candidate_without_modifying_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = prepare_proposal(task(), SITES, Path(tmp) / "out")
            self.assertEqual(report["state"], "READY_FOR_INDEPENDENT_CHECK")
            self.assertFalse(report["repository_modified"])
            self.assertFalse(report["write_access"])
            self.assertTrue((Path(report["candidate_directory"]) / "src/example.py").is_file())

    def test_checker_accepts_unchanged_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            proposal = prepare_proposal(task(), SITES, Path(tmp) / "out")
            result = check_proposal(proposal, task(), SITES)
            self.assertEqual(result["state"], "REVIEWED")
            self.assertEqual(result["findings"], [])

    def test_checker_detects_tampered_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            proposal = prepare_proposal(task(), SITES, Path(tmp) / "out")
            (Path(proposal["candidate_directory"]) / "src/example.py").write_text("VALUE = 2\n")
            result = check_proposal(proposal, task(), SITES)
            self.assertEqual(result["state"], "BLOCKED")
            self.assertTrue(any("Hash mismatch" in x for x in result["findings"]))

    def test_rejects_unauthorized_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CodeChangeError):
                prepare_proposal(task(site="other"), SITES, Path(tmp) / "out")

    def test_rejects_repository_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CodeChangeError):
                prepare_proposal(task(repository="attacker/repo"), SITES, Path(tmp) / "out")

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CodeChangeError):
                prepare_proposal(task(allowed_paths=["../outside.py"],
                                      changes=[{"path": "../outside.py", "content": "x"}]),
                                 SITES, Path(tmp) / "out")

    def test_rejects_path_not_in_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CodeChangeError):
                prepare_proposal(task(changes=[{"path": "src/other.py", "content": "x"}]),
                                 SITES, Path(tmp) / "out")

    def test_rejects_sensitive_paths(self):
        for path in (".env", "controller/sites.json", ".github/workflows/deploy.yml", "dist/index.html"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(CodeChangeError):
                    prepare_proposal(task(allowed_paths=[path],
                                          changes=[{"path": path, "content": "x"}]),
                                     SITES, Path(tmp) / "out")

    def test_rejects_wrong_task_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CodeChangeError):
                prepare_proposal(task(task_type="deploy"), SITES, Path(tmp) / "out")

    def test_rejects_duplicate_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CodeChangeError):
                prepare_proposal(task(changes=[
                    {"path": "src/example.py", "content": "a"},
                    {"path": "src/example.py", "content": "b"},
                ]), SITES, Path(tmp) / "out")

    def test_checker_blocks_modified_authority_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            proposal = prepare_proposal(task(), SITES, Path(tmp) / "out")
            proposal["automatic_deploy"] = True
            result = check_proposal(proposal, task(), SITES)
            self.assertEqual(result["state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
