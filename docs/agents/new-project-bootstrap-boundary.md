# New Project Bootstrap Boundary

Use this guide when applying the Codex + Multica + GitHub operating model to a
new product repository.

The default assumption is a shared Multica workspace: live Multica agents,
workspace skills, squads, and workspace-level autopilots are maintained from
this template repository. A product repository should inherit the governance and
review loop, then record only product-specific facts, validation, roadmap, and
safety boundaries.

## Default Profile

Use this profile for normal product repositories in the same Multica workspace.

| Template path or area | Target product repository action | Reason |
| --- | --- | --- |
| `AGENTS.md` | Copy and adapt | The product repo needs durable local operating rules, project facts, commands, data classification, and stop conditions. |
| `Makefile` | Copy and adapt | The product repo should expose `make verify` as the standard local and CI verification entrypoint. |
| `README.md` | Create or adapt | The product repo needs its own purpose, bootstrap state, and operator instructions. Do not keep template-specific dogfood history. |
| `.github/pull_request_template.md` | Copy and adapt | Every PR should report summary, validation, risk, rollback, and security notes. |
| `.codex/config.example.toml` | Optional | Copy only if the product repo wants a safe repo-local Codex config starter. |
| `.github/codex/prompts/` | Copy and adapt if GitHub review workflows use them | These are repo-local review and triage prompts, not live Multica agent prompts. |
| `.github/scripts/deepseek_pr_review.py` and `.github/scripts/review_decision.py` | Copy if using DeepSeek PR review | The review workflow depends on both the provider adapter and the review decision policy. |
| `.github/workflows/ci.yml` | Copy and adapt | The readiness job must run the product repo's real `make verify`. |
| `.github/workflows/deepseek-pr-review.yml` | Copy and adapt if using DeepSeek PR review | The product repo needs its own GitHub review check and `DEEPSEEK_API_KEY` secret. |
| `.github/workflows/codeql.yml` | Copy and adapt | The languages must match the product repo's real stack. |
| `.github/dependabot.yml.disabled` and `.github/workflows/dependency-review.yml.disabled` | Optional parked copy | Copy only when the product repo wants reviewed placeholders for future dependency automation. Keep them disabled until the repo has a real dependency surface, GitHub Dependency Graph is enabled, and automated review checks are stable. |
| `.github/ISSUE_TEMPLATE/` | Optional | Use only if the product repo mirrors work into GitHub issues. Multica remains the source of truth for intake. |
| `docs/agents/` | Copy the general policy docs and adapt project-specific language | Review, security, issue tracker, PR, domain, and ADR rules are useful in product repos, but template-only live sync docs may not apply. |
| `scripts/` | Copy only repo-local validation helpers needed by the product repo | Do not copy template-only live sync, audit, or template-catalog scripts unless the product repo intentionally forks live workspace configuration. |
| `docs/roadmap.md` or equivalent | Create in the target repo | The product repo needs its own roadmap and phase boundaries. Do not copy this template repo's dogfood roadmap as product truth. |

## Do Not Copy by Default

These paths describe the shared live Multica workspace runtime or this template
repository's dogfood maintenance surface. They should stay in this template
repository unless a future issue explicitly creates a project-specific fork.

| Template path or area | Default action | Reason |
| --- | --- | --- |
| `.agents/skills/` | Do not copy | Workspace skills are shared live objects maintained from this template repository. Product repos should reuse the live workspace skills. |
| `multica/agent-system-prompts/` | Do not copy | These are shared live agent prompt templates, not product repo code. |
| `multica/agents.yaml` | Do not copy | Live workspace agent definitions are shared across projects in the workspace. |
| `multica/squads.yaml` | Do not copy | Squad routing is shared workspace configuration. |
| `multica/autopilots.yaml` | Do not copy | Workspace autopilots are shared automation. |
| `scripts/audit-multica-live-config.py` | Do not copy | Drift detection for shared live Multica configuration belongs in this template repository. |
| `scripts/sync-multica-live-config.py` and `scripts/live_sync_policy.py` | Do not copy | Human-confirmed live sync is an operator workflow for shared workspace config, not normal product repo maintenance. |
| `scripts/template_catalog.py` | Do not copy by default | It supports template repo audit/sync/validation surfaces. Product repos should have their own simpler validation helpers. |
| `docs/personal/` | Do not copy | These are dogfood and operator notes for this template repository. |
| Template dogfood issues, PR evidence, or live sync plans | Do not copy | They are historical evidence, not reusable product repository state. |

## Optional Fork Profile

Use a project-specific fork of live Multica configuration only when a human
explicitly decides that the project needs its own agent prompts, workspace
skills, squad routing, or autopilots.

That decision must be recorded before copying any of these paths:

- `.agents/skills/`
- `multica/agent-system-prompts/`
- `multica/agents.yaml`
- `multica/squads.yaml`
- `multica/autopilots.yaml`
- live sync audit or apply scripts

The fork decision must state:

- why shared workspace agents or skills are insufficient
- which live objects become project-specific
- who owns future live sync and drift audits
- how the product repo avoids storing secrets, tokens, cookies, `custom_env`,
  or workspace credentials
- how the fork will be validated before any human merge

Absent that decision, keep using the default shared-workspace profile.

## Bootstrap PR Checklist

For the first product repository PR:

1. Copy and adapt only the default-profile files.
2. Remove template dogfood history, operator-only docs, and unused workflow
   surfaces.
3. Replace product facts in `AGENTS.md`, `README.md`, and roadmap docs.
4. Make `make verify` run the target repository's actual validation.
5. Keep product-specific safety rules in the product repo.
6. Keep shared agent prompt, skill, squad, autopilot, and live sync changes in
   this template repository.
7. Run `make verify` in the target repo.
8. Confirm the product repo does not contain default-excluded shared runtime
   paths unless the optional fork profile was explicitly approved.
9. From this template repository, run the product bootstrap boundary check
   against the target repo:

   ```bash
   python3 scripts/repository_readiness.py --profile product-bootstrap --root <target-repo>
   ```

10. Open a bootstrap PR and wait for readiness, review, CodeQL, and human
    review.

## Boundary Validation

The template readiness checker has two profiles:

- `template` validates this template repository's own required files, workflow
  markers, and bundled shared workspace skills.
- `product-bootstrap` validates that a target product repository does not carry
  default-excluded shared Multica runtime paths.

Use the product bootstrap profile from this template repository before opening
or reviewing a target product repository bootstrap PR:

```bash
python3 scripts/repository_readiness.py --profile product-bootstrap --root <target-repo>
```

This check fails if the target repository contains shared live workspace source
paths such as `.agents/skills/`, `multica/agent-system-prompts/`,
`multica/agents.yaml`, `multica/squads.yaml`, `multica/autopilots.yaml`, or the
template-only live audit/sync helpers. It does not replace the target repo's own
`make verify`; it is an export-boundary guard.

## Drift Handling

If a product issue reveals that shared live Multica behavior is stale or wrong,
do not patch product repo copies of prompts, skills, agents, squads, or
autopilots. Instead:

1. Open a template repository change for the shared prompt, skill, squad, or
   autopilot template.
2. Merge it through the normal template PR path.
3. Run the read-only drift audit from this template repository.
4. Use the human-confirmed live sync workflow only when a human operator
   explicitly approves the apply action.
5. Record the sync evidence in the template repository PR or follow-up note.
