# Multica Live Configuration Sync Audit

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

## Manual Sync Checklist

Use this checklist after any PR changes the template paths above.

- [ ] Confirm the local clone used for copy or import is current before copying
      prompt or skill text into Multica. Run `git fetch origin main`, inspect
      `git status --short --branch`, and use `git pull --ff-only` on stale
      local clones before copying from `main`.
- [ ] Review `git diff --name-only origin/main...HEAD` and confirm the changed
      files are limited to the approved issue scope.
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
      operator action is complete.

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

## Repo Audit Command

Run this local read-only audit after documentation, prompt, skill, or Multica
template changes:

```bash
rg -n "Multica live|live configuration|sync|drift|agent-system-prompts|.agents/skills|Handoff Back|Context pack|compact resume|manual sync|stale local" README.md AGENTS.md NEW-REPO-BOOTSTRAP-CHECKLIST.md docs .agents multica scripts tests
```

This command does not prove the live workspace is current. It only confirms
that repository guidance and templates still contain the expected drift, sync,
and handoff markers.

## Stop Conditions

Stop and ask a human before proceeding if a sync or audit would require:

- modifying live Multica workspace configuration from an agent run
- a Multica API token, browser session, cookie, or other credential
- renaming existing agents, skills, prompt files, squad names, or autopilots
- changing automatic sync behavior or adding live write automation
- touching repositories or workspaces outside the issue scope
- copying from a stale or dirty local clone whose source revision is unclear
