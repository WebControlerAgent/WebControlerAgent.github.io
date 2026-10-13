"""Contract tests for the validated worker execution bridge."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from controller.task_dispatcher import load_json
from controller.worker_execution_bridge import execute_validated_task

ROOT = Path(__file__).resolve().parent.parent


class WorkerExecutionBridgeTests(unittest.TestCase):
    def setUp(self):
        self.routing = load_json(ROOT / "agents" / "task_routing.json")
        self.sites = load_json(ROOT / "controller" / "sites.json")
        site = next(s for s in self.sites["sites"] if s.get("enabled") and s.get("authorized"))
        self.task = {
            "task_id": "bridge-test",
            "site": site["id"],
            "repository": site["repository"],
            "parent_captain": "bug-solver",
            "task_type": "bug_fix",
            "objective": "Fix the approved bug",
            "allowed_paths": ["src/fix.py"],
            "constraints": ["Do not deploy"],
            "success_criteria": ["Regression test passes"],
        }

    def test_valid_task_calls_adapter_and_keeps_review_gate(self):
        with patch(
            "controller.worker_execution_bridge.run_coding_task",
            return_value={"state": "READY_FOR_INDEPENDENT_CHECK", "executed": True},
        ) as worker:
            result = execute_validated_task(
                self.task, self.routing, self.sites, "/tmp/checkout", "/tmp/artifacts", environ={}
            )
        worker.assert_called_once()
        self.assertTrue(result["dispatch_validated"])
        self.assertEqual(result["assignment"]["primary_worker"], "bug-solver/patch-agent")
        self.assertEqual(result["assignment"]["independent_checker"], "bug-solver/patch-reviewer")
        self.assertTrue(result["assignment"]["captain_approval_required"])

    def test_invalid_captain_is_blocked_before_worker_launch(self):
        task = dict(self.task, parent_captain="not-a-captain")
        with patch("controller.worker_execution_bridge.run_coding_task") as worker:
            result = execute_validated_task(
                task, self.routing, self.sites, "/tmp/checkout", "/tmp/artifacts"
            )
        worker.assert_not_called()
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["executed"])

    def test_research_task_never_reaches_coding_adapter(self):
        task = dict(self.task, task_type="research", parent_captain="researcher")
        with patch("controller.worker_execution_bridge.run_coding_task") as worker:
            result = execute_validated_task(
                task, self.routing, self.sites, "/tmp/checkout", "/tmp/artifacts"
            )
        worker.assert_not_called()
        self.assertEqual(result["state"], "BLOCKED")
        self.assertTrue(result["dispatch_validated"])


if __name__ == "__main__":
    unittest.main()
