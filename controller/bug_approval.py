"""Build a proposal-only coding task after explicit Bug Hunter approval.

The diagnosis comment is untrusted input. Only an owner command can authorize
one task, and the resulting worker remains read-only against the target repo.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import re
from pathlib import Path
from typing import Any

MARKER_RE = re.compile(
    r"<!--\s*bug-captain-tasks-b64\s*([A-Za-z0-9+/=]+)\s*-->",
    re.DOTALL,
)
COMMAND_RE = re.compile(r"^/approve-bug-task\s+([A-Za-z0-9_-]{1,40})\s*$")
FORBIDDEN_PARTS = {
    ".git", ".github", "admin", "ads", "secrets", "credentials",
}
FORBIDDEN_NAMES = {
    "sites.json", "config.json", "package-lock.json", "pnpm-lock.yaml",
    "yarn.lock",
}


class ApprovalError(ValueError):
    """Raised when a Bug Hunter approval is unauthorized or unsafe."""


def _safe_paths(value: Any) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= 10:
        raise ApprovalError("Task must list 1–10 exact files for the patch scope.")
    paths: list[str] = []
    for raw in value:
        if not isinstance(raw, str) or not raw or len(raw) > 240:
            raise ApprovalError("Every allowed path must be a non-empty file path.")
        path = Path(raw)
        parts = path.parts
        name = path.name.lower()
        if (
            path.is_absolute()
            or "\\" in raw
            or any(part in {"", ".", ".."} for part in parts)
            or any(part.lower() in FORBIDDEN_PARTS for part in parts)
            or name in FORBIDDEN_NAMES
            or name.startswith(".env")
            or "secret" in name
            or "credential" in name
            or "*" in raw
            or "?" in raw
        ):
            raise ApprovalError(f"Path is outside the safe patch policy: {raw}")
        if raw in paths:
            raise ApprovalError("Duplicate paths are not allowed.")
        paths.append(raw)
    return paths


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
        raise ApprovalError("Only the repository owner may approve a Bug Hunter task.")
    if not str(issue.get("title", "")).startswith("[Bug Review]"):
        raise ApprovalError("Approval comments are accepted only on Bug Review issues.")

    command = COMMAND_RE.fullmatch(str(comment.get("body", "")).strip())
    if not command:
        raise ApprovalError("Use exactly: /approve-bug-task <task-id>")
    selected_id = command.group(1)
    issue_number = int(issue.get("number", 0))
    if issue_number < 1:
        raise ApprovalError("Issue number is missing.")
    dispatch_marker = f"BUG_APPROVAL_DISPATCHED:{issue_number}:{selected_id}"
    if any(dispatch_marker in str(item.get("body", "")) for item in comments if isinstance(item, dict)):
        raise ApprovalError("This Bug Hunter task has already been dispatched.")

    plan_comments = [
        item for item in comments
        if isinstance(item, dict)
        and isinstance(item.get("body"), str)
        and "bug-captain-tasks-b64" in item["body"]
    ]
    if not plan_comments:
        raise ApprovalError("No machine-readable Bug Hunter task plan exists on this issue.")
    latest = max(plan_comments, key=lambda item: str(item.get("created_at", "")))
    marker = MARKER_RE.search(latest["body"])
    if not marker:
        raise ApprovalError("Bug Hunter task metadata is malformed.")
    try:
        encoded = base64.b64decode(marker.group(1).encode("ascii"), validate=True)
        plan = json.loads(encoded.decode("utf-8"))
    except (json.JSONDecodeError, binascii.Error, UnicodeDecodeError) as exc:
        raise ApprovalError("Bug Hunter task metadata is not valid encoded JSON.") from exc
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list):
        raise ApprovalError("Bug Hunter plan must contain a tasks list.")

    selected = next(
        (item for item in plan["tasks"] if isinstance(item, dict) and item.get("id") == selected_id),
        None,
    )
    if selected is None:
        raise ApprovalError("The requested task ID was not present in the latest Bug Hunter plan.")
    if selected.get("requires_captain_approval") is not True or selected.get("auto_apply") is not False:
        raise ApprovalError("Task metadata must explicitly require Captain approval and disable auto-apply.")

    title = str(selected.get("title", "")).strip()
    finding = str(selected.get("finding", "")).strip()
    action = str(selected.get("proposed_action", "")).strip()
    acceptance = str(selected.get("acceptance_criteria", "")).strip()
    if not title or len(title) > 200 or not finding or not action or not acceptance:
        raise ApprovalError("Task title, finding, proposed action, and acceptance criteria are required.")

    allowed_paths = _safe_paths(selected.get("allowed_paths"))
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
        raise ApprovalError("The Bug Hunter target is not uniquely enabled and authorized.")

    task_id = f"bug-{issue_number}-{selected_id}"
    return {
        "task_id": task_id,
        "site": site_id,
        "repository": repository,
        "parent_captain": "bug-solver",
        "origin_captain": "bug-hunter",
        "approved_task_id": selected_id,
        "approval_issue": issue_number,
        "approved_by": author,
        "task_type": "bug_fix",
        "objective": (
            f"Prepare a bounded patch proposal for the approved diagnosis on {site_id}. "
            f"Finding: {finding[:700]} Proposed action: {action[:700]} "
            f"Acceptance criteria: {acceptance[:700]}"
        ),
        "allowed_paths": allowed_paths,
        "constraints": [
            "Proposal only: do not commit, push, merge, or deploy to the target repository.",
            "Do not modify secrets, credentials, authentication, admin, ads, or deployment configuration.",
            "Keep all changes within the exact owner-approved file allowlist.",
            "Do not claim a defect is fixed unless the patch and independent review evidence support it.",
            "Return a patch artifact and evidence for independent review.",
        ],
        "success_criteria": [
            acceptance,
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
        Path(args.output).write_text(json.dumps(task, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"state": "APPROVED_FOR_PATCH_PROPOSAL", "task_id": task["task_id"]}))
        return 0
    except (OSError, json.JSONDecodeError, ApprovalError, TypeError, ValueError) as exc:
        print(json.dumps({"state": "BLOCKED", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
