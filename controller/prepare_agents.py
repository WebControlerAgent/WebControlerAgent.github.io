"""Register all captain and child-agent roles from the canonical contracts.

READY means registered and available for dispatch; it does not mean an LLM
adapter is connected or a role is currently executing.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def write(rel, data):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")

def main():
    registry = read("agents/registry.json")
    teams = read("agents/teams.json")["templates"]
    contracts = read("agents/team_runtime.json")["teams"]
    captains = [a for a in registry["agents"] if a.get("type") == "captain"]
    if len(captains) != 9:
        raise SystemExit(f"Expected exactly 9 captains; found {len(captains)}")
    captain_ids = [a["id"] for a in captains]
    if len(set(captain_ids)) != len(captain_ids):
        raise SystemExit("Duplicate captain IDs found")

    child_agents = []
    for captain in captains:
        team = captain.get("team_template")
        if team not in teams or team not in contracts:
            raise SystemExit(f"Missing team contract for captain {captain['id']}: {team}")
        declared = teams[team]
        defined = contracts[team]
        if len(declared) != 10 or len(defined) != 10:
            raise SystemExit(f"Team {team} must have exactly ten child-agent roles (five worker/checker pairs)")
        declared_ids = set(declared)
        defined_ids = {item[0] for item in defined}
        if declared_ids != defined_ids:
            raise SystemExit(f"Team template and runtime contract mismatch: {team}")
        for role_id, mission, evidence in defined:
            child_agents.append({
                "id": f"{captain['id']}/{role_id}",
                "role_id": role_id,
                "name": role_id.replace("-", " ").title(),
                "parent_captain": captain["id"],
                "team": team,
                "mission": mission,
                "expected_evidence": evidence,
                "readiness": "READY",
                "state": "WAITING",
                "execution_status": "REGISTERED_NOT_RUNNING",
                "adapter": "contract-defined",
            })
    child_ids = [a["id"] for a in child_agents]
    if len(child_agents) != 90 or len(set(child_ids)) != 90:
        raise SystemExit(f"Expected 90 unique child-agent roles; found {len(child_agents)}")

    inventory = {
        "version": 1,
        "architecture": "universe/captain/team/agent/task",
        "readiness_semantics": "READY means registered and dispatchable, not currently running",
        "captain_count": len(captains),
        "child_agent_count": len(child_agents),
        "total_roles": len(captains) + len(child_agents),
        "minimum_small_agents_per_task": 2,
        "task_pairing_policy": "primary_worker_plus_independent_checker",
        "captains": [{
            "id": a["id"],
            "name": a["name"],
            "role": a.get("role", a.get("name", a["id"])),
            "mission": a.get("mission", ""),
            "team_template": a["team_template"],
            "readiness": "READY",
            "state": "WAITING",
            "execution_status": "REGISTERED_NOT_RUNNING",
        } for a in captains],
        "child_agents": child_agents,
        "runtime_capabilities": {
            "persistent_roster": True,
            "one_active_site_lock": registry.get("execution", {}).get("max_active_sites") == 1,
            "evidence_required_for_completion": True,
            "ai_provider_adapter_connected": False,
            "child_role_execution_adapter": "pending",
        },
    }
    write("agents/agent_inventory.json", inventory)

    state = read("controller/agent_state.json")
    previous_captains = state.get("captain_states", {})
    previous_children = state.get("child_agent_states", {})
    state["captain_states"] = {
        a["id"]: {
            **previous_captains.get(a["id"], {}),
            "id": a["id"], "name": a["name"], "role": a.get("role", a["name"]),
            "team_template": a["team_template"], "readiness": "READY",
            "state": previous_captains.get(a["id"], {}).get("state", "WAITING"),
            "execution_status": "REGISTERED_NOT_RUNNING",
        } for a in captains
    }
    state["child_agent_states"] = {
        a["id"]: {
            **previous_children.get(a["id"], {}),
            **a,
            "state": previous_children.get(a["id"], {}).get("state", "WAITING"),
            "readiness": "READY",
            "execution_status": "REGISTERED_NOT_RUNNING",
        } for a in child_agents
    }
    state["agent_inventory_summary"] = {
        "captains_ready": len(captains),
        "child_agents_ready": len(child_agents),
        "total_roles_ready": len(captains) + len(child_agents),
        "minimum_small_agents_per_task": 2,
        "task_pairing_policy": "primary_worker_plus_independent_checker",
    }
    write("controller/agent_state.json", state)

    status_path = ROOT / "public/status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    status["agent_inventory"] = {
        "captains_ready": len(captains),
        "child_agents_ready": len(child_agents),
        "total_roles_ready": len(captains) + len(child_agents),
        "registry_valid": True,
        "readiness_semantics": "Registered and available; not necessarily executing",
        "child_role_execution_adapter": "pending",
        "ai_provider_adapter_connected": False,
    }
    status["agent_runtime"] = state
    write("public/status.json", status)
    print(f"Agent registry ready: {len(captains)} captains + {len(child_agents)} child roles = {len(captains)+len(child_agents)} roles")
    print("Task policy: every dispatched task requires a primary worker plus an independent checker.")
    print("Execution status: registered/WAITING; no role is falsely marked as actively running.")

if __name__ == "__main__":
    main()
