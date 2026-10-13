"""Read-only SEO audit worker with an independent checker pass.

This adapter uses deterministic endpoint checks today. It does not yet invoke
an external open-source LLM/agent package and does not modify site content.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from .agent_checks import check_seo
    from .worker_contract import validate_result_pair
except ImportError:
    from agent_checks import check_seo
    from worker_contract import validate_result_pair

TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
PRIMARY_ID = "seo/metadata-worker"
CHECKER_ID = "seo/metadata-auditor"


class SeoWorkerError(ValueError):
    """Raised when a task is outside the read-only SEO worker's scope."""


def execute_task(task: dict[str, Any], sites_config: dict[str, Any],
                 check_fn: Callable[[str], tuple[bool, str]] = check_seo) -> dict[str, Any]:
    task_id = str(task.get("task_id", ""))
    if not TASK_ID_RE.fullmatch(task_id):
        raise SeoWorkerError("task_id must contain 1-100 safe filename characters")
    matches = [
        site for site in sites_config.get("sites", [])
        if site.get("id") == task.get("site") and site.get("enabled") and site.get("authorized")
    ]
    if len(matches) != 1:
        raise SeoWorkerError("Task site is not uniquely enabled and authorized")
    site = matches[0]
    if task.get("repository") != site.get("repository"):
        raise SeoWorkerError("Task repository does not match the authorized site")
    if task.get("task_type") != "seo_issue":
        raise SeoWorkerError("Only seo_issue tasks are supported")
    if not str(task.get("objective", "")).strip():
        raise SeoWorkerError("Task objective is required")
    live_url = str(site.get("live_url", "")).strip()
    if not live_url.startswith(("https://", "http://")):
        raise SeoWorkerError("Authorized site must have an HTTP(S) live_url")

    primary_ok, primary_detail = check_fn(live_url)
    checker_ok, checker_detail = check_fn(live_url)
    consistent = primary_ok == checker_ok and primary_detail == checker_detail
    primary = {
        "task_id": task_id, "agent_id": PRIMARY_ID,
        "state": "DONE" if primary_ok else "FAILED",
        "summary": "Read-only SEO endpoint audit completed.",
        "evidence": [primary_detail], "artifacts": [], "changed_files": [],
        "next_action": "Independent SEO evidence review",
    }
    checker = {
        "task_id": task_id, "agent_id": CHECKER_ID,
        "state": "REVIEWED" if checker_ok and consistent else "BLOCKED",
        "independent_summary": "Repeated the SEO endpoint audit independently.",
        "independent_evidence": [checker_detail],
        "findings": [] if checker_ok and consistent else [
            "SEO check failed or primary/checker evidence differs."
        ],
        "next_action": "Captain review" if checker_ok and consistent else "Investigate SEO findings",
    }
    assignment = {"assignments": [
        {"agent_id": PRIMARY_ID, "role": "primary_worker"},
        {"agent_id": CHECKER_ID, "role": "independent_checker"},
    ]}
    gate = validate_result_pair({"task_id": task_id}, assignment, primary, checker)
    passed = primary_ok and checker_ok and consistent and gate["state"] == "READY_FOR_CAPTAIN_REVIEW"
    if not passed:
        gate["state"] = "VERIFYING"
        gate["automatic_merge"] = False
        gate["automatic_deploy"] = False
        gate["captain_approval_required"] = True
        gate.setdefault("problems", []).append("SEO check failed or evidence was inconsistent.")
    return {
        "schema_version": 1, "task_id": task_id, "site": site["id"],
        "repository": site["repository"], "worker_type": "deterministic_read_only_seo",
        "state": "READY_FOR_CAPTAIN_REVIEW" if passed else "VERIFYING",
        "primary_result": primary, "independent_checker_result": checker,
        "contract_gate": gate, "evidence_consistent": consistent,
        "write_access": False, "model_invoked": False,
        "automatic_merge": False, "automatic_deploy": False,
        "captain_approval_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_json")
    parser.add_argument("--output", default="-")
    parser.add_argument("--sites", default=str(Path(__file__).with_name("sites.json")))
    args = parser.parse_args()
    try:
        task = json.loads(Path(args.task_json).read_text(encoding="utf-8"))
        sites = json.loads(Path(args.sites).read_text(encoding="utf-8"))
        report = execute_task(task, sites)
        serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output == "-":
            print(serialized, end="")
        else:
            output = Path(args.output).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(serialized, encoding="utf-8")
            print(json.dumps({"report": str(output), "state": report["state"]}))
        return 0 if report["state"] == "READY_FOR_CAPTAIN_REVIEW" else 2
    except (OSError, json.JSONDecodeError, SeoWorkerError) as exc:
        print(json.dumps({"state": "BLOCKED", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
