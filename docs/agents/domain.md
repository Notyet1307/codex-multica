# Domain Language for Agents

Use this file to keep product and engineering language consistent.

## Glossary

| Term | Meaning | Avoid saying | Notes |
|---|---|---|---|
| Template | This repository: the reusable Codex + Multica + GitHub operating model | boilerplate | Template changes affect future rollout quality. |
| Dogfood | Using this repository as its own pilot project | self-test only | Dogfood work must go through Multica issues and PRs. |
| Agent operating layer | Rules, skills, prompts, workflows, and routing for agent collaboration | app runtime | Current scope of this repo. |
| Product starter | Future full-stack app template with frontend, backend, database, auth, tests, and deployment | current app | Future scope only during dogfood. |
| Multica issue | The source of truth for requested work | GitHub issue as source of truth | GitHub may mirror or link work, but Multica owns intake. |
| Agent | A configured Codex worker in Multica | bot | Agents have bounded roles and must not auto-merge. |
| Squad | A Multica routing group led by `OpenAI-scoper` | team | The squad routes issues to the narrowest competent owner. |
| Autopilot | A Multica automation that creates or updates issues | cron job only | Prefer create-issue mode for auditability. |
| Readiness check | `scripts/repository_readiness.py` with `scripts/check-agent-ready.sh` as the Bash adapter | test suite | Verifies required template files, workflow policy markers, and bundled skills exist and are usable. |
| Bootstrap boundary | The copy/adapt/do-not-copy decision for applying this template to a product repository | copying the whole template | See `docs/agents/new-project-bootstrap-boundary.md`. |

## Bounded contexts

| Context | Owns | Does not own | Main directories |
|---|---|---|---|
| Agent operating rules | Durable instructions and review policy | Product runtime code | `AGENTS.md`, `docs/agents/` |
| Multica configuration | Agents, squads, autopilots, issue templates | GitHub Actions execution | `multica/` |
| GitHub automation | CI, Codex review, security review, dependency review | Multica routing policy | `.github/` |
| Repo-scoped skills | Reusable agent workflows bundled with this template | Third-party skill source of truth | `.agents/skills/` |
| Readiness scripts | Local validation helpers | Full CI simulation | `scripts/` |
| Future product starter | Planned frontend, backend, database, auth, deployment, and tests | Current dogfood scope | `docs/product-starter-roadmap.md` |

## Decision log pointers

ADRs live in `docs/adr/`. Use short ADRs for decisions future agents may otherwise re-litigate.
