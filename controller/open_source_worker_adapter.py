"""Guarded preflight for optional open-source worker runtimes.

This module intentionally does not launch an agent. mini-SWE-agent can execute
arbitrary shell commands, so the manager must first provide a separately
configured sandbox and an explicit runtime opt-in. A missing prerequisite
returns BLOCKED rather than pretending an agent ran.
"""
from __future__ import annotations

import json
import os
import shutil
from typing import Any


UPSTREAMS: dict[str, dict[str, str]] = {
    "coding": {
        "project": "mini-swe-agent",
        "repository": "https://github.com/SWE-agent/mini-swe-agent",
        "command_env": "MINI_SWE_AGENT_BIN",
        "sandbox_env": "MINI_SWE_AGENT_SANDBOX",
    },
    "browser_qa": {
        "project": "Playwright",
        "repository": "https://github.com/microsoft/playwright",
        "command_env": "PLAYWRIGHT_TEST_COMMAND",
        "sandbox_env": "PLAYWRIGHT_SANDBOX",
    },
}


def inspect_adapter(name: str, environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Return an honest readiness result without running untrusted task code."""
    env = os.environ if environ is None else environ
    spec = UPSTREAMS.get(name)
    if spec is None:
        return {
            "adapter": name,
            "state": "BLOCKED",
            "reason": "Unknown adapter; no command was executed.",
            "executed": False,
        }

    command_value = env.get(spec["command_env"], "").strip()
    sandbox = env.get(spec["sandbox_env"], "").strip().lower()
    command = command_value.split()[0] if command_value else ""
    binary_found = bool(command and (shutil.which(command) or (command.startswith("/") and os.path.isfile(command))))
    checks = {
        "runtime_command_configured": bool(command_value),
        "runtime_binary_found": binary_found,
        "explicit_sandbox_enabled": sandbox in {"docker", "podman", "true", "enabled"},
    }
    ready = all(checks.values())
    return {
        "adapter": name,
        "project": spec["project"],
        "upstream": spec["repository"],
        "state": "PREFLIGHT_READY_NOT_EXECUTED" if ready else "BLOCKED",
        "checks": checks,
        "executed": False,
        "reason": (
            "Preflight passed only. Execution still requires a reviewed runtime bridge and scoped task contract."
            if ready else
            "Runtime is not connected: configure the command and explicit container sandbox first."
        ),
        "automatic_merge": False,
        "automatic_deploy": False,
        "captain_approval_required": True,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("adapter", choices=sorted(UPSTREAMS))
    args = parser.parse_args()
    result = inspect_adapter(args.adapter)
    print(json.dumps(result, indent=2))
    return 0 if result["state"] == "PREFLIGHT_READY_NOT_EXECUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
