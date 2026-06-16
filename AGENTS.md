# AGENTS.md

## Purpose

This file is the durable operating manual for Codex and other coding agents working in this repository. Follow it unless a human explicitly overrides it in a task, issue, or PR comment.

## Project facts

- Product: Codex + Multica Application Development Management Template
- Repository: codex-multica
- Primary users: engineering leads, solo builders, and teams using Codex with Multica and GitHub
- Runtime: Markdown, YAML, Bash, GitHub Actions
- Package manager: none
- Product runtime: not applicable during dogfood phase
- Future product starter scope: frontend, backend, database, auth, tests, deployment
- Issue tracker: Multica. GitHub PRs must reference Multica issue IDs, for example `MUL-123`.
- Production data classification: Internal

## Repository layout

Current dogfood layout:

```text
<repo-root>/
├── AGENTS.md
├── README.md
├── NEW-REPO-BOOTSTRAP-CHECKLIST.md
├── .agents/skills/
├── .codex/
├── .github/
├── docs/agents/
├── multica/
└── scripts/
```

Future product starter layout, not active during dogfood:

```text
<repo-root>/
├── apps/web/                 # planned frontend app
├── apps/api/                 # planned backend API
├── packages/db/              # planned database schema and migrations
├── packages/auth/            # planned auth/session helpers
├── packages/shared/          # planned shared types and utilities
├── infra/                    # planned deployment and IaC
└── tests/e2e/                # planned product-level tests
```

Do not create future product runtime directories during dogfood unless a Multica issue explicitly says this repository is entering the product starter phase.

## Commands

```bash
# Install dependencies
# No dependency installation is required.

# Run unit tests
bash scripts/check-agent-ready.sh

# Run integration tests
# Not configured during dogfood phase.

# Run e2e tests
# Not configured during dogfood phase.

# Lint shell scripts
bash -n scripts/*.sh

# Typecheck / compile
# Not applicable; this repo contains Markdown, YAML, Bash, and GitHub Actions templates.

# Build
# Not applicable.

# Run local app
# Not applicable during dogfood phase.
```

## Dogfood rules

This repository is the pilot project for the Codex + Multica operating model.

Use Multica issue IDs for all changes, including changes to this template itself. Example: `MUL-123`.

Treat template changes as product changes:

- Update `README.md` when rollout behavior changes.
- Update `AGENTS.md` when agent operating rules change.
- Update `docs/agents/*.md` when review, security, triage, or domain rules change.
- Update `multica/*.yaml` when agent, squad, or autopilot configuration changes.
- Update `.github/workflows/*.yml` when GitHub automation changes.
- Update `scripts/*.sh` when readiness or validation behavior changes.

Do not enable automatic merge. Human review is required for every PR.

Default merge path:

1. Multica issue
2. Branch referencing the Multica issue ID
3. GitHub PR referencing the Multica issue ID
4. `make verify`
5. GitHub `readiness`
6. DeepSeek `review`
7. CodeQL when applicable
8. Human review
9. Human final merge

Checks may run concurrently, but every required check must pass before human
review or final merge. If any required check fails, agents must fix the scoped
failure or report the blocker; do not proceed to human review until all required
checks re-pass.

Agents must not merge PRs, direct push to `main`, or bypass branch protection.
Owner/admin direct push or bypass to `main` is allowed only for narrow
operator-controlled exceptions:

- Emergency rollback of a broken governance or template change.
- Fixing repository configuration that prevents PR creation or CI execution.
- Repairing branch protection, workflow, or repository metadata when the normal PR path is unavailable.
- Human-approved trivial correction where the operator explicitly accepts bypass risk.

Those cases are for human operators only. Agents must never initiate, suggest,
approve, or execute a bypass, even if the conditions appear to match an allowed
exception or a human asks the agent to perform the bypass. If asked to bypass,
agents must stop and ask the human operator to perform the action and record the
required evidence.

After any bypass, record a visible Multica issue comment or follow-up note with
the commit SHA or link, reason for bypass, files changed, validation run or
skipped-validation reason, risk and rollback note, and whether a follow-up PR or
issue is needed. Commit `6878e31` is the motivating example: a human-requested
direct push succeeded while GitHub reported bypassed pull request and required
status check rules.

During dogfood, GitHub PR review uses DeepSeek API instead of OpenAI Codex Action. Do not require `OPENAI_API_KEY` unless the project explicitly switches back to OpenAI Codex Action.

Do not create frontend, backend, database, auth, deployment, or product runtime directories during dogfood unless a Multica issue explicitly moves this repository into the product starter phase.

## Language policy

Use English for durable project artifacts:

- issue titles and descriptions
- branch names
- commit messages
- pull request titles and bodies
- agent system prompts
- code comments
- documentation committed to the repository
- GitHub Actions and script output intended for CI logs

