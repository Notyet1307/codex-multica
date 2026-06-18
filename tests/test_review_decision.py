import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / ".github/scripts/review_decision.py"


def load_review_decision_module():
    spec = importlib.util.spec_from_file_location("review_decision", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReviewDecisionTests(unittest.TestCase):
    def test_markdown_section_stops_at_next_heading_regardless_of_level(self) -> None:
        decision = load_review_decision_module()
        review = """## Codex PR Review

### Blocking findings

None.

# Validation gaps

- Add unit tests.
"""

        self.assertEqual(decision.markdown_section(review, "Blocking findings"), "None.")

    def test_count_blocking_findings_treats_empty_variants_as_zero(self) -> None:
        decision = load_review_decision_module()
        variants = ("No blocking findings", "No issues", "None", "N/A", "Nothing blocking")

        for variant in variants:
            with self.subTest(variant=variant):
                review = f"""## Codex PR Review

### Blocking findings

{variant}

### Validation gaps

None.
"""

                self.assertEqual(decision.count_blocking_findings(review), 0)

    def test_count_blocking_findings_detects_p0_p1_variants(self) -> None:
        decision = load_review_decision_module()

        self.assertEqual(
            decision.count_blocking_findings(
                """## Codex PR Review

### Blocking findings

**Severity: P1**
**File/area:** `.github/workflows/deepseek-pr-review.yml`

**Impact:**
- API errors should not be counted as review findings.
"""
            ),
            1,
        )
        self.assertEqual(
            decision.count_blocking_findings(
                """## Codex PR Review

### Blocking findings

1. Severity: P1
   File: .github/workflows/deepseek-pr-review.yml

2. Severity: P0
   File: .github/scripts/deepseek_pr_review.py
"""
            ),
            2,
        )
        self.assertEqual(
            decision.count_blocking_findings(
                """## Codex PR Review

### Blocking findings

No Severity: P0 findings.
"""
            ),
            0,
        )

    def test_decide_review_keeps_validation_gaps_advisory(self) -> None:
        decision = load_review_decision_module()
        result = decision.decide_review(
            """## Codex PR Review

### Blocking findings

No P0/P1 blocking findings found.

### Validation gaps

- Add an integration test for the workflow gate.
"""
        )

        self.assertEqual(result.blocking_findings, 0)
        self.assertEqual(result.validation_gaps, 1)
        self.assertEqual(result.recommendation, "Review required")
        self.assertEqual(result.exit_code, 0)

    def test_count_validation_gaps_treats_no_gap_variants_as_zero(self) -> None:
        decision = load_review_decision_module()
        variants = ("No validation gaps", "No gaps.", "No validation issues.")

        for variant in variants:
            with self.subTest(variant=variant):
                review = f"""## Codex PR Review

### Validation gaps

{variant}
"""

                self.assertEqual(decision.count_validation_gaps(review), 0)

    def test_decide_review_fails_only_for_blocking_findings(self) -> None:
        decision = load_review_decision_module()
        result = decision.decide_review(
            """## Codex PR Review

### Blocking findings

- Severity: P1
  File: .github/scripts/deepseek_pr_review.py
  Problem: Blocking findings do not fail the check.

### Validation gaps

None.

### Security notes

No security-specific concerns.
"""
        )

        self.assertEqual(result.blocking_findings, 1)
        self.assertEqual(result.validation_gaps, 0)
        self.assertEqual(result.security_review_required, False)
        self.assertEqual(result.recommendation, "Changes requested")
        self.assertEqual(result.exit_code, 1)

    def test_security_review_required_does_not_change_exit_code(self) -> None:
        decision = load_review_decision_module()
        result = decision.decide_review(
            """## Codex PR Review

### Blocking findings

No P0/P1 blocking findings found.

### Validation gaps

None.

### Security notes

Security review required because CI permissions changed.
"""
        )

        self.assertTrue(result.security_review_required)
        self.assertEqual(result.exit_code, 0)

    def test_security_review_required_handles_no_content_and_mixed_content(self) -> None:
        decision = load_review_decision_module()

        self.assertFalse(
            decision.security_review_required(
                """## Codex PR Review

### Security notes

None.
"""
            )
        )
        self.assertFalse(
            decision.security_review_required(
                """## Codex PR Review

### Security notes

No security-specific concerns.
"""
            )
        )
        self.assertTrue(
            decision.security_review_required(
                """## Codex PR Review

### Security notes

Security review required because CI permissions changed.
"""
            )
        )

    def test_security_review_required_handles_negative_security_bullets(self) -> None:
        decision = load_review_decision_module()

        result = decision.decide_review(
            """## Codex PR Review

### Blocking findings

No P0/P1 blocking findings found.

### Validation gaps

None.

### Security notes

- The `review_decision.py` module doesn't handle any sensitive data or authentication
- The refactoring doesn't introduce new security concerns
- No secrets, tokens, or permissions are handled in the new module
"""
        )

        self.assertFalse(result.security_review_required)

    def test_security_review_required_handles_mixed_negative_and_positive_lines(self) -> None:
        decision = load_review_decision_module()

        negative_result = decision.decide_review(
            """## Codex PR Review

### Security notes


- No auth changes.
- This doesn't handle auth, secrets, tokens, or permissions.
- No security issues.
"""
        )
        positive_result = decision.decide_review(
            """## Codex PR Review

### Security notes

- No auth changes in the parser itself.
- Security review required because CI permissions changed.
"""
        )

        self.assertFalse(negative_result.security_review_required)
        self.assertTrue(positive_result.security_review_required)


if __name__ == "__main__":
    unittest.main()
