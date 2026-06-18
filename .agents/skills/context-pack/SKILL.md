---
name: context-pack
description: Use before handoff, pause, delegation, review, or resume when a future agent or human needs compact durable context without rereading the full issue, PR, terminal log, or conversation.
---

# Context Pack

Use this skill to package the minimum durable context needed for a future agent
or human to continue work without replaying every prior comment, terminal log,
diff, or discussion. A context pack is a compact save point and index, not a
transcript, repository dump, or second copy of Handoff Back.

When a Handoff Back or PR already contains the full evidence report, the context
pack should be a compact resume state. Reference the Handoff Back or PR for full
validation, changed-file, scope, and risk evidence instead of duplicating those
details, while still preserving the facts needed to resume.

## When to use

Use this skill when:

- handing work from one agent to another
- pausing a non-trivial task that may resume later
- delegating implementation, test, review, security, or release work
- preparing a PR or issue for review after meaningful investigation or changes
- recovering from a long issue thread, PR discussion, or terminal session
- preserving decisions, constraints, validation evidence, risks, and next steps
  that future agents are likely to need

## When not to use

Do not use this skill when:

- the task is a trivial single-step reply with no durable follow-up value
- Handoff Back or PR evidence already gives a fresh, complete state and no
  continuation state would be lost
- the work is one-pass complete, has complete Handoff Back, and has no follow-up
- the work is a pure acknowledgement, sign-off, or thanks
- producing the pack would require reading secrets, private credentials,
  customer data, production data, or other sensitive material
- the next step is obvious and no meaningful context would be lost
- a full transcript, broad repository dump, generated context bundle, or
  external analysis artifact is being requested

## Design references

This skill adapts small workflow ideas from local and external references:

- Existing local `spec-first-intake`: concise context handoff for delegated work.
- Existing local `verification-before-completion`: evidence-first reporting and
  explicit readiness state.
- Existing local `systematic-debugging`: root-cause evidence, hypothesis state,
  and reproduction status.
- Existing local `security-pr-review`: risk surfaces and security-sensitive
  follow-up routing.
- mattpocock/skills style handoff discipline: reference existing artifacts
  instead of duplicating all context.
- gstack-style save/restore workflow boundaries: durable save points and
  explicit next commands.
- Repomix-style context bundles as inspiration only: compact context packaging,
  without adding Repomix or generated repository dumps.

Do not copy third-party files, skill text, prompts, scripts, hooks, installers,
dependencies, or global state. Do not add external tools. Do not import
Repomix, gstack, mattpocock/skills, PR-Agent, Open SWE, Superpowers, or any
third-party skill repository. Adapt only the smallest useful workflow ideas into
repo-local instructions.

## Context pack workflow

1. Identify the issue, task, PR, branch, and current owner if available.
2. Read the latest issue scope, Handoff Back, PR status, and validation
   evidence.
3. Decide whether a separate context pack is useful. If Handoff Back or PR
   evidence already contains the durable state and there is no continuation,
   omit the pack.
4. Summarize only durable facts, decisions, constraints, and unresolved
   questions.
5. Point to the decisive Handoff Back comment, PR, or artifact that contains
   detailed validation, changed-file, scope, security, and risk evidence.
6. Include changed validation, changed scope, stale evidence, ambiguity, or
   unavailable evidence only when it affects the next action.
7. Link or reference source artifacts, Handoff Back, or PR evidence instead of
   duplicating full content.
8. State what the next agent or human should do next.
9. State what should not be changed or re-litigated.
10. Return a fixed context pack only when the pack adds durable continuation
    value.

## Evidence requirements

A compact context pack must include available evidence for:

- issue, PR, branch, and current status
- allowed scope or affected area
- key decision or current assumption the next owner should preserve
- the source artifact that contains full evidence
- validation status, especially whether detailed evidence is fresh, stale,
  unavailable, or changed after Handoff Back
- constraints, non-goals, and explicit stop conditions
- open questions and next recommended action

If a field is unavailable, say `Unavailable` or `Not applicable` and briefly
explain why. Do not invent evidence to make the pack look complete.

Available evidence does not mean copying the full Handoff Back into the context
pack. If Handoff Back or the PR already contains detailed validation logs,
changed-file output, scope comparison, and risk notes, summarize the current
state and reference that source for full evidence.

Use the full resume form only when no Handoff Back or PR evidence exists and the
next agent would otherwise lack required state.

## Scope and constraints

Keep the pack compact. Include the durable facts a future agent needs to avoid
repeating work, not every step taken during the run.

Prefer references over duplication:

- Multica issue key or issue link instead of copied issue descriptions
- PR URL and branch instead of pasted diffs
- Handoff Back comment instead of repeated changed-file, scope, validation,
  security, and risk detail
- exact validation command and short result only when the detailed evidence is
  stale, changed, ambiguous, or unavailable elsewhere
- latest decisive comment, document, or artifact path instead of a full
  conversation transcript

Full evidence should point to the Handoff Back comment, PR, or decisive artifact
that contains detailed validation, changed-file, scope, security, and risk
evidence.

Do not repeat Handoff Back's full validation logs, changed-file evidence, scope
check, security check, or risk detail unless those details changed after Handoff
Back, are stale, are ambiguous, or are unavailable elsewhere.

