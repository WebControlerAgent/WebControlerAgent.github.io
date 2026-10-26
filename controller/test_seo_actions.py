"""Tests for turning read-only SEO evidence into Captain-review tasks."""
import unittest

from controller.seo_actions import build_captain_tasks


class CaptainSeoActionTests(unittest.TestCase):
    def test_maps_missing_description_to_review_task(self):
        report = {
            "site": "demo",
            "repository": "owner/site",
            "evidence_consistent": True,
            "primary_result": {"evidence": ["findings=Homepage meta description is missing or empty."]},
            "independent_checker_result": {"independent_evidence": ["checker findings=Homepage meta description is missing or empty."]},
        }
        result = build_captain_tasks(report)
        self.assertEqual(result["state"], "READY_FOR_CAPTAIN_REVIEW")
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["title"], "Add or correct the homepage meta description")
        self.assertTrue(result["tasks"][0]["requires_captain_approval"])
        self.assertFalse(result["tasks"][0]["auto_apply"])

    def test_inconsistent_evidence_adds_reconciliation_task(self):
        result = build_captain_tasks({
            "evidence_consistent": False,
            "primary_result": {"evidence": ["findings=none detected"]},
            "independent_checker_result": {"independent_evidence": ["checker findings=none detected"]},
        })
        self.assertEqual(result["tasks"][0]["id"], "seo-evidence-review")
        self.assertFalse(result["automatic_merge"])
        self.assertFalse(result["automatic_deploy"])

    def test_clean_audit_creates_baseline_not_fake_issue(self):
        result = build_captain_tasks({
            "site": "demo",
            "repository": "owner/site",
            "evidence_consistent": True,
            "primary_result": {"evidence": ["homepage: HTTP 200; findings=none detected"]},
            "independent_checker_result": {"independent_evidence": ["checker findings=none detected"]},
        })
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["title"], "Record clean technical SEO audit")
        self.assertIn("No technical SEO findings", result["tasks"][0]["finding"])

    def test_duplicate_findings_are_deduplicated(self):
        result = build_captain_tasks({
            "evidence_consistent": True,
            "primary_result": {"evidence": ["findings=/robots.txt does not declare a Sitemap URL"]},
            "independent_checker_result": {"independent_evidence": ["checker findings=/robots.txt does not declare a Sitemap URL"]},
        })
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["title"], "Fix the robots.txt Sitemap directive")

    def test_every_task_is_review_only(self):
        result = build_captain_tasks({
            "evidence_consistent": True,
            "primary_result": {"evidence": ["findings=Homepage robots meta contains noindex"]},
        })
        for task in result["tasks"]:
            self.assertTrue(task["requires_captain_approval"])
            self.assertFalse(task["auto_apply"])
        self.assertFalse(result["write_access"])


if __name__ == "__main__":
    unittest.main()
