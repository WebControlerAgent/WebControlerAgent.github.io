"""Connect validated Captain assignments to the bounded coding adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from controller.open_source_worker_adapter import run_coding_task
from controller.task_dispatcher import DispatchError, prepare_assignment


def execute_validated_task(
    task: dict[str, Any],
    routing: dict[str, Any],
    sites: dict[str, Any],
    repository_checkout: str | Path,
    output_dir: str | Path,
    environ: dict[str, str] | None = None,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    """Validate task routing before creating a scoped patch candidate."""
    try:
        assignment = prepare_assignment(task, routing, sites)
    except (DispatchError, TypeError, KeyError) as exc:
        return {"state": "BLOCKED", "executed": False, "reason": f"Dispatch rejected: {exc}"}

    if task.get("task_type") not in {"bug_fix", "code_change_proposal"}:
        return {
            "state": "BLOCKED",
            "executed": False,
            "dispatch_validated": True,
            "reason": "This adapter only executes bug_fix and code_change_proposal tasks.",
            "assignment": assignment,
        }

    result = run_coding_task(
        repository_checkout=repository_checkout,
        task=task,
        sites=sites,
        output_dir=output_dir,
        environ=environ,
        timeout_seconds=timeout_seconds,
    )
    result["dispatch_validated"] = True
    result["assignment"] = {
        "task_id": assignment["task_id"],
        "primary_worker": assignment["assignments"][0]["agent_id"],
        "independent_checker": assignment["assignments"][1]["agent_id"],
        "captain_approval_required": assignment["acceptance_gate"]["captain_must_approve"],
    }
    return result
