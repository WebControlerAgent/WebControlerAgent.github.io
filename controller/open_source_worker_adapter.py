"""Guarded open-source worker runtime adapters.

The coding adapter invokes mini-SWE-agent against a disposable copy mounted into
an isolated Docker container with networking disabled. It returns a patch artifact
only: it never writes back to the caller's checkout, commits, merges, or deploys.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
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
    """Check configuration without launching an agent."""
    env = os.environ if environ is None else environ
    spec = UPSTREAMS.get(name)
    if spec is None:
        return {"adapter": name, "state": "BLOCKED", "reason": "Unknown adapter.", "executed": False}

    command_value = env.get(spec["command_env"], "").strip()
    sandbox = env.get(spec["sandbox_env"], "").strip().lower()
    command = command_value.split()[0] if command_value else ""
    binary_found = bool(command and (shutil.which(command) or (command.startswith("/") and os.path.isfile(command))))
    checks = {
        "runtime_command_configured": bool(command_value),
        "runtime_binary_found": binary_found,
        "explicit_sandbox_enabled": sandbox == "docker",
    }
    if name == "coding":
        checks["container_image_configured"] = bool(env.get("MINI_SWE_AGENT_IMAGE", "").strip())
    ready = all(checks.values())
    return {
        "adapter": name,
        "project": spec["project"],
        "upstream": spec["repository"],
        "state": "PREFLIGHT_READY_NOT_EXECUTED" if ready else "BLOCKED",
        "checks": checks,
        "executed": False,
        "reason": "Preflight only; call run_coding_task with a validated task to execute." if ready
        else "Runtime configuration incomplete; no command was executed.",
        "automatic_merge": False,
        "automatic_deploy": False,
        "captain_approval_required": True,
    }


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"})
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=cwd, env=env, text=True, capture_output=True, check=True, timeout=30,
    )


def run_coding_task(
    *,
    repository_checkout: str | Path,
    task: dict[str, Any],
    sites: dict[str, Any],
    output_dir: str | Path,
    environ: dict[str, str] | None = None,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    """Run mini-SWE-agent in Docker on a disposable copy and export only scoped changes.

    The caller must provide an already validated task/site registry. The model API
    key remains in the host process and is not forwarded to the container. Container
    networking is disabled; no source checkout is modified by this function.
    """
    env = os.environ if environ is None else environ
    preflight = inspect_adapter("coding", dict(env))
    if preflight["state"] != "PREFLIGHT_READY_NOT_EXECUTED":
        return {"state": "BLOCKED", "executed": False, "reason": preflight["reason"]}
    if task.get("task_type") not in {"bug_fix", "code_change_proposal"}:
        return {"state": "BLOCKED", "executed": False, "reason": "Unsupported task type."}
    required = ("task_id", "site", "repository", "objective", "allowed_paths")
    if any(not task.get(key) for key in required) or not isinstance(task.get("allowed_paths"), list):
        return {"state": "BLOCKED", "executed": False, "reason": "Task contract incomplete."}
    task_id = str(task["task_id"])
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", task_id):
        return {"state": "BLOCKED", "executed": False, "reason": "Unsafe task_id."}
    if len(str(task["objective"])) > 4000 or len(task["allowed_paths"]) > 40:
        return {"state": "BLOCKED", "executed": False, "reason": "Task exceeds runtime limits."}
    matches = [s for s in sites.get("sites", []) if s.get("id") == task["site"] and s.get("enabled") and s.get("authorized")]
    if len(matches) != 1 or matches[0].get("repository") != task["repository"]:
        return {"state": "BLOCKED", "executed": False, "reason": "Site authorization or repository mismatch."}

    source = Path(repository_checkout).resolve()
    destination = Path(output_dir).resolve()
    if not source.is_dir() or not (source / ".git").exists():
        return {"state": "BLOCKED", "executed": False, "reason": "A git checkout is required."}
    allowed = [str(p).replace("\\", "/") for p in task["allowed_paths"]]
    if not allowed or any(
        p.startswith("/") or ".." in Path(p).parts or p.startswith(".github/")
        or any(part in {"node_modules", "dist", "build", ".git"} for part in Path(p).parts)
        or Path(p).suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".md"}
        or Path(p).name.startswith(".env") or Path(p).name in {"sites.json", "config.json"}
        or "lock" in Path(p).name.lower()
        for p in allowed
    ):
        return {"state": "BLOCKED", "executed": False, "reason": "Unsafe allowed_paths."}

    # Never place artifacts inside the source checkout: even a safe patch
    # output directory there would violate the read-only source guarantee.
    if destination == source or source in destination.parents:
        return {"state": "BLOCKED", "executed": False, "reason": "Output directory must be outside the source checkout."}

    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bounded-mini-swe-") as tmp:
        workspace = Path(tmp) / "workspace"
        shutil.copytree(
            source, workspace,
            ignore=shutil.ignore_patterns(
                ".git", ".github", ".env", ".env.*", "secrets", "secrets.*",
                "*.pem", "*.key", "id_rsa", "credentials*", "__pycache__",
                ".pytest_cache", "node_modules", "dist", "build",
            ),
        )
        _run_git(["init"], workspace)
        _run_git(["config", "user.name", "Bounded Worker"], workspace)
        _run_git(["config", "user.email", "bounded-worker@localhost"], workspace)
        _run_git(["add", "-A"], workspace)
        _run_git(["commit", "-m", "Isolated baseline"], workspace)
        baseline = _run_git(["rev-parse", "HEAD"], workspace).stdout.strip()
        # A fresh output directory avoids inheriting repository credentials or hooks.
        output_file = Path(tmp) / "trajectory.json"
        config_file = Path(tmp) / "mini-sandbox.yaml"
        run_args = [
            "--rm", "--network", "none", "-v", f"{workspace}:/workspace",
            "-e", "GIT_CONFIG_COUNT=1",
            "-e", "GIT_CONFIG_KEY_0=safe.directory",
            "-e", "GIT_CONFIG_VALUE_0=/workspace",
        ]
        config_file.write_text(
            "environment:\n"
            "  image: " + json.dumps(env["MINI_SWE_AGENT_IMAGE"]) + "\n"
            "  cwd: /workspace\n"
            "  run_args: " + json.dumps(run_args) + "\n",
            encoding="utf-8",
        )
        objective = (
            "Work only inside /workspace. Do not access secrets, network, credentials, or attempt deployment. "
            "Implement the requested change and run relevant local tests if available. "
            "Do not commit or push. Task ID: " + str(task["task_id"]) +
            "\nObjective: " + str(task["objective"]) +
            "\nAllowed paths (do not modify anything else): " + ", ".join(allowed) +
            "\nFinish by printing COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT on its own line."
        )
        command = [
            shutil.which(env["MINI_SWE_AGENT_BIN"].strip()) or env["MINI_SWE_AGENT_BIN"].strip(), "-y", "--exit-immediately",
            "--environment-class", "minisweagent.environments.docker.DockerEnvironment",
            "-c", "mini.yaml", "-c", str(config_file),
            "-t", objective, "-o", str(output_file),
        ]
        try:
            completed = subprocess.run(
                command, cwd=workspace, env=dict(env), text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=timeout_seconds, check=False,
            )
        except subprocess.TimeoutExpired:
            return {"state": "VERIFYING", "executed": True, "reason": "Agent timed out; candidate not accepted."}

        # Include untracked files in scope validation. Plain git diff silently
        # omits them, which could otherwise hide a worker-created file.
        status_lines = _run_git(
            ["status", "--porcelain", "--untracked-files=all"], workspace
        ).stdout.splitlines()
        untracked = [line[3:] for line in status_lines if line.startswith("?? ")]
        changed = sorted(set(_run_git(["diff", "--name-only", baseline], workspace).stdout.splitlines() + untracked))
        unsafe = [
            p for p in changed
            if not any(p == a or (a.endswith("/") and p.startswith(a)) for a in allowed)
        ]
        if unsafe:
            return {
                "state": "VERIFYING",
                "executed": True,
                "return_code": completed.returncode,
                "changed_files": changed,
                "blocked_paths": unsafe,
                "reason": "Worker touched paths outside the explicit allowlist; no patch exported.",
            }
        if untracked:
            _run_git(["add", "-N", "--", *untracked], workspace)
        changed = _run_git(["diff", "--name-only", baseline], workspace).stdout.splitlines()
        if completed.returncode != 0 or not changed:
            return {
                "state": "VERIFYING" if completed.returncode == 0 else "BLOCKED",
                "executed": True,
                "return_code": completed.returncode,
                "changed_files": changed,
                "blocked_paths": [],
                "reason": "No scoped patch was accepted; independent checker and Captain review are required.",
            }
        patch = _run_git(["diff", "--binary", baseline], workspace).stdout
        patch_path = destination / f"{task_id}.patch"
        patch_path.write_text(patch, encoding="utf-8")
        return {
            "state": "READY_FOR_INDEPENDENT_CHECK",
            "executed": True,
            "task_id": task_id,
            "changed_files": changed,
            "patch_artifact": str(patch_path),
            "repository_modified": False,
            "write_access": False,
            "automatic_merge": False,
            "automatic_deploy": False,
            "captain_approval_required": True,
            "agent_return_code": completed.returncode,
            "baseline_sha": baseline,
        }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("adapter", choices=sorted(UPSTREAMS))
    parser.add_argument("--task-json", help="Validated task JSON; required to execute the coding adapter.")
    parser.add_argument("--checkout", help="Local disposable source checkout for the authorized site.")
    parser.add_argument("--sites-json", default="controller/sites.json", help="Authorized site registry JSON.")
    parser.add_argument("--output-dir", default="worker-artifacts", help="Directory for candidate patch artifacts.")
    parser.add_argument("--timeout", type=int, default=900, help="Maximum agent runtime in seconds.")
    args = parser.parse_args()

    if args.task_json:
        if args.adapter != "coding" or not args.checkout:
            parser.error("--task-json requires adapter=coding and --checkout")
        try:
            task = json.loads(Path(args.task_json).read_text(encoding="utf-8"))
            sites = json.loads(Path(args.sites_json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(json.dumps({"state": "BLOCKED", "executed": False, "reason": f"Cannot read task/registry JSON: {exc}"}))
            return 2
        result = run_coding_task(
            repository_checkout=args.checkout,
            task=task,
            sites=sites,
            output_dir=args.output_dir,
            timeout_seconds=args.timeout,
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("state") == "READY_FOR_INDEPENDENT_CHECK" else 2

    result = inspect_adapter(args.adapter)
    print(json.dumps(result, indent=2))
    return 0 if result["state"] == "PREFLIGHT_READY_NOT_EXECUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
