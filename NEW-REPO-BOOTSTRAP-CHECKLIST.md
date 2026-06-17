# New Repo Bootstrap Checklist

Use this checklist when applying the Codex + Multica + GitHub operating model to
a new repository. The goal of the bootstrap PR is governance setup only: copy and
adapt the agent, validation, issue, and review scaffolding before product runtime
work begins.

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
- [ ] Copy `.agents/skills/`.
- [ ] Copy `.github/ISSUE_TEMPLATE/`.
- [ ] Copy `.github/codex/prompts/`.
- [ ] Copy `.github/scripts/deepseek_pr_review.py`.
- [ ] Copy `.github/workflows/ci.yml`.
- [ ] Copy `.github/workflows/codeql.yml`.
- [ ] Copy `.github/workflows/deepseek-pr-review.yml`.
- [ ] Copy `.github/pull_request_template.md`.
- [ ] Copy `docs/agents/`.
- [ ] Copy `multica/`.
- [ ] Copy `scripts/`.

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
- [ ] Do not rename existing skills or modify skill content as part of the
      bootstrap unless a separate issue explicitly asks for it.
- [ ] Do not change Multica workspace runtime directly from the bootstrap PR.
- [ ] If prompt, skill, agent, squad, or autopilot templates changed, plan a
      separate manual live configuration sync after review and merge. Use
      `docs/agents/multica-live-config-sync.md` as the audit checklist.

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
- [ ] Reuse existing workspace skills where possible, including:
  - `spec-first-intake`
  - `tdd-vertical-slice`
  - `systematic-debugging`
  - `verification-before-completion`
  - `security-pr-review`
  - `context-pack`
- [ ] Create or reuse these Multica workspace agents:
  - `OpenAI-scoper`
  - `OpenAI-fullstack`
  - `OpenAI-frontend`
  - `OpenAI-backend`
  - `OpenAI-test`
  - `OpenAI-security-reviewer`
  - `OpenAI-release-manager`
- [ ] Create or reuse AppDev Squad with `OpenAI-scoper` as leader.
- [ ] Ensure squad routing, issue assignment, and handoff text use `OpenAI-*`
      workspace agent names.
- [ ] Confirm repo templates are not assumed to sync live configuration
      automatically. Live Multica agent prompts, workspace skills, squads, and
      autopilots must be updated or confirmed separately by an operator.
- [ ] Before copying prompt or skill text into Multica, refresh the local clone
      with `git fetch origin main` and `git pull --ff-only` if it is stale.
- [ ] Check live prompts and skills for the current handoff markers:
      `Handoff Back is the detailed evidence report`, `Context pack is the
      compact resume state`, `## Context pack`, and `compact index to the
      Handoff Back and PR`.
- [ ] Compare live `OpenAI-*` agents against `multica/agents.yaml`, live AppDev
      Squad routing against `multica/squads.yaml`, and live autopilots against
      `multica/autopilots.yaml`.
- [ ] Do not add automatic sync, live write automation, credential-dependent
      scripts, agent renames, or skill renames during bootstrap.

## 6. Open the First Bootstrap PR

- [ ] Create a Multica issue for the bootstrap.
- [ ] Create a branch such as `agent/bootstrap-codex-multica` or another branch
      name that includes the Multica issue ID.
- [ ] Copy and adapt only the governance files needed for the target repository.
- [ ] Run `make verify` locally.
- [ ] Run the repo-local drift audit:
      `rg -n "Multica live|live configuration|sync|drift|agent-system-prompts|.agents/skills|Handoff Back|Context pack|compact resume|manual sync|stale local" README.md AGENTS.md NEW-REPO-BOOTSTRAP-CHECKLIST.md docs .agents multica scripts tests`
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
