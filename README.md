# Codex + Multica Application Development Management Template

This starter kit gives you a concrete operating model for using Multica as the task / routing / collaboration layer and Codex as the coding / review / CI feedback layer.

## What this package contains

```text
.
├── AGENTS.md                                  # Repo-wide durable instructions for Codex and other agents
├── .codex/config.example.toml                 # Safe Codex local/project config starter
├── .agents/skills/                            # Repo-scoped reusable agent skills
├── .github/
│   ├── ISSUE_TEMPLATE/                        # GitHub issue forms if you mirror work to GitHub
│   ├── codex/prompts/                         # Prompts consumed by Codex GitHub Action
│   ├── workflows/                             # CI, Codex review, CodeQL, dependency review
│   ├── dependabot.yml                         # Dependency update configuration
│   └── pull_request_template.md
├── docs/agents/                               # Review rules, domain language, triage labels, ADR format
├── multica/                                   # Agent, squad, autopilot, issue templates
└── scripts/                                   # Helper scripts for CI and readiness checks
```

## Current scope

This repository is currently dogfooding the agent operating layer for Codex + Multica + GitHub.

It intentionally does not include a frontend app, backend API, database schema, authentication system, deployment target, or production runtime.

Those pieces are future scope for turning this template into a full product starter. See `docs/product-starter-roadmap.md`.

## Dogfood loop

1. Create a Multica issue using `multica/issue-template.md`.
2. Include a `MUL-123` style issue ID in the branch and PR.
3. Route unclear work to `codex-scoper`.
4. Route low-risk template changes to `codex-fullstack`.
5. Route workflow or CI failures to `codex-test`.
6. Route security, permissions, dependency, or CI-token changes to `codex-security-reviewer`.
7. Open a GitHub PR.
8. Run CI and Codex review.
9. Human reviews and merges.
10. Patch `AGENTS.md`, `docs/agents/*.md`, or `.agents/skills/*` when an agent repeats a mistake.

## Recommended first rollout

1. Copy this whole folder into a branch in one representative repository.
2. Edit placeholders: project name, issue prefix, test commands, package manager, deployment target, data classification.
3. Put `AGENTS.md`, `.agents/skills`, `.github/codex/prompts`, and `docs/agents` under version control.
4. Import each `.agents/skills/*` folder into Multica as workspace skills, or keep them repo-scoped if you want Codex to load them directly from the repository.
5. Create the Multica agents listed in `multica/agents.yaml` and paste the matching system prompts from `multica/agent-system-prompts/`.
6. Enable GitHub PR linking in Multica. Make every branch, PR title, or PR body include the Multica issue ID, such as `MUL-123`.
7. Add `OPENAI_API_KEY` as a GitHub Actions secret only for the Codex review workflow. Do not store OpenAI keys or production secrets in `AGENTS.md`, Skill files, Multica descriptions, or committed config.
8. Enable CI first, then Codex PR review, then dependency review, then CodeQL.
9. Start with low-risk issues for 1 week. Do not let agents merge code automatically.
10. Every repeated agent mistake becomes a patch to `AGENTS.md`, `docs/agents/*.md`, or a Skill.

## Import guidance for third-party skills

Third-party skills such as `mattpocock/skills` are useful reference material, especially `tdd`, `diagnose`, `grill-with-docs`, `to-issues`, `triage`, and `improve-codebase-architecture`. Do not import them blindly. Review every `SKILL.md`, script, hook, and installer first. Prefer copying the workflow idea into your own shorter company-specific skill.

## Minimal operating rule

Agents may write feature branches, tests, documentation, comments, and PR review feedback. Humans own product direction, architecture acceptance, security exceptions, production deployment, and final merge.
