import unittest

from controller.manager_ai import fast_reply, validate_plan


class ManagerPlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.sites = {
            "sites": [
                {"id": "site-a", "enabled": True, "authorized": True},
                {"id": "site-disabled", "enabled": False, "authorized": True},
                {"id": "site-unapproved", "enabled": True, "authorized": False},
            ]
        }
        self.idle = {"active_site": None}
        self.active = {"active_site": {"id": "site-a"}}

    def test_authorized_claim_is_allowed(self):
        plan = validate_plan({"action": "claim", "site": "site-a", "reply": "Starting"}, self.sites, self.idle)
        self.assertEqual(plan["action"], "claim")
        self.assertEqual(plan["site"], "site-a")

    def test_unauthorized_or_disabled_claim_is_rejected(self):
        for site in ("site-unapproved", "site-disabled", "unknown"):
            with self.subTest(site=site):
                plan = validate_plan({"action": "claim", "site": site}, self.sites, self.idle)
                self.assertEqual(plan["action"], "none")

    def test_claim_cannot_start_second_site(self):
        plan = validate_plan({"action": "claim", "site": "site-a"}, self.sites, self.active)
        self.assertEqual(plan["action"], "none")

    def test_assignment_requires_known_agent_and_task(self):
        valid = validate_plan(
            {"action": "assign", "site": "site-a", "agent": "qa", "task": "Check deployment"},
            self.sites, self.active,
        )
        self.assertEqual(valid["action"], "assign")
        invalid = validate_plan(
            {"action": "assign", "site": "site-a", "agent": "made-up-agent", "task": "Do work"},
            self.sites, self.active,
        )
        self.assertEqual(invalid["action"], "none")

    def test_state_transition_requires_active_site(self):
        plan = validate_plan({"action": "complete"}, self.sites, self.idle)
        self.assertEqual(plan["action"], "none")

    def test_fast_reply_handles_wrapped_latest_instruction(self):
        wrapped = """Website Manager Chat request (GitHub-only).
Active site: kingdom-raw (kingdom-raw)

Recent conversation context (background only):
(no previous conversation)

LATEST USER INSTRUCTION — this is the only request to answer or act on now:
hi"""
        reply = fast_reply(wrapped)
        self.assertIsNotNone(reply)
        self.assertEqual(reply["action"], "none")
        self.assertIn("kya kaam karna hai", reply["reply"])

    def test_fast_reply_handles_roman_urdu_thanks(self):
        self.assertEqual(fast_reply("shukriya")["action"], "none")

    def test_fast_reply_does_not_match_longer_instruction(self):
        self.assertIsNone(fast_reply("hi please audit my website"))


if __name__ == "__main__":
    unittest.main()
