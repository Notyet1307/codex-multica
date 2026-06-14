import importlib.util
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

    def test_workflow_updates_existing_marker_comment(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn('AI_REVIEW_MARKER: "<!-- ai-review:deepseek -->"', workflow)
        self.assertIn("github.rest.issues.listComments", workflow)
        self.assertIn("comment.body?.includes(marker)", workflow)
        self.assertIn("github.rest.issues.updateComment", workflow)
        self.assertIn("github.rest.issues.createComment", workflow)


if __name__ == "__main__":
    unittest.main()