Use Chinese when explaining status, decisions, and next steps directly to the human operator in chat.

When a Multica issue or PR needs both, keep the durable artifact in English and provide a short Chinese summary only in the interactive chat, not in committed files.

## Work intake rules

For every task, identify:

1. Goal — what user-visible or operator-visible behavior changes.
2. Context — issue ID, PR, affected files, logs, screenshots, prior decisions.
3. Constraints — compatibility, security, performance, architecture, non-goals.
4. Done when — tests, CI, review, documentation, deployment notes.

If these are missing and the task is small, make explicit assumptions and proceed conservatively. If the task is high risk, ask for clarification before changing code.

## Change rules

- Prefer small, reviewable changes.
- Do not perform unrelated refactors.
- Do not reformat entire files unless the repository formatter requires it.
- Preserve public API compatibility unless the issue explicitly asks for a breaking change.
- Add or update tests for behavior changes.
- Add a regression test for bug fixes where a correct test seam exists.
- Keep generated files out of commits unless they are already tracked or required by the project.
- Never overwrite human work. Before editing, check current diffs if possible.
- Do not modify `.env`, private credentials, production secrets, or local auth files.

## Security baseline

- Never log secrets, tokens, passwords, session cookies, PII, financial data, medical data, or customer confidential content.
- Authentication checks must occur before sensitive actions.
- Authorization must be resource-specific and tenant-aware.
- Validate and normalize untrusted input at trust boundaries.
- Use parameterized database queries or ORM-safe APIs.
- Avoid shelling out with untrusted input. If unavoidable, escape arguments and add tests.
- Avoid SSRF by using allowlists for outbound URLs and blocking private/internal IP ranges.
- Avoid path traversal by resolving paths and checking containment.
- Do not introduce new dependencies unless justified in the PR.
- For cryptography, use standard libraries. Do not design custom crypto.
- Treat AI-generated code as untrusted until reviewed and tested.

## Data handling rules

- Do not copy production data into tests.
- Use synthetic fixtures.
- Redact secrets and PII in logs, screenshots, PR descriptions, comments, and issue text.
- Do not store credentials in `custom_env`, committed config, `AGENTS.md`, Skill files, or prompts.
- Use short-lived, least-privilege credentials for agent runtimes.

## Testing strategy

Use the test level that proves behavior with the least brittleness.

Preferred order:

1. Unit tests for pure logic.
2. Integration tests through public interfaces.
3. Contract tests for API compatibility.
4. E2E tests for critical user journeys.
5. Manual verification only when automation is impractical; document exact steps.

Avoid tests that assert implementation details, private method calls, arbitrary mocks, or fragile DOM structure unless that is the public contract.

## TDD mode

When the task is a feature or bug fix and the behavior can be tested:

1. Write one failing test for one vertical slice.
2. Run the test and confirm it fails for the expected reason.
3. Write the minimal implementation.
4. Run the test and related checks.
5. Refactor only after green.
6. Repeat for the next slice.

Do not write all tests first and all implementation after. Use thin vertical slices.

## Debugging mode

For bugs:

1. Build a deterministic reproduction loop.
2. Confirm the reproduced symptom matches the user-reported issue.
3. List 3–5 ranked falsifiable hypotheses.
4. Instrument narrowly; tag temporary logs with `[DEBUG-<id>]`.
5. Fix after the cause is identified.
6. Add a regression test where possible.
7. Remove all debug instrumentation.
8. Record the root cause in the PR.

## Review guidelines

Also read `docs/agents/code-review.md` and `docs/agents/security-review.md` when reviewing.

Focus on blocking issues:

- Incorrect behavior
- Security regression
- Data loss or data exposure
- Broken migration or rollback
- Missing tests for risky change
- Public API compatibility break
- Performance regression on hot path
- Deployment or configuration risk

Do not flood reviews with style comments if formatter/linter covers them.

## Pull request requirements

Every PR must include:

- Multica issue ID in branch, title, or body.
- Summary of changes.
- Validation commands and results.
- Risk assessment.
- Rollback notes if applicable.
- Security notes if auth, data, logging, dependencies, network calls, file upload, or tenancy are touched.

## Definition of done

A task is done only when:

- Acceptance criteria are satisfied.
- Relevant tests pass.
- Lint/typecheck/build pass or exceptions are documented.
- Security-sensitive changes have been reviewed.
- PR links to the Multica issue ID.
- Any user-facing behavior change is documented if needed.
- The agent has left a concise summary of changed files, validation, and risks.

## When to stop and escalate

Stop and ask a human when:

- The task requires production access.
- The task requires customer data.
- The issue conflicts with documented architecture decisions.
- There are multiple reasonable product behaviors.
- A migration may cause data loss.
- Security policy requires exception approval.
- The task requires spending money or provisioning cloud resources.
- The repository lacks enough tests to verify a high-risk change.
