#!/usr/bin/env python3
"""Human-confirmed Multica live prompt and skill sync helper."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts/audit-multica-live-config.py"
MAX_INLINE_WRITE_VALUE_BYTES = 128 * 1024
WRITE_VALUE_SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:export\s+)?[\"']?"
    r"(api[_-]?key|auth|cookie|credential|custom[_-]?env|password|secret|session|token)"
    r"[\"']?\s*[:=]\s*[\"']?[^\s\"',;}]+",
    re.IGNORECASE | re.MULTILINE,
)
# Apply writes need a narrower check than the audit redaction pattern because
# skill prose contains words like "terminal session". Keep prose detection for
# high-signal secret terms, but require assignment syntax for "session".
WRITE_VALUE_SENSITIVE_PROSE_PATTERN = re.compile(
    r"\b(api[_-]?key|auth|cookie|credential|custom[_-]?env|password|secret|token)"
    r"\b\s+(is|are|was|were|equals?)\s+[^\s\"',;}]+",
    re.IGNORECASE | re.MULTILINE,
)
FIELDS_NOT_TOUCHED = (
    "custom_env",
    "secrets",
    "tokens",
    "credentials",
    "cookies",
    "api_keys",
    "runtime_config",
    "model",
    "visibility",
    "concurrency",
    "status",
    "agent_name",
    "skill_name",
    "squads",
    "autopilots",
)


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_multica_live_config", AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit = load_audit_module()


def sha256_text(value: str) -> str:
    return hashlib.sha256(audit.normalize_text(value).encode("utf-8")).hexdigest()


def run_capture(command: Sequence[str], cwd: Path = ROOT) -> str:
    completed = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def source_repository(root: Path) -> str:
    try:
        return run_capture(("git", "remote", "get-url", "origin"), root)
    except subprocess.CalledProcessError:
        return "unavailable"


def source_commit_sha(root: Path) -> str:
    try:
        return run_capture(("git", "rev-parse", "HEAD"), root)
    except subprocess.CalledProcessError:
        return "unavailable"


def worktree_is_clean(root: Path) -> bool:
    unstaged = subprocess.run(("git", "diff", "--quiet"), cwd=root)
    staged = subprocess.run(("git", "diff", "--cached", "--quiet"), cwd=root)
    return unstaged.returncode == 0 and staged.returncode == 0


def workspace_id(timeout_seconds: int) -> str:
    data, error = run_json_command(("multica", "workspace", "get", "--output", "json"), timeout_seconds)
    if error or not isinstance(data, dict):
        return "unavailable"
    return str(data.get("id") or "unavailable")


def run_json_command(command: Sequence[str], timeout_seconds: int) -> tuple[Any | None, str | None]:
    if tuple(command) != ("multica", "workspace", "get", "--output", "json"):
        audit.assert_read_only_multica_command(command)
    binary, binary_error = audit.resolve_multica_binary(command[0])
    if binary_error:
        return None, binary_error
    try:
        completed = subprocess.run(
            (binary, *command[1:]),
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return None, f"{' '.join(command[:3])} timed out"
    except subprocess.CalledProcessError as error:
        message = audit.normalize_text(error.stderr or error.stdout).splitlines()
        return None, message[0] if message else f"{' '.join(command[:3])} failed"
    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError:
        return None, f"{' '.join(command[:3])} did not return JSON"


def redacted_diff_summary(old_text: str, new_text: str) -> dict[str, Any]:
    old_lines = audit.normalize_text(old_text).splitlines()
    new_lines = audit.normalize_text(new_text).splitlines()
    marker_changes: list[str] = []
    for marker_name, variants in audit.MARKER_GROUPS.items():
        old_has = any(variant in audit.normalize_text(old_text) for variant in variants)
        new_has = any(variant in audit.normalize_text(new_text) for variant in variants)
        if old_has != new_has:
            marker_changes.append(f"{marker_name}: {'added' if new_has else 'removed'}")
    return {
        "old_line_count": len(old_lines),
        "new_line_count": len(new_lines),
        "line_count_delta": len(new_lines) - len(old_lines),
        "content_changed": audit.normalize_text(old_text) != audit.normalize_text(new_text),
        "marker_changes": marker_changes,
        "redaction": "full text omitted; hashes identify exact old/new values",
    }


def plan_entry(
    *,
    workspace_id: str,
    source_repository: str,
    source_commit_sha: str,
    repo_file_path: str,
    live_object_type: str,
    live_object_name: str,
    live_object_id: str,
    field: str,
    old_live_value: str,
    new_repo_value: str,
    command_class: str,
) -> dict[str, Any]:
    return {
        "workspace_id": workspace_id,
        "source_repository": source_repository,
        "source_commit_sha": source_commit_sha,
        "repo_file_path": repo_file_path,
        "live_object_type": live_object_type,
        "live_object_name": live_object_name,
        "live_object_id": live_object_id,
        "field": field,
        "old_live_hash": sha256_text(old_live_value),
        "new_repo_hash": sha256_text(new_repo_value),
        "redacted_diff_summary": redacted_diff_summary(old_live_value, new_repo_value),
        "command_class": command_class,
        "rollback_note": "Re-run plan from a reviewed commit containing the desired previous value, then apply with human confirmation.",
        "fields_explicitly_not_touched": list(FIELDS_NOT_TOUCHED),
    }


def build_sync_plan(
    *,
    root: Path,
    live: Any,
    workspace_id: str,
    source_repository: str,
    source_commit_sha: str,
) -> dict[str, Any]:
    templates = audit.load_repo_templates(root)
    entries: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    out_of_scope_drift: list[dict[str, str]] = []

    live_agents = {str(agent.get("name")): agent for agent in live.agents if agent.get("name")}
    for repo_agent in templates["agents"]:
        name = str(repo_agent.get("name"))
        live_agent = live_agents.get(name)
        if live_agent is None:
            skipped.append({"type": "agent", "name": name, "reason": "missing live agent; create is out of scope"})
            continue
        repo_concurrency = str(repo_agent.get("concurrency_limit", ""))
        live_concurrency = str(live_agent.get("max_concurrent_tasks", ""))
        if repo_concurrency and live_concurrency and repo_concurrency != live_concurrency:
            out_of_scope_drift.append(
                {
                    "type": "agent",
                    "name": name,
                    "field": "concurrency",
                    "repo_value": repo_concurrency,
                    "live_value": live_concurrency,
                    "action_required": "manual operator decision required; sync helper does not write concurrency",
                }
            )
        prompt_path = root / str(repo_agent.get("system_prompt_file", ""))
        repo_prompt = audit.read_text_if_present(prompt_path)
        live_prompt = str(live_agent.get("instructions", ""))
        if audit.normalize_text(repo_prompt) == audit.normalize_text(live_prompt):
            continue
        live_id = str(live_agent.get("id", ""))
        if not live_id:
            skipped.append({"type": "agent", "name": name, "reason": "live agent id unavailable"})
            continue
        entries.append(
            plan_entry(
                workspace_id=workspace_id,
                source_repository=source_repository,
                source_commit_sha=source_commit_sha,
                repo_file_path=prompt_path.relative_to(root).as_posix(),
                live_object_type="agent",
                live_object_name=name,
                live_object_id=live_id,
                field="instructions",
                old_live_value=live_prompt,
                new_repo_value=repo_prompt,
                command_class="multica agent update --instructions",
            )
        )

    live_skills = {str(skill.get("name")): skill for skill in live.skills if skill.get("name")}
    for name, repo_skill in sorted(templates["skills"].items()):
        live_skill = live_skills.get(name)
        if live_skill is None:
            skipped.append({"type": "skill", "name": name, "reason": "missing live skill; create/import is out of scope"})
            continue
        detail = live.skill_details.get(name)
        if detail is None:
            skipped.append({"type": "skill", "name": name, "reason": "live skill content unavailable"})
            continue
        repo_content = repo_skill["content"]
        live_content = str(detail.get("content", ""))
        if audit.normalize_text(repo_content) == audit.normalize_text(live_content):
            continue
        live_id = str(live_skill.get("id") or detail.get("id") or "")
        if not live_id:
            skipped.append({"type": "skill", "name": name, "reason": "live skill id unavailable"})
            continue
        entries.append(
            plan_entry(
                workspace_id=workspace_id,
                source_repository=source_repository,
                source_commit_sha=source_commit_sha,
                repo_file_path=repo_skill["path"],
                live_object_type="skill",
                live_object_name=name,
                live_object_id=live_id,
                field="content",
                old_live_value=live_content,
                new_repo_value=repo_content,
                command_class="multica skill update --content",
            )
        )

    return {
        "version": 1,
        "mode": "plan",
        "workspace_id": workspace_id,
        "source_repository": source_repository,
        "source_commit_sha": source_commit_sha,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "entries": entries,
        "skipped": skipped,
        "out_of_scope_drift": out_of_scope_drift,
        "apply_confirmation": f"APPLY {workspace_id} {source_commit_sha}",
        "safety": {
            "plan_is_read_only": True,
            "apply_requires_exact_confirmation": True,
            "apply_rechecks_old_live_hash": True,
            "syncable_fields": ["agent.instructions", "skill.content"],
            "out_of_scope": list(FIELDS_NOT_TOUCHED),
        },
    }


def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plan_for_apply(plan: dict[str, Any], root: Path, confirm: str, current_workspace_id: str) -> None:
    expected_confirm = f"APPLY {plan.get('workspace_id')} {plan.get('source_commit_sha')}"
    if confirm != expected_confirm:
        raise ValueError("confirmation string does not match the plan")
    if current_workspace_id != plan.get("workspace_id"):
        raise ValueError("current workspace id does not match the plan")
    if source_commit_sha(root) != plan.get("source_commit_sha"):
        raise ValueError("current source commit does not match the plan")
    for entry in plan.get("entries", []):
        if entry.get("live_object_type") == "agent" and entry.get("field") == "instructions":
            continue
        if entry.get("live_object_type") == "skill" and entry.get("field") == "content":
            continue
        raise ValueError(f"plan contains out-of-scope update: {entry!r}")


def repo_value_for_entry(root: Path, entry: dict[str, Any]) -> str:
    path = root / str(entry["repo_file_path"])
    return audit.read_text_if_present(path)


def live_value_for_entry(live: Any, entry: dict[str, Any]) -> str:
    if entry["live_object_type"] == "agent":
        for agent in live.agents:
            if str(agent.get("id")) == str(entry["live_object_id"]):
                return str(agent.get("instructions", ""))
    if entry["live_object_type"] == "skill":
        for detail in live.skill_details.values():
            if str(detail.get("id")) == str(entry["live_object_id"]):
                return str(detail.get("content", ""))
    raise ValueError(f"live object not found for {entry['live_object_type']} {entry['live_object_name']}")


def apply_plan(
    *,
    root: Path,
    plan: dict[str, Any],
    confirm: str,
    timeout_seconds: int,
    command_runner: Callable[[Sequence[str], int], tuple[Any | None, str | None]] | None = None,
) -> dict[str, Any]:
    current_workspace_id = workspace_id(timeout_seconds)
    validate_plan_for_apply(plan, root, confirm, current_workspace_id)
    live = audit.fetch_live_state(root, timeout_seconds)

    for entry in plan.get("entries", []):
        old_live_value = live_value_for_entry(live, entry)
        if sha256_text(old_live_value) != entry["old_live_hash"]:
            raise ValueError(f"live object changed since plan was generated: {entry['live_object_name']}")
        new_repo_value = repo_value_for_entry(root, entry)
        if sha256_text(new_repo_value) != entry["new_repo_hash"]:
            raise ValueError(f"repo file changed since plan was generated: {entry['repo_file_path']}")

    runner = command_runner or run_multica_write_command
    updated: list[dict[str, str]] = []
    for entry in plan.get("entries", []):
        new_repo_value = repo_value_for_entry(root, entry)
        if entry["live_object_type"] == "agent":
            command = ("multica", "agent", "update", entry["live_object_id"], "--instructions", new_repo_value, "--output", "json")
        else:
            command = ("multica", "skill", "update", entry["live_object_id"], "--content", new_repo_value, "--output", "json")
        _, error = runner(command, timeout_seconds)
        if error:
            raise ValueError(error)
        updated.append(
            {
                "live_object_type": entry["live_object_type"],
                "live_object_name": entry["live_object_name"],
                "field": entry["field"],
                "old_live_hash": entry["old_live_hash"],
                "new_repo_hash": entry["new_repo_hash"],
            }
        )

    return {
        "workspace_id": plan["workspace_id"],
        "source_commit_sha": plan["source_commit_sha"],
        "operator": "local multica CLI user",
        "applied_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "objects_updated": updated,
        "fields_explicitly_not_touched": list(FIELDS_NOT_TOUCHED),
        "rollback_note": "Prefer rolling forward with a reviewed repository commit and a new confirmed plan.",
    }


def is_allowlisted_write_command(command: Sequence[str]) -> bool:
    if len(command) < 6:
        return False
    executable, resource, action, object_id = command[:4]
    if executable != "multica" or resource not in {"agent", "skill"} or action != "update" or not object_id:
        return False

    field_flags: list[str] = []
    output_format = None
    index = 4
    while index < len(command):
        flag = command[index]
        if index + 1 >= len(command):
            return False
        value = command[index + 1]
        if flag in {"--instructions", "--content"}:
            if not value:
                return False
            field_flags.append(flag)
        elif flag == "--output":
            output_format = value
        else:
            return False
        index += 2

    return output_format == "json" and field_flags == [
        "--instructions" if resource == "agent" else "--content"
    ]


def sync_write_value(command: Sequence[str]) -> str:
    for index, item in enumerate(command[:-1]):
        if item in {"--instructions", "--content"}:
            return str(command[index + 1])
    return ""


def validate_write_value(value: str) -> str | None:
    encoded = value.encode("utf-8")
    if len(encoded) > MAX_INLINE_WRITE_VALUE_BYTES:
        return "write value is too large for inline CLI argument; wait for file/stdin support"
    if WRITE_VALUE_SENSITIVE_ASSIGNMENT_PATTERN.search(value) or WRITE_VALUE_SENSITIVE_PROSE_PATTERN.search(value):
        return "write value appears to contain secret-like text"
    return None


def run_multica_write_command(command: Sequence[str], timeout_seconds: int) -> tuple[Any | None, str | None]:
    if not is_allowlisted_write_command(command):
        return None, "write command is not in the sync allowlist"
    value_error = validate_write_value(sync_write_value(command))
    if value_error:
        return None, value_error
    binary, binary_error = audit.resolve_multica_binary(command[0])
    if binary_error:
        return None, binary_error
    try:
        completed = subprocess.run(
            (binary, *command[1:]),
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return None, f"{' '.join(command[:3])} timed out"
    except subprocess.CalledProcessError as error:
        message = audit.normalize_text(error.stderr or error.stdout).splitlines()
        return None, audit.redact_sensitive_text(message[0] if message else f"{' '.join(command[:3])} failed")
    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError:
        return {}, None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Human-confirmed Multica live prompt and skill sync helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Generate a read-only sync plan.")
    plan_parser.add_argument("--output", required=True, help="Path to write the JSON sync plan.")
    plan_parser.add_argument("--timeout-seconds", type=int, default=20)

    apply_parser = subparsers.add_parser("apply", help="Apply a reviewed sync plan with exact human confirmation.")
    apply_parser.add_argument("--plan", required=True, help="Path to the JSON sync plan.")
    apply_parser.add_argument("--confirm", required=True, help='Exact string: "APPLY <workspace-id> <source-commit-sha>".')
    apply_parser.add_argument("--timeout-seconds", type=int, default=20)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    try:
        if args.command == "plan":
            if not worktree_is_clean(root):
                raise ValueError("worktree is not clean; commit or stash changes before generating a sync plan")
            live = audit.fetch_live_state(root, args.timeout_seconds)
            current_workspace_id = workspace_id(args.timeout_seconds)
            if current_workspace_id == "unavailable":
                raise ValueError("workspace id unavailable; run `multica workspace get --output json` and authenticate first")
            plan = build_sync_plan(
                root=root,
                live=live,
                workspace_id=current_workspace_id,
                source_repository=source_repository(root),
                source_commit_sha=source_commit_sha(root),
            )
            output = Path(args.output)
            output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(
                f"Wrote sync plan with {len(plan['entries'])} update entries "
                f"and {len(plan['out_of_scope_drift'])} out-of-scope drift warnings to {output}"
            )
            for warning in plan["out_of_scope_drift"]:
                print(
                    "WARNING: "
                    f"{warning['type']} {warning['name']} {warning['field']} "
                    f"repo={warning['repo_value']} live={warning['live_value']} - {warning['action_required']}"
                )
            return 0
        if args.command == "apply":
            if os.environ.get("MULTICA_SYNC_ALLOWED") != "true":
                print(
                    "ERROR: apply is a live operator action. Set MULTICA_SYNC_ALLOWED=true only after human plan review.",
                    file=sys.stderr,
                )
                return 2
            evidence = apply_plan(
                root=root,
                plan=load_plan(Path(args.plan)),
                confirm=args.confirm,
                timeout_seconds=args.timeout_seconds,
            )
            print(json.dumps(evidence, indent=2, sort_keys=True))
            return 0
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
