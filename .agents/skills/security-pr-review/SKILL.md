---
name: security-pr-review
description: Use for security review of PRs touching auth, authorization, tenancy, secrets, PII, dependency changes, CI/CD, file handling, outbound network, database queries, logging, or admin functions.
---

# Security PR Review

## Inputs

- PR diff
- AGENTS.md
- docs/agents/security-review.md
- Related issue and acceptance criteria

## Process

1. Identify changed trust boundaries.
2. List attacker-controlled inputs.
3. Identify protected assets and security invariants.
4. Check changed code for the security categories in `docs/agents/security-review.md`.
5. Look for missing tests that would prove the security invariant.
6. Produce findings with evidence and concrete fixes.

## Findings should be blocking when

- A user can access another user's or tenant's data.
- An unauthenticated user can reach authenticated behavior.
- Secrets or PII can be logged or exposed.
- Untrusted input reaches SQL, shell, filesystem, template, or network sink unsafely.
- CI workflow exposes write token or secrets to untrusted PR code.
- A migration can destroy or corrupt data without a safe rollback or verified plan.

## Output

```md
## Security review
Verdict: pass | conditional-pass | block

### Threat model delta
- Assets:
- Trust boundaries:
- Attacker inputs:

### Findings
#### P0/P1/P2: <title>
- Evidence:
- Exploit scenario:
- Impact:
- Fix:
- Blocks merge: yes/no

### Tests required
```
