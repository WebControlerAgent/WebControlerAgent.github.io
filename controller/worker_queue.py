"""Create deterministic, scoped job packets for a primary worker and checker.

This adapter prepares queue artifacts only. It does not invoke an LLM, run
worker-supplied commands, write to the target repository, merge, or deploy.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from task_dispatcher import DispatchError, load_json, prepare_assignment

ROOT = Path(__file__).resolve().parent.parent
SAFE_PATH_PREFIXES = ("agents/", "controller/", "tests/", "public/", "docs/")
SAFE_ROOT_FILES = {"README.md", "CONTRIBUTING.md"}
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def validate_task_scope(task: dict[str, Any]) -> None:
    task_id = str(task.get("task_id", ""))
    if not TASK_ID_RE.fullmatch(task_id):
        raise DispatchError("task_id must be 1-100 safe filename characters")
    paths = task.get("allowed_paths")
    if not isinstance(paths, list) or not paths:
        raise DispatchError("allowed_paths must be a non-empty list")
    for item in paths:
        if not isinstance(item, str) or not item.strip():
            raise DispatchError("Each allowed path must be a non-empty string")
        path = item.replace("\\", "/").strip()
        parts = path.split("/")
        if path.startswith("/") or any(part in ("", ".", "..") for part in parts):
            raise DispatchError(f"Unsafe allowed path: {item!r}")
        if path.startswith(".github/") or any(
            marker in path.lower() for marker in (".env", "secret", "credential", "token", "private_key")
        ):
            raise DispatchError(f"Protected path cannot be delegated: {item!r}")
        if path not in SAFE_ROOT_FILES and not path.startswith(SAFE_PATH_PREFIXES):
            raise DispatchError(f"Path is outside the worker allowlist: {item!r}")


def make_job_packet(task: dict[str, Any], assignment: dict[str, Any],
                    assigned: dict[str, Any], created_at: str) -> dict[str, Any]:
    checker = assigned.get("role") == "independent_checker"
    return {
        "schema_version": 1,
        "task_id": assignment["task_id"],
        "queue_state": "PENDING",
        "created_at": created_at,
        "site": assignment["site"],
        "repository": assignment["repository"],
        "parent_captain": assignment["parent_captain"],
        "task_type": assignment["task_type"],
        "agent_id": assigned["agent_id"],
        "role": assigned["role"],
        "objective": task["objective"],
        "allowed_paths": task["allowed_paths"],
        "constraints": task["constraints"],
        "success_criteria": task["success_criteria"],
        "instructions": (
            [
                "Review the primary worker's proposed result independently.",
                "Do not edit files or run commands.",
                "Return independent_summary, independent_evidence, findings, and next_action.",
                "Challenge unsupported claims; cite reproducible evidence.",
                "Do not approve merge or deployment."
            ] if checker else [
                "Prepare a proposed result within allowed_paths only.",
                "Return summary, evidence, artifacts, changed_files, and next_action.",
                "Do not execute untrusted commands or access credentials.",
                "Return a patch/artifact for review; do not merge or deploy."
            ]
        ),
        "execution": {
            "mode": "packet_only",
            "model_invoked": False,
            "commands_executed": False,
            "repository_write_access": False,
            "automatic_merge": False,
            "automatic_deploy": False,
            "captain_approval_required": True
        }
    }


def prepare_queue(task: dict[str, Any], routing: dict[str, Any],
                  sites: dict[str, Any]) -> dict[str, Any]:
    validate_task_scope(task)
    assignment = prepare_assignment(task, routing, sites)
    created_at = datetime.now(timezone.utc).isoformat()
    packets = [
        make_job_packet(task, assignment, assigned, created_at)
        for assigned in assignment["assignments"]
    ]
    return {
        "schema_version": 1,
        "task_id": assignment["task_id"],
        "queue_state": "PENDING_WORKER_RUNTIME",
        "created_at": created_at,
        "assignment": assignment,
        "jobs": packets,
        "execution_note": (
            "Queue packets are prepared. No AI worker was invoked; an isolated "
            "runtime/provider adapter is still required to execute these jobs."
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_json", help="Path to a task JSON file")
    parser.add_argument("--output-dir", default="artifacts/worker-queue",
                        help="Directory for queue.json and per-agent job packets")
    args = parser.parse_args()
    task_path = Path(args.task_json).resolve()
    output_dir = Path(args.output_dir).resolve()
    try:
        task = load_json(task_path)
        queue = prepare_queue(task, load_json(ROOT / "agents" / "task_routing.json"),
                              load_json(ROOT / "controller" / "sites.json"))
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "queue.json").write_text(
            json.dumps(queue, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8"
        )
        for job in queue["jobs"]:
            role = "checker" if job["role"] == "independent_checker" else "primary"
            (output_dir / f"{queue['task_id']}-{role}.json").write_text(
                json.dumps(job, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8"
            )
    except (DispatchError, OSError) as exc:
        print(json.dumps({"ok": False, "queue_state": "BLOCKED", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps({
        "ok": True,
        "task_id": queue["task_id"],
        "queue_state": queue["queue_state"],
        "job_packets": len(queue["jobs"]),
        "output_dir": str(output_dir),
        "model_invoked": False
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
