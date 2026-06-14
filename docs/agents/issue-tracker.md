# Issue Tracker Rules

Primary tracker: Multica.

## Issue ID convention

- Format: `<PREFIX>-<NUMBER>`, for example `MUL-123`.
- Every branch, PR title, or PR body must include the issue ID so Multica can link the PR.

## Branch naming

```text
agent/<ISSUE-ID>-<short-slug>
feature/<ISSUE-ID>-<short-slug>
fix/<ISSUE-ID>-<short-slug>
security/<ISSUE-ID>-<short-slug>
```

## Issue quality standard

A ready issue includes:

- Goal
- Background/context
- Acceptance criteria
- Constraints/non-goals
- Suggested validation
- Risk level
- Suggested agent or squad

## Agent brief

When handing work to an agent, include:

```md
## Agent brief
Issue: <ISSUE-ID>
Role: <scoper/frontend/backend/test/security/fullstack/release>

### Goal

### Context

### Files likely involved

### Constraints

### Acceptance criteria

### Validation commands

### Risk notes

### Stop conditions
```
