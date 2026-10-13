"""Tests for the paired read-only SEO audit worker."""
from __future__ import annotations

import unittest
from controller.seo_worker import SeoWorkerError, execute_task

SITES = {"sites": [{
    "id": "demo", "repository": "owner/site", "live_url": "https://example.com/",
    "enabled": True, "authorized": True,
}]}


def task(**updates):
    result = {
        "task_id": "seo-001", "site": "demo", "repository": "owner/site",
        "task_type": "seo_issue", "objective": "Check robots and sitemap endpoints",
    }
    result.update(updates)
    return result


class SeoWorkerTests(unittest.TestCase):
    def test_success_requires_two_matching_passes_and_gate(self):
        calls = []
        def check(url):
            calls.append(url)
            return True, "robots and sitemap reachable"
        report = execute_task(task(), SITES, check)
        self.assertEqual(len(calls), 2)
        self.assertEqual(report["state"], "READY_FOR_CAPTAIN_REVIEW")
        self.assertFalse(report["write_access"])
        self.assertFalse(report["automatic_deploy"])

    def test_failed_check_is_not_approved(self):
        report = execute_task(task(), SITES, lambda url: (False, "sitemap missing"))
        self.assertEqual(report["state"], "VERIFYING")
        self.assertEqual(report["independent_checker_result"]["state"], "BLOCKED")

    def test_inconsistent_evidence_is_not_approved(self):
        calls = iter([(True, "sitemap ok"), (True, "sitemap stale")])
        report = execute_task(task(), SITES, lambda url: next(calls))
        self.assertEqual(report["state"], "VERIFYING")
        self.assertFalse(report["contract_gate"]["automatic_merge"])

    def test_rejects_unauthorized_site(self):
        with self.assertRaises(SeoWorkerError):
            execute_task(task(site="unknown"), SITES, lambda url: (True, "ok"))

    def test_rejects_repository_mismatch(self):
        with self.assertRaises(SeoWorkerError):
            execute_task(task(repository="other/repo"), SITES, lambda url: (True, "ok"))

    def test_rejects_wrong_task_type(self):
        with self.assertRaises(SeoWorkerError):
            execute_task(task(task_type="code_change_proposal"), SITES, lambda url: (True, "ok"))

    def test_rejects_non_http_url(self):
        with self.assertRaises(SeoWorkerError):
            execute_task(task(), {"sites": [{**SITES["sites"][0], "live_url": "file:///etc/passwd"}]},
                         lambda url: (True, "ok"))


if __name__ == "__main__":
    unittest.main()
