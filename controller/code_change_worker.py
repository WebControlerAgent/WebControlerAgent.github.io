"""Bounded code-change proposal worker.

The worker prepares candidate files in an isolated output directory. It never
writes to the repository checkout, commits, merges, executes proposed code, or
deploys. A separate checker validates the manifest before human review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
SAFE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".md"}
DENIED_PARTS = {".git", ".github", "node_modules", "dist", "build", "__pycache__"}
DENIED_NAMES = {
    ".env", ".env.local", ".env.production", "secrets.json",
    "sites.json", "config.json", "package-lock.json", "pnpm-lock.yaml",
    "yarn.lock",
}


class CodeChangeError(ValueError):
    """Raised when a proposed change violates the task's bounded scope."""


def _safe_relative_path(raw: Any) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise CodeChangeError("Each path must be a non-empty POSIX relative path")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CodeChangeError(f"Unsafe relative path: {raw!r}")
    if any(part in DENIED_PARTS for part in path.parts):
        raise CodeChangeError(f"Protected directory cannot be changed: {raw}")
    if path.name.lower() in DENIED_NAMES or path.name.lower().startswith(".env"):
        raise CodeChangeError(f"Protected file cannot be changed: {raw}")
    if path.suffix.lower() not in SAFE_SUFFIXES:
        raise CodeChangeError(f"File type is not allowed: {raw}")
    return path.as_posix()


