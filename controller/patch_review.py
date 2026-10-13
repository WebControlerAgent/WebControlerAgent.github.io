"""Deterministic second-pass validator for bounded worker patch artifacts.

This checker does not execute the patch or claim to replace a human/AI code review.
It verifies patch shape, changed-path allowlisting, and a small set of high-risk
patterns before the artifact is marked ready for Captain review.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def validate_patch(task: dict[str, Any], patch_text: str) -> dict[str, Any]:
    allowed = task.get("allowed_paths")
    if not isinstance(allowed, list) or not allowed:
        return {"state": "BLOCKED", "passed": False, "reason": "Task allowlist is missing."}
    paths = re.findall(r"^diff --git a/(.*?) b/(.*?)$", patch_text, flags=re.MULTILINE)
    if not paths:
        return {"state": "BLOCKED", "passed": False, "reason": "Patch has no parseable diff headers."}
    changed = sorted({b for _, b in paths})
    unsafe = []
    for old, new in paths:
        if old != new or new.startswith("/") or ".." in Path(new).parts:
            unsafe.append(new)
            continue
        if not any(new == item or (item.endswith("/") and new.startswith(item)) for item in allowed):
            unsafe.append(new)
        if new.startswith(".github/") or any(part in {".git", "node_modules", "dist", "build"} for part in Path(new).parts):
            unsafe.append(new)
        if Path(new).name.startswith(".env") or Path(new).name.lower() in {"sites.json", "config.json"} or "lock" in Path(new).name.lower():
            unsafe.append(new)
    if unsafe:
        return {"state": "BLOCKED", "passed": False, "changed_files": changed,
                "blocked_paths": sorted(set(unsafe)), "reason": "Patch touches paths outside the safe task scope."}
    if len(patch_text.encode("utf-8")) > 2_000_000:
        return {"state": "BLOCKED", "passed": False, "changed_files": changed,
                "reason": "Patch exceeds the 2 MB review limit."}
    high_risk = [
        (r"(?i)-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "private-key material"),
        (r"(?i)(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})", "token-like secret"),
        (r"(?i)\bcurl\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba)?sh\b", "download-and-execute shell pattern"),
        (r"(?i)\b(?:git\s+push|gh\s+pr\s+merge|npm\s+publish)\b", "publishing/deployment command"),
    ]
    flagged = [label for pattern, label in high_risk if re.search(pattern, patch_text)]
    if flagged:
        return {"state": "NEEDS_HUMAN_REVIEW", "passed": False, "changed_files": changed,
                "flags": flagged, "reason": "High-risk pattern found; no automatic acceptance."}
    return {
        "state": "READY_FOR_CAPTAIN_REVIEW",
        "passed": True,
        "changed_files": changed,
        "independent_check": "deterministic_patch_scope_and_risk_scan",
        "human_or_ai_code_review_still_required": True,
        "automatic_merge": False,
        "automatic_deploy": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-json", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--output", default="worker-artifacts/patch-review.json")
    args = parser.parse_args()
    try:
        task = json.loads(Path(args.task_json).read_text(encoding="utf-8"))
        patch = Path(args.patch).read_text(encoding="utf-8")
        result = validate_patch(task, patch)
    except (OSError, json.JSONDecodeError) as exc:
        result = {"state": "BLOCKED", "passed": False, "reason": str(exc)}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
