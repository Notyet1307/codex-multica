import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from scripts import validate_intake_spec as validator


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

Ask Codex to use ask-matt and spec-first-intake to refine the split.

## Risks

Runtime scope could expand into live API ingestion.

## Validation

- `make verify`
- `python3 scripts/validate-exposure-fixtures.py`

## Suggested Slices

### Slice 1: Add runtime entrypoint

- Goal: add the command shell.
- Scope: synthetic fixtures only.
- Acceptance criteria: command runs against fixtures.
- Validation: `make verify`
- Stop conditions: stop if real API ingestion is required.

### Slice 2: Add report output

- Goal: emit a deterministic report.
- Scope: local report generation only.
- Acceptance criteria: report has stable fields.
- Validation: snapshot check.
- Stop conditions: stop if customer data is required.

## Links / Evidence

- docs/roadmap.md
"""


class ValidateIntakeSpecTests(unittest.TestCase):
    def test_complete_spec_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "spec.md", COMPLETE_SPEC)
            spec = validator.parse_intake_spec(spec_path)

            result = validator.validate_spec(spec)

        self.assertFalse(result.errors)

    def test_missing_required_top_level_section_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "thin.md", "# Thin\n\n## Goal\n\nDo a thing.\n")
            spec = validator.parse_intake_spec(spec_path)

            result = validator.validate_spec(spec)

        self.assertIn("missing required section: Background", result.errors)
        self.assertIn("missing required section: Suggested Slices", result.errors)

    def test_slice_missing_required_field_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "slice.md", COMPLETE_SPEC.replace("- Stop conditions: stop if customer data is required.\n", ""))
            spec = validator.parse_intake_spec(spec_path)

            result = validator.validate_spec(spec)

        self.assertIn("slice 2 missing required field: Stop conditions", result.errors)

    def test_empty_slice_required_field_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "empty-field.md", COMPLETE_SPEC.replace("- Scope: local report generation only.", "- Scope:"))
            spec = validator.parse_intake_spec(spec_path)

            result = validator.validate_spec(spec)

        self.assertIn("slice 2 has empty required field: Scope", result.errors)

    def test_placeholders_and_todos_are_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "placeholder.md", COMPLETE_SPEC.replace("Exposure Runtime Intake", "<Project Name>").replace("Create a safe first runtime slice.", "TODO"))
            spec = validator.parse_intake_spec(spec_path)

            result = validator.validate_spec(spec)

        self.assertIn("title contains placeholder text", result.errors)
        self.assertIn("section contains TODO placeholder: Goal", result.errors)

    def test_cli_reports_success_for_valid_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "spec.md", COMPLETE_SPEC)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = validator.main(["--spec", str(spec_path)])

        self.assertEqual(exit_code, 0)
        self.assertIn("OK: intake spec is structurally ready", stdout.getvalue())

    def test_cli_reports_failure_for_invalid_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = write(root, "thin.md", "# Thin\n\n## Goal\n\nDo a thing.\n")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = validator.main(["--spec", str(spec_path)])

        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR: missing required section: Background", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
