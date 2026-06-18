import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/sync-multica-live-config.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_multica_live_config", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MulticaLiveConfigSyncPlanTests(unittest.TestCase):
    def test_plan_includes_only_agent_instructions_and_skill_content(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt = root / "multica/agent-system-prompts/codex-fullstack.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text("new prompt\n", encoding="utf-8")
            agents_yaml = root / "multica/agents.yaml"
            agents_yaml.write_text(
                "\n".join(
                    [
                        "agents:",
                        "  - name: OpenAI-fullstack",
                        "    visibility: workspace",
                        "    concurrency_limit: 6",
                        "    skills:",
                        "      - context-pack",
                        "    system_prompt_file: multica/agent-system-prompts/codex-fullstack.md",
                    ]
                ),
                encoding="utf-8",
            )
            skill = root / ".agents/skills/context-pack/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: context-pack\ndescription: test\n---\nnew skill\n", encoding="utf-8")

            live = sync.audit.LiveState(
                agents=[
                    {
                        "id": "agent-1",
                        "name": "OpenAI-fullstack",
                        "instructions": "old prompt",
                        "visibility": "workspace",
                        "max_concurrent_tasks": 1,
                        "skills": [{"name": "context-pack"}],
                    }
                ],
                skills=[{"id": "skill-1", "name": "context-pack"}],
                skill_details={"context-pack": {"id": "skill-1", "name": "context-pack", "content": "old skill"}},
            )

            plan = sync.build_sync_plan(
                root=root,
                live=live,
                workspace_id="workspace-1",
                source_repository="https://example.test/repo.git",
                source_commit_sha="abc123",
            )

        self.assertEqual(plan["workspace_id"], "workspace-1")
        self.assertEqual(plan["source_commit_sha"], "abc123")
        self.assertEqual(len(plan["entries"]), 2)
        entry_fields = {(entry["live_object_type"], entry["field"]) for entry in plan["entries"]}
        self.assertEqual(entry_fields, {("agent", "instructions"), ("skill", "content")})
        rendered = json.dumps(plan, sort_keys=True)
        self.assertIn("multica agent update --instructions", rendered)
        self.assertIn("multica skill update --content", rendered)
        self.assertIn("concurrency", plan["safety"]["out_of_scope"])
        self.assertEqual(
            plan["out_of_scope_drift"],
            [
                {
                    "type": "agent",
                    "name": "OpenAI-fullstack",
                    "field": "concurrency",
                    "repo_value": "6",
                    "live_value": "1",
                    "action_required": "manual operator decision required; sync helper does not write concurrency",
                }
            ],
        )
        self.assertFalse(any(entry["field"] == "concurrency" for entry in plan["entries"]))
        self.assertNotIn("max_concurrent_tasks", rendered)
        self.assertNotIn("old prompt", rendered)
        self.assertNotIn("new prompt", rendered)
        self.assertNotIn("old skill", rendered)
        self.assertNotIn("new skill", rendered)

    def test_apply_rejects_wrong_confirmation_before_writes(self) -> None:
        sync = load_sync_module()
        plan = {
            "workspace_id": "workspace-1",
            "source_commit_sha": "abc123",
            "entries": [],
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "confirmation string"):
                sync.validate_plan_for_apply(
                    plan,
                    root,
                    confirm="APPLY workspace-1 wrong",
                    current_workspace_id="workspace-1",
                )

    def test_apply_aborts_when_live_hash_changed_before_writes(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt = root / "multica/agent-system-prompts/codex-fullstack.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text("new prompt\n", encoding="utf-8")
            plan = {
                "workspace_id": "workspace-1",
                "source_commit_sha": "abc123",
                "entries": [
                    {
                        "repo_file_path": "multica/agent-system-prompts/codex-fullstack.md",
                        "live_object_type": "agent",
                        "live_object_name": "OpenAI-fullstack",
                        "live_object_id": "agent-1",
                        "field": "instructions",
                        "old_live_hash": sync.sha256_text("old prompt"),
                        "new_repo_hash": sync.sha256_text("new prompt"),
                    }
                ],
            }
            live = sync.audit.LiveState(
                agents=[
                    {
                        "id": "agent-1",
                        "name": "OpenAI-fullstack",
                        "instructions": "changed prompt",
                    }
                ]
            )
            writes = []

            def write_runner(command, timeout_seconds):
                writes.append(command)
                return {}, None

            with mock.patch.object(sync, "workspace_id", return_value="workspace-1"), mock.patch.object(
                sync, "source_commit_sha", return_value="abc123"
            ), mock.patch.object(sync.audit, "fetch_live_state", return_value=live):
                with self.assertRaisesRegex(ValueError, "changed since plan"):
                    sync.apply_plan(
                        root=root,
                        plan=plan,
                        confirm="APPLY workspace-1 abc123",
                        timeout_seconds=1,
                        command_runner=write_runner,
                    )

        self.assertEqual(writes, [])

    def test_apply_writes_allowlisted_command_when_hashes_match(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt = root / "multica/agent-system-prompts/codex-fullstack.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text("new prompt\n", encoding="utf-8")
            plan = {
                "workspace_id": "workspace-1",
                "source_commit_sha": "abc123",
                "entries": [
                    {
                        "repo_file_path": "multica/agent-system-prompts/codex-fullstack.md",
                        "live_object_type": "agent",
                        "live_object_name": "OpenAI-fullstack",
                        "live_object_id": "agent-1",
                        "field": "instructions",
                        "old_live_hash": sync.sha256_text("old prompt"),
                        "new_repo_hash": sync.sha256_text("new prompt"),
                    }
                ],
            }
            live = sync.audit.LiveState(
                agents=[
                    {
                        "id": "agent-1",
                        "name": "OpenAI-fullstack",
                        "instructions": "old prompt",
                    }
                ]
            )
            writes = []

            def write_runner(command, timeout_seconds):
                writes.append(command)
                return {}, None

            with mock.patch.object(sync, "workspace_id", return_value="workspace-1"), mock.patch.object(
                sync, "source_commit_sha", return_value="abc123"
            ), mock.patch.object(sync.audit, "fetch_live_state", return_value=live):
                evidence = sync.apply_plan(
                    root=root,
                    plan=plan,
                    confirm="APPLY workspace-1 abc123",
                    timeout_seconds=1,
                    command_runner=write_runner,
                )

        self.assertEqual(
            writes,
            [("multica", "agent", "update", "agent-1", "--instructions", "new prompt\n", "--output", "json")],
        )
        self.assertEqual(evidence["objects_updated"][0]["field"], "instructions")

    def test_write_command_allowlist_rejects_other_update_fields(self) -> None:
        sync = load_sync_module()

        self.assertTrue(
            sync.is_allowlisted_write_command(
                ("multica", "agent", "update", "agent-1", "--instructions", "new prompt", "--output", "json")
            )
        )
        self.assertTrue(
            sync.is_allowlisted_write_command(
                ("multica", "agent", "update", "agent-1", "--output", "json", "--instructions", "new prompt")
            )
        )
        self.assertTrue(
            sync.is_allowlisted_write_command(
                ("multica", "skill", "update", "skill-1", "--content", "new skill", "--output", "json")
            )
        )
        self.assertFalse(
            sync.is_allowlisted_write_command(
                ("multica", "skill", "update", "skill-1", "--content", "", "--output", "json")
            )
        )
        self.assertFalse(
            sync.is_allowlisted_write_command(
                ("multica", "agent", "update", "agent-1", "--visibility", "workspace", "--output", "json")
            )
        )
        _, error = sync.run_multica_write_command(
            ("multica", "agent", "update", "agent-1", "--max-concurrent-tasks", "6", "--output", "json"),
            timeout_seconds=1,
        )

        self.assertEqual(error, "write command is not in the sync allowlist")

    def test_write_value_validation_rejects_secret_like_text(self) -> None:
        sync = load_sync_module()

        self.assertEqual(sync.validate_write_value(""), "write value is empty")
        self.assertEqual(sync.validate_write_value("token=abc123"), "write value appears to contain secret-like text")
        self.assertEqual(sync.validate_write_value('"session": "abc123"'), "write value appears to contain secret-like text")
        self.assertEqual(sync.validate_write_value("export API_KEY=abc123"), "write value appears to contain secret-like text")
        self.assertEqual(sync.validate_write_value("The token is abc123"), "write value appears to contain secret-like text")
        self.assertEqual(sync.validate_write_value("my secret password is hunter2"), "write value appears to contain secret-like text")
        self.assertIsNone(sync.validate_write_value("ordinary prompt text"))
        self.assertIsNone(sync.validate_write_value("recovering from a long issue thread, PR discussion, or terminal session\n- preserving decisions"))

    def test_default_write_runner_blocks_inline_prompt_transport(self) -> None:
        sync = load_sync_module()

        _, error = sync.run_multica_write_command(
            ("multica", "agent", "update", "agent-1", "--instructions", "new prompt", "--output", "json"),
            timeout_seconds=1,
        )

        self.assertEqual(
            error,
            "inline prompt/skill writes are disabled until the Multica CLI supports file or stdin transport for instructions and skill content",
        )

    def test_hashes_are_normalized(self) -> None:
        sync = load_sync_module()

        self.assertEqual(sync.sha256_text("value\n"), sync.sha256_text(" value\r\n"))

    def test_worktree_clean_check_detects_uncommitted_changes(self) -> None:
        sync = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess_run = __import__("subprocess").run
            subprocess_run(("git", "init"), cwd=root, check=True, capture_output=True)
            subprocess_run(("git", "config", "user.email", "test@example.test"), cwd=root, check=True)
            subprocess_run(("git", "config", "user.name", "Test User"), cwd=root, check=True)
            tracked = root / "tracked.txt"
            tracked.write_text("clean\n", encoding="utf-8")
            subprocess_run(("git", "add", "tracked.txt"), cwd=root, check=True)
            subprocess_run(("git", "commit", "-m", "initial"), cwd=root, check=True, capture_output=True)

            self.assertTrue(sync.worktree_is_clean(root))
            tracked.write_text("dirty\n", encoding="utf-8")

            self.assertFalse(sync.worktree_is_clean(root))

    def test_apply_cli_requires_operator_environment_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "plan.json"
            plan.write_text('{"workspace_id":"workspace-1","source_commit_sha":"abc123","entries":[]}', encoding="utf-8")
            env = dict(os.environ)
            env.pop("MULTICA_SYNC_ALLOWED", None)

            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "apply",
                    "--plan",
                    str(plan),
                    "--confirm",
                    "APPLY workspace-1 abc123",
                ],
                capture_output=True,
                text=True,
                cwd=SCRIPT_PATH.parents[1],
                env=env,
            )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("MULTICA_SYNC_ALLOWED=true", completed.stderr)
