import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts import intake_to_issue_drafts as drafts


def write(root: Path, relative_path: str, content: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


COMPLETE_SPEC = """# Exposure Runtime Intake

## Goal

Create a safe first runtime slice.

## Background

The project currently has fixtures and validators.

## Current State

`make verify` passes and no product runtime exists.

## Desired Behavior

The first runtime command reads synthetic fixtures and emits a report.

## Non-goals

- Do not ingest real data.
- Do not call external APIs.

## Constraints

- Use Python standard library.
- Do not touch live Multica configuration.

## Proposed Approach

Add a deterministic CLI around existing fixture contracts.

## Risks

Runtime scope could expand into live API ingestion.

## Validation

- `make verify`
- `python3 scripts/validate-exposure-fixtures.py`

## Suggested Slices

### Slice 1: Add runtime entrypoint

- Goal: add the command shell.
- Acceptance criteria: command runs against fixtures.
- Validation: `make verify`

### Slice 2: Add report output

- Goal: emit a deterministic report.
- Acceptance criteria: report has stable fields.
- Validation: snapshot check.

## Links / Evidence

- docs/roadmap.md
"""


class IntakeToIssueDraftTests(unittest.TestCase):
    def test_builds_one_draft_per_suggested_slice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "spec.md", COMPLETE_SPEC)
            spec = drafts.parse_intake_spec(spec_path)

            draft_issues = drafts.build_draft_issues(spec)

        self.assertEqual([draft.title for draft in draft_issues], ["Add runtime entrypoint", "Add report output"])
        self.assertEqual(draft_issues[0].filename, "01-add-runtime-entrypoint.md")
        self.assertIn("## Stop conditions", draft_issues[0].body)
        self.assertIn("Source intake spec:", draft_issues[0].body)
        self.assertFalse(draft_issues[0].warnings)

    def test_missing_sections_create_quality_warnings_and_todo_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "thin.md", "# Thin\n\n## Goal\n\nDo a thing.\n")
            spec = drafts.parse_intake_spec(spec_path)

            draft_issue = drafts.build_draft_issues(spec)[0]

        self.assertIn("source spec missing section: Background", draft_issue.warnings)
        self.assertIn("contains TODO placeholders", draft_issue.warnings)
        self.assertIn("TODO: state what must not be changed", draft_issue.body)

    def test_cli_writes_drafts_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "spec.md", COMPLETE_SPEC)
            output_dir = root / "out"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = drafts.main(["--spec", str(spec_path), "--output-dir", str(output_dir)])

            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(manifest["draft_count"], 2)
        self.assertEqual(Path(manifest["drafts"][0]["path"]).name, "01-add-runtime-entrypoint.md")

    def test_cli_can_fail_on_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "thin.md", "# Thin\n\n## Goal\n\nDo a thing.\n")
            output_dir = root / "out"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = drafts.main(["--spec", str(spec_path), "--output-dir", str(output_dir), "--fail-on-warnings"])

        self.assertEqual(exit_code, 2)

    def test_placeholder_text_creates_quality_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "placeholder.md", COMPLETE_SPEC.replace("Exposure Runtime Intake", "<Project Name>"))
            spec = drafts.parse_intake_spec(spec_path)

            draft_issue = drafts.build_draft_issues(spec)[0]

        self.assertIn("source spec title contains placeholder text", draft_issue.warnings)
        self.assertIn("source spec title contains placeholder text", draft_issue.body)


if __name__ == "__main__":
    unittest.main()
