# Control Layer Lite Roadmap

This roadmap defines the lightweight control-layer direction for the Codex +
Multica dogfood template. The goal is a small, explicit skill kernel that keeps
agent work controlled, evidence-based, and context-aware without accumulating
overlapping skills, external tools, or runtime scaffolding.

## Direction

Use six core skills as the default control layer:

1. `spec-first-intake`
2. `tdd-vertical-slice`
3. `systematic-debugging`
4. `verification-before-completion`
5. `security-pr-review`
6. `context-pack`

These skills cover the normal issue lifecycle:

- define the work before execution
- implement in thin tested slices
- debug failures systematically
- verify before claiming completion
- review trust-boundary changes
- preserve durable context for future agents

## Current transitional skills

The current repository has useful skills that predate the final lightweight
kernel. Keep them unchanged until a dedicated issue approves consolidation.

| Current skill | Target direction |
| --- | --- |
| `multica-issue-brief` | Merge into `spec-first-intake`. |
| `issue-slicing` | Merge into `spec-first-intake`. |
| `ci-failure-triage` | Become part of `systematic-debugging`. |
| `tdd-vertical-slice` | Keep as a core kernel skill. |
| `security-pr-review` | Keep as a core kernel skill. |
| `architecture-review` | Keep optional/manual, or fold selected planning checks into `spec-first-intake`. |
| `release-notes-drafter` | Keep low-frequency/manual-only, outside the default kernel. |

`verification-before-completion` and `context-pack` are target kernel skills
even though this repository does not have matching skill directories yet.

## Manual-only capabilities

Manual-only means a human or explicitly assigned agent can invoke the capability
when needed, but it is not part of the default routing path for ordinary issues.

- architecture review beyond normal planning checks
- release note drafting
- external tool evaluation or adoption
- third-party skill import
- production deployment or rollback
- security exception approval
- broad repo-wide rewrites
- product runtime scaffolding

## Guardrails

- Do not add external tools such as PR-Agent or Repomix as part of the lite
  control-layer roadmap.
- Do not add, delete, rename, or merge skill directories without a dedicated
  Multica issue.
- Do not update Multica agent configuration as a side effect of documenting the
  roadmap.
- Do not change GitHub workflows for this roadmap unless a future issue scopes
  that workflow change directly.
- Do not create frontend, backend, database, auth, deployment, observability, or
  e2e runtime directories during dogfood.

## Next migration slices

Future issues should be small and reversible:

1. Draft `spec-first-intake` from `multica-issue-brief` and `issue-slicing`.
2. Draft `systematic-debugging` from `ci-failure-triage` plus local debugging
   discipline.
3. Add `verification-before-completion` as an evidence gate for completion
   claims.
4. Add `context-pack` for compact durable handoff notes.
5. Retire or park transitional skills only after references and agent routing
   are updated.

Each slice should update routing documentation, run `make verify`, and keep
skill directory changes separate from external tooling or Multica config
changes.
