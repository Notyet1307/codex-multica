#!/usr/bin/env python3
"""Lightweight structural validation for the AgentOps template repository."""

from __future__ import annotations

import re
import importlib.util
import sys
from pathlib import Path
from typing import Iterable


OUTPUT_EXPECTATION_PATTERN = re.compile(r"\b(return|output|respond|response|format)\b", re.IGNORECASE)
DISABLED_REASON_PATTERN = re.compile(r"\b(disabled|parked|restore|enable|re-enable|reenable)\b", re.IGNORECASE)


def load_template_catalog_module():
    catalog_path = Path(__file__).resolve().parent / "template_catalog.py"
    spec = importlib.util.spec_from_file_location("template_catalog", catalog_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


template_catalog = load_template_catalog_module()


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    return template_catalog.parse_frontmatter(path)


def skill_names(root: Path) -> set[str]:
    return set(template_catalog.TemplateCatalog.load(root).skills)


def validate_skills(root: Path) -> list[str]:
    errors: list[str] = []
    skills_dir = root / ".agents/skills"
    if not skills_dir.is_dir():
        return [".agents/skills is missing"]

    catalog = template_catalog.TemplateCatalog.load(root)
    skills_by_path = {root / skill.path: skill for skill in catalog.skills.values()}
    skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    if not skill_dirs:
        errors.append(".agents/skills has no skill directories")

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{relative(skill_file, root)} is missing")
            continue

        skill_template = skills_by_path.get(skill_file)
        fields = skill_template.frontmatter if skill_template is not None else {}
        frontmatter_errors = skill_template.frontmatter_errors if skill_template is not None else []
        errors.extend(f"{relative(skill_file, root)} {error}" for error in frontmatter_errors)
        for field in ("name", "description"):
            if not fields.get(field):
                errors.append(f"{relative(skill_file, root)} frontmatter missing {field}")

    return errors


def parse_agents_config(path: Path) -> list[dict[str, object]]:
    root = path.parents[1]
    return [agent.as_dict() for agent in template_catalog.TemplateCatalog.load(root).agents]


def validate_multica_config(root: Path) -> list[str]:
    errors: list[str] = []
    agents_path = root / "multica/agents.yaml"
    if not agents_path.is_file():
        return ["multica/agents.yaml is missing"]

    known_skills = skill_names(root)
    agents = parse_agents_config(agents_path)
    if not agents:
        errors.append("multica/agents.yaml defines no agents")

    for agent in agents:
        name = str(agent.get("name", "<unnamed>"))
        for skill in agent.get("skills", []):
            if str(skill) not in known_skills:
                errors.append(f"{name} references missing skill {skill}")

        prompt_file = agent.get("system_prompt_file")
        if not prompt_file:
            errors.append(f"{name} is missing system_prompt_file")
            continue

        prompt_path = root / str(prompt_file)
        if not prompt_path.is_file():
            errors.append(f"{name} references missing system_prompt_file {prompt_file}")
        elif not prompt_path.read_text(encoding="utf-8").strip():
            errors.append(f"{prompt_file} is empty")

    prompts_dir = root / "multica/agent-system-prompts"
    if not prompts_dir.is_dir():
        errors.append("multica/agent-system-prompts is missing")
    else:
        for prompt_path in sorted(prompts_dir.glob("*.md")):
            if not prompt_path.read_text(encoding="utf-8").strip():
                errors.append(f"{relative(prompt_path, root)} is empty")

    return errors


def validate_prompts(root: Path) -> list[str]:
    errors: list[str] = []
    prompts_dir = root / ".github/codex/prompts"
    if not prompts_dir.is_dir():
        return [".github/codex/prompts is missing"]

    prompt_files = sorted(prompts_dir.glob("*.md"))
    if not prompt_files:
        errors.append(".github/codex/prompts has no prompt files")

    for prompt_path in prompt_files:
        text = prompt_path.read_text(encoding="utf-8")
        path_label = relative(prompt_path, root)
        if not text.strip():
            errors.append(f"{path_label} is empty")
            continue
        if not OUTPUT_EXPECTATION_PATTERN.search(text):
            errors.append(f"{path_label} lacks an output or response expectation")

    return errors


def top_level_yaml_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        if line.startswith((" ", "\t")) or not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):", line)
        if match:
            keys.add(match.group(1))
    return keys


def workflow_files(root: Path) -> Iterable[Path]:
    workflows_dir = root / ".github/workflows"
    if not workflows_dir.is_dir():
        return []
    patterns = ("*.yml", "*.yaml", "*.yml.disabled", "*.yaml.disabled")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(workflows_dir.glob(pattern))
    return sorted(set(files))


def validate_workflows(root: Path) -> list[str]:
    errors: list[str] = []
    workflows = list(workflow_files(root))
    if not workflows:
        return [".github/workflows has no workflow files"]

    for workflow_path in workflows:
        text = workflow_path.read_text(encoding="utf-8")
        path_label = relative(workflow_path, root)
        keys = top_level_yaml_keys(text)
        for required_key in ("name", "on", "jobs"):
            if required_key not in keys:
                errors.append(f"{path_label} missing top-level {required_key}")

        if workflow_path.name.endswith(".disabled") and not DISABLED_REASON_PATTERN.search(text):
            errors.append(f"{path_label} lacks a documented disabled reason or restore condition")

    return errors


def validate_readme_paths(root: Path) -> list[str]:
    readme_path = root / "README.md"
    if not readme_path.is_file():
        return ["README.md is missing"]

    readme = readme_path.read_text(encoding="utf-8")
    key_paths = (
        "AGENTS.md",
        ".codex/config.example.toml",
        ".agents/skills",
        ".github/codex/prompts",
        ".github/workflows",
        ".github/dependabot.yml.disabled",
        ".github/workflows/dependency-review.yml.disabled",
        ".github/pull_request_template.md",
        "docs/agents",
        "multica",
        "scripts",
    )

    errors: list[str] = []
    for key_path in key_paths:
        if key_path in readme and not (root / key_path).exists():
            errors.append(f"README.md references missing path {key_path}")
    return errors


def run_checks(root: Path, checks: Iterable[tuple[str, callable]]) -> int:
    all_errors: list[str] = []
    for name, check in checks:
        errors = check(root)
        if errors:
            all_errors.extend(f"{name}: {error}" for error in errors)
        else:
            print(f"OK: {name}")

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}")
        return 1
    return 0


def main(check_name: str | None = None) -> int:
    root = Path.cwd()
    checks = {
        "skills": validate_skills,
        "multica-config": validate_multica_config,
        "prompts": validate_prompts,
        "workflows": validate_workflows,
        "readme-paths": validate_readme_paths,
    }

    if check_name:
        return run_checks(root, [(check_name, checks[check_name])])
    return run_checks(root, checks.items())


if __name__ == "__main__":
    sys.exit(main())
