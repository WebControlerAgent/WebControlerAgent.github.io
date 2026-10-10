"""Worker result contract and independent-review acceptance gate.

This module validates reports from worker adapters. It does not call an LLM,
execute code, merge changes, or deploy. Missing/conflicting evidence remains
VERIFYING and requires Captain review.
"""
from __future__ import annotations

from typing import Any

RESULT_FIELDS = ("task_id", "agent_id", "state", "summary", "evidence", "artifacts", "changed_files", "next_action")
CHECKER_FIELDS = ("task_id", "agent_id", "state", "independent_summary", "independent_evidence", "findings", "next_action")


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def validate_result_pair(task: dict[str, Any], assignment: dict[str, Any],
                         primary: dict[str, Any] | None,
                         checker: dict[str, Any] | None) -> dict[str, Any]:
    """Return a deterministic gate decision; never equate reports with approval."""
    problems: list[str] = []
    task_id = str(task.get("task_id", ""))
    assigned = assignment.get("assignments", [])
    primary_id = next((a.get("agent_id") for a in assigned if a.get("role") == "primary_worker"), None)
    checker_id = next((a.get("agent_id") for a in assigned if a.get("role") == "independent_checker"), None)

    if not isinstance(primary, dict):
        problems.append("Primary worker result is missing.")
    else:
        missing = [field for field in RESULT_FIELDS if field not in primary]
        if missing:
            problems.append("Primary result missing fields: " + ", ".join(missing))
        if primary.get("task_id") != task_id:
            problems.append("Primary result task_id does not match task.")
        if primary.get("agent_id") != primary_id:
            problems.append("Primary result agent_id does not match assignment.")
        if not str(primary.get("summary", "")).strip():
            problems.append("Primary result summary is empty.")
        if not _nonempty_list(primary.get("evidence")):
            problems.append("Primary result must include evidence.")
        if not isinstance(primary.get("changed_files"), list):
            problems.append("Primary changed_files must be a list.")

    if not isinstance(checker, dict):
        problems.append("Independent checker result is missing.")
    else:
        missing = [field for field in CHECKER_FIELDS if field not in checker]
        if missing:
            problems.append("Checker result missing fields: " + ", ".join(missing))
        if checker.get("task_id") != task_id:
            problems.append("Checker result task_id does not match task.")
        if checker.get("agent_id") != checker_id:
            problems.append("Checker result agent_id does not match assignment.")
        if checker.get("agent_id") == primary_id:
            problems.append("Checker must be a different agent from the primary worker.")
        if not str(checker.get("independent_summary", "")).strip():
            problems.append("Checker independent_summary is empty.")
        if not _nonempty_list(checker.get("independent_evidence")):
            problems.append("Checker must include independent evidence.")
        if not isinstance(checker.get("findings"), list):
            problems.append("Checker findings must be a list.")

    if problems:
        state = "VERIFYING"
    else:
        state = "READY_FOR_CAPTAIN_REVIEW"

    return {
        "task_id": task_id,
        "state": state,
        "primary_agent_id": primary_id,
        "checker_agent_id": checker_id,
        "problems": problems,
        "captain_approval_required": True,
        "automatic_merge": False,
        "automatic_deploy": False,
        "decision_note": (
            "Both reports passed structural/evidence checks; Captain review is still required."
            if not problems else
            "Do not mark complete. Obtain missing or corrected independent evidence."
        ),
    }
