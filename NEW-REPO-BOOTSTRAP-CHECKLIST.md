# New Repo Bootstrap Checklist

Use this checklist when applying the Codex + Multica + GitHub operating model to
a new repository. The goal of the bootstrap PR is governance setup only: copy and
adapt the repository-local validation, issue, and review scaffolding before
product runtime work begins.

This checklist assumes a shared Multica workspace runtime: live Multica agents,
workspace skills, squads, and workspace-level autopilots are maintained by this
template repository, not copied into each product repository. A target product
repository should record project facts, safety boundaries, roadmap, validation,
and GitHub review automation. It should not become another source of truth for
the shared live agent runtime.

Use `docs/agents/new-project-bootstrap-boundary.md` as the detailed export
profile for deciding what to copy, what to adapt, and what to leave in this
template repository.

Do not create frontend, backend, database, auth, deployment, or other product
runtime directories during governance bootstrap unless the target repository
explicitly needs product code changes.

## 1. Choose the Pilot Repository

- [ ] Confirm the GitHub repository owner and canonical repository URL.
- [ ] Confirm the Multica issue prefix that PRs and branches should reference.
- [ ] Confirm the repository data classification and any stop conditions for
      agents.
- [ ] Confirm the actual stack, package manager, and real local validation
      commands.
- [ ] Confirm whether the repository is governance-only during bootstrap or also
      needs product code changes.

## 2. Copy Governance Files

- [ ] Copy `AGENTS.md`.
- [ ] Copy `Makefile`.
- [ ] Copy `.codex/config.example.toml` only if the target repository wants a
      repo-local Codex config example.
- [ ] Copy `.github/ISSUE_TEMPLATE/` only if the target repository mirrors work
      into GitHub issues.
- [ ] Copy `.github/codex/prompts/`.
- [ ] Copy `.github/scripts/deepseek_pr_review.py`.
- [ ] Copy `.github/scripts/review_decision.py` if using DeepSeek PR review.
- [ ] Copy `.github/workflows/ci.yml`.
- [ ] Copy `.github/workflows/codeql.yml`.
- [ ] Copy `.github/workflows/deepseek-pr-review.yml`.
- [ ] Copy `.github/pull_request_template.md`.
- [ ] Copy selected `docs/agents/` policy docs and adapt project-specific
      language.
- [ ] Copy selected `scripts/` helpers.
- [ ] Keep only target repo validation helpers under `scripts/`; do not copy
      template-only Multica live audit/sync helpers by default.
- [ ] Do not copy `.agents/skills/`; live workspace skills are maintained from
      this template repository.
- [ ] Do not copy `multica/agent-system-prompts/`, `multica/agents.yaml`,
      `multica/squads.yaml`, or `multica/autopilots.yaml`; those files describe
      the shared live Multica runtime, not a single product repository.
- [ ] Copy or create `multica/issue-template.md` only if the target repository
      needs a repo-local issue brief template.

Repo-local prompt filenames under `.github/codex/prompts/` may still use
`codex-*.md` names. Those filenames are prompt template names, not Multica
workspace agent names.

## 3. Adapt Repository-Specific Files

- [ ] Update `AGENTS.md` for the real product, stack, commands, package manager,
      data classification, and stop conditions.
- [ ] Update `Makefile` so `make verify` is the single standard verification
      entrypoint for both local runs and CI.
- [ ] Update `.github/workflows/ci.yml` so the `readiness` job runs the project's
      real validation through `make verify`.
- [ ] Keep DeepSeek PR review configured for dogfood unless the repository
      explicitly switches review providers.
- [ ] Remove bootstrap validation requirements that assume repo-local
      `.agents/skills/`, `multica/agents.yaml`, or
      `multica/agent-system-prompts/` exist in the target repository.
- [ ] Keep project-specific safety rules in `AGENTS.md`, `docs/roadmap.md`, and
      issue briefs instead of editing shared workspace agent prompts.
- [ ] Do not change Multica workspace runtime directly from the bootstrap PR.
- [ ] If the bootstrap reveals that shared prompts, skills, agents, squads, or
      workspace-level autopilots need changes, make that change in this template
      repository first, then run the live configuration audit/sync process from
      this template repository after review and merge.
