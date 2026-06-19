#!/usr/bin/env python3
"""Validate a project intake spec before ask-matt/spec-first-intake review."""

from __future__ import annotations

import argparse
import hashlib
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
    "Proposed Approach",
    "Risks",
    "Validation",
    "Suggested Slices",
)

REQUIRED_SLICE_FIELDS = (
    "Goal",
    "Scope",
    "Acceptance criteria",
    "Validation",
    "Stop conditions",
)

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
SLICE_HEADING_PATTERN = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
PLACEHOLDER_PATTERN = re.compile(r"<[^>\n]+>")
TODO_PATTERN = re.compile(r"\bTODO\b", re.IGNORECASE)


@dataclass(frozen=True)
class IntakeSpec:
    title: str
    source_path: Path
    sections: dict[str, str]
    source_hash: str


@dataclass(frozen=True)
class IntakeSlice:
    title: str
    body: str
    index: int


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]


def normalize_heading(heading: str) -> str:
    return re.sub(r"\s+", " ", heading.strip())


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


def extract_slices(spec: IntakeSpec) -> list[IntakeSlice]:
    suggested = section(spec, "Suggested Slices")
    if not suggested:
        return []

    matches = list(SLICE_HEADING_PATTERN.finditer(suggested))
    slices: list[IntakeSlice] = []
    for index, match in enumerate(matches, start=1):
        start = match.end()
        end = matches[index].start() if index < len(matches) else len(suggested)
        slices.append(IntakeSlice(title=match.group(1).strip(), body=suggested[start:end].strip(), index=index))
    return slices


def has_placeholder(text: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.search(text))


def has_todo(text: str) -> bool:
    return bool(TODO_PATTERN.search(text))


def slice_field_value(intake_slice: IntakeSlice, field_name: str) -> str | None:
    pattern = re.compile(
        rf"^[ \t]*[-*][ \t]*{re.escape(field_name)}[ \t]*:[ \t]*(.*?)[ \t]*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(intake_slice.body)
    if not match:
        return None
    return match.group(1).strip()


def validate_spec(spec: IntakeSpec) -> ValidationResult:
    errors: list[str] = []

    if has_placeholder(spec.title):
        errors.append("title contains placeholder text")
    if has_todo(spec.title):
        errors.append("title contains TODO placeholder")

    for section_name in REQUIRED_SPEC_SECTIONS:
        body = section(spec, section_name)
        if not body:
            errors.append(f"missing required section: {section_name}")
            continue
        if has_placeholder(body):
            errors.append(f"section contains placeholder text: {section_name}")
        if has_todo(body):
            errors.append(f"section contains TODO placeholder: {section_name}")

    slices = extract_slices(spec)
    if section(spec, "Suggested Slices") and not slices:
        errors.append("Suggested Slices must contain at least one level-3 slice heading")

    for intake_slice in slices:
        if has_placeholder(intake_slice.title):
            errors.append(f"slice {intake_slice.index} title contains placeholder text")
        if has_todo(intake_slice.title):
            errors.append(f"slice {intake_slice.index} title contains TODO placeholder")
        for field_name in REQUIRED_SLICE_FIELDS:
            value = slice_field_value(intake_slice, field_name)
            if value is None:
                errors.append(f"slice {intake_slice.index} missing required field: {field_name}")
            elif not value:
                errors.append(f"slice {intake_slice.index} has empty required field: {field_name}")
            elif has_placeholder(value):
                errors.append(f"slice {intake_slice.index} field contains placeholder text: {field_name}")
            elif has_todo(value):
                errors.append(f"slice {intake_slice.index} field contains TODO placeholder: {field_name}")

    return ValidationResult(errors=errors)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Path to the GPT Pro/project intake Markdown spec.")
    args = parser.parse_args(argv)

    spec_path = Path(args.spec).resolve()
    if not spec_path.is_file():
        print(f"ERROR: intake spec does not exist: {spec_path}")
        return 1

    spec = parse_intake_spec(spec_path)
    result = validate_spec(spec)
    if result.errors:
        print(f"Intake spec validation failed: {spec_path}")
        for error in result.errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: intake spec is structurally ready for ask-matt/spec-first-intake review: {spec_path}")
    print(f"Source spec SHA-256: {spec.source_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
