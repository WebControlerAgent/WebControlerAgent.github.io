"""Security and scope tests for explicit SEO Captain approval."""
import base64
import json
import unittest

from controller.seo_approval import ApprovalError, build_approved_task

SITES = {"sites": [{
    "id": "kingdom-raw",
    "repository": "kindgommangaraw/kindgommangaraw.github.io",
    "enabled": True,
    "authorized": True,
}]}
PLAN = {
    "site": "kingdom-raw",
    "repository": "kindgommangaraw/kindgommangaraw.github.io",
    "tasks": [
        {
            "id": "seo-01",
            "title": "Add or correct the homepage meta description",
            "finding": "Homepage meta description is missing.",
            "proposed_action": "Add a concise description.",
            "acceptance_criteria": "A fresh audit detects a non-empty description.",
        },
        {
            "id": "seo-review-01",
            "title": "Record clean technical SEO audit",
            "finding": "No technical findings.",
            "proposed_action": "Keep as baseline.",
            "acceptance_criteria": "Captain acknowledges baseline.",
        },
    ],
}
COMMENTS = [{
    "created_at": "2026-11-02T10:00:00Z",
    "body": "<!-- seo-captain-tasks-json\n" + __import__("json").dumps(PLAN) + "\n-->",
}]


def event(body="/approve-seo-task seo-01", author="WebControlerAgent", association="OWNER"):
    return {
        "issue": {"number": 51, "title": "[SEO Audit] Verify SEO"},
        "comment": {
            "body": body,
            "author_association": association,
            "user": {"login": author},
        },
    }


class SeoApprovalTests(unittest.TestCase):
    def test_owner_approval_builds_narrow_proposal_task(self):
        task = build_approved_task(event(), COMMENTS, SITES)
        self.assertEqual(task["task_type"], "code_change_proposal")
        self.assertEqual(task["allowed_paths"], ["index.html"])
        self.assertEqual(task["parent_captain"], "bug-solver")
        self.assertEqual(task["origin_captain"], "seo-agent")
        self.assertTrue(task["captain_approval"]["approved"])

    def test_non_owner_cannot_approve(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event(author="random-user", association="CONTRIBUTOR"), COMMENTS, SITES)

    def test_clean_baseline_cannot_launch_code_worker(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event("/approve-seo-task seo-review-01"), COMMENTS, SITES)

    def test_unknown_task_cannot_launch_worker(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event("/approve-seo-task seo-99"), COMMENTS, SITES)

    def test_unknown_task_type_without_allowlist_is_blocked(self):
        changed = {"site": PLAN["site"], "repository": PLAN["repository"], "tasks": [{
            "id": "seo-02", "title": "Review technical SEO finding",
            "finding": "Unknown issue", "proposed_action": "Investigate",
            "acceptance_criteria": "Verified",
        }]}
        comments = [{"body": "<!-- seo-captain-tasks-json\n" + __import__("json").dumps(changed) + "\n-->"}]
        with self.assertRaises(ApprovalError):
            build_approved_task(event("/approve-seo-task seo-02"), comments, SITES)

    def test_unauthorized_site_is_blocked(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event(), COMMENTS, {"sites": []})

    def test_command_must_be_exact(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event("/approve-seo-task seo-01 please"), COMMENTS, SITES)

    def test_duplicate_approval_dispatch_is_rejected(self):
        comments = COMMENTS + [{
            "body": "<!-- SEO_APPROVAL_DISPATCHED:51:seo-01 -->",
            "created_at": "2026-11-02T10:01:00Z",
        }]
        with self.assertRaises(ApprovalError):
            build_approved_task(event(), comments, SITES)


if __name__ == "__main__":
    unittest.main()
