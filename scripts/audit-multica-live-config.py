#!/usr/bin/env python3
"""Read-only Multica live configuration drift audit helper."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence


STATUS_CURRENT = "current"
STATUS_STALE = "stale"
STATUS_MISSING = "missing"
STATUS_EXTRA = "extra"
STATUS_UNAVAILABLE = "unavailable"
STATUS_UNKNOWN = "unknown"

READ_ONLY_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("multica", "agent", "list", "--output", "json"),
    ("multica", "skill", "list", "--output", "json"),
    ("multica", "skill", "get", "<id>", "--output", "json"),
    ("multica", "squad", "list", "--output", "json"),
    ("multica", "squad", "get", "<id>", "--output", "json"),
    ("multica", "autopilot", "list", "--output", "json"),
    ("multica", "autopilot", "get", "<id>", "--output", "json"),
)

ALLOWED_MULTICA_ACTIONS = {"list", "get"}
FORBIDDEN_MULTICA_WORDS = {
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
TRUSTED_MULTICA_BINARY_DIRS = (
    Path("/Applications/Multica.app/Contents/Resources/app.asar.unpacked/resources/bin"),
    Path("/opt/homebrew/bin"),
    Path("/opt/homebrew/Cellar/multica"),
    Path("/usr/local/bin"),
    Path("/usr/local/Cellar/multica"),
    Path("/usr/bin"),
    Path("/bin"),
    Path.home() / ".local/bin",
    Path.home() / ".multica/bin",
)
SENSITIVE_KEY_PATTERN = re.compile(
    r"(api[_-]?key|auth|cookie|credential|custom[_-]?env|password|secret|session|token)",
    re.IGNORECASE,
)
SENSITIVE_TEXT_PATTERN = re.compile(
    r"\b(api[_-]?key|cookie|credential|custom[_-]?env|password|secret|session|token)(\s*[=:]\s*|\s+)([^\s,;]+)",
    re.IGNORECASE,
)

MARKER_GROUPS: dict[str, tuple[str, ...]] = {
    "Handoff Back evidence wording": (
        "Handoff Back is the detailed evidence report",
        "Handoff Back as the detailed evidence report",
        "Handoff Back carries detailed implementation evidence",
    ),
    "Context pack resume wording": (
        "Context pack is the compact resume state",
        "compact durable resume state",
        "compact resume state",
    ),
    "Context pack heading": ("## Context pack",),
    "Context pack compact index wording": (
        "compact index to the Handoff Back and PR",
        "reference Handoff Back and the PR",
    ),
    "Changed-file evidence command": ("git diff --name-only origin/main...HEAD",),
}

LIVE_MARKER_OBJECTS = {
    "agents": {"OpenAI-scoper", "OpenAI-fullstack"},
    "skills": {"spec-first-intake", "context-pack", "verification-before-completion"},
}


@dataclass
class AuditItem:
    category: str
    name: str
    status: str
    detail: str
    differences: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        data = {
            "category": self.category,
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
        }
        if self.differences:
            data["differences"] = self.differences
        return data


@dataclass
class LiveState:
    agents: list[dict[str, Any]] = field(default_factory=list)
    skills: list[dict[str, Any]] = field(default_factory=list)
    skill_details: dict[str, dict[str, Any]] = field(default_factory=dict)
    squads: list[dict[str, Any]] = field(default_factory=list)
    squad_details: dict[str, dict[str, Any]] = field(default_factory=dict)
    autopilots: list[dict[str, Any]] = field(default_factory=list)
    autopilot_details: dict[str, dict[str, Any]] = field(default_factory=dict)
    unavailable: list[str] = field(default_factory=list)


def build_live_command_plan() -> list[tuple[str, ...]]:
    """Return the static live-read command plan used before object-specific gets."""
    return list(READ_ONLY_COMMANDS)


def assert_read_only_multica_command(command: Sequence[str]) -> None:
    parts = tuple(command)
    if len(parts) < 3 or parts[0] != "multica":
        raise ValueError(f"not a multica command: {parts!r}")
    if parts[2] not in ALLOWED_MULTICA_ACTIONS:
        raise ValueError(f"multica command is not read-only: {parts!r}")
    forbidden = FORBIDDEN_MULTICA_WORDS.intersection(parts)
    if forbidden:
        raise ValueError(f"multica command contains forbidden words: {sorted(forbidden)}")


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def has_world_writable_component(path: Path, stop_dir: Path) -> bool:
    current = path
    while True:
        try:
            mode = current.stat().st_mode
        except OSError:
            return True
        if mode & stat.S_IWOTH:
            return True
        if current == stop_dir or current.parent == current:
            return False
        current = current.parent


def resolve_multica_binary(
    binary: str = "multica",
    cwd: Path | None = None,
    trusted_dirs: Iterable[Path] = TRUSTED_MULTICA_BINARY_DIRS,
) -> tuple[str | None, str | None]:
    binary_path = Path(binary)
    resolved = str(binary_path) if binary_path.is_absolute() else shutil.which(binary)
    if resolved is None:
        return None, "multica CLI is not available on PATH"

    candidate = Path(resolved).resolve()
    cwd = (cwd or Path.cwd()).resolve()
    if candidate.name != "multica":
        return None, f"resolved CLI is not named multica: {candidate}"
    if path_is_relative_to(candidate, cwd):
        return None, f"refusing to execute repo-local multica binary: {candidate}"
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        return None, f"resolved multica binary is not executable: {candidate}"

    trusted = tuple(path.resolve() for path in trusted_dirs)
    trusted_parent = next((directory for directory in trusted if path_is_relative_to(candidate, directory)), None)
    if trusted_parent is None:
        trusted_labels = ", ".join(str(directory) for directory in trusted)
        return None, f"resolved multica binary is outside trusted directories: {candidate}; trusted: {trusted_labels}"
    if has_world_writable_component(candidate, trusted_parent):
        return None, f"resolved multica binary path has a world-writable component: {candidate}"
    # This is a local operator safety guard, not an anti-malware boundary against
    # users who can modify trusted installation directories between validation
    # and execution.
    return str(candidate), None


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            if SENSITIVE_KEY_PATTERN.search(str(key)):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact_sensitive(child)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value


def redact_sensitive_text(value: str) -> str:
    return SENSITIVE_TEXT_PATTERN.sub(lambda match: f"{match.group(1)}{match.group(2)}<redacted>", value)


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    result: list[str] = []
    for char in value:
        if escaped:
            result.append(char)
            escaped = False
            continue
        if char == "\\":
            result.append(char)
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            break
        result.append(char)
    return "".join(result).strip()


def clean_scalar(value: str) -> str:
    value = strip_inline_comment(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def read_text_if_present(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def parse_frontmatter_name(path: Path) -> str:
    text = read_text_if_present(path)
    if not text.startswith("---\n"):
        return path.parent.name
    for line in text.splitlines()[1:]:
        if line == "---":
            break
        key, separator, value = line.partition(":")
        if separator and key.strip() == "name":
            return clean_scalar(value)
    return path.parent.name


def parse_agents_template(root: Path) -> list[dict[str, Any]]:
    path = root / "multica/agents.yaml"
    agents: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_skills = False

    for raw_line in read_text_if_present(path).splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = re.match(r"^\s*-\s+name:\s*(.+)$", line)
        if match:
            current = {"name": clean_scalar(match.group(1)), "skills": []}
            agents.append(current)
            in_skills = False
            continue
        if current is None:
            continue
        if re.match(r"^\s*skills:\s*$", line):
            in_skills = True
            continue
        list_match = re.match(r"^\s*-\s*(.+)$", line)
        if in_skills and list_match:
            current.setdefault("skills", []).append(clean_scalar(list_match.group(1)))
            continue
        key_match = re.match(r"^\s*([A-Za-z_][\w_-]*):\s*(.+)$", line)
        if key_match:
            key, value = key_match.groups()
            current[key] = clean_scalar(value)
            in_skills = False

    return agents


def parse_block(lines: list[str], start_index: int, base_indent: int) -> tuple[str, int]:
    block: list[str] = []
    index = start_index
    while index < len(lines):
        raw = lines[index]
        if raw.strip() and (len(raw) - len(raw.lstrip(" "))) <= base_indent:
            break
        block.append(raw[base_indent + 2 :] if len(raw) >= base_indent + 2 else "")
        index += 1
    return "\n".join(block).rstrip(), index - 1


def parse_squads_template(root: Path) -> list[dict[str, Any]]:
    path = root / "multica/squads.yaml"
    lines = read_text_if_present(path).splitlines()
    squads: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_member: dict[str, str] | None = None
    in_members = False
    index = 0

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        match = re.match(r"^\s*-\s+name:\s*(.+)$", line)
        if match and indent == 2:
            current = {"name": clean_scalar(match.group(1)), "members": []}
            squads.append(current)
            in_members = False
            current_member = None
            index += 1
            continue
        if current is None:
            index += 1
            continue
        if re.match(r"^\s*members:\s*$", line):
            in_members = True
            index += 1
            continue
        member_match = re.match(r"^\s*-\s+name:\s*(.+)$", line)
        if in_members and member_match and indent > 2:
            current_member = {"name": clean_scalar(member_match.group(1))}
            current.setdefault("members", []).append(current_member)
            index += 1
            continue
        role_match = re.match(r"^\s*role:\s*(.+)$", line)
        if in_members and current_member is not None and role_match:
            current_member["role"] = clean_scalar(role_match.group(1))
            index += 1
            continue
        block_match = re.match(r"^(\s*)(instructions):\s*\|\s*$", line)
        if block_match:
            block, index = parse_block(lines, index + 1, len(block_match.group(1)))
            current["instructions"] = block
            index += 1
            continue
        key_match = re.match(r"^\s*([A-Za-z_][\w_-]*):\s*(.+)$", line)
        if key_match and not in_members:
            key, value = key_match.groups()
            current[key] = clean_scalar(value)
        index += 1

    return squads


def parse_autopilots_template(root: Path) -> list[dict[str, Any]]:
    path = root / "multica/autopilots.yaml"
    lines = read_text_if_present(path).splitlines()
    autopilots: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    index = 0

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        match = re.match(r"^\s*-\s+name:\s*(.+)$", line)
        if match:
            current = {"name": clean_scalar(match.group(1))}
            autopilots.append(current)
            index += 1
            continue
        if current is None:
            index += 1
            continue
        block_match = re.match(r"^(\s*)(prompt):\s*\|\s*$", line)
        if block_match:
            block, index = parse_block(lines, index + 1, len(block_match.group(1)))
            current["prompt"] = block
            index += 1
            continue
        key_match = re.match(r"^\s*([A-Za-z_][\w_-]*):\s*(.+)$", line)
        if key_match:
            key, value = key_match.groups()
            current[key] = clean_scalar(value)
        index += 1

    return autopilots


def load_repo_templates(root: Path) -> dict[str, Any]:
    skills: dict[str, dict[str, str]] = {}
    for skill_path in sorted((root / ".agents/skills").glob("*/SKILL.md")):
        name = parse_frontmatter_name(skill_path)
        skills[name] = {
            "name": name,
            "path": skill_path.relative_to(root).as_posix(),
            "content": read_text_if_present(skill_path),
        }
    return {
        "agents": parse_agents_template(root),
        "skills": skills,
        "squads": parse_squads_template(root),
        "autopilots": parse_autopilots_template(root),
    }


def run_json_command(command: tuple[str, ...], timeout_seconds: int) -> tuple[Any | None, str | None]:
    assert_read_only_multica_command(command)
    binary, binary_error = resolve_multica_binary(command[0])
    if binary_error:
        return None, binary_error
    execution_command = (binary, *command[1:])
    try:
        completed = subprocess.run(
            execution_command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return None, f"{' '.join(command[:3])} timed out"
    except subprocess.CalledProcessError as error:
        message = normalize_text(error.stderr or error.stdout).splitlines()
        return None, message[0] if message else f"{' '.join(command[:3])} failed"
    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError:
        return None, f"{' '.join(command[:3])} did not return JSON"


def extract_list(value: Any, key: str) -> list[dict[str, Any]]:
    value = redact_sensitive(value)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return [item for item in value[key] if isinstance(item, dict)]
    return []


def fetch_live_state(
    root: Path,
    timeout_seconds: int,
    runner: Callable[[tuple[str, ...], int], tuple[Any | None, str | None]] = run_json_command,
) -> LiveState:
    repo_templates = load_repo_templates(root)
    state = LiveState()

    data, error = runner(("multica", "agent", "list", "--output", "json"), timeout_seconds)
    if error:
        state.unavailable.append(f"agents: {redact_sensitive_text(error)}")
    else:
        state.agents = extract_list(data, "agents")

    data, error = runner(("multica", "skill", "list", "--output", "json"), timeout_seconds)
    if error:
        state.unavailable.append(f"skills: {redact_sensitive_text(error)}")
    else:
        state.skills = extract_list(data, "skills")
        repo_skill_names = set(repo_templates["skills"])
        for skill in state.skills:
            name = str(skill.get("name", ""))
            skill_id = str(skill.get("id", ""))
            if not name or name not in repo_skill_names or not skill_id:
                continue
            detail, detail_error = runner(("multica", "skill", "get", skill_id, "--output", "json"), timeout_seconds)
            if detail_error:
                state.unavailable.append(f"skill {name}: {redact_sensitive_text(detail_error)}")
            elif isinstance(detail, dict):
                state.skill_details[name] = redact_sensitive(detail)

    data, error = runner(("multica", "squad", "list", "--output", "json"), timeout_seconds)
    if error:
        state.unavailable.append(f"squads: {redact_sensitive_text(error)}")
    else:
        state.squads = extract_list(data, "squads")
        for squad in state.squads:
            name = str(squad.get("name", ""))
            squad_id = str(squad.get("id", ""))
            if not name or not squad_id:
                continue
            detail, detail_error = runner(("multica", "squad", "get", squad_id, "--output", "json"), timeout_seconds)
            if detail_error:
                state.unavailable.append(f"squad {name}: {redact_sensitive_text(detail_error)}")
            elif isinstance(detail, dict):
                state.squad_details[name] = redact_sensitive(detail)

    data, error = runner(("multica", "autopilot", "list", "--output", "json"), timeout_seconds)
    if error:
        state.unavailable.append(f"autopilots: {redact_sensitive_text(error)}")
    else:
        state.autopilots = extract_list(data, "autopilots")
        for autopilot in state.autopilots:
            name = str(autopilot.get("name", ""))
            autopilot_id = str(autopilot.get("id", ""))
            if not name or not autopilot_id:
                continue
            detail, detail_error = runner(("multica", "autopilot", "get", autopilot_id, "--output", "json"), timeout_seconds)
            if detail_error:
                state.unavailable.append(f"autopilot {name}: {redact_sensitive_text(detail_error)}")
            elif isinstance(detail, dict):
                state.autopilot_details[name] = redact_sensitive(detail)

    return state


def live_category_unavailable(live: LiveState, category: str) -> bool:
    return any(message.startswith(f"{category}:") for message in live.unavailable)


def names_by_id(live_agents: list[dict[str, Any]]) -> dict[str, str]:
    return {str(agent.get("id")): str(agent.get("name")) for agent in live_agents if agent.get("id") and agent.get("name")}


def live_agent_skill_names(agent: dict[str, Any]) -> set[str]:
    skills = agent.get("skills", [])
    names: set[str] = set()
    if isinstance(skills, list):
        for skill in skills:
            if isinstance(skill, dict) and skill.get("name"):
                names.add(str(skill["name"]))
            elif isinstance(skill, str):
                names.add(skill)
    return names


def compare_agents(root: Path, repo_agents: list[dict[str, Any]], live: LiveState | None) -> list[AuditItem]:
    items: list[AuditItem] = []
    if live is None:
        return [
            AuditItem("agent", str(agent.get("name")), STATUS_UNKNOWN, "repo template present; live comparison skipped")
            for agent in repo_agents
        ]
    if not live.agents and live_category_unavailable(live, "agents"):
        return [
            AuditItem("agent", str(agent.get("name")), STATUS_UNAVAILABLE, "live agent data unavailable")
            for agent in repo_agents
        ]

    live_by_name = {str(agent.get("name")): agent for agent in live.agents if agent.get("name")}
    repo_names = {str(agent.get("name")) for agent in repo_agents}
    for repo_agent in repo_agents:
        name = str(repo_agent.get("name"))
        live_agent = live_by_name.get(name)
        if live_agent is None:
            items.append(AuditItem("agent", name, STATUS_MISSING, "repo agent not found in live workspace"))
            continue
        differences: list[str] = []
        prompt_file = root / str(repo_agent.get("system_prompt_file", ""))
        repo_prompt = normalize_text(read_text_if_present(prompt_file))
        if repo_prompt and normalize_text(live_agent.get("instructions")) != repo_prompt:
            differences.append("system prompt differs from repo prompt file")
        if repo_agent.get("visibility") and str(live_agent.get("visibility")) != str(repo_agent.get("visibility")):
            differences.append("visibility differs")
        repo_concurrency = str(repo_agent.get("concurrency_limit", ""))
        live_concurrency = str(live_agent.get("max_concurrent_tasks", ""))
        if repo_concurrency and live_concurrency and repo_concurrency != live_concurrency:
            differences.append("concurrency limit differs")
        repo_skills = set(str(skill) for skill in repo_agent.get("skills", []))
        live_skills = live_agent_skill_names(live_agent)
        if repo_skills != live_skills:
            differences.append("skill bindings differ")
        status = STATUS_STALE if differences else STATUS_CURRENT
        detail = "live agent matches repo template" if not differences else "live agent differs from repo template"
        items.append(AuditItem("agent", name, status, detail, differences))

    for name in sorted(set(live_by_name) - repo_names):
        items.append(AuditItem("agent", name, STATUS_EXTRA, "live agent has no repo template entry"))
    return items


def compare_skills(repo_skills: dict[str, dict[str, str]], live: LiveState | None) -> list[AuditItem]:
    items: list[AuditItem] = []
    if live is None:
        return [
            AuditItem("skill", name, STATUS_UNKNOWN, "repo skill present; live comparison skipped")
            for name in sorted(repo_skills)
        ]
    if not live.skills and live_category_unavailable(live, "skills"):
        return [
            AuditItem("skill", name, STATUS_UNAVAILABLE, "live skill data unavailable")
            for name in sorted(repo_skills)
        ]

    live_by_name = {str(skill.get("name")): skill for skill in live.skills if skill.get("name")}
    for name, repo_skill in sorted(repo_skills.items()):
        if name not in live_by_name:
            items.append(AuditItem("skill", name, STATUS_MISSING, "repo skill not found in live workspace"))
            continue
        detail = live.skill_details.get(name)
        if detail is None:
            items.append(AuditItem("skill", name, STATUS_UNKNOWN, "live skill content unavailable from get command"))
            continue
        differences = []
        if normalize_text(detail.get("content")) != normalize_text(repo_skill["content"]):
            differences.append("skill content differs from repo SKILL.md")
        status = STATUS_STALE if differences else STATUS_CURRENT
        message = "live skill matches repo template" if not differences else "live skill differs from repo template"
        items.append(AuditItem("skill", name, status, message, differences))

    for name in sorted(set(live_by_name) - set(repo_skills)):
        items.append(AuditItem("skill", name, STATUS_EXTRA, "live skill has no repo template entry"))
    return items


def compare_squads(repo_squads: list[dict[str, Any]], live: LiveState | None) -> list[AuditItem]:
    items: list[AuditItem] = []
    if live is None:
        return [
            AuditItem("squad", str(squad.get("name")), STATUS_UNKNOWN, "repo squad present; live comparison skipped")
            for squad in repo_squads
        ]
    if not live.squads and live_category_unavailable(live, "squads"):
        return [
            AuditItem("squad", str(squad.get("name")), STATUS_UNAVAILABLE, "live squad data unavailable")
            for squad in repo_squads
        ]

    id_to_name = names_by_id(live.agents)
    live_by_name = {str(squad.get("name")): squad for squad in live.squads if squad.get("name")}
    repo_names = {str(squad.get("name")) for squad in repo_squads}
    for repo_squad in repo_squads:
        name = str(repo_squad.get("name"))
        live_squad = live.squad_details.get(name) or live_by_name.get(name)
        if live_squad is None:
            items.append(AuditItem("squad", name, STATUS_MISSING, "repo squad not found in live workspace"))
            continue
        differences: list[str] = []
        unknowns: list[str] = []
        leader_id = str(live_squad.get("leader_id", ""))
        live_leader = id_to_name.get(leader_id, leader_id)
        if repo_squad.get("leader") and live_leader != str(repo_squad.get("leader")):
            differences.append("leader differs")
        if normalize_text(live_squad.get("instructions")) != normalize_text(repo_squad.get("instructions")):
            differences.append("routing instructions differ")
        repo_member_count = len(repo_squad.get("members", []))
        live_member_count = live_squad.get("member_count")
        if isinstance(live_member_count, int) and repo_member_count != live_member_count:
            differences.append("member count differs")
        if live_squad.get("member_preview") and repo_member_count:
            unknowns.append("full live member roles are not available from squad get output")
        if differences:
            status = STATUS_STALE
            detail = "live squad differs from repo template"
        elif unknowns:
            status = STATUS_UNKNOWN
            detail = "live squad matches available fields; some member fields are unavailable"
        else:
            status = STATUS_CURRENT
            detail = "live squad matches repo template"
        items.append(AuditItem("squad", name, status, detail, differences + unknowns))

    for name in sorted(set(live_by_name) - repo_names):
        items.append(AuditItem("squad", name, STATUS_EXTRA, "live squad has no repo template entry"))
    return items


def first_present(mapping: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def autopilot_trigger_value(live_autopilot: dict[str, Any], field_name: str) -> Any:
    value = first_present(live_autopilot, (field_name, f"{field_name}_type"))
    if value is not None:
        return value
    triggers = live_autopilot.get("triggers")
    if isinstance(triggers, list) and triggers:
        first = triggers[0]
        if isinstance(first, dict):
            if field_name == "trigger":
                return first_present(first, ("trigger", "trigger_type", "type"))
            if field_name == "schedule":
                return first_present(first, ("schedule", "cron", "cron_expression"))
    return None


def compare_autopilots(repo_autopilots: list[dict[str, Any]], live: LiveState | None) -> list[AuditItem]:
    items: list[AuditItem] = []
    if live is None:
        return [
            AuditItem("autopilot", str(autopilot.get("name")), STATUS_UNKNOWN, "repo autopilot present; live comparison skipped")
            for autopilot in repo_autopilots
        ]
    if not live.autopilots and live_category_unavailable(live, "autopilots"):
        return [
            AuditItem("autopilot", str(autopilot.get("name")), STATUS_UNAVAILABLE, "live autopilot data unavailable")
            for autopilot in repo_autopilots
        ]
    if not live.autopilots:
        return [
            AuditItem("autopilot", str(autopilot.get("name")), STATUS_MISSING, "no live autopilots found")
            for autopilot in repo_autopilots
        ]

    id_to_name = names_by_id(live.agents)
    live_by_name = {str(autopilot.get("name")): autopilot for autopilot in live.autopilots if autopilot.get("name")}
    repo_names = {str(autopilot.get("name")) for autopilot in repo_autopilots}
    for repo_autopilot in repo_autopilots:
        name = str(repo_autopilot.get("name"))
        detail_unavailable = False
        if name in live.autopilot_details:
            live_autopilot = live.autopilot_details[name]
        elif name in live_by_name:
            live_autopilot = live_by_name[name]
            detail_unavailable = True
        else:
            items.append(AuditItem("autopilot", name, STATUS_MISSING, "repo autopilot not found in live workspace"))
            continue
        differences: list[str] = []
        unknowns: list[str] = []
        if detail_unavailable:
            unknowns.append("detailed autopilot data unavailable; prompt comparison skipped")
        field_map = {
            "mode": ("mode", "execution_mode"),
            "issue_title": ("issue_title", "title", "title_template"),
            "prompt": ("prompt", "instructions"),
        }
        for repo_field, live_fields in field_map.items():
            live_value = first_present(live_autopilot, live_fields)
            if live_value is None:
                unknowns.append(f"{repo_field} unavailable from live output")
            elif normalize_text(live_value) != normalize_text(repo_autopilot.get(repo_field)):
                differences.append(f"{repo_field} differs")
        for trigger_field in ("trigger", "schedule"):
            repo_value = repo_autopilot.get(trigger_field)
            live_value = autopilot_trigger_value(live_autopilot, trigger_field)
            if repo_value and live_value is None:
                unknowns.append(f"{trigger_field} unavailable from live output")
            elif repo_value and normalize_text(live_value) != normalize_text(repo_value):
                differences.append(f"{trigger_field} differs")
        live_assignee = first_present(live_autopilot, ("assignee", "assignee_name"))
        if isinstance(live_assignee, dict):
            live_assignee = first_present(live_assignee, ("name", "id"))
        if isinstance(live_assignee, str) and live_assignee in id_to_name:
            live_assignee = id_to_name[live_assignee]
        if repo_autopilot.get("assignee") and live_assignee is None:
            unknowns.append("assignee unavailable from live output")
        elif repo_autopilot.get("assignee") and str(live_assignee) != str(repo_autopilot.get("assignee")):
            differences.append("assignee differs")
        if differences:
            status = STATUS_STALE
            detail = "live autopilot differs from repo template"
        elif unknowns:
            status = STATUS_UNKNOWN
            detail = "live autopilot matches available fields; some fields are unavailable"
        else:
            status = STATUS_CURRENT
            detail = "live autopilot matches repo template"
        items.append(AuditItem("autopilot", name, status, detail, differences + unknowns))

    for name in sorted(set(live_by_name) - repo_names):
        items.append(AuditItem("autopilot", name, STATUS_EXTRA, "live autopilot has no repo template entry"))
    return items


def marker_items_for_texts(category: str, texts: dict[str, str], live_mode: bool) -> list[AuditItem]:
    combined = "\n".join(normalize_text(text) for text in texts.values())
    items: list[AuditItem] = []
    for marker_name, variants in MARKER_GROUPS.items():
        found = any(variant in combined for variant in variants)
        if found:
            items.append(AuditItem(category, marker_name, STATUS_CURRENT, "marker wording found"))
        else:
            status = STATUS_STALE if live_mode else STATUS_MISSING
            items.append(AuditItem(category, marker_name, status, "marker wording not found"))
    return items


def collect_repo_marker_texts(root: Path) -> dict[str, str]:
    paths = [
        "AGENTS.md",
        "README.md",
        "docs/agents/multica-live-config-sync.md",
        "multica/agent-system-prompts/codex-scoper.md",
        "multica/agent-system-prompts/codex-fullstack.md",
        ".agents/skills/spec-first-intake/SKILL.md",
        ".agents/skills/context-pack/SKILL.md",
        ".agents/skills/verification-before-completion/SKILL.md",
    ]
    return {path: read_text_if_present(root / path) for path in paths}


def collect_live_marker_texts(live: LiveState) -> dict[str, str]:
    texts: dict[str, str] = {}
    for agent in live.agents:
        name = str(agent.get("name", ""))
        if name in LIVE_MARKER_OBJECTS["agents"]:
            texts[f"agent:{name}"] = str(agent.get("instructions", ""))
    for name in LIVE_MARKER_OBJECTS["skills"]:
        detail = live.skill_details.get(name)
        if detail:
            texts[f"skill:{name}"] = str(detail.get("content", ""))
    return texts


def build_audit(root: Path, live: LiveState | None) -> list[AuditItem]:
    templates = load_repo_templates(root)
    items: list[AuditItem] = []
    items.extend(compare_agents(root, templates["agents"], live))
    items.extend(compare_skills(templates["skills"], live))
    items.extend(compare_squads(templates["squads"], live))
    items.extend(compare_autopilots(templates["autopilots"], live))
    items.extend(marker_items_for_texts("repo-marker", collect_repo_marker_texts(root), live_mode=False))
    if live is None:
        for marker_name in MARKER_GROUPS:
            items.append(AuditItem("live-marker", marker_name, STATUS_UNKNOWN, "live marker comparison skipped"))
    elif collect_live_marker_texts(live):
        items.extend(marker_items_for_texts("live-marker", collect_live_marker_texts(live), live_mode=True))
    else:
        for marker_name in MARKER_GROUPS:
            items.append(AuditItem("live-marker", marker_name, STATUS_UNAVAILABLE, "live marker source text unavailable"))
    if live is not None:
        for message in live.unavailable:
            items.append(AuditItem("live-access", "Multica CLI", STATUS_UNAVAILABLE, message))
    return items


def render_text(items: list[AuditItem], live_enabled: bool) -> str:
    lines = [
        "Multica live configuration drift audit",
        f"Mode: {'live read-only' if live_enabled else 'repo-only'}",
        "",
    ]
    for item in items:
        lines.append(f"[{item.status}] {item.category}: {item.name} - {item.detail}")
        for difference in item.differences:
            lines.append(f"  - {difference}")
    summary: dict[str, int] = {}
    for item in items:
        summary[item.status] = summary.get(item.status, 0) + 1
    lines.extend(["", "Summary:"])
    for status in (STATUS_CURRENT, STATUS_STALE, STATUS_MISSING, STATUS_EXTRA, STATUS_UNAVAILABLE, STATUS_UNKNOWN):
        if status in summary:
            lines.append(f"- {status}: {summary[status]}")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only audit of repo Multica templates against live Multica workspace configuration.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--repo-only", action="store_true", help="Audit repo templates and markers without Multica CLI access.")
    mode.add_argument("--live", action="store_true", help="Use read-only Multica CLI list/get commands for live drift checks.")
    parser.add_argument(
        "--no-secrets",
        action="store_true",
        help="Document the default safety posture: reports omit secret/custom_env/token/cookie values.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument("--timeout-seconds", type=int, default=20, help="Timeout for each Multica CLI read command.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    live_enabled = bool(args.live)
    live = fetch_live_state(root, args.timeout_seconds) if live_enabled else None
    items = build_audit(root, live)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "mode": "live" if live_enabled else "repo-only",
                    "items": [item.as_dict() for item in items],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render_text(items, live_enabled))
    return 0


if __name__ == "__main__":
    sys.exit(main())
