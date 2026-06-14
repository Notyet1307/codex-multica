# Triage Labels

Multica does not currently expose issue labels or tags as first-class fields. Use these values as structured issue fields in the Multica issue body or in a routing comment.

Preferred issue body block:

```md
## Agent routing

Readiness: needs-triage | needs-info | ready-for-agent | ready-for-human | blocked
Type: type:bug | type:feature | type:refactor | type:test | type:docs | type:security | type:ci | type:release
Risk: risk:low | risk:medium | risk:high
Suggested agent: agent:scoper | agent:frontend | agent:backend | agent:fullstack | agent:test | agent:security | agent:release
```

Agents must treat these values as routing signals, not as proof that the issue is safe to execute. If the fields conflict with the issue body, acceptance criteria, or security notes, stop and ask `codex-scoper` or a human to clarify.

## Readiness

- `needs-triage`: not yet classified.
- `needs-info`: cannot proceed without more details.
- `ready-for-agent`: can be delegated to an agent.
- `ready-for-human`: needs human judgment or external access.
- `blocked`: waiting on external dependency.

## Type

- `type:bug`
- `type:feature`
- `type:refactor`
- `type:test`
- `type:docs`
- `type:security`
- `type:ci`
- `type:release`

## Risk

- `risk:low`: isolated, reversible, tests exist.
- `risk:medium`: touches shared code, migrations, auth-adjacent behavior, or weak tests.
- `risk:high`: auth, authorization, tenant isolation, data deletion, billing, production deployment, secrets, migrations with data risk.

## Agent ownership

- `agent:scoper`
- `agent:frontend`
- `agent:backend`
- `agent:fullstack`
- `agent:test`
- `agent:security`
- `agent:release`
