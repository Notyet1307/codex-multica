---
name: architecture-review
description: Use to review or improve codebase architecture, module boundaries, domain language, seams for testing, and complexity hotspots before or after agent-authored changes.
---

# Architecture Review

## Use when

- The same bug pattern appears repeatedly.
- Tests are hard to write because there is no good seam.
- A feature spreads changes across too many files.
- Module boundaries are unclear.
- Agents produce tangled code or excessive glue.

## Process

1. Read `AGENTS.md`, `docs/agents/domain.md`, and relevant ADRs.
2. Identify the current module boundary and public interface.
3. Identify complexity that should move behind a deeper module.
4. Classify dependencies:
   - in-process
   - local-substitutable
   - external-service
   - human/manual
5. Propose 2–3 candidate seams.
6. For each candidate, state:
   - new interface
   - hidden complexity
   - tests that become easier
   - migration path
   - risk
7. Recommend the smallest architecture improvement that unlocks current work.

## Output

```md
## Architecture review

### Current issue

### Candidate seams

### Recommended change

### Migration plan

### Tests enabled

### ADR needed
```
