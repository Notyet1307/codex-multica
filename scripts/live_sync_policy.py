#!/usr/bin/env python3
"""Safety policy for human-confirmed Multica live configuration sync."""

from __future__ import annotations

import re
from typing import Any, Sequence


MAX_INLINE_WRITE_VALUE_BYTES = 128 * 1024
SYNCABLE_FIELDS = (("agent", "instructions"), ("skill", "content"))
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


def apply_confirmation(workspace_id: str, source_commit_sha: str) -> str:
    return f"APPLY {workspace_id} {source_commit_sha}"


def safety_metadata() -> dict[str, object]:
    return {
        "plan_is_read_only": True,
        "apply_requires_exact_confirmation": True,
        "apply_rechecks_old_live_hash": True,
        "syncable_fields": [f"{object_type}.{field}" for object_type, field in SYNCABLE_FIELDS],
        "out_of_scope": list(FIELDS_NOT_TOUCHED),
    }


def validate_confirmation(plan: dict[str, Any], confirm: str) -> str | None:
    expected_confirm = apply_confirmation(str(plan.get("workspace_id")), str(plan.get("source_commit_sha")))
    if confirm != expected_confirm:
        return "confirmation string does not match the plan"
    return None


def validate_plan_entry(entry: dict[str, Any]) -> str | None:
    object_type = str(entry.get("live_object_type"))
    field = str(entry.get("field"))
    if (object_type, field) in SYNCABLE_FIELDS:
        return None
    return f"plan contains out-of-scope update: {object_type}.{field}"


def is_allowlisted_write_command(command: Sequence[str]) -> bool:
    if len(command) < 6:
        return False
    executable, resource, action, object_id = command[:4]
    if executable != "multica" or action != "update" or not object_id:
        return False
    if resource not in {"agent", "skill"}:
        return False

    flags: dict[str, str] = {}
    index = 4
    while index < len(command):
        flag = command[index]
        if index + 1 >= len(command):
            return False
        value = command[index + 1]
        if flag in flags:
            return False
        if flag in {"--instructions", "--content"}:
            if not value:
                return False
        elif flag == "--output":
            if value != "json":
                return False
        else:
            return False
        flags[flag] = value
        index += 2

    expected_content_flag = "--instructions" if resource == "agent" else "--content"
    return set(flags) == {expected_content_flag, "--output"}


def sync_write_value(command: Sequence[str]) -> str:
    for index, item in enumerate(command[:-1]):
        if item in {"--instructions", "--content"}:
            return str(command[index + 1])
    return ""


def validate_write_value(value: str) -> str | None:
    if not value:
        return "write value is empty"
    if len(value.encode("utf-8")) > MAX_INLINE_WRITE_VALUE_BYTES:
        return "write value is too large for inline CLI argument; wait for file/stdin support"
    if WRITE_VALUE_SENSITIVE_ASSIGNMENT_PATTERN.search(value) or WRITE_VALUE_SENSITIVE_PROSE_PATTERN.search(value):
        return "write value appears to contain secret-like text"
    return None


def validate_write_transport(command: Sequence[str]) -> str | None:
    if any(flag in command for flag in ("--instructions", "--content")):
        return (
            "inline prompt/skill writes are disabled until the Multica CLI supports "
            "file or stdin transport for instructions and skill content"
        )
    return None
