#!/usr/bin/env python3
"""Convert a planning intake spec into local Multica issue draft files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


REQUIRED_SPEC_SECTIONS = (
    "Goal",
    "Background",
    "Current State",
    "Desired Behavior",
    "Non-goals",
    "Constraints",
    "Validation",
)

ISSUE_REQUIRED_HEADINGS = (
    "Goal",
    "Context",
    "Scope",
    "Non-goals",
    "Acceptance criteria",
    "Agent routing",
    "Suggested validation",
    "Stop conditions",
)

SLICE_HEADING_PATTERN = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
SAFE_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")
PLACEHOLDER_PATTERN = re.compile(r"<[^>\n]+>")
HIGH_RISK_PATTERNS = (
    re.compile(r"\bsecret(?:s)?\b"),
    re.compile(r"\bcredential(?:s)?\b"),
    re.compile(r"\b(?:auth|authentication|authorization|authz)\b"),
    re.compile(r"\bproduction\b"),
    re.compile(r"\bmigration(?:s)?\b"),
    re.compile(r"\bpii\b"),
    re.compile(r"\bpayment(?:s)?\b"),
    re.compile(r"\blive\s+write(?:s)?\b"),
)
MEDIUM_RISK_PATTERNS = (
    re.compile(r"\bapi(?:s)?\b"),
    re.compile(r"\bworkflow(?:s)?\b"),
    re.compile(r"\b(?:dependency|dependencies)\b"),
    re.compile(r"\bci\b"),
    re.compile(r"\bsecurity\b"),
    re.compile(r"\bruntime\b"),
    re.compile(r"\bdatabase(?:s)?\b"),
)


@dataclass(frozen=True)
class IntakeSpec:
    title: str
    source_path: Path
    sections: dict[str, str]
    source_hash: str


@dataclass(frozen=True)
class IssueSlice:
    title: str
    body: str
    index: int


@dataclass(frozen=True)
class DraftIssue:
    title: str
    filename: str
    body: str
    warnings: list[str]


def normalize_heading(heading: str) -> str:
    return re.sub(r"\s+", " ", heading.strip())


def slugify(value: str) -> str:
    slug = SAFE_SLUG_PATTERN.sub("-", value.lower()).strip("-")
    return slug[:80] or "issue-draft"


def clean_slice_title(title: str) -> str:
    cleaned = re.sub(r"^slice\s+\d+\s*[:.-]\s*", "", title.strip(), flags=re.IGNORECASE)
    return cleaned or title.strip()


def parse_intake_spec(path: Path) -> IntakeSpec:
    text = path.read_text(encoding="utf-8")
    title = path.stem.replace("-", " ").strip().title()
    sections: dict[str, str] = {}

    matches = list(HEADING_PATTERN.finditer(text))
    for index, match in enumerate(matches):
        level = len(match.group(1))
        heading = normalize_heading(match.group(2))
        start = match.end()
        end = len(text)
        for next_match in matches[index + 1 :]:
            next_level = len(next_match.group(1))
            if level == 1 or next_level <= level:
                end = next_match.start()
                break
        body = text[start:end].strip()
        if level == 1 and heading:
            title = heading
        elif level == 2:
            sections[heading.lower()] = body

    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return IntakeSpec(title=title, source_path=path, sections=sections, source_hash=source_hash)


def section(spec: IntakeSpec, name: str) -> str:
    return spec.sections.get(name.lower(), "").strip()


def missing_sections(spec: IntakeSpec) -> list[str]:
    return [name for name in REQUIRED_SPEC_SECTIONS if not section(spec, name)]


def placeholder_warnings(spec: IntakeSpec) -> list[str]:
    warnings: list[str] = []
    if PLACEHOLDER_PATTERN.search(spec.title):
        warnings.append("source spec title contains placeholder text")
    for name, body in spec.sections.items():
        if PLACEHOLDER_PATTERN.search(body):
            warnings.append(f"source spec section contains placeholder text: {name}")
    return warnings


def extract_slices(spec: IntakeSpec) -> list[IssueSlice]:
    suggested = section(spec, "Suggested Slices")
    if not suggested:
        return [IssueSlice(title=spec.title, body="", index=1)]

    matches = list(SLICE_HEADING_PATTERN.finditer(suggested))
    if not matches:
        return [IssueSlice(title=spec.title, body=suggested, index=1)]

    slices: list[IssueSlice] = []
    for index, match in enumerate(matches, start=1):
        start = match.end()
        end = matches[index].start() if index < len(matches) else len(suggested)
        slices.append(IssueSlice(title=clean_slice_title(match.group(1)), body=suggested[start:end].strip(), index=index))
    return slices


def list_or_todo(text: str, fallback: str) -> str:
    if text.strip():
        return text.strip()
    return f"- TODO: {fallback}"


def infer_risk(spec: IntakeSpec) -> str:
    risk_text = " ".join(
        [
            section(spec, "Risks"),
            section(spec, "Constraints"),
            section(spec, "Proposed Approach"),
        ]
    ).lower()
    if any(pattern.search(risk_text) for pattern in HIGH_RISK_PATTERNS):
        return "risk:high"
    if any(pattern.search(risk_text) for pattern in MEDIUM_RISK_PATTERNS):
        return "risk:medium"
    return "risk:low"


def build_issue_body(spec: IntakeSpec, issue_slice: IssueSlice, warnings: list[str]) -> str:
    goal_text = issue_slice.body or section(spec, "Desired Behavior") or section(spec, "Goal")
    scope_text = issue_slice.body or section(spec, "Proposed Approach")
    validation_text = section(spec, "Validation")
    risk = infer_risk(spec)
    warning_block = "\n".join(f"- {warning}" for warning in warnings) if warnings else "- None"

    return "\n".join(
        [
            f"# {issue_slice.title}",
            "",
            "## Goal",
            "",
            list_or_todo(goal_text, "state the concrete user/operator/developer outcome"),
            "",
            "## Context",
            "",
            f"- Source intake spec: `{spec.source_path.as_posix()}`",
            f"- Source spec SHA-256: `{spec.source_hash}`",
            "- Background:",
            list_or_todo(section(spec, "Background"), "summarize why this matters now"),
            "- Current state:",
            list_or_todo(section(spec, "Current State"), "summarize verified current state before implementation"),
            "- Links / evidence:",
            list_or_todo(section(spec, "Links / Evidence"), "add relevant links, files, screenshots, logs, or PRs"),
            "",
            "## Scope",
            "",
            "In scope:",
            list_or_todo(scope_text, "define the smallest reviewable slice"),
            "",
            "## Non-goals",
            "",
            list_or_todo(section(spec, "Non-goals"), "state what must not be changed"),
            "",
            "## Acceptance criteria",
            "",
            "- [ ] Goal is satisfied for this slice.",
            "- [ ] Scope and non-goals are respected.",
            "- [ ] Required validation passes or skipped checks are explicitly documented.",
            "",
            "## Agent routing",
            "",
            "Readiness: needs-scoper-review",
            "Type: type:planning",
            f"Risk: {risk}",
            "Suggested agent: agent:scoper",
            "",
            "## Technical notes",
            "",
            "- Proposed approach:",
            list_or_todo(section(spec, "Proposed Approach"), "add implementation notes after scoper review"),
            "- Constraints:",
            list_or_todo(section(spec, "Constraints"), "add technical, security, data, cost, timing, and workflow constraints"),
            "",
            "## Security and privacy notes",
            "",
            "- Auth/authz touched: unknown until scoper review",
            "- PII/secrets/logging touched: unknown until scoper review",
            "- Dependencies touched: unknown until scoper review",
            "- CI/CD touched: unknown until scoper review",
            f"- Risk level: {risk.removeprefix('risk:')}",
            "",
            "## Suggested validation",
            "",
            list_or_todo(validation_text, "define command or manual validation before implementation starts"),
            "",
            "## Stop conditions",
            "",
            "Stop and ask a human if:",
            "- implementation would require live Multica writes or automatic issue creation",
            "- required facts from the intake spec cannot be verified from repository, issue, PR, or linked evidence",
            "- scope would expand beyond this draft issue",
            "- secrets, credentials, production data, customer data, or browser session state are required",
            "- security, migration, product direction, or architecture decisions are unclear",
            "",
            "## Draft quality warnings",
            "",
            warning_block,
            "",
        ]
    )


def validate_draft_issue(body: str) -> list[str]:
    warnings: list[str] = []
    for heading in ISSUE_REQUIRED_HEADINGS:
        if f"## {heading}" not in body:
            warnings.append(f"missing issue heading: {heading}")
    if "TODO:" in body:
        warnings.append("contains TODO placeholders")
    return warnings


def build_draft_issues(spec: IntakeSpec) -> list[DraftIssue]:
    spec_warnings = [f"source spec missing section: {name}" for name in missing_sections(spec)] + placeholder_warnings(spec)
    drafts: list[DraftIssue] = []
    for issue_slice in extract_slices(spec):
        body = build_issue_body(spec, issue_slice, spec_warnings)
        warnings = spec_warnings + validate_draft_issue(body)
        filename = f"{issue_slice.index:02d}-{slugify(issue_slice.title)}.md"
        drafts.append(DraftIssue(title=issue_slice.title, filename=filename, body=body, warnings=warnings))
    return drafts


def write_drafts(drafts: Sequence[DraftIssue], output_dir: Path, spec: IntakeSpec) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_spec": spec.source_path.as_posix(),
        "source_sha256": spec.source_hash,
        "draft_count": len(drafts),
        "drafts": [],
    }
    for draft in drafts:
        path = output_dir / draft.filename
        path.write_text(draft.body, encoding="utf-8")
        manifest["drafts"].append(
            {
                "title": draft.title,
                "path": path.as_posix(),
                "warnings": draft.warnings,
            }
        )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Path to the GPT Pro/project intake Markdown spec.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated issue draft files.")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Exit non-zero when generated drafts have warnings.")
    args = parser.parse_args(argv)

    spec_path = Path(args.spec).resolve()
    output_dir = Path(args.output_dir).resolve()
    if not spec_path.is_file():
        print(f"ERROR: intake spec does not exist: {spec_path}", file=sys.stderr)
        return 1

    spec = parse_intake_spec(spec_path)
    drafts = build_draft_issues(spec)
    manifest_path = write_drafts(drafts, output_dir, spec)

    print(f"Wrote {len(drafts)} issue draft(s) to {output_dir}")
    print(f"Wrote manifest to {manifest_path}")
    warning_count = sum(len(draft.warnings) for draft in drafts)
    if warning_count:
        print(f"Warnings: {warning_count}")
        for draft in drafts:
            for warning in draft.warnings:
                print(f"WARNING: {draft.filename}: {warning}")
        return 2 if args.fail_on_warnings else 0
    print("Draft quality check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
