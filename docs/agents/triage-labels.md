# Triage Labels

Use these labels in Multica comments, GitHub labels, or both.

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
