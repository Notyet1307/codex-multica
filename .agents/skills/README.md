# Skill Kernel Routing

This directory contains repo-scoped skills for the Codex + Multica dogfood
operating template. The target operating model is a small Skill Kernel: six
routing responsibilities that cover common agent work without accumulating
overlapping skills, agent configs, or external toolchains.

## Target six-skill kernel

Use these responsibilities as the routing layer for future work:

| Kernel responsibility | Use when | Current skill path |
| --- | --- | --- |
| Issue intake and scoping | Turn vague requests into agent-ready briefs, classify risk, or slice large work into thin Multica issues. | `.agents/skills/multica-issue-brief/` and `.agents/skills/issue-slicing/` |
| Implementation and TDD | Implement a low- or medium-risk vertical slice with test-first discipline where behavior is testable. | `.agents/skills/tdd-vertical-slice/` |
| CI and test triage | Investigate failing checks, classify the failure, reproduce locally when possible, and propose or apply the smallest safe fix. | `.agents/skills/ci-failure-triage/` |
| Security review | Review PRs or plans that touch auth, authorization, tenancy, secrets, PII, dependencies, CI permissions, file handling, outbound network, or other trust boundaries. | `.agents/skills/security-pr-review/` |
| Architecture review | Review module boundaries, domain language, test seams, and complexity hotspots before or after agent-authored changes. | `.agents/skills/architecture-review/` |
| Release notes | Draft release notes from merged PRs, Multica issues, Git history, or milestone content. | `.agents/skills/release-notes-drafter/` |

The kernel is intentionally responsibility-based. It does not require a
one-directory-per-responsibility layout today.

## Current-to-target migration notes

- Keep the existing skill directories unchanged until a dedicated Multica issue
  explicitly approves a rename, merge, or deletion.
- Treat `multica-issue-brief` and `issue-slicing` as the current implementation
  of the single target responsibility: issue intake and scoping.
- Treat `tdd-vertical-slice`, `ci-failure-triage`, `security-pr-review`,
  `architecture-review`, and `release-notes-drafter` as already aligned with the
  target kernel responsibilities.
- When a future issue proposes consolidation, preserve the behavior first:
  document the old-to-new route, update references, and validate with
  `make verify` before removing any path.
- Do not update Multica agent configuration just to match this routing document.
  Agent config changes need their own issue and review.

## Manual-only policy

Low-frequency or high-cost capabilities stay manual-only unless a future issue
explicitly scopes and approves automation. Examples include:

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

- add, delete, rename, or merge skills
- change Multica agents, squads, autopilots, or workspace skill bindings
- add PR-Agent, Repomix, or another external tool
- change GitHub Actions, CodeQL, dependency review, Dependabot, or branch
  protection
- create product runtime directories
- make agents responsible for final merge, production release, security
  exceptions, or product direction

## Dogfood guidance for future skill changes

- Start with the six kernel responsibilities before proposing a new skill.
- Prefer improving an existing skill or this routing guide over adding a
  specialized skill for a one-off workflow.
- Use a Multica issue ID in every branch and PR that changes skills or routing.
- Keep each skill change small enough for human review, and explain the routing
  impact in the PR body.
- Validate skill and template changes with `make verify`.
- Do not bulk import third-party skills. Review their instructions, scripts,
  hooks, and installers first, then adapt only the minimal workflow that fits
  this repository.
- During dogfood, keep this repository focused on the agent operating layer. Do
  not use skill changes as a reason to add product runtime directories or
  production deployment behavior.
