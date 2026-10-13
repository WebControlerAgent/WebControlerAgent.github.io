"""Tests for guarded open-source runtime adapters."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from controller.open_source_worker_adapter import inspect_adapter, run_coding_task


class OpenSourceAdapterPreflightTests(unittest.TestCase):
    def test_unknown_adapter_is_blocked(self):
        result = inspect_adapter("unknown", {})
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["executed"])

    def test_missing_configuration_is_blocked(self):
        result = inspect_adapter("coding", {})
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["executed"])
        self.assertFalse(result["checks"]["explicit_sandbox_enabled"])

    def test_missing_binary_is_blocked_even_if_configured(self):
        env = {
            "MINI_SWE_AGENT_BIN": "mini",
            "MINI_SWE_AGENT_SANDBOX": "docker",
            "MINI_SWE_AGENT_IMAGE": "bounded-worker:latest",
        }
        with patch("controller.open_source_worker_adapter.shutil.which", return_value=None):
            result = inspect_adapter("coding", env)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["checks"]["runtime_binary_found"])

    def test_preflight_never_claims_execution(self):
        env = {
            "MINI_SWE_AGENT_BIN": "mini",
            "MINI_SWE_AGENT_SANDBOX": "docker",
            "MINI_SWE_AGENT_IMAGE": "bounded-worker:latest",
        }
        with patch("controller.open_source_worker_adapter.shutil.which", return_value="/usr/bin/mini"):
            result = inspect_adapter("coding", env)
        self.assertEqual(result["state"], "PREFLIGHT_READY_NOT_EXECUTED")
        self.assertFalse(result["executed"])
        self.assertTrue(result["captain_approval_required"])
        self.assertFalse(result["automatic_merge"])
        self.assertFalse(result["automatic_deploy"])

    def test_browser_qa_requires_explicit_sandbox(self):
        env = {
            "PLAYWRIGHT_TEST_COMMAND": "npx playwright test",
            "PLAYWRIGHT_SANDBOX": "false",
        }
        with patch("controller.open_source_worker_adapter.shutil.which", return_value="/usr/bin/npx"):
            result = inspect_adapter("browser_qa", env)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["checks"]["explicit_sandbox_enabled"])

    def test_executor_blocks_unauthorized_repository_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / "repo"
            checkout.mkdir()
            (checkout / ".git").mkdir()
            result = run_coding_task(
                repository_checkout=checkout,
                task={
                    "task_id": "t1", "site": "other", "repository": "bad/repo",
                    "task_type": "bug_fix", "objective": "fix", "allowed_paths": ["src/a.py"],
                },
                sites={"sites": []}, output_dir=Path(tmp) / "out", environ={},
            )
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["executed"])

    def test_executor_rejects_path_like_task_id(self):
        env = {
            "MINI_SWE_AGENT_BIN": "mini",
            "MINI_SWE_AGENT_SANDBOX": "docker",
            "MINI_SWE_AGENT_IMAGE": "bounded-worker:latest",
        }
        with tempfile.TemporaryDirectory() as tmp, patch(
            "controller.open_source_worker_adapter.shutil.which", return_value="/usr/bin/mini"
        ):
            checkout = Path(tmp) / "repo"
            checkout.mkdir()
            (checkout / ".git").mkdir()
            result = run_coding_task(
                repository_checkout=checkout,
                task={
                    "task_id": "../escape", "site": "demo", "repository": "owner/site",
                    "task_type": "bug_fix", "objective": "fix", "allowed_paths": ["src/a.py"],
                },
                sites={"sites": [{"id": "demo", "repository": "owner/site", "enabled": True, "authorized": True}]},
                output_dir=Path(tmp) / "out", environ=env,
            )
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["executed"])

    def test_executor_blocks_unsafe_path_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / "repo"
            checkout.mkdir()
            (checkout / ".git").mkdir()
            result = run_coding_task(
                repository_checkout=checkout,
                task={
                    "task_id": "t1", "site": "demo", "repository": "owner/site",
                    "task_type": "bug_fix", "objective": "fix", "allowed_paths": ["../.env"],
                },
                sites={"sites": [{"id": "demo", "repository": "owner/site", "enabled": True, "authorized": True}]},
                output_dir=Path(tmp) / "out", environ={},
            )
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["executed"])


    def test_executor_exports_allowed_untracked_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkout = root / "repo"
            checkout.mkdir()
            (checkout / ".git").mkdir()
            (checkout / "src").mkdir()
            (checkout / "src" / "main.py").write_text("print('base')\n", encoding="utf-8")
            env = {
                "MINI_SWE_AGENT_BIN": "mini",
                "MINI_SWE_AGENT_SANDBOX": "docker",
                "MINI_SWE_AGENT_IMAGE": "bounded-worker:test",
            }
            real_run = subprocess.run

            def fake_run(command, **kwargs):
                if command[0] == "/usr/bin/mini":
                    workspace = Path(kwargs["cwd"])
                    (workspace / "src" / "new.py").write_text("print('new')\n", encoding="utf-8")
                    return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")
                return real_run(command, **kwargs)

            with patch("controller.open_source_worker_adapter.shutil.which", return_value="/usr/bin/mini"), patch(
                "controller.open_source_worker_adapter.subprocess.run", side_effect=fake_run
            ):
                result = run_coding_task(
                    repository_checkout=checkout,
                    task={
                        "task_id": "untracked-test", "site": "demo", "repository": "owner/site",
                        "task_type": "bug_fix", "objective": "add a file", "allowed_paths": ["src/new.py"],
                    },
                    sites={"sites": [{"id": "demo", "repository": "owner/site", "enabled": True, "authorized": True}]},
                    output_dir=root / "artifacts", environ=env,
                )
            self.assertEqual(result["state"], "READY_FOR_INDEPENDENT_CHECK")
            self.assertIn("src/new.py", result["changed_files"])
            self.assertIn("src/new.py", (root / "artifacts" / "untracked-test.patch").read_text(encoding="utf-8"))
            self.assertFalse((checkout / "src" / "new.py").exists())

    def test_executor_rejects_disallowed_untracked_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkout = root / "repo"
            checkout.mkdir()
            (checkout / ".git").mkdir()
            (checkout / "base.py").write_text("print('base')\n", encoding="utf-8")
            env = {
                "MINI_SWE_AGENT_BIN": "mini",
                "MINI_SWE_AGENT_SANDBOX": "docker",
                "MINI_SWE_AGENT_IMAGE": "bounded-worker:test",
            }
            real_run = subprocess.run

            def fake_run(command, **kwargs):
                if command[0] == "/usr/bin/mini":
                    (Path(kwargs["cwd"]) / "outside.py").write_text("bad\n", encoding="utf-8")
                    return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")
                return real_run(command, **kwargs)

            with patch("controller.open_source_worker_adapter.shutil.which", return_value="/usr/bin/mini"), patch(
                "controller.open_source_worker_adapter.subprocess.run", side_effect=fake_run
            ):
                result = run_coding_task(
                    repository_checkout=checkout,
                    task={
                        "task_id": "out-of-scope-test", "site": "demo", "repository": "owner/site",
                        "task_type": "bug_fix", "objective": "add a file", "allowed_paths": ["src/allowed.py"],
                    },
                    sites={"sites": [{"id": "demo", "repository": "owner/site", "enabled": True, "authorized": True}]},
                    output_dir=root / "artifacts", environ=env,
                )
            self.assertEqual(result["state"], "VERIFYING")
            self.assertEqual(result["blocked_paths"], ["outside.py"])
            self.assertFalse((root / "artifacts" / "out-of-scope-test.patch").exists())

    def test_executor_rejects_output_directory_inside_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkout = root / "repo"
            checkout.mkdir()
            (checkout / ".git").mkdir()
            env = {
                "MINI_SWE_AGENT_BIN": "mini",
                "MINI_SWE_AGENT_SANDBOX": "docker",
                "MINI_SWE_AGENT_IMAGE": "bounded-worker:test",
            }
            with patch("controller.open_source_worker_adapter.shutil.which", return_value="/usr/bin/mini"):
                result = run_coding_task(
                    repository_checkout=checkout,
                    task={
                        "task_id": "inside-output", "site": "demo", "repository": "owner/site",
                        "task_type": "bug_fix", "objective": "fix", "allowed_paths": ["src/a.py"],
                    },
                    sites={"sites": [{"id": "demo", "repository": "owner/site", "enabled": True, "authorized": True}]},
                    output_dir=checkout / "artifacts", environ=env,
                )
            self.assertEqual(result["state"], "BLOCKED")
            self.assertFalse(result["executed"])
            self.assertFalse((checkout / "artifacts").exists())

if __name__ == "__main__":
    unittest.main()
