"""Tests for the deterministic read-only QA worker."""
import unittest

from controller.health_worker import HealthWorkerError, execute_task


SITES = {"sites": [{
    "id": "kingdom-raw",
    "repository": "kindgommangaraw/kindgommangaraw.github.io",
    "live_url": "https://jpmangaatlis.online/",
    "enabled": True,
    "authorized": True,
}]}
TASK = {
    "task_id": "health-test-001",
    "site": "kingdom-raw",
    "repository": "kindgommangaraw/kindgommangaraw.github.io",
    "task_type": "read_only_health_check",
    "objective": "Verify live site and SEO endpoints",
}


class HealthWorkerTests(unittest.TestCase):
    def test_success_requires_matching_primary_and_checker_evidence(self):
        calls = []
        def check(site, agent):
            calls.append((site["id"], agent))
            return True, "HTTP 200; robots and sitemap valid"
        report = execute_task(TASK, SITES, check)
        self.assertEqual(report["state"], "READY_FOR_CAPTAIN_REVIEW")
        self.assertEqual(len(calls), 2)
        self.assertEqual(report["primary_result"]["agent_id"], "qa/seo-tester")
        self.assertEqual(report["independent_checker_result"]["agent_id"], "qa/seo-independent-checker")
        self.assertTrue(report["captain_approval_required"])
        self.assertFalse(report["automatic_merge"])
        self.assertFalse(report["automatic_deploy"])

    def test_failed_health_check_cannot_pass_gate(self):
        report = execute_task(TASK, SITES, lambda site, agent: (False, "sitemap returned 503"))
        self.assertEqual(report["state"], "VERIFYING")
        self.assertFalse(report["contract_gate"]["state"] == "READY_FOR_CAPTAIN_REVIEW")

    def test_mismatched_primary_and_checker_evidence_is_blocked(self):
        values = iter([(True, "HTTP 200"), (True, "HTTP 503")])
        report = execute_task(TASK, SITES, lambda site, agent: next(values))
        self.assertFalse(report["evidence_consistent"])
        self.assertEqual(report["state"], "VERIFYING")

    def test_unauthorized_site_is_rejected(self):
        task = dict(TASK, site="unknown")
        with self.assertRaises(HealthWorkerError):
            execute_task(task, SITES, lambda site, agent: (True, "ok"))

    def test_repository_must_match_authorized_site(self):
        task = dict(TASK, repository="someone/else.github.io")
        with self.assertRaises(HealthWorkerError):
            execute_task(task, SITES, lambda site, agent: (True, "ok"))

    def test_only_read_only_health_task_type_is_allowed(self):
        task = dict(TASK, task_type="bug_fix")
        with self.assertRaises(HealthWorkerError):
            execute_task(task, SITES, lambda site, agent: (True, "ok"))


if __name__ == "__main__":
    unittest.main()
