# Repo-Scoped Agent Skills

These skills define reusable workflows for Codex and Multica agents in this template.

## Target Skill Kernel

| Skill | Status |
| --- | --- |
| `spec-first-intake` | Present. Primary intake entrypoint for ambiguous, multi-step, risky, or oversized work that needs a Multica-ready spec, routing decision, or child issue split. |
| `tdd-vertical-slice` | Present. Test-first feature and bug-fix implementation. |
| `systematic-debugging` | Planned. |
| `verification-before-completion` | Planned. |
| `security-pr-review` | Present. Security review for sensitive PRs and changes. |
| `context-pack` | Planned. |

## Transitional Skills

- `issue-slicing` - replaced by `spec-first-intake` for new intake, kept for compatibility.
- `multica-issue-brief` - replaced by `spec-first-intake` for new intake, kept for compatibility.

Other repo-specific support skills remain available for current routing, including `architecture-review`, `ci-failure-triage`, and `release-notes-drafter`.
