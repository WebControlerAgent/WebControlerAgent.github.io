"""Unit tests for the two-agent dispatch contract."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "controller"))
from task_dispatcher import DispatchError, prepare_assignment

ROUTING = json.loads((ROOT / "agents" / "task_routing.json").read_text(encoding="utf-8"))
SITES = json.loads((ROOT / "controller" / "sites.json").read_text(encoding="utf-8"))
AUTHORIZED = next(s for s in SITES["sites"] if s.get("enabled") and s.get("authorized"))

def sample_task(**updates):
    task = {
        "task_id": "test-feature-001",
        "site": AUTHORIZED["id"],
        "repository": "WebControlerAgent/WebControlerAgent.github.io",
        "parent_captain": "publisher",
        "task_type": "feature_or_visual_change",
        "objective": "Verify two-agent assignment",
        "allowed_paths": ["src/main.tsx"],
        "constraints": ["Do not deploy during test"],
        "success_criteria": ["Assignment contains distinct worker and checker"],
        "depends_on": [],
        "completed_dependencies": [],
    }
    task.update(updates)
    return task

class DispatchPairTests(unittest.TestCase):
    def test_assigns_two_distinct_agents(self):
        result = prepare_assignment(sample_task(), ROUTING, SITES)
        assignments = result["assignments"]
        self.assertEqual(result["minimum_small_agents"], 2)
        self.assertEqual(len(assignments), 2)
        self.assertNotEqual(assignments[0]["agent_id"], assignments[1]["agent_id"])
        self.assertEqual(assignments[0]["role"], "primary_worker")
        self.assertEqual(assignments[1]["role"], "independent_checker")

    def test_rejects_unknown_captain_pair(self):
        with self.assertRaises(DispatchError):
            prepare_assignment(sample_task(parent_captain="qa"), ROUTING, SITES)

    def test_rejects_unresolved_dependencies(self):
        with self.assertRaises(DispatchError):
            prepare_assignment(sample_task(depends_on=["prep-1"]), ROUTING, SITES)

    def test_rejects_missing_success_criteria(self):
        with self.assertRaises(DispatchError):
            prepare_assignment(sample_task(success_criteria=[]), ROUTING, SITES)

if __name__ == "__main__":
    unittest.main()
