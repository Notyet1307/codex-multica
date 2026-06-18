import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/template_catalog.py"


def load_catalog_module():
    spec = importlib.util.spec_from_file_location("template_catalog", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TemplateCatalogTests(unittest.TestCase):
    def test_loads_repo_multica_templates(self) -> None:
        catalog_module = load_catalog_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / ".agents/skills/context-pack/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: context-pack\ndescription: Compact state\n---\nBody\n", encoding="utf-8")

            prompt = root / "multica/agent-system-prompts/codex-fullstack.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text("Prompt text\n", encoding="utf-8")

            (root / "multica/agents.yaml").write_text(
                "\n".join(
                    [
                        "agents:",
                        "  - name: OpenAI-fullstack",
                        "    visibility: workspace",
                        "    concurrency_limit: 6",
                        "    purpose: Implement slices.",
                        "    skills:",
                        "      - context-pack",
                        "    system_prompt_file: multica/agent-system-prompts/codex-fullstack.md",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "multica/squads.yaml").write_text(
                "squads:\n"
                "  - name: AppDev Squad\n"
                "    leader: OpenAI-scoper\n"
                "    instructions: |\n"
                "      Route narrowly.\n"
                "    members:\n"
                "      - name: OpenAI-fullstack\n"
                "        role: Worker\n",
                encoding="utf-8",
            )
            (root / "multica/autopilots.yaml").write_text(
                "autopilots:\n"
                "  - name: Daily standup summary\n"
                "    mode: create_issue\n"
                "    trigger: cron\n"
                "    schedule: 0 0 * * 1-5\n"
                "    assignee: OpenAI-scoper\n"
                "    issue_title: Daily engineering standup {{date}}\n"
                "    prompt: |\n"
                "      Summarize work.\n",
                encoding="utf-8",
            )

            catalog = catalog_module.TemplateCatalog.load(root)

        self.assertEqual(set(catalog.skills), {"context-pack"})
        self.assertEqual(catalog.skills["context-pack"].path, ".agents/skills/context-pack/SKILL.md")
        self.assertEqual(catalog.skills["context-pack"].content, "---\nname: context-pack\ndescription: Compact state\n---\nBody\n")
        self.assertEqual(catalog.agents[0].name, "OpenAI-fullstack")
        self.assertEqual(catalog.agents[0].skills, ["context-pack"])
        self.assertEqual(catalog.agents[0].system_prompt_file, "multica/agent-system-prompts/codex-fullstack.md")
        self.assertEqual(catalog.agent_prompt_content(catalog.agents[0]), "Prompt text\n")
        self.assertEqual(catalog.squads[0].instructions, "Route narrowly.")
        self.assertEqual(catalog.autopilots[0].prompt, "Summarize work.")

    def test_skill_frontmatter_errors_are_preserved(self) -> None:
        catalog_module = load_catalog_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / ".agents/skills/no-frontmatter/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("# No frontmatter\n", encoding="utf-8")

            catalog = catalog_module.TemplateCatalog.load(root)

        self.assertEqual(set(catalog.skills), {"no-frontmatter"})
        self.assertEqual(catalog.skills["no-frontmatter"].frontmatter, {})
        self.assertEqual(catalog.skills["no-frontmatter"].frontmatter_errors, ["SKILL.md missing frontmatter block"])


if __name__ == "__main__":
    unittest.main()
