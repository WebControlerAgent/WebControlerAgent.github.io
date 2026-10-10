"""Tests for deterministic worker queue packet creation."""
import unittest

from controller.task_dispatcher import DispatchError, load_json
from controller.worker_queue import ROOT, prepare_queue, validate_task_scope

TASK = {
    "task_id": "queue-test-001",
    "site": "kingdom-raw",
    "repository": "kindgommangaraw/kindgommangaraw.github.io",
    "parent_captain": "publisher",
    "task_type": "feature_or_visual_change",
    "objective": "Prepare a small UI improvement proposal",
    "allowed_paths": ["public/"],
    "constraints": ["No deploy", "Return evidence"],
    "success_criteria": ["Proposal is reviewable"],
}

class WorkerQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routing = load_json(ROOT / "agents" / "task_routing.json")
        cls.sites = load_json(ROOT / "controller" / "sites.json")

    def test_queue_has_primary_and_independent_checker(self):
        queue = prepare_queue(TASK, self.routing, self.sites)
        self.assertEqual(queue["queue_state"], "PENDING_WORKER_RUNTIME")
        self.assertEqual(len(queue["jobs"]), 2)
        self.assertEqual({job["role"] for job in queue["jobs"]},
                         {"primary_worker", "independent_checker"})
        self.assertTrue(all(job["execution"]["captain_approval_required"]
                            for job in queue["jobs"]))
        self.assertTrue(all(not job["execution"]["model_invoked"] for job in queue["jobs"]))

    def test_rejects_traversal_path(self):
        task = dict(TASK, allowed_paths=["public/../../.github/workflows"])
        with self.assertRaises(DispatchError):
            validate_task_scope(task)

    def test_rejects_workflow_and_secret_paths(self):
        for path in (".github/workflows/deploy.yml", "agents/api_token.json"):
            with self.subTest(path=path), self.assertRaises(DispatchError):
                validate_task_scope(dict(TASK, allowed_paths=[path]))

    def test_rejects_unknown_site(self):
        task = dict(TASK, site="unapproved-site")
        with self.assertRaises(DispatchError):
            prepare_queue(task, self.routing, self.sites)

if __name__ == "__main__":
    unittest.main()
