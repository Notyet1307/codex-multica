# Codex + Multica Application Development Management Template

This starter kit gives you a concrete operating model for using Multica as the task / routing / collaboration layer and Codex as the coding / review / CI feedback layer.

## What this package contains

```text
.
├── AGENTS.md                                  # Repo-wide durable instructions for Codex and other agents
├── .codex/config.example.toml                 # Safe Codex local/project config starter
├── .agents/skills/                            # Shared workspace skill source; not copied to product repos by default
├── .github/
│   ├── ISSUE_TEMPLATE/                        # GitHub issue forms if you mirror work to GitHub
│   ├── codex/prompts/                         # Prompts consumed by Codex GitHub Action
│   ├── workflows/                             # CI, Codex review, CodeQL, dependency review
│   ├── dependabot.yml.disabled                # Parked dependency update configuration
│   └── pull_request_template.md
├── docs/agents/                               # Review rules, domain language, drift audit, triage labels, ADR format
├── multica/                                   # Agent, squad, autopilot, issue templates
└── scripts/                                   # Helper scripts for CI and readiness checks
```

## Current scope

This repository is currently dogfooding the agent operating layer for Codex + Multica + GitHub.

It intentionally does not include a frontend app, backend API, database schema, authentication system, deployment target, or production runtime.

Those pieces are future scope for turning this template into a full product starter. See `docs/product-starter-roadmap.md`.

## Dogfood loop

The first successful dogfood loop has validated the current operating path:

- `MUL-1` fixed CodeQL language selection for this dogfood repository.
- The DeepSeek PR review workflow runs and posts comments.
- `MUL-2` parked Dependency Review until GitHub Dependency Graph is enabled.
- Multica routed work through `OpenAI-scoper`, `OpenAI-fullstack`, and `OpenAI-test`.
- GitHub PRs and checks are the merge gate.

Run the standard local and CI verification entrypoint before opening or updating a PR:

```bash
make verify
```

`make verify` runs the agent readiness check, shell syntax checks, DeepSeek review self-test, unit tests for the repository validators, and structural validation for skills, Multica agent references, Codex prompts, workflows, and README key paths.

Use this checklist for the current issue -> PR -> checks -> merge -> close issue flow:

1. Create a Multica issue using `multica/issue-template.md`.
2. Include a `MUL-123` style issue ID in the branch and PR.
3. Route unclear work to `OpenAI-scoper`.
4. Route low-risk template changes to `OpenAI-fullstack`.
5. Route workflow or CI failures to `OpenAI-test`.
6. Route security, permissions, dependency, or CI-token changes to `OpenAI-security-reviewer`.
7. Open a GitHub PR.
8. Run CI, GitHub `readiness`, DeepSeek `review`, and CodeQL when applicable.
9. Human reviews and performs the final merge.
10. Close the Multica issue after the merged PR has satisfied the issue acceptance criteria.
11. Patch `AGENTS.md`, `docs/agents/*.md`, or `.agents/skills/*` when an agent repeats a mistake.

## Intake spec to issue drafts

Use `docs/agents/project-intake-spec.md` when discussing a larger project,
feature, or architecture direction with GPT Pro before creating Multica issues.
That document is a source spec, not an implementation order.

First-version conversion is local and read-only against Multica:

1. Save the GPT Pro output as a Markdown intake spec.
2. Ask Codex to review it with `ask-matt` / `spec-first-intake`.
3. Generate draft issue files:
   `python3 scripts/intake_to_issue_drafts.py --spec <spec.md> --output-dir artifacts/issues/<topic>`.
4. Review and edit the generated drafts before copying them into Multica.

The generator writes local Markdown drafts and a `manifest.json`. It does not
create Multica issues, call Multica write APIs, or assign agents. Live issue
creation remains a separate human-confirmed workflow.

Current parked and future items:

- Dependabot remains disabled during dogfood. Restore it by renaming `.github/dependabot.yml.disabled` back to `.github/dependabot.yml` after this repository has a real dependency surface to update, GitHub Dependency Graph / Dependency Review are ready, and automated review checks are no longer known-noisy on Dependabot PRs.
- Dependency Review remains disabled until a repository administrator enables GitHub Dependency Graph.
- Product runtime directories remain future scope; this repository is still an agent operating template, not a frontend/backend runtime.
- Branch protection or repository rules may report bypassed pull request or
  required-check rules. `AGENTS.md` contains the mandatory agent-facing rules,
  and the durable detailed policy is documented in
  `docs/personal/branch-protection-policy.md`: default work uses issue ->
  branch -> PR -> all required checks passing -> human review -> human final
  merge; agents must not merge, direct push, suggest bypass, execute bypass, or
  approve bypass; owner/admin bypass is only for narrow operator-approved
  exceptions with recorded evidence.

## Recommended first rollout

Use `docs/agents/new-project-bootstrap-boundary.md` as the source of truth for
what a product repository should inherit from this template and what should stay
owned by the shared Multica workspace.

