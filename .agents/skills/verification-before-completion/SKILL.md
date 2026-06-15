---
name: verification-before-completion
description: Use before an agent claims work is done, complete, ready for review, ready to merge, validated, passing, or needing no further work.
---

# Verification Before Completion

Use this skill as an evidence gate before making completion claims. A task is
not complete because an agent says it is complete; it is complete, ready for
review, blocked, or in need of correction based on current evidence.

## When to use

Use this skill before claiming:

- done
- complete
- ready for review
- ready to merge
- validation passed
- no further work is needed
- a Multica issue, GitHub PR, branch, or delegated task is ready for the next
  owner

## When not to use

Do not use this skill:

- before implementation or debugging starts
- as a substitute for `spec-first-intake`, `tdd-vertical-slice`,
  `systematic-debugging`, or `security-pr-review`
- to bypass missing validation, failing checks, unclear CI, or human review
- to approve final merge, production deployment, security exceptions, or
  product direction

## Design references

This skill adapts small workflow ideas from mature agent workflows and local
skills:

- mattpocock/skills: short handoff-style reports that reference existing
  artifacts instead of duplicating all context.
- gstack-style command workflows: fixed command boundaries, explicit stop
  conditions, and structured completion output contracts.
- Superpowers workflow discipline: implementation is not complete until the
  planned validation and review evidence has been checked.
- Open SWE reviewer pattern: implementation and review are separate, and the
  worker should not be the only source of completion truth.
- PR-Agent style review summaries: concise changed-file, validation-gap,
  security-note, and risk/rollback evidence.
- Existing local skills: `spec-first-intake`, `systematic-debugging`,
  `security-pr-review`, and `tdd-vertical-slice` provide the local intake,
  debugging, security, and implementation conventions.

Do not copy third-party files, skill text, prompts, scripts, hooks, installers,
dependencies, or global state. Do not add external tools. Do not import
PR-Agent, Repomix, Open SWE, gstack, Superpowers, or third-party skill
repositories. Adapt only the smallest useful workflow ideas into repo-local
instructions.

## Completion gate workflow

1. Identify the issue or task reference.
2. Identify the branch and PR when available.
3. Read the latest handoff, issue scope, PR body, or task acceptance criteria.
4. List changed files using `git diff --name-only origin/main...HEAD` or the
   equivalent comparison for the task branch.
5. Compare changed files against allowed files or allowed areas.
6. Check acceptance criteria one by one.
7. List validation commands actually run and their results.
8. Report CI status when a PR exists.
9. Report known failures, skipped checks, or unavailable checks.
10. Check whether the change touches security-sensitive surfaces.
11. If security-sensitive surfaces are touched, require `security-pr-review`
    before completion or merge unless the issue is explicitly review-only.
12. Decide exactly one completion state: complete, ready for review, needs
    correction, or blocked.
13. Return the fixed Completion report.

## Evidence requirements

The completion report must include:

- issue or task reference
- branch or PR reference when available
- changed-file evidence
- scope comparison against allowed files or allowed areas
- acceptance criteria status
- validation commands and results
- CI status when a PR exists
- known failures
- skipped checks
- security-sensitive surface check
- whether security review is required
- whether follow-up issues are needed
- final completion decision

## Scope check

Changed-file evidence is required. Use `git diff --name-only origin/main...HEAD`
when the branch is based on `origin/main`; otherwise name the exact command used
and why.

Compare the changed-file output against the allowed files or allowed areas from
the issue, handoff, or PR. If changed files exceed the allowed scope, do not
claim ready for review. Mark the result as needs correction or blocked.

## Validation check

List only commands that were actually run for the current branch or task state.
For each command, include pass, fail, skipped, or unavailable. If a required
validation command cannot be run, explain why and do not claim complete unless
the issue explicitly allows that validation to be skipped.

Do not weaken tests, bypass validation, remove checks, or hide failures to make
completion easier.

## CI check

If a PR exists, report CI status from the PR, GitHub, or Multica-linked PR
state. Include pending, failed, passed, unavailable, or not configured.

If CI is failing for unclear reasons, mark the completion decision as blocked
or needs correction. If no PR exists, report CI status as not applicable and say
why.

## Security-sensitive check

Treat these surfaces as security-sensitive:

- auth or authorization
- tenancy or permissions
- secrets or tokens
- PII or customer confidential data
- dependency changes
- GitHub Actions or CI permissions
- file upload or file handling
- outbound network calls
- database queries or migrations
- logging of sensitive data
- admin or privileged operations

If any security-sensitive surface is touched, Security review required must be
yes unless the issue explicitly scopes a review-only task. Security-sensitive
work must not bypass `security-pr-review` before completion or merge.

## Completion decision

Choose exactly one:

- complete: acceptance criteria, scope, validation, CI, and security review
  requirements are satisfied, and no PR or human review remains.
- ready for review: implementation evidence is sufficient, and human or PR
  review is the next step.
- needs correction: the agent can make a scoped fix before review.
- blocked: progress requires a human decision, unavailable access, unclear CI,
  production data, security review, or files outside the allowed scope.

## Stop conditions

Stop and ask a human or route to the right reviewer if:

- changed files exceed allowed files or allowed areas
- required validation cannot be run
- validation fails and the agent cannot identify a scoped fix
- CI is failing for unclear reasons
- security-sensitive changes lack `security-pr-review`
- production access is required
- secrets, customer data, or production data are required
- a migration may cause data loss
- product behavior has multiple reasonable interpretations
- completion would require bypassing validation or weakening tests

## Output contract

Return exactly this report shape when using this skill:

## Completion report

- Issue:
- PR:
- Branch:
- Completion decision:
- Changed files:
- Scope check:
- Acceptance criteria:
- Validation commands:
- Validation results:
- CI status:
- Known failures:
- Skipped checks:
- Security-sensitive surfaces touched:
- Security review required:
- Follow-up issues needed:
- Ready for human review:
- Notes:
