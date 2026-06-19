#!/usr/bin/env python3
"""Repository readiness checks for the Codex + Multica template."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


TEMPLATE_REQUIRED_FILES = (
    "AGENTS.md",
    "docs/agents/code-review.md",
    "docs/agents/new-project-bootstrap-boundary.md",
    "docs/agents/project-intake-spec.md",
    "docs/agents/security-review.md",
    "docs/agents/issue-tracker.md",
    ".github/pull_request_template.md",
    ".github/codex/prompts/review.md",
    ".github/scripts/deepseek_pr_review.py",
    ".github/workflows/deepseek-pr-review.yml",
    ".github/workflows/codeql.yml",
)

TEMPLATE_REQUIRED_TEXT = (
    (".github/workflows/codeql.yml", "language: ['python']"),
    (".github/workflows/deepseek-pr-review.yml", "pull-requests: write"),
    (
        ".github/workflows/deepseek-pr-review.yml",
        "steps.deepseek_review.outputs.exit_code != '0'",
    ),
    (".github/workflows/deepseek-pr-review.yml", "exit 0"),
    (
        ".github/workflows/deepseek-pr-review.yml",
        "always() && steps.deepseek_review.outputs.exit_code != '0'",
    ),
)

TEMPLATE_FORBIDDEN_TEXT = (
    (".github/workflows/codeql.yml", "language: ['javascript-typescript']"),
    (".github/workflows/deepseek-pr-review.yml", "continue-on-error: true"),
    (".github/workflows/deepseek-pr-review.yml", "hashFiles('deepseek-review.md')"),
)

PRODUCT_BOOTSTRAP_FORBIDDEN_PATHS = (
    ".agents/skills",
    "multica/agent-system-prompts",
    "multica/agents.yaml",
    "multica/squads.yaml",
    "multica/autopilots.yaml",
    "scripts/audit-multica-live-config.py",
    "scripts/sync-multica-live-config.py",
    "scripts/live_sync_policy.py",
    "scripts/template_catalog.py",
)

PRODUCT_BOOTSTRAP_REQUIRED_FILES = (
    "AGENTS.md",
    "README.md",
    "docs/agents/new-project-bootstrap-boundary.md",
)


CommandRunner = Callable[[Sequence[str], Path], int]


@dataclass
class ReadinessResult:
    messages: list[str]
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def default_runner(command: Sequence[str], cwd: Path) -> int:
    completed = subprocess.run(command, cwd=cwd, check=False)
    return completed.returncode


def _read_text(root: Path, relative_path: str) -> str | None:
    path = root / relative_path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _check_required_files(root: Path, messages: list[str], errors: list[str]) -> None:
    for relative_path in TEMPLATE_REQUIRED_FILES:
        if (root / relative_path).is_file():
            messages.append(f"OK: {relative_path}")
        else:
            errors.append(f"MISSING: {relative_path}")


def _check_required_text(root: Path, messages: list[str], errors: list[str]) -> None:
    for relative_path, expected_text in TEMPLATE_REQUIRED_TEXT:
        text = _read_text(root, relative_path)
        if text is not None and expected_text in text:
            messages.append(f"OK: {relative_path} contains {expected_text}")
        else:
            errors.append(f"MISSING: {relative_path} does not contain {expected_text}")


def _check_forbidden_text(root: Path, messages: list[str], errors: list[str]) -> None:
    for relative_path, forbidden_text in TEMPLATE_FORBIDDEN_TEXT:
        text = _read_text(root, relative_path)
        if text is not None and forbidden_text in text:
            errors.append(f"UNEXPECTED: {relative_path} contains {forbidden_text}")
        else:
            messages.append(f"OK: {relative_path} does not contain {forbidden_text}")


def _check_deepseek_self_test(root: Path, runner: CommandRunner, messages: list[str], errors: list[str]) -> None:
    command = [sys.executable, ".github/scripts/deepseek_pr_review.py", "--self-test"]
    exit_code = runner(command, root)
    if exit_code == 0:
        messages.append("OK: DeepSeek review self-test")
    else:
        errors.append(f"ERROR: DeepSeek review self-test failed with exit code {exit_code}")


def _check_template_skills(root: Path, messages: list[str], errors: list[str]) -> None:
    skills_dir = root / ".agents/skills"
    if not skills_dir.is_dir():
        errors.append("MISSING: .agents/skills")
        return

    for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
        messages.append(skill_file.relative_to(root).as_posix())


def _check_template_profile(root: Path, runner: CommandRunner) -> ReadinessResult:
    messages: list[str] = []
    errors: list[str] = []
    _check_required_files(root, messages, errors)
    _check_required_text(root, messages, errors)
    _check_forbidden_text(root, messages, errors)
    _check_deepseek_self_test(root, runner, messages, errors)
    _check_template_skills(root, messages, errors)
    return ReadinessResult(messages=messages, errors=errors)


def _check_product_bootstrap_profile(root: Path) -> ReadinessResult:
    messages: list[str] = []
    errors: list[str] = []
    for relative_path in PRODUCT_BOOTSTRAP_REQUIRED_FILES:
        path = root / relative_path
        if path.is_file():
            messages.append(f"OK: product bootstrap repository contains {relative_path}")
        else:
            errors.append(f"MISSING: product bootstrap repository missing required file {relative_path}")
    for relative_path in PRODUCT_BOOTSTRAP_FORBIDDEN_PATHS:
        path = root / relative_path
        if path.exists():
            errors.append(f"UNEXPECTED: product bootstrap repository contains shared runtime path {relative_path}")
        else:
            messages.append(f"OK: product bootstrap repository does not contain {relative_path}")
    return ReadinessResult(messages=messages, errors=errors)


def check_repository(
    root: Path,
    *,
    profile: str = "template",
    runner: CommandRunner = default_runner,
) -> ReadinessResult:
    if profile == "template":
        return _check_template_profile(root, runner)
    if profile == "product-bootstrap":
        return _check_product_bootstrap_profile(root)
    return ReadinessResult(messages=[], errors=[f"ERROR: unknown readiness profile {profile}"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="template", help="Readiness profile to check. Default: template.")
    parser.add_argument("--root", default=".", help="Repository root to check. Default: current directory.")
    args = parser.parse_args(argv)

    result = check_repository(Path(args.root).resolve(), profile=args.profile)
    for message in result.messages:
        print(message)
    for error in result.errors:
        print(error)

    if result.ok:
        print("Agent readiness check passed.")
        return 0

    print("Agent readiness check failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
