# Main Branch Protection and Bypass Policy

## Default merge path

Every repository change should use the normal governed path:

1. Create or identify the Multica issue.
2. Create a branch that references the Multica issue ID.
3. Open a GitHub PR that references the Multica issue ID.
4. Run `make verify`.
5. Wait for the GitHub `readiness` check.
6. Wait for the DeepSeek `review` check.
7. Wait for CodeQL when it applies.
8. Complete human review.
9. Let a human perform the final merge.

Checks may run concurrently, but every required check must pass before human
review or final merge. If any required check fails, the failure must be fixed or
reported as a blocker before review proceeds.

Agents must not merge PRs, direct push to `main`, or bypass branch protection.
Agents may prepare branches, commits, validation evidence, PRs, and review
notes for human review.

## Owner and admin bypass

Direct push or branch protection bypass to `main` is allowed only for narrow
operator-controlled exceptions. It is not the normal path for feature work,
workflow changes, skill changes, agent configuration changes, or governance
changes.

Allowed bypass cases:

- Emergency rollback of a broken governance or template change.
- Fixing repository configuration that prevents PR creation or CI execution.
- Repairing branch protection, workflow, or repository metadata when the normal
  PR path is unavailable.
- Human-approved trivial correction where the operator explicitly accepts bypass
  risk.

Bypass does not transfer merge authority to agents. Human final merge ownership
still applies to normal PRs, and only a human operator may approve a bypass.
Agents must never initiate, suggest, approve, or execute a bypass, even if the
conditions appear to match an allowed exception or a human asks the agent to
perform the bypass.

## Required evidence after bypass

After any direct push or branch protection bypass, record a visible Multica issue
comment or follow-up note with:

- The commit SHA or commit link.
- The reason for bypass.
- The files changed.
- The validation run, or the explicit reason validation was skipped.
- The risk and rollback note.
- Whether a follow-up PR or issue is needed.

Commit `6878e31` is the motivating example for this policy. That direct push was
human-requested and renamed the new repository bootstrap checklist, while GitHub
reported bypassed rules for pull request and required status check enforcement.
Future bypasses must leave the evidence above so the exception remains auditable.
