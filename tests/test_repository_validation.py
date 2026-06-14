import tempfile
import unittest
from pathlib import Path

from scripts import repository_validation as validation


def write(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class RepositoryValidationTests(unittest.TestCase):
    def test_validate_skills_requires_skill_file_and_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root,
                ".agents/skills/good/SKILL.md",
                "---\nname: good\ndescription: Good skill.\n---\n\n# Good\n",
            )
            (root / ".agents/skills/missing").mkdir(parents=True)
            write(root, ".agents/skills/incomplete/SKILL.md", "---\nname: incomplete\n---\n")

            errors = validation.validate_skills(root)

        self.assertIn(".agents/skills/missing/SKILL.md is missing", errors)
        self.assertIn(
            ".agents/skills/incomplete/SKILL.md frontmatter missing description",
            errors,
        )

    def test_validate_multica_config_rejects_missing_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root,
                ".agents/skills/existing/SKILL.md",
                "---\nname: existing\ndescription: Existing skill.\n---\n",
            )
            write(
                root,
                "multica/agents.yaml",
                """
agents:
  - name: codex-test
    skills:
      - existing
      - missing-skill
    system_prompt_file: multica/agent-system-prompts/missing.md
""",
            )

            errors = validation.validate_multica_config(root)

        self.assertIn("codex-test references missing skill missing-skill", errors)
        self.assertIn(
            "codex-test references missing system_prompt_file multica/agent-system-prompts/missing.md",
            errors,
        )

    def test_validate_prompts_requires_content_and_response_expectation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, ".github/codex/prompts/empty.md", "\n")
            write(root, ".github/codex/prompts/no-output.md", "Review the pull request.\n")
            write(root, ".github/codex/prompts/good.md", "Review the pull request.\n\nReturn Markdown.\n")

            errors = validation.validate_prompts(root)

        self.assertIn(".github/codex/prompts/empty.md is empty", errors)
        self.assertIn(
            ".github/codex/prompts/no-output.md lacks an output or response expectation",
            errors,
        )

    def test_validate_workflows_checks_structure_and_disabled_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, ".github/workflows/good.yml", "name: Good\non:\n  push:\njobs:\n  test:\n")
            write(root, ".github/workflows/bad.yml", "name: Bad\njobs:\n  test:\n")
            write(root, ".github/workflows/paused.yml.disabled", "name: Paused\non:\n  pull_request:\njobs:\n  test:\n")
            write(
                root,
                ".github/workflows/documented.yml.disabled",
                "# Disabled during dogfood; restore after the external service is configured.\nname: Documented\non:\n  pull_request:\njobs:\n  test:\n",
            )

            errors = validation.validate_workflows(root)

        self.assertIn(".github/workflows/bad.yml missing top-level on", errors)
        self.assertIn(
            ".github/workflows/paused.yml.disabled lacks a documented disabled reason or restore condition",
            errors,
        )
        self.assertNotIn(
            ".github/workflows/documented.yml.disabled lacks a documented disabled reason or restore condition",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
