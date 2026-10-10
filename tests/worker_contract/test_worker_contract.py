"""Tests for the worker-result pair acceptance gate."""
import unittest

from controller.worker_contract import validate_result_pair


TASK = {"task_id": "task-001"}
ASSIGNMENT = {"assignments": [
    {"agent_id": "bug-solver/patch-agent", "role": "primary_worker"},
    {"agent_id": "bug-solver/patch-reviewer", "role": "independent_checker"},
]}
PRIMARY = {
    "task_id": "task-001",
    "agent_id": "bug-solver/patch-agent",
    "state": "DONE",
    "summary": "Prepared a candidate patch.",
    "evidence": ["unit tests executed: 5 passed"],
    "artifacts": ["candidate.patch"],
    "changed_files": ["controller/worker_contract.py"],
    "next_action": "Review patch",
}
CHECKER = {
    "task_id": "task-001",
    "agent_id": "bug-solver/patch-reviewer",
    "state": "REVIEWED",
    "independent_summary": "Reviewed patch and test evidence.",
    "independent_evidence": ["independent review checklist completed"],
    "findings": [],
    "next_action": "Captain review",
}


class WorkerContractTests(unittest.TestCase):
    def test_valid_pair_still_requires_captain_approval(self):
        result = validate_result_pair(TASK, ASSIGNMENT, PRIMARY, CHECKER)
        self.assertEqual(result["state"], "READY_FOR_CAPTAIN_REVIEW")
        self.assertTrue(result["captain_approval_required"])
        self.assertFalse(result["automatic_merge"])
        self.assertFalse(result["automatic_deploy"])

    def test_missing_checker_blocks_completion(self):
        result = validate_result_pair(TASK, ASSIGNMENT, PRIMARY, None)
        self.assertEqual(result["state"], "VERIFYING")
        self.assertTrue(any("missing" in p.lower() for p in result["problems"]))

    def test_wrong_task_id_blocks_pair(self):
        bad_checker = dict(CHECKER, task_id="other-task")
        result = validate_result_pair(TASK, ASSIGNMENT, PRIMARY, bad_checker)
        self.assertEqual(result["state"], "VERIFYING")
        self.assertTrue(any("task_id" in p for p in result["problems"]))

    def test_primary_cannot_impersonate_checker(self):
        bad_checker = dict(CHECKER, agent_id=PRIMARY["agent_id"])
        result = validate_result_pair(TASK, ASSIGNMENT, PRIMARY, bad_checker)
        self.assertEqual(result["state"], "VERIFYING")
        self.assertTrue(any("different agent" in p for p in result["problems"]))

    def test_empty_checker_evidence_blocks_pair(self):
        bad_checker = dict(CHECKER, independent_evidence=[])
        result = validate_result_pair(TASK, ASSIGNMENT, PRIMARY, bad_checker)
        self.assertEqual(result["state"], "VERIFYING")


if __name__ == "__main__":
    unittest.main()
