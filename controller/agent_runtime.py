"""Deterministic Agent Runtime contract.

This module does not perform external actions by itself. It defines the safe,
persistent state transitions used by the controller when real agent adapters
are connected.
"""
from __future__ import annotations

from copy import deepcopy

STATES = {
    "WAITING", "CLAIMED", "WORKING", "VERIFYING",
    "COMPLETED", "FAILED", "REPAIRING", "RETRY",
}

AGENTS = {
    "manager": {"name": "Manager", "role": "Team Lead"},
    "researcher": {"name": "Researcher", "role": "Research & Discovery"},
    "image-agent": {"name": "Image Agent", "role": "Authorized Media"},
    "publisher": {"name": "Publisher", "role": "Build & Deploy"},
    "seo-agent": {"name": "SEO Agent", "role": "Search Specialist"},
    "qa": {"name": "QA Agent", "role": "Final Verification"},
    "bug-hunter": {"name": "Bug Hunter", "role": "Find & Diagnose"},
    "bug-solver": {"name": "Bug Solver", "role": "Repair & Fix"},
    "idea-builder": {"name": "Idea Builder", "role": "Innovation Captain"},
}

PIPELINE = [
    "manager", "researcher", "image-agent", "publisher", "seo-agent", "qa",
]
FAILURE_PIPELINE = ["bug-hunter", "bug-solver", "qa"]

def new_runtime_state():
    return {
        "active_site": None,
        "queue": [],
        "agent_states": {
            agent_id: {
                "id": agent_id,
                "name": data["name"],
                "role": data["role"],
                "state": "WAITING",
                "site": None,
                "task": None,
                "error": None,
            }
            for agent_id, data in AGENTS.items()
        },
        "events": [],
    }

def normalize(state):
    base = new_runtime_state()
    if not isinstance(state, dict):
        return base
    base.update({k: deepcopy(v) for k, v in state.items() if k in base})
    if not isinstance(base["agent_states"], dict):
        base["agent_states"] = new_runtime_state()["agent_states"]
    if not isinstance(base["queue"], list):
        base["queue"] = []
    if not isinstance(base["events"], list):
        base["events"] = []
    return base

def claim_site(state, site_id):
    state = normalize(state)
    if state["active_site"] is not None:
        raise RuntimeError("Only one site may be active at a time")
    site = {"id": str(site_id), "state": "CLAIMED", "retries": 0}
    state["active_site"] = site
    state["events"].append({"type": "site_claimed", "site": site["id"]})
    return state

def assign(state, agent_id, task, site_id=None):
    state = normalize(state)
    if agent_id not in AGENTS:
        raise KeyError("Unknown agent: " + agent_id)
    if state["active_site"] is None:
        raise RuntimeError("No active site")
    site = site_id or state["active_site"]["id"]
    if site != state["active_site"]["id"]:
        raise RuntimeError("Agent cannot work on a non-active site")
    state["agent_states"][agent_id].update({
        "state": "WORKING",
        "site": site,
        "task": task,
        "error": None,
    })
    state["events"].append({
        "type": "agent_assigned",
        "agent": agent_id,
        "site": site,
        "task": task,
    })
    return state

def verify(state, agent_id, passed, error=None):
    state = normalize(state)
    if agent_id not in state["agent_states"]:
        raise KeyError("Unknown agent: " + agent_id)
    state["agent_states"][agent_id]["state"] = "VERIFYING"
    state["agent_states"][agent_id]["error"] = error
    state["events"].append({
        "type": "verification",
        "agent": agent_id,
        "passed": bool(passed),
        "error": error,
    })
    return state

def complete_site(state):
    state = normalize(state)
    if state["active_site"] is None:
        return state
    site_id = state["active_site"]["id"]
    for item in state["agent_states"].values():
        if item.get("site") == site_id:
            item.update({"state": "WAITING", "site": None, "task": None, "error": None})
    state["events"].append({"type": "site_completed", "site": site_id})
    state["active_site"] = None
    return state

def fail_site(state, error):
    state = normalize(state)
    if state["active_site"] is None:
        raise RuntimeError("No active site")
    state["active_site"]["state"] = "FAILED"
    state["events"].append({
        "type": "site_failed",
        "site": state["active_site"]["id"],
        "error": str(error),
    })
    return state
