"""Security tests for the explicit Bug Hunter -> Bug Solver approval gate."""
import base64
import json
import unittest

from controller.bug_approval import ApprovalError, build_approved_task

SITES = {"sites": [{
    "id": "kingdom-raw",
    "repository": "kindgommangaraw/kindgommangaraw.github.io",
    "enabled": True,
    "authorized": True,
}]}
PLAN = {
    "site": "kingdom-raw",
    "repository": "kindgommangaraw/kindgommangaraw.github.io",
    "tasks": [{
        "id": "bug-01",
        "title": "Fix broken chapter navigation",
        "finding": "The chapter next link points to a missing slug.",
        "proposed_action": "Correct the next-chapter URL generation.",
        "acceptance_criteria": "The next and previous chapter links resolve to existing chapters.",
        "allowed_paths": ["chapter.html", "assets/js/reader.js"],
        "requires_captain_approval": True,
        "auto_apply": False,
    }],
}
ENCODED = base64.b64encode(json.dumps(PLAN).encode("utf-8")).decode("ascii")
COMMENTS = [{
    "created_at": "2026-11-03T10:00:00Z",
    "body": "<!-- bug-captain-tasks-b64\n" + ENCODED + "\n-->",
}]


def event(body="/approve-bug-task bug-01", author="WebControlerAgent", association="OWNER", title="[Bug Review] Chapter navigation"):
    return {
        "issue": {"number": 62, "title": title},
        "comment": {"body": body, "author_association": association, "user": {"login": author}},
    }


class BugApprovalTests(unittest.TestCase):
    def test_owner_approval_builds_bug_solver_task(self):
        task = build_approved_task(event(), COMMENTS, SITES)
        self.assertEqual(task["parent_captain"], "bug-solver")
        self.assertEqual(task["origin_captain"], "bug-hunter")
        self.assertEqual(task["task_type"], "bug_fix")
        self.assertEqual(task["allowed_paths"], ["chapter.html", "assets/js/reader.js"])
        self.assertTrue(task["captain_approval"]["approved"])

    def test_non_owner_is_rejected(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event(author="someone-else", association="CONTRIBUTOR"), COMMENTS, SITES)

    def test_wrong_issue_type_is_rejected(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event(title="[SEO Audit] wrong queue"), COMMENTS, SITES)

    def test_command_must_be_exact(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event("/approve-bug-task bug-01 please"), COMMENTS, SITES)

    def test_unknown_task_id_is_rejected(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event("/approve-bug-task bug-99"), COMMENTS, SITES)

    def test_duplicate_dispatch_is_rejected(self):
        comments = COMMENTS + [{"body": "<!-- BUG_APPROVAL_DISPATCHED:62:bug-01 -->"}]
        with self.assertRaises(ApprovalError):
            build_approved_task(event(), comments, SITES)

    def test_unapproved_or_auto_apply_task_is_rejected(self):
        plan = json.loads(json.dumps(PLAN))
        plan["tasks"][0]["auto_apply"] = True
        comments = [{"body": "<!-- bug-captain-tasks-b64 " + base64.b64encode(json.dumps(plan).encode()).decode() + " -->"}]
        with self.assertRaises(ApprovalError):
            build_approved_task(event(), comments, SITES)

    def test_forbidden_admin_and_secret_paths_are_rejected(self):
        for path in ("admin/login.js", ".env.production", ".github/workflows/deploy.yml", "config.json"):
            plan = json.loads(json.dumps(PLAN))
            plan["tasks"][0]["allowed_paths"] = [path]
            comments = [{"body": "<!-- bug-captain-tasks-b64 " + base64.b64encode(json.dumps(plan).encode()).decode() + " -->"}]
            with self.subTest(path=path), self.assertRaises(ApprovalError):
                build_approved_task(event(), comments, SITES)

    def test_untrusted_site_is_rejected(self):
        with self.assertRaises(ApprovalError):
            build_approved_task(event(), COMMENTS, {"sites": []})

    def test_missing_acceptance_criteria_is_rejected(self):
        plan = json.loads(json.dumps(PLAN))
        plan["tasks"][0]["acceptance_criteria"] = ""
        comments = [{"body": "<!-- bug-captain-tasks-b64 " + base64.b64encode(json.dumps(plan).encode()).decode() + " -->"}]
        with self.assertRaises(ApprovalError):
            build_approved_task(event(), comments, SITES)


if __name__ == "__main__":
    unittest.main()
