from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import repository_readiness as readiness


def write(root: Path, relative_path: str, content: str = "content\n") -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_template_repo(root: Path, *, deepseek_workflow: str | None = None) -> None:
    for path in readiness.TEMPLATE_REQUIRED_FILES:
        write(root, path)

    write(
        root,
        ".github/workflows/codeql.yml",
        "name: CodeQL\non:\n  pull_request:\njobs:\n  analyze:\n    strategy:\n      matrix:\n        language: ['python']\n",
    )
    write(
        root,
        ".github/workflows/deepseek-pr-review.yml",
        deepseek_workflow
        or "\n".join(
            [
                "name: DeepSeek",
                "permissions:",
                "  pull-requests: write",
                "jobs:",
                "  review:",
                "    steps:",
                "      - run: steps.deepseek_review.outputs.exit_code != '0'",
                "      - run: exit 0",
                "      - if: always() && steps.deepseek_review.outputs.exit_code != '0'",
            ]
        ),
    )
    write(
        root,
        ".agents/skills/context-pack/SKILL.md",
        "---\nname: context-pack\ndescription: Compact state.\n---\n",
    )


class RepositoryReadinessTests(unittest.TestCase):
    def test_template_profile_passes_for_current_required_files_and_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_template_repo(root)

            result = readiness.check_repository(root, runner=lambda command, cwd: 0)

        self.assertFalse(result.errors)
        self.assertIn("OK: AGENTS.md", result.messages)
        self.assertIn("OK: .github/workflows/deepseek-pr-review.yml contains pull-requests: write", result.messages)
        self.assertIn(".agents/skills/context-pack/SKILL.md", result.messages)

    def test_template_profile_reports_missing_files_and_forbidden_workflow_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_template_repo(
                root,
                deepseek_workflow="pull-requests: write\ncontinue-on-error: true\n",
            )
            (root / "docs/agents/security-review.md").unlink()

            result = readiness.check_repository(root, runner=lambda command, cwd: 0)

        self.assertIn("MISSING: docs/agents/security-review.md", result.errors)
        self.assertIn(
            "UNEXPECTED: .github/workflows/deepseek-pr-review.yml contains continue-on-error: true",
            result.errors,
        )

    def test_deepseek_self_test_failure_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_template_repo(root)

            result = readiness.check_repository(root, runner=lambda command, cwd: 7)

        self.assertIn("ERROR: DeepSeek review self-test failed with exit code 7", result.errors)

    def test_unknown_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = readiness.check_repository(Path(tmp), profile="unknown", runner=lambda command, cwd: 0)

        self.assertIn("ERROR: unknown readiness profile unknown", result.errors)


if __name__ == "__main__":
    unittest.main()
