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

Current kernel status:

| Target skill | Status |
| --- | --- |
| `spec-first-intake` | Present. Created from the previous intake skills and now owns intake, scoping, and context handoff for non-trivial delegated work. |
| `tdd-vertical-slice` | Present. Existing implementation skill remains part of the core kernel. |
| `systematic-debugging` | Present. Created from the previous CI-focused triage workflow and now owns CI, local test, build, lint, typecheck, flaky, environment-dependent, and reproduced defect debugging. |
| `verification-before-completion` | Present. Created as the evidence gate before agents claim completion, passing validation, or readiness for review. |
| `security-pr-review` | Present. Existing security review skill remains part of the core kernel. |
| `context-pack` | Not present yet. Add this only after dogfood proves which handoff fields are repeatedly needed across issues. |

## Context handoff direction

Multica comments are useful as an event stream, but they are not enough as the
current source of truth for a multi-agent task. The lightweight control layer
should therefore add a small context handoff contract before adding heavier
context storage, new agents, or new skills.

For the next context-management slice, prefer this minimum shape:

- Keep `OpenAI-scoper` as the lightweight squad leader and context steward.
- Add a `Context Ledger` pattern for non-trivial issues, either in the issue
  body or as the latest structured leader comment.
- Require a structured delegation comment before assigning implementation,
  testing, security review, or documentation work.
- Require a structured result packet from the worker before the leader routes
  the task onward or marks it ready for human review.
- Keep context handoff responsibilities inside `spec-first-intake` until
  `context-pack` is implemented.
- Do not introduce a separate `codex-context-manager` agent, context database,
  or issue-scoped `.agent-context/` directory by default.

The `Context Ledger` should stay compact and point to durable evidence instead
of copying all prior discussion. It should track the current phase, owner,
branch or PR, latest validation, open risks, and the minimal artifacts a
zero-context worker must read.

## Open-source reference map

External projects are reference material only. Do not copy third-party skill
files, scripts, hooks, installers, global state, or dependencies into this
repository unless a dedicated Multica issue explicitly approves that adoption.

| Reference | Borrow | Do not borrow |
| --- | --- | --- |
| Multica squads | The leader-worker shape: one leader keeps issue state coherent and delegates to the narrowest capable worker. | Do not add dynamic squads or new squad topologies just to document context handoff. |
| CCPM | Spec-first discipline, traceability from request to issue to PR, and refusal to code directly from vague work. | Do not import CCPM project layout, commands, automation, or GitHub issue machinery. |
| Open SWE | Manager/Planner/Programmer/Reviewer separation, human approval gates, and independent review before completion. | Do not adopt Open SWE runtime, service architecture, queueing model, or deployment assumptions. |
| Superpowers | The sequence of clarify intent, write a spec, produce a plan, implement, then review. | Do not install the full workflow or make every small task follow a heavyweight ceremony. |
| gstack | Command-like skill boundaries such as `/spec`, plus context-save/context-restore concepts for decisions, validation, and remaining work. | Do not create separate `context-save`, `context-restore`, or `squad-leader-learn` skills during the lite kernel phase. Fold useful ideas into `spec-first-intake` first, then later into `context-pack`. |
| mattpocock/skills | Short handoff documents that reference existing artifacts instead of duplicating PRDs, plans, diffs, logs, or issue history. | Do not bulk import skills. Adapt only the small handoff, TDD, diagnosis, and issue-splitting patterns that fit this repo. |
| Agent Orchestrator style worktrees | Branch/worktree-per-task isolation and routing CI or review feedback back to the originating issue. | Do not add worktree automation or parallel write agents until a dedicated issue scopes it. |
| PR-Agent / review tools | Manual benchmarking ideas for concise PR review summaries and finding validation gaps. | Do not add PR-Agent or other external review automation to the default path. |
| Repomix | Future `context-pack` inspiration for compact repository context bundles. | Do not add Repomix, MCP servers, or generated context dumps by default. |

The practical rule is: borrow workflow constraints, output contracts, and stop
conditions; avoid importing runtime systems.

## Context handoff contract

The first handoff implementation should update existing skill and prompt
surfaces instead of creating new runtime storage.

`spec-first-intake` should learn to produce a copy-safe handoff for ambiguous,
multi-step, risky, or oversized work:

- source of truth: issue, PR, branch, and relevant docs
- verified current state
- decisions already made
- known facts versus assumptions
- allowed files or areas
- explicit non-goals
- stop conditions
- suggested next owner
- expected worker output
- required validation

`OpenAI-scoper` should not delegate non-trivial implementation work until this
handoff exists. After a worker finishes, the leader should require a result
packet with:

- summary of work performed
- files changed
- validation commands and results
- known failures
- risks or uncertainty
- scope check against allowed files
- recommended next owner or human review

Use copy-safe Markdown for Multica issue bodies and comments. Avoid fenced code
blocks in issue templates and delegation comments because they have already
caused copied issue text to truncate during dogfood. Prefer inline commands
such as `make verify`.

## Current transitional skills

The current repository has useful skills that predate the final lightweight
kernel. Keep them unchanged until a dedicated issue approves consolidation.

| Current skill | Target direction |
| --- | --- |
| `multica-issue-brief` | Transitional/deprecated. New intake should route to `spec-first-intake`; keep this directory for compatibility until a dedicated cleanup issue. |
| `issue-slicing` | Transitional/deprecated. New intake should route to `spec-first-intake`; keep this directory for compatibility until a dedicated cleanup issue. |
| `ci-failure-triage` | Transitional/deprecated. New debugging should route to `systematic-debugging`; keep this directory for compatibility until a dedicated cleanup issue. |
| `tdd-vertical-slice` | Keep as a core kernel skill. |
| `security-pr-review` | Keep as a core kernel skill. |
| `architecture-review` | Keep optional/manual, or fold selected planning checks into `spec-first-intake`. |
| `release-notes-drafter` | Keep low-frequency/manual-only, outside the default kernel. |

`context-pack` is the remaining target kernel skill that does not have a
matching skill directory yet.

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

Future issues should be small and reversible. The remaining migration order is:

1. Add `context-pack` for compact durable handoff notes.
2. Retire or park transitional skills only after references and agent routing
   are updated.

Each slice should update routing documentation, run `make verify`, and keep
skill directory changes separate from external tooling or Multica config
changes.

Before adding the `context-pack` skill directory, add the lightweight context
handoff contract to `spec-first-intake` and `OpenAI-scoper`. Only promote it into
`context-pack` after dogfood proves which context fields are repeatedly needed
across issues.
