# Multica Live Configuration Sync Audit and Design

This repository stores source templates for Multica agents, skills, squads, and
autopilots. A repository PR does not update already-created Multica workspace
objects by itself.

Live Multica configuration changes are separate operator actions. Do not build
or run automatic live sync, write, import, or mutation behavior from this
repository unless a future issue explicitly scopes that tool and its review
path.

## Source Templates

Treat these repository paths as desired-state templates:

- `multica/agent-system-prompts/` contains agent system prompt text to paste or
  import into live Multica agents.
- `.agents/skills/` contains repo-scoped skill templates that may also be
  imported into Multica workspace skills.
- `multica/agents.yaml` maps live workspace agent names to repo-local prompt
  files and skill bindings.
- `multica/squads.yaml` describes desired squad routing, leader, and member
  roles.
- `multica/autopilots.yaml` describes desired autopilot triggers, modes,
  assignees, and prompts.

The live workspace is authoritative for what agents actually run today. The
repository is authoritative for reviewed template changes after they merge.
Drift exists whenever those two states differ.

## Design Boundary

The repository includes read-only audit behavior and a human-confirmed sync
helper. The sync helper is not automatic live sync: `plan` is read-only, and
`apply` is a separate operator action guarded by exact confirmation and
`MULTICA_SYNC_ALLOWED=true`. This workflow does not approve imports, automatic
sync, browser automation, session capture, or writes beyond the allowlisted
first-version fields below.

The first syncable fields are intentionally narrow:

| Repository source | Live object | Syncable field |
| --- | --- | --- |
| `multica/agent-system-prompts/<agent-prompt>.md` | Multica agent | agent instructions |
| `.agents/skills/<skill-name>/SKILL.md` | Multica skill | skill content |

All other fields and resources remain manual or future work. The first version
must not update `custom_env`, secrets, tokens, credentials, cookies, API keys,
runtime config, model, visibility, concurrency, status, agent names, skill
names, create/delete/archive/restore state, squad membership, squad routing,
autopilot triggers, autopilot schedules, autopilot assignees, autopilot modes,
autopilot titles, or autopilot prompts.

## Human-Confirmed Sync Workflow

A future sync helper must keep `plan` and `apply` separate:

1. **Audit**: run the existing read-only drift audit to identify stale, missing,
   extra, unavailable, or unknown live objects. Audit output is evidence only;
   it does not authorize writes.
2. **Plan**: create a read-only sync plan from the reviewed repository commit
   and current live state. The local worktree must be clean so the plan's
   source commit SHA exactly identifies the repository content being proposed
   for sync. The plan may inspect repo files and live Multica objects through
   allowlisted read commands, then write a local plan artifact such as
   `/tmp/multica-sync-plan.json`. It must not write to the live workspace.
3. **Human confirm**: require an operator to inspect the plan and provide an
   exact confirmation string before any apply attempt:

   ```text
   APPLY <workspace-id> <source-commit-sha>
   ```

   A yes/no prompt, default flag, environment variable, saved preference, or
   PR approval is not enough. The confirmation string must match the workspace
   id and source commit SHA embedded in the plan.
4. **Apply**: immediately re-read the live object before each proposed update,
   verify that the live object still matches the plan, and update only the
   allowlisted field explicitly present in the approved plan. If any stale-state
   or scope check fails during preflight, abort the apply before writing any
   object and report the blocker.
5. **Evidence**: emit redacted sync evidence suitable for a Multica issue or PR
   comment. Evidence must say exactly what changed, what did not change, and
   how to validate or roll back.

Current command shape:

```bash
python3 scripts/sync-multica-live-config.py plan --output /tmp/multica-sync-plan.json
MULTICA_SYNC_ALLOWED=true MULTICA_SYNC_ALLOW_INLINE_TRANSPORT=true python3 scripts/sync-multica-live-config.py apply --plan /tmp/multica-sync-plan.json --confirm "APPLY <workspace-id> <source-commit-sha>"
```

The helper is intentionally narrow. It can plan and apply only the first
syncable fields listed above: live agent `instructions` and live skill
`content`. It must not apply concurrency differences. For this dogfood
workspace, `multica/agents.yaml` records the desired live concurrency limit of
6, but the sync helper treats concurrency as out of scope and never writes it.
If the plan detects concurrency or another out-of-scope drift, it must report an
`out_of_scope_drift` warning so the operator can decide whether a separate
manual action or follow-up is required.

The code-level source of truth for syncable fields, forbidden fields, exact
confirmation, write-command allowlisting, and inline write-value validation is
`scripts/live_sync_policy.py`. Future sync expansion must update that policy
module and its tests before changing apply behavior.

