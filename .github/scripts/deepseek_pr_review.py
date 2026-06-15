#!/usr/bin/env python3
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request


DEFAULT_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"
AI_REVIEW_MARKER = "<!-- ai-review:deepseek -->"
PROVIDER_NAME = "DeepSeek"
REVIEWER_SYSTEM_PROMPT = "You are a pragmatic senior code reviewer. Prioritize correctness, security, data loss, broken CI, and missing validation."
PASS_EXIT_CODE = 0
BLOCKING_FINDINGS_EXIT_CODE = 1
OPERATIONAL_FAILURE_EXIT_CODE = 2
VALIDATION_GAPS_WITHOUT_BLOCKING_EXIT_CODE = PASS_EXIT_CODE


def build_payload(diff_text, prompt_text, model):
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": REVIEWER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"{prompt_text}\n\nReview this PR diff:\n\n```diff\n{diff_text}\n```",
            },
        ],
        "thinking": {"type": "disabled"},
        "stream": False,
    }


def call_deepseek(payload, api_key, api_url):
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API request failed: HTTP {error.code}: {detail}")


def extract_review(response):
    try:
        return response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"DeepSeek API response did not include review content: {error}")


def markdown_section(text, heading):
    pattern = re.compile(
        rf"^#{{1,6}}\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^#{{1,6}}\s+\S|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group("body").strip()


def section_is_empty(section):
    normalized = re.sub(r"[^a-z0-9/]+", " ", section.lower()).strip()
    return normalized in {"", "none", "n/a", "no", "not applicable"}


def section_says_no_findings(section):
    normalized = re.sub(r"[^a-z0-9/]+", " ", section.lower()).strip()
    no_finding_phrases = {
        "no blocking findings",
        "no issues",
        "nothing blocking",
        "no findings",
        "no blocking issues",
    }
    if section_is_empty(section) or normalized in no_finding_phrases:
        return True
    return bool(re.search(r"\bno\b.*\bp[01]\b.*\b(findings|issues)\b", section, re.IGNORECASE))


def count_blocking_findings(review):
    section = markdown_section(review, "Blocking findings")
    if section_says_no_findings(section) or re.search(r"no\s+p0/p1\s+blocking\s+findings\s+found", section, re.IGNORECASE):
        return 0

    severity_lines = re.findall(
        r"^\s*(?:[-*]\s*|\d+\.\s*)?(?:\*\*)?Severity:\s*P[01]\b",
        section,
        re.IGNORECASE | re.MULTILINE,
    )
    if severity_lines:
        return len(severity_lines)

    bullet_lines = re.findall(r"^\s*[-*]\s+\S", section, re.MULTILINE)
    return len(bullet_lines) if bullet_lines else 1


def count_validation_gaps(review):
    section = markdown_section(review, "Validation gaps")
    if section_is_empty(section):
        return 0

    bullet_lines = re.findall(r"^\s*[-*]\s+\S", section, re.MULTILINE)
    return len(bullet_lines) if bullet_lines else 1


def security_review_required(review):
    section = markdown_section(review, "Security notes")
    if section_is_empty(section):
        return False
    if re.search(r"\b(no|none|not)\b.*\b(security|concern|required|risk|issue)s?\b", section, re.IGNORECASE):
        return False
    return bool(re.search(r"\b(required|review|risk|issue|auth|secret|token|permission|vulnerab)", section, re.IGNORECASE))


def review_recommendation(blocking_findings, validation_gaps):
    if blocking_findings:
        return "Changes requested"
    if validation_gaps:
        return "Review required"
    return "No P0/P1 blocking findings found"


def review_exit_code(review):
    if count_blocking_findings(review):
        return BLOCKING_FINDINGS_EXIT_CODE
    return VALIDATION_GAPS_WITHOUT_BLOCKING_EXIT_CODE


def format_review_body(review):
    review = review.strip()
    blocking_findings = count_blocking_findings(review)
    validation_gaps = count_validation_gaps(review)
    needs_security_review = security_review_required(review)
    recommendation = review_recommendation(blocking_findings, validation_gaps)

    summary = "\n".join(
        [
            "| Field | Value |",
            "| --- | --- |",
            f"| Provider | {PROVIDER_NAME} |",
            f"| Recommendation | {recommendation} |",
            f"| Blocking findings | {blocking_findings} |",
            f"| Validation gaps | {validation_gaps} |",
            f"| Security review required | {'Yes' if needs_security_review else 'No'} |",
        ]
    )

    return f"{AI_REVIEW_MARKER}\n## DeepSeek PR Review\n\n{summary}\n\n{review}\n"


def run(diff_path, prompt_path, output_path):
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is required")

    model = os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)
    api_url = os.environ.get("DEEPSEEK_API_URL", DEFAULT_API_URL)

    with open(diff_path, "r", encoding="utf-8", errors="replace") as file:
        diff_text = file.read()

    with open(prompt_path, "r", encoding="utf-8", errors="replace") as file:
        prompt_text = file.read()

    payload = build_payload(diff_text, prompt_text, model)
    response = call_deepseek(payload, api_key, api_url)
    review = extract_review(response)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(format_review_body(review))

    return review_exit_code(review)


