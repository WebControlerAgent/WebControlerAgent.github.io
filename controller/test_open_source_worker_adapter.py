"""Tests for honest and fail-closed open-source runtime preflight."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from controller.open_source_worker_adapter import inspect_adapter


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
        }
        with patch("controller.open_source_worker_adapter.shutil.which", return_value=None):
            result = inspect_adapter("coding", env)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertFalse(result["checks"]["runtime_binary_found"])

    def test_preflight_never_claims_execution(self):
        env = {
            "MINI_SWE_AGENT_BIN": "mini",
            "MINI_SWE_AGENT_SANDBOX": "docker",
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


if __name__ == "__main__":
    unittest.main()
