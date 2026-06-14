---
name: tdd-vertical-slice
description: Use for feature or bug-fix implementation where behavior can be tested. Guides the agent through one failing test, minimal implementation, green test, refactor, and repeat using thin vertical slices.
---

# TDD Vertical Slice

## Use when

- Building a new feature.
- Fixing a bug with a testable reproduction.
- Adding behavior across API, service, database, and UI.
- The user asks for TDD, regression tests, or test-first development.

## Do not use when

- Pure documentation change.
- Mechanical formatting.
- Exploratory spike where no stable behavior exists yet.
- Emergency production mitigation where speed overrides test-first discipline; document why.

## Workflow

1. Read the issue and `AGENTS.md`.
2. Identify the smallest user-visible or API-visible behavior slice.
3. Define the public interface to test through.
4. Write one failing test for that slice.
5. Run only the relevant test; confirm failure reason.
6. Implement the minimum code to pass.
7. Run the test again; confirm green.
8. Run nearby tests.
9. Refactor only while green.
10. Repeat until acceptance criteria are satisfied.

## Rules

- One behavior per cycle.
- Tests should assert observable behavior, not private implementation.
- Avoid broad mocks of internals.
- Do not add speculative generality.
- Do not silently skip tests. If a test cannot be written, explain the missing seam.

## Output

When done, report:

```md
## TDD summary
- First failing test:
- Implemented behavior:
- Tests added/changed:
- Commands run:
- Refactors performed:
- Remaining test gaps:
```