def self_test():
    payload = build_payload("diff --git a/file b/file\n+hello\n", "Review carefully.", DEFAULT_MODEL)
    assert payload["model"] == DEFAULT_MODEL
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["stream"] is False
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][0]["content"] == REVIEWER_SYSTEM_PROMPT
    assert payload["messages"][1]["role"] == "user"
    assert "Review carefully." in payload["messages"][1]["content"]
    assert "```diff" in payload["messages"][1]["content"]
    assert extract_review({"choices": [{"message": {"content": "Looks good."}}]}) == "Looks good."
    review_body = format_review_body(
        """## Codex PR Review

### Blocking findings

No P0/P1 blocking findings found.

### Validation gaps

None.

### Security notes

No security-specific concerns.
"""
    )
    assert review_body.startswith(f"{AI_REVIEW_MARKER}\n")
    assert "| Provider | DeepSeek |" in review_body
    assert "| Blocking findings | 0 |" in review_body
    assert (
        count_blocking_findings(
            """## Codex PR Review

### Blocking findings

**Severity: P1**
**File/area:** `.github/workflows/deepseek-pr-review.yml`

**Impact:**
- API errors should not be counted as review findings.
- File errors should not be counted as review findings.
"""
        )
        == 1
    )
    assert (
        count_blocking_findings(
            """## Codex PR Review

### Blocking findings

1. Severity: P1
   File: .github/workflows/deepseek-pr-review.yml

2. Severity: P0
   File: .github/scripts/deepseek_pr_review.py
"""
        )
        == 2
    )
    assert (
        count_blocking_findings(
            """## Codex PR Review

### Blocking findings

No Severity: P0 findings.
"""
        )
        == 0
    )

    def run_with_review(review):
        previous_api_key = os.environ.get("DEEPSEEK_API_KEY")
        previous_call_deepseek = globals()["call_deepseek"]
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        def fake_call_deepseek(payload, api_key, api_url):
            assert api_key == "test-key"
            return {"choices": [{"message": {"content": review}}]}

        globals()["call_deepseek"] = fake_call_deepseek
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                diff_path = os.path.join(tmpdir, "pr.diff")
                prompt_path = os.path.join(tmpdir, "review.md")
                output_path = os.path.join(tmpdir, "deepseek-review.md")
                with open(diff_path, "w", encoding="utf-8") as file:
                    file.write("diff --git a/file b/file\n+hello\n")
                with open(prompt_path, "w", encoding="utf-8") as file:
                    file.write("Review carefully.")

                exit_code = run(diff_path, prompt_path, output_path)

                with open(output_path, "r", encoding="utf-8") as file:
                    return exit_code, file.read()
        finally:
            globals()["call_deepseek"] = previous_call_deepseek
            if previous_api_key is None:
                os.environ.pop("DEEPSEEK_API_KEY", None)
            else:
                os.environ["DEEPSEEK_API_KEY"] = previous_api_key

    clean_exit_code, clean_body = run_with_review(
        """## Codex PR Review

### Blocking findings

No P0/P1 blocking findings found.

### Validation gaps

None.
"""
    )
    assert clean_exit_code == 0
    assert "| Recommendation | No P0/P1 blocking findings found |" in clean_body
    assert "| Blocking findings | 0 |" in clean_body

    validation_gap_exit_code, validation_gap_body = run_with_review(
        """## Codex PR Review

### Blocking findings

No P0/P1 blocking findings found.

### Validation gaps

- Add an integration test for the workflow gate.
"""
    )
    assert validation_gap_exit_code == 0
    assert "| Recommendation | Review required |" in validation_gap_body
    assert "| Validation gaps | 1 |" in validation_gap_body

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
    assert blocking_exit_code == 1
    assert "| Recommendation | Changes requested |" in blocking_body
    assert "| Blocking findings | 1 |" in blocking_body

    previous_argv = sys.argv
    previous_api_key = os.environ.get("DEEPSEEK_API_KEY")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            diff_path = os.path.join(tmpdir, "pr.diff")
            prompt_path = os.path.join(tmpdir, "review.md")
            output_path = os.path.join(tmpdir, "deepseek-review.md")
            with open(diff_path, "w", encoding="utf-8") as file:
                file.write("diff --git a/file b/file\n+hello\n")
            with open(prompt_path, "w", encoding="utf-8") as file:
                file.write("Review carefully.")

            os.environ.pop("DEEPSEEK_API_KEY", None)
            sys.argv = ["deepseek_pr_review.py", diff_path, prompt_path, output_path]

            with contextlib.redirect_stderr(io.StringIO()):
                assert main() == 2
            assert not os.path.exists(output_path)
    finally:
        sys.argv = previous_argv
        if previous_api_key is None:
            os.environ.pop("DEEPSEEK_API_KEY", None)
        else:
            os.environ["DEEPSEEK_API_KEY"] = previous_api_key


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return 0

    if len(sys.argv) != 4:
        print(
            "Usage: deepseek_pr_review.py <diff-path> <prompt-path> <output-path>",
            file=sys.stderr,
        )
        return 2

    try:
        return run(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return OPERATIONAL_FAILURE_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
