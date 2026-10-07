"""Validate the GitHub Agent Studio runtime without requiring external services."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "controller/config.json",
    "controller/sites.json",
    "controller/agent_state.json",
    "controller/agent_worker.py",
    "controller/agent_runtime.py",
    "public/status.json",
    "package.json",
    "index.html",
]

def main() -> int:
    errors = []
    for rel in REQUIRED:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"missing: {rel}")

    for rel in ("controller/config.json","controller/sites.json","controller/agent_state.json","public/status.json"):
        p = ROOT / rel
        if p.exists():
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"invalid json {rel}: {exc}")

    sites = json.loads((ROOT/"controller/sites.json").read_text(encoding="utf-8"))
    enabled = [s for s in sites.get("sites", []) if s.get("enabled") and s.get("authorized")]
    if len(enabled) > 1:
        errors.append("more than one enabled authorized site is configured")

    if errors:
        print("\n".join("ERROR: "+e for e in errors))
        return 1

    print("Agent runtime structure: OK")
    print(f"Authorized enabled sites: {len(enabled)}")
    print("One-site execution policy: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
