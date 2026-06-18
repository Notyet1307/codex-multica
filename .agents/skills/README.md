# Skill Kernel Routing

This directory contains repo-scoped skills for the Codex + Multica dogfood
operating template. The target operating model is a small Skill Kernel optimized
for control, evidence, and context management rather than a mirror of the
current skill inventory.

See `docs/personal/control-layer-lite-roadmap.md` for the durable lightweight
control-layer roadmap that this routing guide follows.

## Target six-skill kernel

The target kernel is exactly these six core skills:

| Target skill | Core responsibility | Current state |
| --- | --- | --- |
| `spec-first-intake` | Convert ambiguous work into a scoped, testable, agent-ready spec before implementation. | Exists as `.agents/skills/spec-first-intake/`. Former `multica-issue-brief` and `issue-slicing` responsibilities now route here. |
| `tdd-vertical-slice` | Implement one thin behavior slice with tests, validation, and minimal drift from the spec. | Exists as `.agents/skills/tdd-vertical-slice/`. |
| `systematic-debugging` | Reproduce failures, form hypotheses, isolate root cause, and fix with evidence. | Present as `.agents/skills/systematic-debugging/`. Former `ci-failure-triage` responsibilities now route here. |
| `verification-before-completion` | Require fresh verification evidence before claiming work is complete, passing, or ready. | Present as `.agents/skills/verification-before-completion/`. |
| `security-pr-review` | Review changes that touch trust boundaries, secrets, PII, permissions, dependencies, CI tokens, or similar security-sensitive surfaces. | Exists as `.agents/skills/security-pr-review/`. |
| `context-pack` | Package the minimum durable context future agents need: decisions, constraints, evidence, links, and unresolved questions. | Present as `.agents/skills/context-pack/`. |

The six-skill kernel is now present. Do not create new skill directories without
a dedicated Multica issue.

## Retired transitional skills

The transitional skills below were removed from the repository-local skill set
after repo-local routing checks found no agent bindings to them. Live Multica
workspace sync and binding checks remain separate operator responsibilities;
record live audit evidence in the PR or follow-up notes when live access is
available.

| Retired skill | Replacement path |
| --- | --- |
| `multica-issue-brief` | Use `spec-first-intake` for vague request intake, Multica-ready briefs, risk classification, routing, and stop-condition decisions. |
| `issue-slicing` | Use `spec-first-intake` for ambiguous, oversized, risky, or multi-step intake and issue slicing. |
| `ci-failure-triage` | Use `systematic-debugging` for CI failures, local test failures, build/lint/typecheck failures, flaky failures, and reproduced defects. |

Do not reintroduce retired transitional skill directories unless a future issue
or explicitly recorded operator exception explains why the six-skill kernel no
longer covers the workflow.

## Current-to-target migration notes

- `architecture-review` is not a core kernel responsibility. Use it only as an
  optional manual planning review, or fold its useful checks into
  `spec-first-intake` when shaping high-risk work.
- `release-notes-drafter` is low-frequency and manual-only. It should not be in
  the default kernel path for ordinary issue implementation.
- `tdd-vertical-slice` and `security-pr-review` are already aligned with target
  kernel responsibilities and should stay small.
- `context-pack` now owns compact durable handoff and resume context.
- Keep Multica agent configuration aligned with the kernel only through
  dedicated issues and review.

## Manual-only policy

Low-frequency or high-cost capabilities stay manual-only unless a future issue
explicitly scopes and approves automation. Examples include:

- `architecture-review` when used as a broader planning review
- `release-notes-drafter`
- bulk importing third-party skills
- adding PR-Agent, Repomix, or other external analysis tools
- broad architecture rewrites or cross-repo skill migrations
- production deployment, rollback, or infrastructure provisioning
- security exceptions and final security acceptance
- dependency automation changes that require repository administrator settings
- product runtime scaffolding such as frontend, backend, database, auth,
  deployment, observability, or e2e directories

Agents may study external workflows as reference material, but should copy only
the small company-specific workflow that this repository needs.

## Non-goals

This routing document does not:

- change Multica agents, squads, autopilots, or workspace skill bindings
- add PR-Agent, Repomix, or another external tool
- change GitHub Actions, CodeQL, dependency review, Dependabot, or branch
  protection
- create product runtime directories
- make agents responsible for final merge, production release, security
  exceptions, or product direction

## Dogfood guidance for future skill changes

- Start with the six kernel skills before proposing any new skill.
- Prefer improving an existing kernel/manual skill or this routing guide over
  adding a specialized skill for a one-off workflow.
- Treat each skill merge, rename, addition, or deletion as a dedicated
  Multica issue with explicit old-to-new routing notes.
- Use a Multica issue ID in every branch and PR that changes skills or routing
  unless a human operator explicitly authorizes and records a narrow
  repository-maintenance exception in the PR body.
- Keep each skill change small enough for human review, and explain the routing
  impact in the PR body.
- Validate skill and template changes with `make verify`.
- Do not bulk import third-party skills. Review their instructions, scripts,
  hooks, and installers first, then adapt only the minimal workflow that fits
  this repository.
- During dogfood, keep this repository focused on the agent operating layer. Do
  not use skill changes as a reason to add product runtime directories or
  production deployment behavior.
