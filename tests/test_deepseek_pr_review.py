import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / ".github/scripts/deepseek_pr_review.py"
WORKFLOW_PATH = ROOT / ".github/workflows/deepseek-pr-review.yml"


def load_deepseek_module():
    spec = importlib.util.spec_from_file_location("deepseek_pr_review", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DeepSeekReviewTests(unittest.TestCase):
    def test_load_review_decision_module_exposes_review_policy(self) -> None:
        deepseek = load_deepseek_module()
        decision = deepseek.load_review_decision_module()

        self.assertTrue(hasattr(decision, "decide_review"))
        self.assertEqual(decision.BLOCKING_FINDINGS_EXIT_CODE, 1)
        self.assertEqual(decision.VALIDATION_GAPS_WITHOUT_BLOCKING_EXIT_CODE, 0)

    def test_format_review_body_adds_marker_and_structured_summary(self) -> None:
        deepseek = load_deepseek_module()
        review = """## Codex PR Review

### Summary

Looks reasonable.

### Blocking findings

No P0/P1 blocking findings found.

### Validation gaps

None.

### Security notes

No security-specific concerns.
"""

        body = deepseek.format_review_body(review)

        self.assertTrue(body.startswith("<!-- ai-review:deepseek -->\n"))
        self.assertIn("## DeepSeek PR Review", body)
        self.assertIn("| Provider | DeepSeek |", body)
        self.assertIn("| Recommendation | No P0/P1 blocking findings found |", body)
        self.assertIn("| Blocking findings | 0 |", body)
        self.assertIn("| Validation gaps | 0 |", body)
        self.assertIn("| Security review required | No |", body)
        self.assertIn(review.strip(), body)

    def test_count_blocking_findings_treats_empty_variants_as_zero(self) -> None:
        deepseek = load_deepseek_module()
        variants = (
            "No blocking findings",
            "No issues",
            "None",
            "N/A",
            "Nothing blocking",
        )

        for variant in variants:
            with self.subTest(variant=variant):
                review = f"""## Codex PR Review

### Blocking findings

{variant}

### Validation gaps

None.
"""

                self.assertEqual(deepseek.count_blocking_findings(review), 0)

    def test_markdown_section_stops_at_next_heading_regardless_of_level(self) -> None:
        deepseek = load_deepseek_module()
        next_headings = ("# Validation gaps", "## Validation gaps")

        for next_heading in next_headings:
            with self.subTest(next_heading=next_heading):
                review = f"""## Codex PR Review

### Blocking findings

None.

{next_heading}

- Add unit tests.
"""

                self.assertEqual(deepseek.markdown_section(review, "Blocking findings"), "None.")

    def test_run_returns_exit_code_from_review_decision_policy(self) -> None:
        deepseek = load_deepseek_module()
        previous_api_key = os.environ.get("DEEPSEEK_API_KEY")
        previous_call_deepseek = deepseek.call_deepseek
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        def run_with_review(review: str) -> tuple[int, str]:
            def fake_call_deepseek(payload, api_key, api_url):
                self.assertEqual(api_key, "test-key")
                return {"choices": [{"message": {"content": review}}]}

            deepseek.call_deepseek = fake_call_deepseek
            with tempfile.TemporaryDirectory() as tmpdir:
                diff_path = Path(tmpdir) / "pr.diff"
                prompt_path = Path(tmpdir) / "review.md"
                output_path = Path(tmpdir) / "deepseek-review.md"
                diff_path.write_text("diff --git a/file b/file\n+hello\n", encoding="utf-8")
                prompt_path.write_text("Review carefully.", encoding="utf-8")

                exit_code = deepseek.run(str(diff_path), str(prompt_path), str(output_path))

                return exit_code, output_path.read_text(encoding="utf-8")

        try:
            validation_gap_exit_code, validation_gap_body = run_with_review(
                """## Codex PR Review

### Blocking findings

No P0/P1 blocking findings found.

### Validation gaps

- Add an integration test for the workflow gate.
"""
            )
            blocking_exit_code, blocking_body = run_with_review(
                """## Codex PR Review

### Blocking findings

- Severity: P1
  File: .github/scripts/deepseek_pr_review.py
  Problem: Blocking findings do not fail the check.

### Validation gaps

None.
"""
            )
        finally:
            deepseek.call_deepseek = previous_call_deepseek
            if previous_api_key is None:
                os.environ.pop("DEEPSEEK_API_KEY", None)
            else:
                os.environ["DEEPSEEK_API_KEY"] = previous_api_key

        self.assertEqual(validation_gap_exit_code, 0)
        self.assertIn("| Recommendation | Review required |", validation_gap_body)
        self.assertIn("| Validation gaps | 1 |", validation_gap_body)
        self.assertEqual(blocking_exit_code, 1)
        self.assertIn("| Recommendation | Changes requested |", blocking_body)
        self.assertIn("| Blocking findings | 1 |", blocking_body)

    def test_workflow_updates_existing_marker_comment(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn('AI_REVIEW_MARKER: "<!-- ai-review:deepseek -->"', workflow)
        self.assertIn("github.rest.issues.listComments", workflow)
        self.assertIn('comment.user?.login === "github-actions[bot]"', workflow)
        self.assertIn("comment.body?.includes(marker)", workflow)
        self.assertIn("github.rest.issues.updateComment", workflow)
        self.assertIn("github.rest.issues.createComment", workflow)


if __name__ == "__main__":
    unittest.main()
