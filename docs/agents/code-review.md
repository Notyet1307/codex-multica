# Code Review Rules for Agents

## Review objective

Find issues that should block merge or should be fixed before release. Prioritize correctness, security, reliability, maintainability, and operability.

## Severity model

- P0: must not merge. Exploit, data loss, broken critical path, irreversible migration, production outage risk.
- P1: should not merge without fix or explicit owner exception. Incorrect behavior, authorization gap, major test gap, high operational risk.
- P2: fix soon but not necessarily blocking. Maintainability, minor correctness, moderate test gap.
- P3: optional suggestion. Do not overuse.

## Review checklist

### Correctness

- Does the implementation match the acceptance criteria?
- Are edge cases handled?
- Are errors handled explicitly?
- Are public API changes backward compatible?
- Are time zones, locales, currency, and encoding handled correctly?

### Tests

- Are tests added or updated for changed behavior?
- Are tests stable and deterministic?
- Do tests assert behavior through public interfaces?
- Is there a regression test for a bug fix?
- Are risky code paths missing coverage?

### Architecture

- Does the change respect module boundaries?
- Does it deepen modules instead of spreading complexity?
- Does it avoid hidden coupling?
- Does it preserve existing domain language from `docs/agents/domain.md` or `CONTEXT.md`?

### Operations

- Are logs useful and safe?
- Are metrics/traces needed for this change?
- Is rollback possible?
- Are migrations reversible or otherwise documented?
- Are feature flags needed?

## Output format

```md
## Review summary
<1-3 sentences>

## Blocking findings
### P0/P1: <title>
- Evidence: <file/function/behavior>
- Why it matters: <impact>
- Suggested fix: <concrete action>

## Non-blocking findings
### P2/P3: <title>
- Evidence:
- Suggested fix:

## Missing validation
- <commands/tests/manual checks that should run>
```
