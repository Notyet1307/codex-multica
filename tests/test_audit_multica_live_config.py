import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/audit-multica-live-config.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_multica_live_config", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MulticaLiveConfigAuditTests(unittest.TestCase):
    def test_live_command_plan_only_uses_multica_read_commands(self) -> None:
        audit = load_audit_module()
        forbidden = {
            "archive",
            "avatar",
            "create",
            "delete",
            "env",
            "import",
            "member",
            "restore",
            "sync",
            "trigger",
            "trigger-add",
            "trigger-delete",
            "trigger-rotate-url",
            "trigger-update",
            "update",
        }

        commands = audit.build_live_command_plan()

        self.assertGreaterEqual(len(commands), 4)
        for command in commands:
            self.assertEqual(command[0], "multica")
            self.assertIn(command[2], {"list", "get"})
            self.assertIn("--output", command)
            self.assertIn("json", command)
            self.assertFalse(forbidden.intersection(command))

    def test_redacts_sensitive_fields_recursively(self) -> None:
        audit = load_audit_module()
        payload = {
            "name": "OpenAI-fullstack",
            "custom_env": {"DEEPSEEK_API_KEY": "live-secret"},
            "nested": {
                "session_cookie": "cookie-value",
                "safe": "visible",
            },
            "items": [{"token": "raw-token"}],
        }

        redacted = audit.redact_sensitive(payload)
        rendered = repr(redacted)

        self.assertIn("visible", rendered)
        self.assertNotIn("live-secret", rendered)
        self.assertNotIn("cookie-value", rendered)
        self.assertNotIn("raw-token", rendered)
        self.assertEqual(redacted["custom_env"], "<redacted>")
        self.assertEqual(redacted["nested"]["session_cookie"], "<redacted>")

    def test_redacts_sensitive_text_patterns(self) -> None:
        audit = load_audit_module()
        message = "\n".join(
            [
                "token=abc123",
                "Token: def456",
                "session cookie-value",
                "credential: ghp_secret",
            ]
        )

        redacted = audit.redact_sensitive_text(message)

        self.assertNotIn("abc123", redacted)
        self.assertNotIn("def456", redacted)
        self.assertNotIn("cookie-value", redacted)
        self.assertNotIn("ghp_secret", redacted)
        self.assertEqual(redacted.count("<redacted>"), 4)

    def test_live_unavailable_is_reported_without_failing_audit(self) -> None:
        audit = load_audit_module()

        def unavailable_runner(command, timeout_seconds):
            return None, "not authenticated with token raw-secret"

        live = audit.fetch_live_state(SCRIPT_PATH.parents[1], 1, runner=unavailable_runner)
        items = audit.build_audit(SCRIPT_PATH.parents[1], live)
        rendered = audit.render_text(items, live_enabled=True)

        self.assertIn("[unavailable] live-access: Multica CLI", rendered)
        self.assertIn("not authenticated", rendered)
        self.assertNotIn("raw-secret", rendered)

    def test_repo_only_cli_runs_end_to_end(self) -> None:
        completed = subprocess.run(
            ["python3", str(SCRIPT_PATH), "--repo-only", "--format", "json"],
            check=True,
            capture_output=True,
            text=True,
            cwd=SCRIPT_PATH.parents[1],
        )

        payload = json.loads(completed.stdout)

        self.assertEqual(payload["mode"], "repo-only")
        self.assertTrue(payload["items"])
        self.assertTrue(any(item["category"] == "repo-marker" for item in payload["items"]))

    def test_compare_agents_reports_current_and_stale_fields(self) -> None:
        audit = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt = root / "multica/agent-system-prompts/codex-fullstack.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text("expected prompt\n", encoding="utf-8")
            repo_agents = [
                {
                    "name": "OpenAI-fullstack",
                    "visibility": "workspace",
                    "concurrency_limit": "1",
                    "skills": ["tdd-vertical-slice"],
                    "system_prompt_file": "multica/agent-system-prompts/codex-fullstack.md",
                }
            ]

            current_live = audit.LiveState(
                agents=[
                    {
                        "name": "OpenAI-fullstack",
                        "visibility": "workspace",
                        "max_concurrent_tasks": 1,
                        "instructions": "expected prompt",
                        "skills": [{"name": "tdd-vertical-slice"}],
                    }
                ]
            )
            stale_live = audit.LiveState(
                agents=[
                    {
                        "name": "OpenAI-fullstack",
                        "visibility": "private",
                        "max_concurrent_tasks": 2,
                        "instructions": "old prompt",
                        "skills": [],
                    }
                ]
            )

            current_items = audit.compare_agents(root, repo_agents, current_live)
            stale_items = audit.compare_agents(root, repo_agents, stale_live)

        self.assertEqual(current_items[0].status, "current")
        self.assertEqual(stale_items[0].status, "stale")
        self.assertIn("system prompt differs from repo prompt file", stale_items[0].differences)
        self.assertIn("visibility differs", stale_items[0].differences)
        self.assertIn("concurrency limit differs", stale_items[0].differences)
        self.assertIn("skill bindings differ", stale_items[0].differences)

    def test_dynamic_live_fetch_commands_are_read_only(self) -> None:
        audit = load_audit_module()
        commands = []

        def runner(command, timeout_seconds):
            commands.append(tuple(command))
            if command[:3] == ("multica", "agent", "list"):
                return [{"id": "agent-1", "name": "OpenAI-scoper"}], None
            if command[:3] == ("multica", "skill", "list"):
                return [{"id": "skill-1", "name": "context-pack"}], None
            if command[:3] == ("multica", "skill", "get"):
                return {"name": "context-pack", "content": ""}, None
            if command[:3] == ("multica", "squad", "list"):
                return [{"id": "squad-1", "name": "AppDev Squad"}], None
            if command[:3] == ("multica", "squad", "get"):
                return {"name": "AppDev Squad"}, None
            if command[:3] == ("multica", "autopilot", "list"):
                return {"autopilots": [{"id": "auto-1", "name": "Daily standup summary"}]}, None
            if command[:3] == ("multica", "autopilot", "get"):
                return {"name": "Daily standup summary"}, None
            return None, "unexpected command"

        audit.fetch_live_state(SCRIPT_PATH.parents[1], 1, runner=runner)

        self.assertIn(("multica", "skill", "get", "skill-1", "--output", "json"), commands)
        self.assertIn(("multica", "squad", "get", "squad-1", "--output", "json"), commands)
        self.assertIn(("multica", "autopilot", "get", "auto-1", "--output", "json"), commands)
        for command in commands:
            audit.assert_read_only_multica_command(command)

    def test_autopilot_list_fallback_reports_detail_unknown(self) -> None:
        audit = load_audit_module()
        repo_autopilots = [
            {
                "name": "Daily standup summary",
                "mode": "create_issue",
                "trigger": "cron",
                "schedule": "0 0 * * 1-5",
                "assignee": "OpenAI-scoper",
                "issue_title": "Daily engineering standup {{date}}",
                "prompt": "Summarize work.",
            }
        ]
        live = audit.LiveState(
            agents=[{"id": "agent-1", "name": "OpenAI-scoper"}],
            autopilots=[
                {
                    "name": "Daily standup summary",
                    "mode": "create_issue",
                    "trigger": "cron",
                    "schedule": "0 0 * * 1-5",
                    "assignee": "agent-1",
                    "issue_title": "Daily engineering standup {{date}}",
                }
            ],
            autopilot_details={},
        )

        items = audit.compare_autopilots(repo_autopilots, live)

        self.assertEqual(items[0].status, "unknown")
        self.assertIn("detailed autopilot data unavailable; prompt comparison skipped", items[0].differences)
        self.assertIn("prompt unavailable from live output", items[0].differences)

    def test_command_guard_rejects_multica_write_words(self) -> None:
        audit = load_audit_module()

        with self.assertRaises(ValueError):
            audit.assert_read_only_multica_command(("multica", "agent", "update", "agent-1"))
        with self.assertRaises(ValueError):
            audit.assert_read_only_multica_command(("multica", "skill", "import", "https://example.test/skill"))

    def test_resolve_multica_binary_accepts_trusted_absolute_path(self) -> None:
        audit = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            trusted = Path(tmp) / "trusted-bin"
            root.mkdir()
            trusted.mkdir()
            binary = trusted / "multica"
            binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            binary.chmod(0o755)

            resolved, error = audit.resolve_multica_binary(str(binary), cwd=root, trusted_dirs=(trusted,))

        self.assertIsNone(error)
        self.assertEqual(resolved, str(binary.resolve()))

    def test_resolve_multica_binary_accepts_homebrew_cellar_symlink_target(self) -> None:
        audit = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            homebrew_bin = Path(tmp) / "opt/homebrew/bin"
            cellar_bin = Path(tmp) / "opt/homebrew/Cellar/multica/0.2.32/bin"
            root.mkdir()
            homebrew_bin.mkdir(parents=True)
            cellar_bin.mkdir(parents=True)
            binary = cellar_bin / "multica"
            binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            binary.chmod(0o755)
            symlink = homebrew_bin / "multica"
            symlink.symlink_to(binary)

            resolved, error = audit.resolve_multica_binary(
                str(symlink),
                cwd=root,
                trusted_dirs=(homebrew_bin, cellar_bin.parents[1]),
            )

        self.assertIsNone(error)
        self.assertEqual(resolved, str(binary.resolve()))

    def test_resolve_multica_binary_rejects_repo_local_path(self) -> None:
        audit = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            binary = root / "multica"
            binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            binary.chmod(0o755)

            resolved, error = audit.resolve_multica_binary(str(binary), cwd=root, trusted_dirs=(root,))

        self.assertIsNone(resolved)
        self.assertIn("repo-local", error)

    def test_squad_template_parser_handles_multiple_squads(self) -> None:
        audit = load_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "multica/squads.yaml"
            path.parent.mkdir(parents=True)
            path.write_text(
                """
squads:
  - name: First Squad
    leader: OpenAI-scoper
    instructions: |
      Route first.
    members:
      - name: OpenAI-scoper
        role: Leader.
  - name: Second Squad
    leader: OpenAI-test
    instructions: |
      Route second.
    members:
      - name: OpenAI-test
        role: Test owner.
""",
                encoding="utf-8",
            )

            squads = audit.parse_squads_template(root)

        self.assertEqual([squad["name"] for squad in squads], ["First Squad", "Second Squad"])
        self.assertEqual(squads[1]["members"][0]["name"], "OpenAI-test")


if __name__ == "__main__":
    unittest.main()
