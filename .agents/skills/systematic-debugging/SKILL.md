---
name: systematic-debugging
description: Use when CI, local tests, builds, lint, typecheck, reproduced product defects, flaky failures, or environment-dependent failures need diagnosis, root cause evidence, and a safe repair decision.
---

# Systematic Debugging

Use this skill to turn a failing signal into a reproducible diagnosis, a minimal
repair, and a clear evidence trail. Keep the work bounded to the failure being
debugged.

## When To Use

Use for:

- CI failures and GitHub Actions failures
- local test failures
- build failures
- lint failures
- typecheck failures
- reproduced product defects
- flaky failures
- environment-dependent, cache-dependent, or dependency-dependent failures

Do not use for:

- vague feature requests that still need scoping
- code review without a reproduced failure
- broad architecture cleanup
- production incident response that requires live production access
- security policy exception decisions

## Design References

- `AGENTS.md` debugging mode is the operating baseline.
- Former CI-specific triage responsibilities are folded into this skill.
- `docs/agents/code-review.md` and `docs/agents/security-review.md` apply when
  the fix touches review or security-sensitive surfaces.

Do not copy third-party files, scripts, hooks, installers, prompts,
dependencies, or global state into this repository. Study outside workflows only
as reference material, then adapt the smallest repo-local workflow needed.

## Workflow

1. Capture the exact failing signal:
   - command, workflow, job, step, branch, PR, commit, or affected screen
   - full relevant error text
   - whether the failure is local, CI-only, product-only, or intermittent
2. Identify the first meaningful error. Ignore cascaded errors until the root
   failure is understood.
3. Reproduce locally when practical. If local reproduction is not practical,
   document why and use the closest deterministic evidence source available.
4. Classify the failure.
5. Before any non-trivial fix, write 3 to 5 ranked falsifiable hypotheses.
6. Test the most likely hypothesis with the narrowest command, inspection, or
   instrumentation that can disprove it.
7. Use temporary debug logs or instrumentation only when inspection and targeted
   commands are insufficient. Tag temporary logs clearly, keep them narrow, and
   remove them before completion.
8. Apply the minimal fix that addresses the proven root cause.
9. Add a regression test when a practical test seam exists. If no test is
   practical, document the reason.
10. Re-run the targeted check and any broader checks needed for confidence.
11. Record root cause, evidence, commands, and safe/unsafe repair decision.

## Failure Classifications

| Classification | Use When | Agent Repair |
| --- | --- | --- |
| deterministic code failure | Same code path fails reliably because implementation or tests are wrong. | Usually safe if scoped and tests can prove the fix. |
| flaky failure | Same inputs pass and fail across runs, or logs match a known flaky signature. | Safe only after evidence; do not guess or weaken assertions. |
| environment/cache/dependency failure | Failure depends on runner image, cache, package resolution, service availability, or local machine state. | Safe for cache or config fixes when evidence is clear; otherwise escalate. |
| secret failure | Logs indicate missing, invalid, or unauthorized secret material. | Unsafe to repair without human-provided credential changes. |
| permission failure | Token, IAM, filesystem, or GitHub permission prevents the step. | Unsafe if it broadens privileges; escalate unless least-privilege fix is obvious and approved. |
| unrelated main-branch failure | Failure exists on main or outside the changed surface. | Do not patch unrelated code; report evidence and suggest a follow-up. |
| reproduced product defect | User-visible behavior is reproduced outside CI. | Safe when behavior is unambiguous and a regression test or manual verification proves the fix. |

## Hypotheses

For non-trivial failures, write 3 to 5 ranked falsifiable hypotheses before
changing code. Each hypothesis must include the evidence that would confirm or
disprove it.

Example:

```md
1. The validator rejects the new skill because the frontmatter is missing
   `description`. Disprove by running `python3 scripts/validate-skills.py`.
2. The agent config references a skill directory that does not exist. Disprove
   by running `python3 scripts/validate-multica-config.py`.
3. The grep check fails because required report labels use different wording.
   Disprove by running the exact `rg` command from the issue.
```

## Repair Rules

- Fix the proven root cause, not the last visible error.
- Prefer the smallest change that makes the failing check pass for the right
  reason.
- Do not weaken tests, delete failing assertions, remove security checks, bypass
  validation, or broaden permissions to make a failure disappear.
- Do not mark a failure flaky without evidence from repeated runs or a known
  flaky signature.
- Do not hide failures with retries unless the root cause is an accepted
  external transient and the retry policy is explicitly justified.
- Remove all temporary debug logs, instrumentation, local cache changes, and
  one-off environment edits before finishing.

## Stop Conditions

Stop and escalate when debugging requires:

- production access
- secrets, credential rotation, or private tokens
- customer data or production data
- security policy exceptions
- destructive migrations or data-loss risk
- unclear product behavior with multiple reasonable outcomes
- broad permission changes
- weakening tests, removing security checks, or bypassing validation

## Output Contract

Return debugging reports in this format:

```md
## Debugging report
- Classification:
- First meaningful error:
- Root cause:
- Evidence:
- Hypotheses considered:
- Minimal fix:
- Regression test:
- Commands run:
- Safe for agent repair: yes/no
- Follow-up needed: yes/no
```
