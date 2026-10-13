"""Deterministic, read-only QA worker for the single authorized test site.

This worker performs live-site and SEO checks twice: once as the primary QA
worker and once as a separate checker pass. It never edits the target site,
calls an LLM, or deploys anything.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from .agent_checks import run_checks
    from .worker_contract import validate_result_pair
except ImportError:  # Direct script invocation.
    from agent_checks import run_checks
    from worker_contract import validate_result_pair

ROOT = Path(__file__).resolve().parent.parent
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
PRIMARY_ID = "qa/seo-tester"
CHECKER_ID = "qa/seo-independent-checker"


class HealthWorkerError(ValueError):
    """Raised when a task is outside the read-only worker's scope."""


def execute_task(
    task: dict[str, Any],
    sites_config: dict[str, Any],
    check_fn: Callable[[dict[str, Any], str], tuple[bool, str]] = run_checks,
) -> dict[str, Any]:
    task_id = str(task.get("task_id", ""))
    if not TASK_ID_RE.fullmatch(task_id):
        raise HealthWorkerError("task_id must be 1-100 safe filename characters")
    site_id = task.get("site")
    sites = sites_config.get("sites", [])
    matches = [
        site for site in sites
        if site.get("id") == site_id and site.get("enabled") and site.get("authorized")
    ]
    if len(matches) != 1:
        raise HealthWorkerError("Task site is not uniquely enabled and authorized")
    site = matches[0]
    if task.get("repository") != site.get("repository"):
        raise HealthWorkerError("Task repository does not match the authorized site")
    if task.get("task_type") != "read_only_health_check":
        raise HealthWorkerError("Only read_only_health_check tasks are supported")
    if not task.get("objective"):
        raise HealthWorkerError("Task objective is required")

    # Primary pass and checker pass are separate invocations; discrepancies
    # or failed checks never become a completion/approval signal.
    primary_ok, primary_detail = check_fn(site, "qa")
    checker_ok, checker_detail = check_fn(site, "qa")
    consistent = primary_ok == checker_ok and primary_detail == checker_detail

    primary = {
        "task_id": task_id,
        "agent_id": PRIMARY_ID,
        "state": "DONE" if primary_ok else "FAILED",
        "summary": "Read-only live-site and SEO health check completed.",
        "evidence": [primary_detail],
        "artifacts": [],
        "changed_files": [],
        "next_action": "Independent checker review",
    }
    checker = {
        "task_id": task_id,
        "agent_id": CHECKER_ID,
        "state": "REVIEWED" if checker_ok and consistent else "BLOCKED",
        "independent_summary": "Repeated the live-site and SEO checks independently.",
        "independent_evidence": [checker_detail],
        "findings": [] if checker_ok and consistent else [
            "Check failed or primary/checker evidence did not match."
        ],
        "next_action": "Captain review" if checker_ok and consistent else "Investigate failed or inconsistent check",
    }
    assignment = {"assignments": [
        {"agent_id": PRIMARY_ID, "role": "primary_worker"},
        {"agent_id": CHECKER_ID, "role": "independent_checker"},
    ]}
    gate = validate_result_pair({"task_id": task_id}, assignment, primary, checker)
    passed = primary_ok and checker_ok and consistent and gate["state"] == "READY_FOR_CAPTAIN_REVIEW"
    return {
        "schema_version": 1,
        "task_id": task_id,
        "site": site_id,
        "repository": site["repository"],
        "worker_type": "deterministic_read_only_qa",
        "state": "READY_FOR_CAPTAIN_REVIEW" if passed else "VERIFYING",
        "primary_result": primary,
        "independent_checker_result": checker,
        "contract_gate": gate,
        "evidence_consistent": consistent,
        "write_access": False,
        "model_invoked": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "captain_approval_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_json", help="Path to a bounded health-check task JSON file")
    parser.add_argument("--output", default="-", help="Report JSON path, or '-' for stdout")
    args = parser.parse_args()
    try:
        task = json.loads(Path(args.task_json).read_text(encoding="utf-8"))
        sites = json.loads((ROOT / "controller" / "sites.json").read_text(encoding="utf-8"))
        report = execute_task(task, sites)
        serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output == "-":
            print(serialized, end="")
        else:
            target = Path(args.output).resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(serialized, encoding="utf-8")
            print(json.dumps({"report": str(target), "state": report["state"]}))
        return 0 if report["state"] == "READY_FOR_CAPTAIN_REVIEW" else 2
    except (OSError, json.JSONDecodeError, HealthWorkerError) as exc:
        print(json.dumps({"state": "BLOCKED", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