- [ ] If the target project needs its own agent prompts, workspace skills,
      squad routing, autopilots, or live sync scripts, record an explicit
      project-specific fork decision before copying those paths.

## 4. Configure GitHub

- [ ] Add `DEEPSEEK_API_KEY` as a GitHub Actions secret.
- [ ] Open the bootstrap branch with the Multica issue ID in the branch, title,
      or PR body, for example `MUL-123`.
- [ ] Include summary, validation, risk, rollback, and security notes in the PR
      body.
- [ ] Use GitHub checks as the merge gate.
- [ ] Wait for the `readiness` check.
- [ ] Wait for the DeepSeek `review` check.
- [ ] Wait for CodeQL.
- [ ] Keep human final merge; do not enable automatic merge.
- [ ] Enable branch protection only after the checks are stable.

## 5. Configure Multica

- [ ] Create or select the Multica project for the repository.
- [ ] Connect the GitHub repository to the Multica project.
- [ ] Reuse the shared workspace skills maintained by this template repository,
      including:
  - `spec-first-intake`
  - `tdd-vertical-slice`
  - `systematic-debugging`
  - `verification-before-completion`
  - `security-pr-review`
  - `context-pack`
- [ ] Reuse the shared workspace agents maintained by this template repository:
  - `OpenAI-scoper`
  - `OpenAI-fullstack`
  - `OpenAI-frontend`
  - `OpenAI-backend`
  - `OpenAI-test`
  - `OpenAI-security-reviewer`
  - `OpenAI-release-manager`
- [ ] Reuse AppDev Squad with `OpenAI-scoper` as leader.
- [ ] Ensure squad routing, issue assignment, and handoff text use `OpenAI-*`
      workspace agent names.
- [ ] Confirm the target repository does not carry its own copy of shared live
      agent prompts, workspace skill content, squad definitions, or
      workspace-level autopilot templates.
- [ ] Check the shared live prompts and skills for the current handoff markers:
      `Handoff Back is the detailed evidence report`, `Context pack is the
      compact resume state`, `## Context pack`, and `compact index to the
      Handoff Back and PR`.
- [ ] If shared live configuration drift is suspected, run the audit from this
      template repository, not from the target product repository.
- [ ] Do not add automatic sync, live write automation, credential-dependent
      scripts, agent renames, or skill renames during bootstrap.

## 6. Open the First Bootstrap PR

- [ ] Create a Multica issue for the bootstrap.
- [ ] Create a branch such as `agent/bootstrap-codex-multica` or another branch
      name that includes the Multica issue ID.
- [ ] Copy and adapt only the governance files needed for the target repository.
- [ ] Use `docs/agents/new-project-bootstrap-boundary.md` to confirm the final
      copied file set.
- [ ] Run `make verify` locally.
- [ ] Run the repo-local drift audit:
      `rg -n "new project|bootstrap|template|shared workspace|live Multica|workspace skills|Handoff Back|Context pack|manual sync|stale local" README.md AGENTS.md docs scripts tests`
- [ ] Confirm the target repository does not include copied shared runtime
      source paths such as `.agents/skills/`, `multica/agent-system-prompts/`,
      `multica/agents.yaml`, `multica/squads.yaml`, or
      `multica/autopilots.yaml` unless a separate issue explicitly creates
      project-specific Multica configuration.
- [ ] Open the PR.
- [ ] Confirm the PR links to the Multica issue through the branch, title, or
      body.
- [ ] Wait for `readiness`, DeepSeek `review`, and CodeQL checks.
- [ ] Have a human review and merge the PR.
- [ ] Close the Multica issue only after merge and acceptance criteria are met.

## 7. Run the First Dogfood Issues

- [ ] Run one documentation-only issue.
- [ ] Run one small tested implementation issue.
- [ ] Run one CI, test failure, or validation issue.
- [ ] Require context handoff and completion evidence on each issue.
- [ ] Patch `AGENTS.md`, `docs/agents/*.md`, or skills when agents repeat
      mistakes.
- [ ] Keep product runtime directories out of the repository until a product
      starter issue explicitly introduces them.