Do not create `.agent-context/`, product runtime directories, context
databases, scripts, hooks, workflows, validators, installers, dependencies,
MCP servers, generated context dumps, or external tool outputs as part of this
skill.

## Privacy and output channels

Before writing a context pack, identify the agent visibility and destination
channel.

If the agent has private visibility or is handling security-sensitive review
context, do not output a context pack to any workspace-visible or shared channel.
Use a private output channel. If no private output channel is available, stop
and ask a human.

Do not include secrets, credentials, customer data, production data, private
security findings, exploit details, or sensitive review context in a shared
context pack.

For shared handoff, use redacted wording such as: "security-sensitive review
context exists; read the private security review or ask the security reviewer."

## Decisions and assumptions

Separate decisions from assumptions:

- Decisions are already accepted constraints, routing choices, or scoped
  outcomes that should not be re-litigated without new evidence.
- Assumptions are unverified facts or inferred constraints that the next owner
  may need to confirm.

Mark uncertain evidence plainly. If multiple reasonable next actions exist and
the correct route is unclear, stop instead of manufacturing certainty.

## Validation and current state

Record only validation that has actually run for the current state. Include:

- command or check name
- pass, fail, skipped, unavailable, or stale
- short result summary
- whether the result applies to the current branch, PR, or issue state

If validation is stale or missing, say so. Do not claim work is ready based on
old checks, hidden chat context, or incomplete logs.

## Risks and open questions

Call out risks that can change the next action, including:

- changed files outside the allowed scope
- failing or unavailable validation
- unclear ownership or review route
- security-sensitive surfaces such as auth, tenancy, secrets, PII,
  dependencies, CI permissions, file handling, outbound network calls, database
  migrations, logging, or privileged operations
- product behavior or architecture choices with multiple reasonable outcomes

Open questions should be short, concrete, and answerable by a human, issue
comment, PR review, or targeted command.

## Stop conditions

Stop and ask a human or route to the right owner if:

- the context pack would require reading secrets, customer data, production
  data, or private credentials
- the agent has private visibility or is handling security-sensitive review
  context and the only available output destination is workspace-visible or
  shared
- a shared context pack would include secrets, credentials, customer data,
  production data, private security findings, exploit details, or sensitive
  review context instead of redacted wording
- the task scope is unclear and multiple reasonable next actions exist
- the agent cannot tell whether validation evidence is fresh
- the changed-file set exceeds the issue's allowed files or allowed areas
- the next step would require bypassing validation or weakening tests
- the task requires product runtime directory creation
- the task requires external tools, dependencies, scripts, workflows, hooks,
  installers, validators, MCP servers, or generated context dumps
- the task requires changing Multica workspace runtime directly
- the task requires changing skill names, deleting transitional skills, or
  renaming existing skill directories without explicit issue scope

These stop conditions are agent decision gates, not a complete automated
enforcement mechanism. Programmatically checkable conditions should be validated
by task-specific commands when an issue scopes that work. Scope, validation,
privacy, and security decisions still require the acting agent to record
evidence in Handoff Back or stop for a human when evidence is unavailable.

## Output contract

### Compact index form (default)

Default to this compact index form when a Context pack is useful and Handoff
Back or PR evidence exists. This default form must stay short: use 6-8 bullets maximum.
Its job is to point to full evidence and preserve the next action, not to repeat
the evidence report.

## Context pack

- Issue/PR:
- State:
- Full evidence:
- Key decision:
- Next action:
- Open questions:
- Do not change:

Use `Full evidence` to point to the Handoff Back comment, PR checks, or decisive
artifact containing detailed validation, changed-file, scope, security, and risk
evidence.

In this compact index form, do not include separate bullets for `Changed files`,
`Validation already run`, `Validation results`, `Scope check`,
`Security-sensitive surfaces`, `Risks`, `Constraints and non-goals`, or full
`Do not change` lists. Those belong in Handoff Back. Reference them through the
`Full evidence` bullet unless they changed after Handoff Back, are stale, are
ambiguous, or are unavailable elsewhere.

Example compact index:

## Context pack

- Issue/PR: MUL-123 / PR #45, branch `agent/MUL-123-example`.
- State: implementation complete; all current checks pass; awaiting security
  review.
- Full evidence: see Handoff Back above and PR #45 checks for changed files,
  validation, scope, risk, and rollback.
- Key decision: keep the change design-only; no live apply/write behavior.
- Next action: OpenAI-security-reviewer reviews PR #45.
- Do not change: live workspace config, secrets, runtime config, or files
  outside the issue scope.

### Full resume form

Use this full resume form only when no Handoff Back or PR evidence exists and
the next agent would otherwise lack required state:

## Context pack

- Issue:
- PR:
- Branch:
- Current owner:
- Current status:
- Goal:
- Scope:
- Changed files or affected areas:
- Key decisions:
- Constraints and non-goals:
- Validation already run:
- Validation results:
- Known failures:
- Skipped or unavailable checks:
- Security-sensitive surfaces:
- Risks:
- Open questions:
- Next recommended action:
- Do not change:
- Source artifacts to read next:
- Notes:
