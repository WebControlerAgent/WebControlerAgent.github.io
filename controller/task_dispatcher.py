"""Validate and prepare two-agent task assignments for the Captain runtime.

This deterministic dispatcher prepares a dispatch record. It does not claim to
execute AI workers; real worker adapters must consume the validated assignment.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ROUTING_PATH = ROOT / "agents" / "task_routing.json"
SITES_PATH = ROOT / "controller" / "sites.json"

TASK_REQUIRED = (
    "task_id", "site", "repository", "parent_captain", "task_type",
    "objective", "allowed_paths", "constraints", "success_criteria",
)
ROLE_BY_TASK = {
    "feature_or_visual_change": ("frontend-worker", "frontend-reviewer"),
    "bug_diagnosis": ("log-analyzer", "log-cross-checker"),
    "bug_fix": ("patch-agent", "patch-reviewer"),
    "seo_issue": ("metadata-worker", "metadata-auditor"),
    "asset_request": ("asset-preparer", "asset-quality-checker"),
    "release": ("release-worker", "release-auditor"),
    "research": ("source-discovery", "source-cross-checker"),
    "new_idea": ("idea-researcher", "idea-fact-checker"),
    "operations": ("planner", "plan-auditor"),
}

class DispatchError(ValueError):
    """Raised when a task violates the dispatch contract."""

def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DispatchError(f"Cannot read valid JSON from {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise DispatchError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value

def _captain_and_pair(task: dict[str, Any], routing: dict[str, Any]) -> tuple[str, dict[str, str]]:
    captain_id = str(task.get("parent_captain", "")).strip()
    captain = routing.get("captains", {}).get(captain_id)
    if not captain:
        raise DispatchError(f"Unknown parent_captain: {captain_id or '(missing)'}")
    task_type = str(task.get("task_type", "")).strip()
    preferred = ROLE_BY_TASK.get(task_type)
    pairs = captain.get("role_pairs", [])
    pair = next((p for p in pairs if preferred and p.get("primary") == preferred[0] and p.get("checker") == preferred[1]), None)
    if pair is None:
        # For team-specific operations, choose the first declared pair. A caller
        # can specify a task type that maps to a role pair only if that pair
        # belongs to the selected Captain.
        if preferred:
            raise DispatchError(
                f"Task type {task_type!r} requires pair {preferred[0]} + {preferred[1]}, "
                f"which is not owned by Captain {captain_id!r}"
            )
        raise DispatchError(f"Unsupported task_type: {task_type or '(missing)'}")
    return captain_id, {"primary": pair["primary"], "checker": pair["checker"]}

def prepare_assignment(task: dict[str, Any], routing: dict[str, Any], sites: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in TASK_REQUIRED if task.get(key) in (None, "", [])]
    if missing:
        raise DispatchError("Missing required task fields: " + ", ".join(missing))
    if not isinstance(task["allowed_paths"], list) or not task["allowed_paths"]:
        raise DispatchError("allowed_paths must be a non-empty list")
    if not isinstance(task["success_criteria"], list) or not task["success_criteria"]:
        raise DispatchError("success_criteria must be a non-empty list")
    if not isinstance(task["constraints"], list):
        raise DispatchError("constraints must be a list")
    if routing.get("pair_policy", {}).get("minimum_small_agents_per_task") != 2:
        raise DispatchError("Routing policy does not require two small agents per task")

    authorized_sites = [
        s for s in sites.get("sites", [])
        if s.get("enabled") and s.get("authorized") and s.get("id") == task["site"]
    ]
    if len(authorized_sites) != 1:
        raise DispatchError(f"Site {task['site']!r} is not uniquely enabled and authorized")

    captain_id, pair = _captain_and_pair(task, routing)
    captain = routing["captains"][captain_id]
    children = set(captain.get("children", []))
    if pair["primary"] not in children or pair["checker"] not in children:
        raise DispatchError("Worker/checker pair is not fully registered under the selected Captain")
    if pair["primary"] == pair["checker"]:
        raise DispatchError("Primary worker and independent checker must be different agents")

    supplied_primary = task.get("primary_agent_id")
    supplied_checker = task.get("checker_agent_id")
    if bool(supplied_primary) != bool(supplied_checker):
        raise DispatchError("A task cannot specify only one agent; provide both IDs or let the dispatcher assign the pair")
    expected_primary = f"{captain_id}/{pair['primary']}"
    expected_checker = f"{captain_id}/{pair['checker']}"
    if supplied_primary and supplied_primary != expected_primary:
        raise DispatchError(f"primary_agent_id must be {expected_primary}")
    if supplied_checker and supplied_checker != expected_checker:
        raise DispatchError(f"checker_agent_id must be {expected_checker}")

    dependencies = task.get("depends_on", [])
    completed_dependencies = set(task.get("completed_dependencies", []))
    if not isinstance(dependencies, list):
        raise DispatchError("depends_on must be a list")
    unresolved = [dep for dep in dependencies if dep not in completed_dependencies]
    if unresolved:
        raise DispatchError("Unmet dependencies: " + ", ".join(map(str, unresolved)))

    return {
        "task_id": str(task["task_id"]),
        "site": task["site"],
        "repository": task["repository"],
        "parent_captain": captain_id,
        "task_type": task["task_type"],
        "objective": task["objective"],
        "status": "READY_FOR_WORKER_ADAPTER",
        "minimum_small_agents": 2,
        "assignments": [
            {
                "agent_id": expected_primary,
                "role": "primary_worker",
                "access": "approved_task_scope",
                "must_return": ["summary", "evidence", "artifacts", "changed_files", "next_action"],
            },
            {
                "agent_id": expected_checker,
                "role": "independent_checker",
                "access": "read_only_review_of_task_scope",
                "must_return": ["independent_summary", "independent_evidence", "findings", "next_action"],
            },
        ],
        "acceptance_gate": {
            "require_both_results": True,
            "require_same_task_id": True,
            "require_independent_checker_evidence": True,
            "captain_must_approve": True,
            "missing_or_conflicting_evidence_state": "VERIFYING",
        },
        "note": "Assignment prepared only. No worker has been executed by this script.",
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_json", help="Path to a task JSON file")
    parser.add_argument("--output", help="Optional output path for the validated assignment JSON")
    args = parser.parse_args()
    task_path = Path(args.task_json)
    if not task_path.is_absolute():
        task_path = (Path.cwd() / task_path).resolve()
    try:
        task = load_json(task_path)
        assignment = prepare_assignment(task, load_json(ROUTING_PATH), load_json(SITES_PATH))
    except DispatchError as exc:
        print(json.dumps({"ok": False, "dispatch": "BLOCKED", "error": str(exc)}, indent=2))
        return 2
    output = json.dumps({"ok": True, "assignment": assignment}, indent=2, ensure_ascii=False) + chr(10)
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = (Path.cwd() / output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