def prepare_proposal(task: dict[str, Any], sites_config: dict[str, Any],
                     output_dir: str | Path) -> dict[str, Any]:
    task_id = str(task.get("task_id", ""))
    if not TASK_ID_RE.fullmatch(task_id):
        raise CodeChangeError("task_id must contain 1-100 safe filename characters")

    matches = [
        site for site in sites_config.get("sites", [])
        if site.get("id") == task.get("site") and site.get("enabled") and site.get("authorized")
    ]
    if len(matches) != 1:
        raise CodeChangeError("Task site is not uniquely enabled and authorized")
    site = matches[0]
    if task.get("repository") != site.get("repository"):
        raise CodeChangeError("Task repository does not match the authorized site")
    if task.get("task_type") != "code_change_proposal":
        raise CodeChangeError("Only code_change_proposal tasks are supported")
    if not str(task.get("objective", "")).strip():
        raise CodeChangeError("Task objective is required")

    allowed = task.get("allowed_paths")
    if not isinstance(allowed, list) or not allowed:
        raise CodeChangeError("An explicit non-empty allowed_paths list is required")
    allowed_paths = {_safe_relative_path(item) for item in allowed}
    changes = task.get("changes")
    if not isinstance(changes, list) or not changes:
        raise CodeChangeError("At least one proposed change is required")

    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in changes:
        if not isinstance(item, dict):
            raise CodeChangeError("Each change must be an object with path and content")
        rel = _safe_relative_path(item.get("path"))
        if rel not in allowed_paths:
            raise CodeChangeError(f"Path is outside task allowlist: {rel}")
        if rel in seen:
            raise CodeChangeError(f"Duplicate proposed path: {rel}")
        content = item.get("content")
        if not isinstance(content, str):
            raise CodeChangeError(f"Content for {rel} must be a string")
        if len(content.encode("utf-8")) > 500_000:
            raise CodeChangeError(f"Proposed file is too large: {rel}")
        seen.add(rel)
        normalized.append((rel, content))

    root = Path(output_dir).resolve()
    candidate_root = root / task_id
    candidate_root.mkdir(parents=True, exist_ok=False)
    manifest_files = []
    try:
        for rel, content in normalized:
            target = (candidate_root / rel).resolve()
            if candidate_root not in target.parents:
                raise CodeChangeError(f"Resolved path escapes proposal directory: {rel}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="")
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            manifest_files.append({"path": rel, "sha256": digest, "bytes": len(content.encode("utf-8"))})
        report = {
            "schema_version": 1,
            "task_id": task_id,
            "site": site["id"],
            "repository": site["repository"],
            "worker_type": "bounded_code_change_proposal",
            "state": "READY_FOR_INDEPENDENT_CHECK",
            "objective": task["objective"],
            "candidate_directory": str(candidate_root),
            "files": manifest_files,
            "write_access": False,
            "repository_modified": False,
            "code_executed": False,
            "automatic_merge": False,
            "automatic_deploy": False,
            "captain_approval_required": True,
        }
        (candidate_root / "proposal-manifest.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return report
    except Exception:
        import shutil
        shutil.rmtree(candidate_root, ignore_errors=True)
        raise


def check_proposal(report: dict[str, Any], task: dict[str, Any],
                   sites_config: dict[str, Any]) -> dict[str, Any]:
    """Independent deterministic review of proposal metadata and file hashes."""
    findings: list[str] = []
    task_id = str(task.get("task_id", ""))
    if report.get("task_id") != task_id:
        findings.append("Task ID mismatch.")
    if report.get("repository_modified") is not False or report.get("write_access") is not False:
        findings.append("Worker claims repository write access or a repository modification.")
    if report.get("automatic_merge") is not False or report.get("automatic_deploy") is not False:
        findings.append("Automatic merge/deploy must remain disabled.")
    matches = [
        s for s in sites_config.get("sites", [])
        if s.get("id") == task.get("site") and s.get("enabled") and s.get("authorized")
    ]
    if len(matches) != 1 or report.get("repository") != matches[0].get("repository"):
        findings.append("Site/repository authorization mismatch.")
    allowed_raw = task.get("allowed_paths", [])
    try:
        allowed = {_safe_relative_path(p) for p in allowed_raw}
    except CodeChangeError:
        allowed = set()
        findings.append("Task path allowlist is invalid.")
    candidate_root = Path(str(report.get("candidate_directory", ""))).resolve()
    if not candidate_root.is_dir() or candidate_root.name != task_id:
        findings.append("Candidate directory is missing or invalid.")
    files = report.get("files")
    if not isinstance(files, list) or not files:
        findings.append("Proposal must contain at least one file.")
        files = []
    seen: set[str] = set()
    for entry in files:
        try:
            rel = _safe_relative_path(entry.get("path"))
            if rel not in allowed:
                findings.append(f"Path outside allowlist: {rel}")
                continue
            if rel in seen:
                findings.append(f"Duplicate path: {rel}")
                continue
            seen.add(rel)
            target = (candidate_root / rel).resolve()
            if candidate_root not in target.parents or not target.is_file():
                findings.append(f"Candidate file missing or escapes output directory: {rel}")
                continue
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if digest != entry.get("sha256"):
                findings.append(f"Hash mismatch: {rel}")
        except (AttributeError, CodeChangeError, OSError) as exc:
            findings.append(f"Invalid file entry: {exc}")
    return {
        "schema_version": 1,
        "task_id": task_id,
        "agent_id": "code/independent-checker",
        "state": "REVIEWED" if not findings else "BLOCKED",
        "independent_summary": "Checked authorization, path boundaries, candidate existence, and file hashes.",
        "independent_evidence": [f"files_checked={len(seen)}", f"findings={len(findings)}"],
        "findings": findings,
        "automatic_merge": False,
        "automatic_deploy": False,
        "captain_approval_required": True,
        "next_action": "Captain review" if not findings else "Revise or reject proposal",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_json")
    parser.add_argument("--sites", default=str(Path(__file__).with_name("sites.json")))
    parser.add_argument("--output-dir", default="artifacts/code-proposals")
    args = parser.parse_args()
    try:
        task = json.loads(Path(args.task_json).read_text(encoding="utf-8"))
        sites = json.loads(Path(args.sites).read_text(encoding="utf-8"))
        report = prepare_proposal(task, sites, args.output_dir)
        checker = check_proposal(report, task, sites)
        report["independent_checker_result"] = checker
        report["state"] = "READY_FOR_CAPTAIN_REVIEW" if checker["state"] == "REVIEWED" else "VERIFYING"
        output = Path(args.output_dir).resolve() / task["task_id"] / "worker-report.json"
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(output), "state": report["state"]}))
        return 0 if report["state"] == "READY_FOR_CAPTAIN_REVIEW" else 2
    except (OSError, json.JSONDecodeError, CodeChangeError, KeyError) as exc:
        print(json.dumps({"state": "BLOCKED", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
