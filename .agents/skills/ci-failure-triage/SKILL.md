---
name: ci-failure-triage
description: Use when CI, GitHub Actions, build, lint, typecheck, or test jobs fail. Classifies the failure, identifies root cause, proposes minimal fix, and states whether an agent can safely repair it.
---

# CI Failure Triage

Transitional/deprecated: keep this skill for compatibility with existing
references. New CI, local test, build, lint, typecheck, flaky, or reproduced
product defect debugging work should use `systematic-debugging`.

## Workflow

1. Gather context:
   - Workflow name
   - Job name
   - Failing step
   - PR/branch/commit
   - Relevant logs
2. Classify:
   - deterministic code failure
   - flaky test
   - environment/cache/dependency failure
   - secret/permission failure
   - unrelated main-branch failure
3. Find first meaningful error. Ignore cascaded failures until root cause is identified.
4. Reproduce locally if commands are available.
5. Propose the smallest repair.
6. If safe, apply the repair and run targeted checks.
7. If unsafe, write an agent-ready brief for a human or specialist agent.

## Guardrails

- Do not weaken tests to make CI pass.
- Do not remove security checks.
- Do not broaden GitHub token permissions without explaining why.
- Do not edit deployment credentials or secrets.
- Do not mark flaky without evidence across multiple runs or a known flaky signature.

## Output

```md
## CI triage
- Classification:
- First failing step:
- Root cause:
- Evidence:
- Minimal fix:
- Commands run:
- Safe for agent fix: yes/no
- Follow-up issue needed: yes/no
```
