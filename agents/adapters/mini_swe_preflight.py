"""Preflight and independent patch gate for mini-SWE-agent.

This script never executes model-generated shell commands. It checks the CLI
and reviews a patch artifact. Actual agent execution stays disabled until a
sandboxed model proxy is configured.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("artifacts/mini-swe-preflight.json")
MAX_PATCH_BYTES = 250_000
ALLOWED_PREFIXES = ("agents/", "controller/", "tests/", "public/")
BLOCKED_PARTS = (".github/workflows/", "package-lock.json", "pnpm-lock.yaml")
BLOCKED_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "credentials.json"}


def run_cli_check() -> dict:
    try:
        proc = subprocess.run(
            ["mini", "--help"], text=True, capture_output=True, timeout=20, check=False
        )
        return {
            "available": proc.returncode == 0,
            "return_code": proc.returncode,
            "help_excerpt": (proc.stdout or proc.stderr)[:3000],
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": type(exc).__name__}


def _patch_paths(content: str) -> list[str]:
    """Return both old and new paths so deletions/renames cannot bypass policy."""
    paths = []
    for line in content.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            value = line[4:].split("\t", 1)[0].strip()
            if value == "/dev/null":
                continue
            if value.startswith(("a/", "b/")):
                value = value[2:]
            paths.append(value)
    return list(dict.fromkeys(paths))


def _path_block_reason(name: str) -> str | None:
    if not name or name.startswith("/") or "\\" in name or ".." in Path(name).parts:
        return "Path traversal, absolute path, or invalid separator"
    if name in BLOCKED_NAMES or Path(name).name in BLOCKED_NAMES:
        return "Protected credential/environment filename"
    if any(part in name for part in BLOCKED_PARTS):
        return "Protected workflow or dependency lockfile"
    if not name.startswith(ALLOWED_PREFIXES):
        return "Path outside allowed prefixes"
    return None


def inspect_patch(path: str) -> dict:
    patch_path = Path(path)
    if not patch_path.exists() or not patch_path.is_file():
        return {"review_state": "NO_PATCH", "reason": "Patch artifact not supplied or not a regular file."}
    raw = patch_path.read_bytes()
    if len(raw) > MAX_PATCH_BYTES:
        return {"review_state": "BLOCKED", "reason": "Patch exceeds size limit."}
    content = raw.decode("utf-8", errors="replace")
    changed = _patch_paths(content)
    blocked = []
    for name in changed:
        reason = _path_block_reason(name)
        if reason:
            blocked.append({"path": name, "reason": reason})
    has_diff = content.startswith("diff --git ") or ("--- " in content and "+++ " in content)
    state = "BLOCKED" if blocked else (
        "PATCH_PRESENT_REQUIRES_HUMAN_REVIEW" if changed and has_diff else "INVALID_PATCH"
    )
    return {
        "review_state": state,
        "changed_files": changed,
        "blocked_paths": blocked,
        "patch_bytes": len(raw),
        "automatic_merge": False,
        "automatic_deploy": False,
    }


def main() -> int:
    if os.environ.get("MINI_SWE_EXECUTION_ENABLED") == "true":
        print("Unsafe direct execution flag is not supported. Use the approved sandbox proxy.", file=sys.stderr)
        return 2
    report = {
        "task_id": os.environ.get("GITHUB_RUN_ID", "local-preflight"),
        "agent_id": "mini-swe-agent-preflight",
        "state": "PREFLIGHT_ONLY",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "cli": run_cli_check(),
        "patch_review": inspect_patch(sys.argv[1]) if len(sys.argv) > 1 else {"review_state": "NO_PATCH"},
        "execution": "DISABLED_PENDING_SANDBOXED_MODEL_PROXY",
        "evidence": [
            "CLI help availability check only; no model prompt was sent.",
            "No model-generated shell commands were executed.",
            "No repository write token or deploy permission was provided.",
            "Patch policy checks both old and new paths, including rename/deletion headers."
        ],
        "artifacts": [str(OUT)],
        "changed_files": [],
        "next_action": "Provide a sandboxed model proxy that keeps provider credentials outside the agent shell before enabling repairs."
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["cli"].get("available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
