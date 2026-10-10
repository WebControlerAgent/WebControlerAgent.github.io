"""Unit tests for the proposal-only model runtime; no network/API calls."""
import unittest
from controller.model_worker_runtime import RuntimeErrorSafe, validate_proposal, validate_task

TASK = {
    "task_id": "runtime-test-001",
    "site": "kingdom-raw",
    "repository": "kindgommangaraw/kindgommangaraw.github.io",
    "parent_captain": "publisher",
    "task_type": "feature_or_visual_change",
    "objective": "Propose a small UI improvement",
    "allowed_paths": ["public/"],
    "constraints": ["No deploy"],
    "success_criteria": ["Reviewable proposal"],
}

class ModelRuntimeTests(unittest.TestCase):
    def test_valid_task(self):
        validate_task(TASK)

    def test_rejects_unapproved_repository(self):
        with self.assertRaises(RuntimeErrorSafe):
            validate_task(dict(TASK, repository="someone/else"))

    def test_rejects_workflow_scope(self):
        with self.assertRaises(RuntimeErrorSafe):
            validate_task(dict(TASK, allowed_paths=[".github/workflows/"]))

    def test_accepts_proposal_within_scope(self):
        proposal = validate_proposal({"summary":"proposal","evidence":[],"files":[
            {"path":"public/example.json","content":"{}"}
        ]}, TASK)
        self.assertEqual(proposal["changed_files"], ["public/example.json"])

    def test_rejects_path_traversal(self):
        with self.assertRaises(RuntimeErrorSafe):
            validate_proposal({"files":[{"path":"public/../.github/workflows/a.yml","content":"x"}]}, TASK)

    def test_rejects_path_outside_allowlist(self):
        with self.assertRaises(RuntimeErrorSafe):
            validate_proposal({"files":[{"path":"controller/admin.py","content":"x"}]}, TASK)

    def test_rejects_large_file(self):
        with self.assertRaises(RuntimeErrorSafe):
            validate_proposal({"files":[{"path":"public/a.txt","content":"x"*100001}]}, TASK)

if __name__ == "__main__":
    unittest.main()
