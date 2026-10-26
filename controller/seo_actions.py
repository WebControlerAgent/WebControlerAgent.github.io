"""Turn read-only SEO audit evidence into Captain-review tasks.

This module only proposes tasks. It never edits the target repository, opens a
write workflow, merges changes, or deploys.
"""
from __future__ import annotations

import re
from typing import Any


RULES = [
    (("no non-empty title", "no detectable <title>", "title is missing"),
     "Add or correct the homepage title", "high",
     "Set one descriptive, non-empty title that accurately represents the site.",
     "A fresh audit detects a non-empty homepage title."),
    (("meta description is missing", "no detectable meta description", "description is missing"),
     "Add or correct the homepage meta description", "medium",
     "Add a concise, unique description that matches the homepage content.",
     "A fresh audit detects a non-empty homepage meta description."),
    (("canonical link is missing", "canonical url host differs", "canonical url is not a valid"),
     "Review the homepage canonical URL", "high",
     "Set a valid HTTP(S) canonical URL on the intended site host.",
     "A fresh audit confirms the canonical URL is valid and uses the intended host."),
    (("noindex",),
     "Review homepage indexing directives", "high",
     "Confirm the homepage should be indexable; remove unintended noindex directives only after Captain approval.",
     "A fresh audit finds no unintended noindex directive."),
    (("robots.txt", "sitemap directive"),
     "Fix the robots.txt Sitemap directive", "medium",
     "Ensure robots.txt declares the correct absolute sitemap URL and that it is reachable.",
     "A fresh audit confirms robots.txt returns success and declares the correct absolute Sitemap URL."),
    (("sitemap.xml", "sitemap has", "sitemap contains", "sitemap.xml root", "sitemap locations"),
     "Repair and validate sitemap.xml", "high",
     "Correct the reported sitemap XML, URL, duplicate, host, or reachability issue.",
     "A fresh audit confirms valid sitemap XML with non-empty, absolute URLs on the intended host."),
    (("homepage http", "homepage fetch failed", "homepage returned http"),
     "Investigate homepage availability", "critical",
     "Check the live homepage response and resolve the reported HTTP or fetch failure.",
     "A fresh audit fetches the homepage successfully."),
    (("canonical",),
     "Review homepage canonical metadata", "medium",
     "Inspect the canonical URL and ensure it identifies the preferred homepage URL.",
     "A fresh audit confirms the canonical URL is valid and points to the intended site."),
]


def _finding_texts(report: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in ("primary_result", "independent_checker_result"):
        result = report.get(key, {})
        if not isinstance(result, dict):
            continue
        for field in ("evidence", "independent_evidence", "findings"):
            values = result.get(field, [])
            if isinstance(values, str):
                values = [values]
            if not isinstance(values, list):
                continue
            for value in values:
                if not isinstance(value, str):
                    continue
                for match in re.finditer(r"findings?\s*=\s*(.*?)(?=(?:;\s*(?:checker\s+)?findings?\s*=)|$)", value, re.I):
                    payload = match.group(1).strip()
                    if payload and payload.lower() not in {"none detected", "none", "[]"}:
                        texts.extend(item.strip(" .") for item in re.split(r"\s*[|]\s*", payload) if item.strip())
                if field == "findings":
                    texts.append(value.strip())
    return list(dict.fromkeys(text for text in texts if text and text.lower() not in {"none detected", "none"}))


def build_captain_tasks(report: dict[str, Any]) -> dict[str, Any]:
    """Create deterministic, review-only tasks from audit evidence."""
    site = str(report.get("site", "unknown"))
    repository = str(report.get("repository", "unknown"))
    findings = _finding_texts(report)
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()

    if not report.get("evidence_consistent", False):
        tasks.append({
            "id": "seo-evidence-review",
            "priority": "high",
            "title": "Reconcile primary and independent SEO evidence",
            "finding": "The two audit passes are not confirmed consistent.",
            "proposed_action": "Re-run the read-only checks and compare endpoint status, metadata, robots.txt, and sitemap evidence.",
            "acceptance_criteria": "Both checks report consistent evidence before any SEO fix is proposed.",
            "requires_captain_approval": True,
            "auto_apply": False,
        })

    for finding in findings:
        lower = finding.lower()
        matched = next((rule for tokens, *rule in RULES if any(token in lower for token in tokens)), None)
        if matched is None:
            title = "Review technical SEO finding"
            priority = "medium"
            action = "Inspect the evidence and determine the smallest safe correction."
            acceptance = "Captain verifies the finding is resolved by a new read-only audit."
        else:
            title, priority, action, acceptance = matched
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        tasks.append({
            "id": "seo-" + str(len(tasks) + 1).zfill(2),
            "priority": priority,
            "title": title,
            "finding": finding[:500],
            "proposed_action": action,
            "acceptance_criteria": acceptance,
            "requires_captain_approval": True,
            "auto_apply": False,
        })

    if not tasks:
        tasks.append({
            "id": "seo-review-01",
            "priority": "low",
            "title": "Record clean technical SEO audit",
            "finding": "No technical SEO findings were detected by the two read-only checks.",
            "proposed_action": "Keep this audit as a baseline; investigate Google indexing separately in Search Console if needed.",
            "acceptance_criteria": "Captain acknowledges the baseline and any separate indexing investigation is tracked independently.",
            "requires_captain_approval": True,
            "auto_apply": False,
        })

    return {
        "schema_version": 1,
        "site": site,
        "repository": repository,
        "source": "read_only_seo_audit",
        "state": "READY_FOR_CAPTAIN_REVIEW",
        "tasks": tasks,
        "write_access": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "note": "Proposals only. No target website files were changed.",
    }
