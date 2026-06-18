#!/usr/bin/env python3
"""Repository-local Multica and skill template catalog."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SkillTemplate:
    name: str
    path: str
    content: str
    frontmatter: dict[str, str] = field(default_factory=dict)
    frontmatter_errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AgentTemplate:
    name: str
    skills: list[str] = field(default_factory=list)
    system_prompt_file: str = ""
    prompt_content: str = ""
    fields: dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "name":
            return self.name
        if key == "skills":
            return self.skills
        if key == "system_prompt_file":
            return self.system_prompt_file
        if key == "prompt_content":
            return self.prompt_content
        return self.fields.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"name": self.name, "skills": list(self.skills)}
        data.update(self.fields)
        if self.system_prompt_file:
            data["system_prompt_file"] = self.system_prompt_file
        return data


@dataclass(frozen=True)
class SquadTemplate:
    name: str
    members: list[dict[str, str]] = field(default_factory=list)
    instructions: str = ""
    fields: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"name": self.name, "members": list(self.members)}
        data.update(self.fields)
        if self.instructions:
            data["instructions"] = self.instructions
        return data


@dataclass(frozen=True)
class AutopilotTemplate:
    name: str
    prompt: str = ""
    fields: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"name": self.name}
        data.update(self.fields)
        if self.prompt:
            data["prompt"] = self.prompt
        return data


@dataclass(frozen=True)
class TemplateCatalog:
    root: Path
    skills: dict[str, SkillTemplate]
    agents: list[AgentTemplate]
    squads: list[SquadTemplate]
    autopilots: list[AutopilotTemplate]

    @classmethod
    def load(cls, root: Path) -> "TemplateCatalog":
        agents = parse_agents_template(root)
        agents = [
            replace(agent, prompt_content=read_text_if_present(root / agent.system_prompt_file))
            if agent.system_prompt_file
            else agent
            for agent in agents
        ]
        return cls(
            root=root,
            skills=load_skill_templates(root),
            agents=agents,
            squads=parse_squads_template(root),
            autopilots=parse_autopilots_template(root),
        )

    def agent_prompt_content(self, agent: AgentTemplate) -> str:
        return agent.prompt_content

    def legacy_dict(self) -> dict[str, Any]:
        return {
            "agents": [agent.as_dict() for agent in self.agents],
            "skills": {
                name: {"name": skill.name, "path": skill.path, "content": skill.content}
                for name, skill in self.skills.items()
            },
            "squads": [squad.as_dict() for squad in self.squads],
            "autopilots": [autopilot.as_dict() for autopilot in self.autopilots],
        }


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


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    text = read_text_if_present(path)
    if not text.startswith("---\n"):
        return {}, [f"{path.name} missing frontmatter block"]

    lines = text.splitlines()
    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            end_index = index
            break

    if end_index is None:
        return {}, [f"{path.name} has unterminated frontmatter block"]

    fields: dict[str, str] = {}
    for line in lines[1:end_index]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = clean_scalar(value)

    return fields, []


def parse_frontmatter_name(path: Path) -> str:
    fields, _ = parse_frontmatter(path)
    return fields.get("name") or path.parent.name


def load_skill_templates(root: Path) -> dict[str, SkillTemplate]:
    skills: dict[str, SkillTemplate] = {}
    for skill_path in sorted((root / ".agents/skills").glob("*/SKILL.md")):
        fields, errors = parse_frontmatter(skill_path)
        name = fields.get("name") or skill_path.parent.name
        skills[name] = SkillTemplate(
            name=name,
            path=skill_path.relative_to(root).as_posix(),
            content=read_text_if_present(skill_path),
            frontmatter=fields,
            frontmatter_errors=errors,
        )
    return skills


def parse_agents_template(root: Path) -> list[AgentTemplate]:
    path = root / "multica/agents.yaml"
    agents: list[AgentTemplate] = []
    current_name: str | None = None
    current_skills: list[str] = []
    current_fields: dict[str, str] = {}
    in_skills = False

    def flush_current() -> None:
        if current_name is not None:
            agents.append(
                AgentTemplate(
                    name=current_name,
                    skills=list(current_skills),
                    system_prompt_file=current_fields.pop("system_prompt_file", ""),
                    fields=dict(current_fields),
                )
            )

    for raw_line in read_text_if_present(path).splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = re.match(r"^\s*-\s+name:\s*(.+)$", line)
        if match:
            flush_current()
            current_name = clean_scalar(match.group(1))
            current_skills = []
            current_fields = {}
            in_skills = False
            continue
        if current_name is None:
            continue
        if re.match(r"^\s*skills:\s*$", line):
            in_skills = True
            continue
        list_match = re.match(r"^\s*-\s*(.+)$", line)
        if in_skills and list_match:
            current_skills.append(clean_scalar(list_match.group(1)))
            continue
        key_match = re.match(r"^\s*([A-Za-z_][\w_-]*):\s*(.+)$", line)
        if key_match:
            key, value = key_match.groups()
            current_fields[key] = clean_scalar(value)
            in_skills = False

    flush_current()
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


def parse_squads_template(root: Path) -> list[SquadTemplate]:
    path = root / "multica/squads.yaml"
    lines = read_text_if_present(path).splitlines()
    squads: list[SquadTemplate] = []
    current_name: str | None = None
    current_members: list[dict[str, str]] = []
    current_fields: dict[str, str] = {}
    current_instructions = ""
    current_member: dict[str, str] | None = None
    in_members = False
    index = 0

    def flush_current() -> None:
        if current_name is not None:
            squads.append(
                SquadTemplate(
                    name=current_name,
                    members=list(current_members),
                    instructions=current_instructions,
                    fields=dict(current_fields),
                )
            )

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        match = re.match(r"^\s*-\s+name:\s*(.+)$", line)
        if match and indent == 2:
            flush_current()
            current_name = clean_scalar(match.group(1))
            current_members = []
            current_fields = {}
            current_instructions = ""
            in_members = False
            current_member = None
            index += 1
            continue
        if current_name is None:
            index += 1
            continue
        if re.match(r"^\s*members:\s*$", line):
            in_members = True
            index += 1
            continue
        member_match = re.match(r"^\s*-\s+name:\s*(.+)$", line)
        if in_members and member_match and indent > 2:
            current_member = {"name": clean_scalar(member_match.group(1))}
            current_members.append(current_member)
            index += 1
            continue
        role_match = re.match(r"^\s*role:\s*(.+)$", line)
        if in_members and current_member is not None and role_match:
            current_member["role"] = clean_scalar(role_match.group(1))
            index += 1
            continue
        block_match = re.match(r"^(\s*)(instructions):\s*\|\s*$", line)
        if block_match:
            current_instructions, index = parse_block(lines, index + 1, len(block_match.group(1)))
            index += 1
            continue
        key_match = re.match(r"^\s*([A-Za-z_][\w_-]*):\s*(.+)$", line)
        if key_match and not in_members:
            key, value = key_match.groups()
            current_fields[key] = clean_scalar(value)
        index += 1

    flush_current()
    return squads


def parse_autopilots_template(root: Path) -> list[AutopilotTemplate]:
    path = root / "multica/autopilots.yaml"
    lines = read_text_if_present(path).splitlines()
    autopilots: list[AutopilotTemplate] = []
    current_name: str | None = None
    current_fields: dict[str, str] = {}
    current_prompt = ""
    index = 0

    def flush_current() -> None:
        if current_name is not None:
            autopilots.append(AutopilotTemplate(name=current_name, prompt=current_prompt, fields=dict(current_fields)))

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        match = re.match(r"^\s*-\s+name:\s*(.+)$", line)
        if match:
            flush_current()
            current_name = clean_scalar(match.group(1))
            current_fields = {}
            current_prompt = ""
            index += 1
            continue
        if current_name is None:
            index += 1
            continue
        block_match = re.match(r"^(\s*)(prompt):\s*\|\s*$", line)
        if block_match:
            current_prompt, index = parse_block(lines, index + 1, len(block_match.group(1)))
            index += 1
            continue
        key_match = re.match(r"^\s*([A-Za-z_][\w_-]*):\s*(.+)$", line)
        if key_match:
            key, value = key_match.groups()
            current_fields[key] = clean_scalar(value)
        index += 1

    flush_current()
    return autopilots
