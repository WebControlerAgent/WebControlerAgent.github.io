"""Create a tightly scoped code-proposal task after an authorized SEO approval.

Approval starts a proposal-only worker. It never grants target-repository write,
merge, or deployment permissions.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path
from typing import Any

MARKER_RE = re.compile(
    r"<!--\s*seo-captain-tasks-b64\s*(\{.*?\})\s*-->",
    re.DOTALL,
)
COMMAND_RE = re.compile(r"^/approve-seo-task\s+([A-Za-z0-9_-]{1,40})\s*$")
SAFE_PATHS = {
    "Add or correct the homepage title": ["index.html"],
    "Add or correct the homepage meta description": ["index.html"],
    "Review the homepage canonical URL": ["index.html"],
    "Review homepage canonical metadata": ["index.html"],
    "Review homepage indexing directives": ["index.html"],
    "Fix the robots.txt Sitemap directive": ["robots.txt"],
    "Repair and validate sitemap.xml": ["sitemap.xml"],
}


class ApprovalError(ValueError):
    """Raised when an approval request is not authorized or safely scoped."""


def build_approved_task(
    event: dict[str, Any],
    comments: list[dict[str, Any]],
    sites_config: dict[str, Any],
) -> dict[str, Any]:
    issue = event.get("issue") or {}
    comment = event.get("comment") or {}
    author = (comment.get("user") or {}).get("login", "")
    association = comment.get("author_association", "")
    if author.lower() != "webcontroleragent" and association != "OWNER":
        raise ApprovalError("Only the repository owner may approve an SEO task.")
    if not str(issue.get("title", "")).startswith("[SEO Audit]"):
        raise ApprovalError("Approval comments are accepted only on SEO Audit issues.")

    command = COMMAND_RE.fullmatch(str(comment.get("body", "")).strip())
    if not command:
        raise ApprovalError("Use exactly: /approve-seo-task <task-id>")
    selected_id = command.group(1)
    issue_number = int(issue.get("number", 0))
    if issue_number < 1:
        raise ApprovalError("Issue number is missing.")
    dispatch_marker = f"SEO_APPROVAL_DISPATCHED:{issue_number}:{selected_id}"
    if any(dispatch_marker in str(item.get("body", "")) for item in comments if isinstance(item, dict)):
        raise ApprovalError("This task approval has already been dispatched.")

    audit_comments = [
        item for item in comments
        if isinstance(item, dict)
        and isinstance(item.get("body"), str)
        and "seo-captain-tasks-b64" in item["body"]
    ]
    if not audit_comments:
        raise ApprovalError("No machine-readable Captain task plan exists on this issue.")
    latest = max(audit_comments, key=lambda item: str(item.get("created_at", "")))
    marker = MARKER_RE.search(latest["body"])
    if not marker:
        raise ApprovalError("Captain task metadata is malformed.")
    try:
        plan_json = base64.b64decode(marker.group(1).encode("ascii"))
        plan = json.loads(plan_json.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ApprovalError("Captain task metadata is not valid JSON.") from exc

    tasks = plan.get("tasks", [])
    selected = next(
        (item for item in tasks if isinstance(item, dict) and item.get("id") == selected_id),
        None,
    )
    if selected is None:
        raise ApprovalError("The requested task ID was not present in the latest audit.")
    if selected.get("title") == "Record clean technical SEO audit":
        raise ApprovalError("This is a clean-audit baseline, not a code-fix task.")
    allowed_paths = SAFE_PATHS.get(str(selected.get("title", "")))
    if not allowed_paths:
        raise ApprovalError("No pre-approved file scope exists for this finding; manual planning is required.")

    site_id = str(plan.get("site", "")).strip()
    repository = str(plan.get("repository", "")).strip()
    matches = [
        site for site in sites_config.get("sites", [])
        if site.get("id") == site_id
        and site.get("repository") == repository
        and site.get("enabled") is True
        and site.get("authorized") is True
    ]
    if len(matches) != 1:
        raise ApprovalError("The audit site is not uniquely enabled and authorized.")

    task_id = f"seo-{issue_number}-{selected_id}"
    objective = (
        f"Prepare a patch proposal for the Captain-approved SEO finding on {site_id}. "
        f"Finding: {str(selected.get('finding', ''))[:500]} "
        f"Proposed action: {str(selected.get('proposed_action', ''))[:500]} "
        "Acceptance criteria: " + str(selected.get("acceptance_criteria", ""))[:500]
    )
    return {
        "task_id": task_id,
        "site": site_id,
        "repository": repository,
        "parent_captain": "bug-solver",
        "origin_captain": "seo-agent",
        "approved_task_id": selected_id,
        "approval_issue": issue_number,
        "approved_by": author,
        "task_type": "code_change_proposal",
        "objective": objective,
        "allowed_paths": allowed_paths,
        "constraints": [
            "Proposal only: do not commit, push, merge, or deploy to the target repository.",
            "Do not modify secrets, credentials, admin/authentication, ads, or deployment configuration.",
            "Keep the change limited to the explicitly allowlisted file(s).",
            "Do not invent missing site content or claim Google indexing has been verified.",
            "Return a patch artifact and evidence for independent review.",
        ],
        "success_criteria": [
            str(selected.get("acceptance_criteria", "A fresh read-only SEO audit verifies the correction.")),
            "The independent patch checker passes the exact allowlisted file scope.",
            "No target repository branch, commit, merge, or deployment is created.",
        ],
        "captain_approval": {
            "required": True,
            "approved": True,
            "approved_by": author,
            "approval_issue": issue_number,
            "approved_task_id": selected_id,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True)
    parser.add_argument("--comments", required=True)
    parser.add_argument("--sites", default="controller/sites.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        event = json.loads(Path(args.event).read_text(encoding="utf-8"))
        comments = json.loads(Path(args.comments).read_text(encoding="utf-8"))
        sites = json.loads(Path(args.sites).read_text(encoding="utf-8"))
        task = build_approved_task(event, comments, sites)
        Path(args.output).write_text(
            json.dumps(task, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"state": "APPROVED_FOR_PATCH_PROPOSAL", "task_id": task["task_id"]}))
        return 0
    except (OSError, json.JSONDecodeError, ApprovalError, TypeError, ValueError) as exc:
        print(json.dumps({"state": "BLOCKED", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