`apply` is a live operator action and requires `MULTICA_SYNC_ALLOWED=true` in
addition to the exact confirmation string. This environment variable is not a
substitute for human review; it is an extra guard against accidental agent or
terminal execution. Because the current Multica CLI accepts agent instructions
and skill content only as command arguments, inline prompt/skill writes also
require `MULTICA_SYNC_ALLOW_INLINE_TRANSPORT=true`. That second guard is an
explicit operator acknowledgement that prompt and skill content can be visible
in process arguments while the CLI process runs. Remove that guard after the
CLI supports file or stdin transport for these fields. The helper still rejects
empty, oversized, and secret-like values before any write runner is allowed. Do
not put secrets in prompt or skill templates.

## Sync Plan Contract

The plan must include one entry per proposed field update. Each entry must be
reviewable without exposing secrets or full live prompt bodies in shared issue
or PR comments.

Each plan entry must include:

- workspace id
- source repository
- source commit SHA
- repo file path
- live object type
- live object name
- live object id
- field proposed for update
- old live hash
- new repo hash
- redacted diff summary
- marker changes when the change affects Handoff Back, Context pack, audit,
  sync, or safety wording
- exact future CLI command class that would be used, such as `multica agent
  update` for agent instructions or `multica skill update` for skill content
- rollback note
- fields explicitly not touched
- out-of-scope drift warnings, such as concurrency differences that require a
  separate operator decision

The plan must not include shell-ready write commands, raw secrets, live
`custom_env`, credentials, browser session data, cookies, or unredacted live
workspace payloads. Hashes should be computed over normalized field content so
apply can detect stale live state precisely.

## Apply Safety Checks

Before apply writes, the helper must verify:

- the `multica` CLI is authenticated for the intended workspace
- the workspace id matches the plan
- the local source commit still matches the plan
- the live object id still matches the plan
- the old live hash still matches the plan
- the target field is allowlisted for the first sync scope
- the approved plan contains no `custom_env`, secrets, runtime config, model,
  visibility, concurrency, status, name, squad, or autopilot fields
- the write command class is allowlisted for the first sync scope
- all output is redacted before it is printed, saved, or posted
- `MULTICA_SYNC_ALLOWED=true` is present for the apply command
- inline prompt or skill content is not oversized and does not contain
  secret-like assignment text

Apply must preflight every approved plan entry before writing. It must update
only fields explicitly present in the approved plan and abort on stale live
state instead of overwriting a live object that changed after the plan was
generated. It must not broaden scope based on detected drift; new drift requires
a new plan and confirmation.

## Evidence and Rollback

Every future apply attempt must produce evidence with:

- workspace id
- source commit SHA
- operator
- UTC timestamp
- objects updated
- fields updated
- old hash -> new hash
- validation after sync
- rollback note
- confirmation that no `custom_env`, secrets, runtime config, model,
  visibility, concurrency, names, squads, or autopilots were changed

Rollback is a human-confirmed operator action, not an automatic background
sync. Prefer rolling forward with a reviewed repository commit and a new plan.
If the previous live value was not represented by a reviewed repository commit,
the operator must use a separately retained private backup or manual live
workspace history; shared issue or PR evidence should contain hashes and
redacted summaries, not sensitive full live content.

## Manual Sync Checklist

Use this checklist after any PR changes the template paths above.

- [ ] Confirm the local clone used for copy or import is current before copying
      prompt or skill text into Multica. Run `git fetch origin main`, inspect
      `git status --short --branch`, and use `git pull --ff-only` on stale
      local clones before copying from `main`.
- [ ] Review `git diff --name-only origin/main...HEAD` and confirm the changed
      files are limited to the approved issue scope.
- [ ] Include the repo audit command result in the PR or Multica handoff
      evidence when prompt, skill, agent, squad, or autopilot templates change.
      This is the review-time evidence path for repository markers. CI cannot
      prove live workspace state.
- [ ] If `multica/agent-system-prompts/` changed, update the corresponding live
      Multica agent system prompt as a separate operator action after the PR is
      reviewed and merged.
- [ ] If `.agents/skills/` changed, update or import the corresponding live
      Multica workspace skill as a separate operator action after the PR is
      reviewed and merged.
- [ ] If `multica/agents.yaml` changed, compare live agent names, prompt text,
      visibility, concurrency, and skill bindings against the reviewed YAML.
- [ ] If `multica/squads.yaml` changed, compare live squad leader, member list,
      roles, and routing instructions against the reviewed YAML.
- [ ] If `multica/autopilots.yaml` changed, compare live autopilot mode,
      trigger, schedule, assignee, title, and prompt against the reviewed YAML.
- [ ] Confirm no sync step requires secrets, tokens, cookies, browser session
      capture, production data, agent renames, skill renames, or live runtime
      behavior changes beyond the reviewed operator action.
- [ ] Record the manual sync outcome in the Multica issue or PR only after the
      operator action is complete. Include the source commit SHA, operator,
      UTC timestamp, live objects checked or updated, relevant markers or
      equivalent wording checked, discrepancies found, and rollback or
      follow-up notes.

Agents may prepare the audit evidence and PR. Humans or explicitly authorized
operators own live workspace updates.

## Verification Markers