1. Create a bootstrap branch in one representative repository.
2. Edit placeholders: project name, issue prefix, test commands, package manager, deployment target, data classification.
3. Put repo-local governance, review, CI, and validation files under version control: `AGENTS.md`, `Makefile`, `.github/codex/prompts`, `.github/scripts`, `.github/workflows`, `.github/pull_request_template.md`, an adapted `docs/agents/new-project-bootstrap-boundary.md`, selected additional `docs/agents` per that boundary guide, and the product repo's own validation scripts.
4. Do not copy `.agents/skills`, `multica/agent-system-prompts`, `multica/agents.yaml`, `multica/squads.yaml`, or `multica/autopilots.yaml` into the target product repository. Those files describe the shared live Multica workspace runtime and are maintained from this template repository.
5. Create or select the Multica project for the repository, connect the GitHub repository, and reuse the shared `OpenAI-*` workspace agents, workspace skills, and AppDev Squad.
6. Enable GitHub PR linking in Multica. Make every branch, PR title, or PR body include the Multica issue ID, such as `MUL-123`.
7. Add `DEEPSEEK_API_KEY` as a GitHub Actions secret for DeepSeek-based PR review during dogfood. Do not store API keys or production secrets in `AGENTS.md`, Skill files, Multica descriptions, or committed config.
8. Enable CI first, then Codex PR review, then GitHub Dependency graph, then dependency review, then CodeQL, then Dependabot. The dependency review workflow is parked as `.github/workflows/dependency-review.yml.disabled` until a repository administrator enables `Settings` > `Advanced Security` > `Dependency Graph`; Dependabot is parked as `.github/dependabot.yml.disabled` until dependency update PRs have a real package/runtime surface and stable automated review checks.
9. Start with low-risk issues for 1 week. Do not let agents merge code automatically.
10. Every repeated agent mistake becomes a patch to the appropriate source of truth: project-specific behavior goes into the product repository's `AGENTS.md`, roadmap, docs, or validation; shared agent, skill, squad, and live configuration behavior goes into this template repository.

## Multica live configuration drift

Repository files are source templates. They do not automatically update live
Multica workspace agents, skills, squads, or autopilots.

When a PR changes `multica/agent-system-prompts/`, `.agents/skills/`,
`multica/agents.yaml`, `multica/squads.yaml`, or `multica/autopilots.yaml`, run
the read-only audit helper documented in
`docs/agents/multica-live-config-sync.md`. Start with
`python3 scripts/audit-multica-live-config.py --repo-only`; use
`python3 scripts/audit-multica-live-config.py --live --no-secrets` only when
the local `multica` CLI is explicitly authenticated and configured for the
target SaaS workspace. The helper does not read browser sessions, Dia/Desktop
app state, cookies, or rendered web UI. Live workspace updates are separate
operator actions after review and merge. Do not add automatic live sync or
mutation behavior from this repository without a future explicit issue.

The same document also defines the human-confirmed plan/apply workflow. The
current helper is `scripts/sync-multica-live-config.py`: use `plan` to generate
a redacted review artifact and `apply` only after the exact confirmation string
is provided. `apply` also requires `MULTICA_SYNC_ALLOWED=true` as an accidental
execution guard. `plan` requires a clean worktree so the source commit SHA
matches the content being proposed for sync. Its syncable fields are limited to
agent instructions and skill content. It does not sync concurrency, model,
runtime, visibility, squads, autopilots, names, secrets, or `custom_env`.

Before copying prompt or skill text into Multica, make sure the local clone is
current with remote `main`; stale clones can reintroduce old Handoff Back or
Context pack instructions. The audit markers should preserve this distinction:
Handoff Back is the detailed evidence report, and Context pack is the compact
resume state.

Current Dogfood agent prompt mapping:

`system_prompt_file` values are literal repo-local paths. Do not infer prompt
paths from workspace agent names or prompt file basenames.

| Workspace agent name | Repo-local prompt file |
| --- | --- |
| `OpenAI-scoper` | `multica/agent-system-prompts/codex-scoper.md` |
| `OpenAI-fullstack` | `multica/agent-system-prompts/codex-fullstack.md` |
| `OpenAI-frontend` | `multica/agent-system-prompts/codex-frontend.md` |
| `OpenAI-backend` | `multica/agent-system-prompts/codex-backend.md` |
| `OpenAI-test` | `multica/agent-system-prompts/codex-test.md` |
| `OpenAI-security-reviewer` | `multica/agent-system-prompts/codex-security-reviewer.md` |
| `OpenAI-release-manager` | `multica/agent-system-prompts/codex-release-manager.md` |

## Import guidance for third-party skills

Third-party skills such as `mattpocock/skills` are useful reference material, especially `tdd`, `diagnose`, `grill-with-docs`, `to-issues`, `triage`, and `improve-codebase-architecture`. Do not import them blindly. Review every `SKILL.md`, script, hook, and installer first. Prefer copying the workflow idea into your own shorter company-specific skill.

## Minimal operating rule

Agents may write feature branches, tests, documentation, comments, and PR review feedback. Agents must not merge, direct push, or bypass branch protection. Humans own product direction, architecture acceptance, security exceptions, production deployment, owner/admin bypass approval, and final merge.
