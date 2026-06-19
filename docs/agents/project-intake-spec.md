# Project Intake Spec

Use this template when discussing a new project, feature, or larger change with
GPT Pro before asking Codex to turn the result into Multica issues.

The output from GPT Pro is a planning artifact, not an implementation order.
Codex must still verify repository state, separate facts from assumptions, add
scope boundaries, and produce Multica-ready issue drafts before any agent starts
implementation.

## How To Use

1. Ask GPT Pro to fill this template.
2. Save the result as a Markdown file.
3. Ask Codex to review and convert it:

   ```text
   Use ask-matt / spec-first-intake on this intake spec. Do not implement.
   Generate Multica issue drafts with scope, non-goals, acceptance criteria,
   allowed files or areas, validation, risk/HITL classification, stop
   conditions, and suggested assignee.
   ```

4. Run the local draft generator:

   ```bash
   python3 scripts/intake_to_issue_drafts.py --spec <spec.md> --output-dir artifacts/issues/<topic>
   ```

5. Review the generated draft issues before copying them into Multica.

This first-version flow does not create Multica issues or call a Multica write
API. Live issue creation must remain a separate human-confirmed workflow.

## Template

# <Project or Feature Name>

## Goal

What should change for users, operators, or developers?

## Background

Why is this worth doing now?

## Current State

What already exists? Include repositories, docs, PRs, issues, screenshots,
logs, and known constraints.

## Desired Behavior

What should be true after the work is complete?

## Non-goals

What should not be done in this effort?

## Constraints

List technical, security, data, cost, timing, workflow, and review constraints.

## Proposed Approach

Describe the recommended approach. Include alternatives only when they affect
scope or risk.

## Risks

List known risks, uncertain assumptions, and decisions that may need human
input.

## Validation

How should a human or agent prove the work is correct? Include commands,
manual checks, PR checks, browser checks, or expected evidence.

## Suggested Slices

Use one `###` heading per possible issue. Keep these rough; Codex will refine
them.

### Slice 1: <Short outcome-oriented title>

- Goal:
- Scope:
- Acceptance criteria:
- Validation:
- Dependencies:

### Slice 2: <Short outcome-oriented title>

- Goal:
- Scope:
- Acceptance criteria:
- Validation:
- Dependencies:

## Links / Evidence

- 