When auditing live prompts or skills for current handoff behavior, look for
these marker phrases or equivalent current wording in the live Multica object:

- `Handoff Back is the detailed evidence report`
- `Context pack is the compact resume state`
- `## Context pack`
- `compact index to the Handoff Back and PR`
- `git diff --name-only origin/main...HEAD`

Check each live object against the markers relevant to that object instead of
requiring every live object to contain every phrase. For example, agent prompts
may use `compact index to the Handoff Back and PR`, while skills may use
`compact resume state` wording.

Use the markers to confirm the distinction is preserved:

- Handoff Back carries detailed implementation evidence: work performed,
  changed files, validation, scope check, risks, rollback notes, PR URL, and
  readiness.
- Context pack is compact resume state: the current goal, status, constraints,
  next action, open questions, and source artifacts to inspect next.
- Context pack should reference Handoff Back or PR evidence instead of
  duplicating full validation logs, changed-file evidence, risk analysis, or
  scope comparison.

For this dogfood template, the most important live objects to audit are:

- `OpenAI-scoper` prompt from `multica/agent-system-prompts/codex-scoper.md`
- `OpenAI-fullstack` prompt from
  `multica/agent-system-prompts/codex-fullstack.md`
- `spec-first-intake` skill from `.agents/skills/spec-first-intake/SKILL.md`
- `context-pack` skill from `.agents/skills/context-pack/SKILL.md`
- `verification-before-completion` skill from
  `.agents/skills/verification-before-completion/SKILL.md`

## Read-Only Drift Audit Helper

Run the repo-only audit any time documentation, prompt, skill, or Multica
template paths change:

```bash
python3 scripts/audit-multica-live-config.py --repo-only
```

`--repo-only` does not require Multica authentication or live workspace access.
It parses repository templates and checks the Handoff Back / Context pack marker
wording in local docs, prompts, and skills. Live object status is reported as
`unknown` because no live comparison was attempted.

When live Multica CLI read access is available, run the optional live audit:

```bash
python3 scripts/audit-multica-live-config.py --live --no-secrets
```

The live audit is an occasional operator-triggered check, not a daemon,
monitor, or CI-required gate. It reads SaaS Multica workspace state only through
an explicitly authenticated local `multica` CLI with a configured
`workspace_id` or `MULTICA_WORKSPACE_ID`. It does not read browser sessions,
Dia/Desktop app state, cookies, or rendered web UI. If CLI authentication,
workspace configuration, network access, or permissions are unavailable, the
helper reports `unavailable` instead of attempting login, browser automation,
sync, or mutation.

The live audit may call only read-only Multica CLI commands:

- `multica agent list --output json`
- `multica skill list --output json`
- `multica skill get <id> --output json`
- `multica squad list --output json`
- `multica squad get <id> --output json`
- `multica autopilot list --output json`
- `multica autopilot get <id> --output json`

The helper must not call Multica create, update, delete, import, sync, trigger,
environment, or member mutation commands. It also must not read or print
`custom_env`, API key, token, credential, cookie, password, or session values.
Reports include object names, statuses, and field-level drift labels, not live
prompt or skill bodies.

Before executing the Multica CLI, the helper resolves `multica` to an absolute
binary path. It refuses repo-local binaries and paths outside the trusted
installation directories used by the Multica desktop app and common system/user
CLI locations, including normal Homebrew `bin` symlinks that resolve into the
Homebrew `Cellar/multica` package directory. If the binary cannot be resolved
safely, the live audit reports `unavailable` instead of executing it.

Status meanings:

- `current`: live and repo values match for the fields checked.
- `stale`: the live object exists but one or more checked fields differ.
- `missing`: the repo template has no matching live object.
- `extra`: the live workspace has an object with no matching repo template.
- `unavailable`: Multica CLI access or a required live read result was not
  available.
- `unknown`: the helper could not determine drift, usually because it ran in
  repo-only mode or the live CLI does not expose that field.

Keep `make verify` independent from Multica auth. It may validate the helper and
its command allowlist locally, but it must not require live workspace access.

## Marker Audit Command

As a lightweight local supplement, this marker search can confirm that
repository guidance and templates still contain expected drift, sync, and
handoff wording:

```bash
rg -n "Multica live|live configuration|sync|drift|agent-system-prompts|.agents/skills|Handoff Back|Context pack|compact resume|manual sync|stale local" README.md AGENTS.md NEW-REPO-BOOTSTRAP-CHECKLIST.md docs .agents multica scripts tests
```

This command does not prove the live workspace is current. It only confirms
that local marker wording is present.

## Stop Conditions

Stop and ask a human before proceeding if a sync or audit would require:

- modifying live Multica workspace configuration from an agent run
- a Multica API token, browser session, cookie, or other credential
- renaming existing agents, skills, prompt files, squad names, or autopilots
- changing automatic sync behavior or adding live write automation
- touching repositories or workspaces outside the issue scope
- copying from a stale or dirty local clone whose source revision is unclear
