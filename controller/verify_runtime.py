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
    "agents/registry.json",
    "agents/teams.json",
    "agents/team_runtime.json",
    "agents/agent_inventory.json",
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

    try:
        registry = json.loads((ROOT/"agents/registry.json").read_text(encoding="utf-8"))
        inventory = json.loads((ROOT/"agents/agent_inventory.json").read_text(encoding="utf-8"))
        captains = [a for a in registry.get("agents", []) if a.get("type") == "captain"]
        if len(captains) != 9:
            errors.append(f"expected 9 captains, found {len(captains)}")
        if inventory.get("captain_count") != 9:
            errors.append("agent inventory captain count is not 9")
        if inventory.get("child_agent_count") != 45:
            errors.append("agent inventory child-agent count is not 45")
        if inventory.get("total_roles") != 54:
            errors.append("agent inventory total role count is not 54")
        if len(inventory.get("child_agents", [])) != 45:
            errors.append("agent inventory does not contain 45 child-agent definitions")
    except Exception as exc:
        errors.append(f"agent inventory validation failed: {exc}")

    if errors:
        print("\n".join("ERROR: "+e for e in errors))
        return 1

    print("Agent runtime structure: OK")
    print(f"Authorized enabled sites: {len(enabled)}")
    print("One-site execution policy: OK")
    print("Captain/child-agent inventory: 9 captains + 45 child roles = 54 roles")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
