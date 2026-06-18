#!/usr/bin/env python3
"""Review decision policy for AI pull request reviews."""

from __future__ import annotations

import re
from dataclasses import dataclass


PASS_EXIT_CODE = 0
BLOCKING_FINDINGS_EXIT_CODE = 1
# Policy: validation gaps without P0/P1 blocking findings are non-blocking.
# The review comment still says "Review required"; the check remains green.
VALIDATION_GAPS_WITHOUT_BLOCKING_EXIT_CODE = PASS_EXIT_CODE


@dataclass(frozen=True)
class ReviewDecision:
    blocking_findings: int
    validation_gaps: int
    security_review_required: bool
    recommendation: str
    exit_code: int


def markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^#{{1,6}}\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^#{{1,6}}\s+\S|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group("body").strip()


def section_is_empty(section: str) -> bool:
    normalized = re.sub(r"[^a-z0-9/]+", " ", section.lower()).strip()
    return normalized in {"", "none", "n/a", "no", "not applicable"}


def section_says_no_findings(section: str) -> bool:
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


def count_blocking_findings(review: str) -> int:
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


def count_validation_gaps(review: str) -> int:
    section = markdown_section(review, "Validation gaps")
    normalized = re.sub(r"[^a-z0-9/]+", " ", section.lower()).strip()
    no_gap_phrases = {
        "no validation gaps",
        "no gaps",
        "no validation issues",
    }
    if section_is_empty(section) or normalized in no_gap_phrases:
        return 0
    if re.search(r"\bno\b.*\b(validation\s+)?(gaps|issues)\b", section, re.IGNORECASE):
        return 0

    bullet_lines = re.findall(r"^\s*[-*]\s+\S", section, re.MULTILINE)
    return len(bullet_lines) if bullet_lines else 1


def security_review_required(review: str) -> bool:
    section = markdown_section(review, "Security notes")
    if section_is_empty(section):
        return False
    positive_pattern = re.compile(
        r"\b(security\s+review|required|risk|issue|auth|authentication|secret|token|permission|vulnerab)",
        re.IGNORECASE,
    )
    negative_pattern = re.compile(r"\b(no|none|not|doesn['’]?t|does\s+not|without)\b", re.IGNORECASE)

    for line in section.splitlines():
        positive_match = positive_pattern.search(line)
        if positive_match is None:
            continue
        prefix = line[: positive_match.start()]
        if negative_pattern.search(prefix):
            continue
        return True
    return False


def review_recommendation(blocking_findings: int, validation_gaps: int) -> str:
    if blocking_findings:
        return "Changes requested"
    if validation_gaps:
        return "Review required"
    return "No P0/P1 blocking findings found"


def decide_review(review: str) -> ReviewDecision:
    blocking_findings = count_blocking_findings(review)
    validation_gaps = count_validation_gaps(review)
    needs_security_review = security_review_required(review)
    return ReviewDecision(
        blocking_findings=blocking_findings,
        validation_gaps=validation_gaps,
        security_review_required=needs_security_review,
        recommendation=review_recommendation(blocking_findings, validation_gaps),
        exit_code=BLOCKING_FINDINGS_EXIT_CODE
        if blocking_findings
        else VALIDATION_GAPS_WITHOUT_BLOCKING_EXIT_CODE,
    )
