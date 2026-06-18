import unittest

from scripts import live_sync_policy as policy


class LiveSyncPolicyTests(unittest.TestCase):
    def test_syncable_entries_are_limited_to_agent_instructions_and_skill_content(self) -> None:
        self.assertIsNone(policy.validate_plan_entry({"live_object_type": "agent", "field": "instructions"}))
        self.assertIsNone(policy.validate_plan_entry({"live_object_type": "skill", "field": "content"}))
        self.assertEqual(
            policy.validate_plan_entry({"live_object_type": "agent", "field": "concurrency"}),
            "plan contains out-of-scope update: agent.concurrency",
        )
        self.assertEqual(
            policy.validate_plan_entry({"live_object_type": "autopilot", "field": "prompt"}),
            "plan contains out-of-scope update: autopilot.prompt",
        )

    def test_confirmation_string_is_exact(self) -> None:
        plan = {"workspace_id": "workspace-1", "source_commit_sha": "abc123"}

        self.assertEqual(policy.apply_confirmation("workspace-1", "abc123"), "APPLY workspace-1 abc123")
        self.assertIsNone(policy.validate_confirmation(plan, "APPLY workspace-1 abc123"))
        self.assertEqual(
            policy.validate_confirmation(plan, "APPLY workspace-1 wrong"),
            "confirmation string does not match the plan",
        )

    def test_safety_metadata_lists_syncable_and_forbidden_fields(self) -> None:
        metadata = policy.safety_metadata()

        self.assertEqual(metadata["syncable_fields"], ["agent.instructions", "skill.content"])
        self.assertIn("concurrency", metadata["out_of_scope"])
        self.assertIn("custom_env", metadata["out_of_scope"])
        self.assertTrue(metadata["apply_requires_exact_confirmation"])

    def test_write_command_allowlist_rejects_mutation_outside_v1_fields(self) -> None:
        self.assertTrue(
            policy.is_allowlisted_write_command(
                ("multica", "agent", "update", "agent-1", "--instructions", "new prompt", "--output", "json")
            )
        )
        self.assertTrue(
            policy.is_allowlisted_write_command(
                ("multica", "agent", "update", "agent-1", "--output", "json", "--instructions", "new prompt")
            )
        )
        self.assertTrue(
            policy.is_allowlisted_write_command(
                ("multica", "skill", "update", "skill-1", "--content", "new skill", "--output", "json")
            )
        )
        self.assertFalse(
            policy.is_allowlisted_write_command(
                ("multica", "skill", "update", "skill-1", "--content", "", "--output", "json")
            )
        )
        self.assertFalse(
            policy.is_allowlisted_write_command(
                (
                    "multica",
                    "agent",
                    "update",
                    "agent-1",
                    "--instructions",
                    "first",
                    "--instructions",
                    "second",
                    "--output",
                    "json",
                )
            )
        )
        self.assertFalse(
            policy.is_allowlisted_write_command(
                ("multica", "agent", "update", "agent-1", "--content", "new prompt", "--output", "json")
            )
        )
        self.assertFalse(
            policy.is_allowlisted_write_command(
                ("multica", "skill", "update", "skill-1", "--instructions", "new skill", "--output", "json")
            )
        )
        self.assertFalse(
            policy.is_allowlisted_write_command(
                ("multica", "agent", "update", "agent-1", "--max-concurrent-tasks", "6", "--output", "json")
            )
        )
        self.assertFalse(
            policy.is_allowlisted_write_command(
                ("multica", "autopilot", "update", "autopilot-1", "--prompt", "new prompt", "--output", "json")
            )
        )

    def test_write_value_validation_rejects_secret_like_text_but_allows_normal_prose(self) -> None:
        self.assertEqual(policy.validate_write_value(""), "write value is empty")
        self.assertEqual(policy.validate_write_value("token=abc123"), "write value appears to contain secret-like text")
        self.assertEqual(policy.validate_write_value('"session": "abc123"'), "write value appears to contain secret-like text")
        self.assertEqual(policy.validate_write_value("export API_KEY=abc123"), "write value appears to contain secret-like text")
        self.assertEqual(policy.validate_write_value("The token is abc123"), "write value appears to contain secret-like text")
        self.assertEqual(policy.validate_write_value("my secret password is hunter2"), "write value appears to contain secret-like text")
        self.assertIsNone(policy.validate_write_value("ordinary prompt text"))
        self.assertIsNone(
            policy.validate_write_value(
                "recovering from a long issue thread, PR discussion, or terminal session\n- preserving decisions"
            )
        )

    def test_write_value_size_limit_is_policy_owned(self) -> None:
        self.assertIsNone(policy.validate_write_value("x" * policy.MAX_INLINE_WRITE_VALUE_BYTES))
        self.assertEqual(
            policy.validate_write_value("x" * (policy.MAX_INLINE_WRITE_VALUE_BYTES + 1)),
            "write value is too large for inline CLI argument; wait for file/stdin support",
        )

    def test_sync_write_value_extracts_the_allowlisted_field_value(self) -> None:
        self.assertEqual(
            policy.sync_write_value(
                ("multica", "agent", "update", "agent-1", "--instructions", "new prompt", "--output", "json")
            ),
            "new prompt",
        )
        self.assertEqual(
            policy.sync_write_value(
                ("multica", "skill", "update", "skill-1", "--output", "json", "--content", "new skill")
            ),
            "new skill",
        )
        self.assertEqual(policy.sync_write_value(("multica", "agent", "get", "agent-1")), "")

    def test_inline_write_transport_is_disabled_until_cli_supports_file_or_stdin(self) -> None:
        self.assertEqual(
            policy.validate_write_transport(
                ("multica", "agent", "update", "agent-1", "--instructions", "new prompt", "--output", "json")
            ),
            "inline prompt/skill writes are disabled until the Multica CLI supports file or stdin transport for instructions and skill content",
        )
        self.assertEqual(
            policy.validate_write_transport(
                ("multica", "skill", "update", "skill-1", "--content", "new skill", "--output", "json")
            ),
            "inline prompt/skill writes are disabled until the Multica CLI supports file or stdin transport for instructions and skill content",
        )
        self.assertIsNone(policy.validate_write_transport(("multica", "agent", "get", "agent-1", "--output", "json")))


if __name__ == "__main__":
    unittest.main()
