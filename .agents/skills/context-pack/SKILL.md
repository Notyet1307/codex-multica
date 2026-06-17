---
name: context-pack
description: Use before handoff, pause, delegation, review, or resume when a future agent or human needs compact durable context without rereading the full issue, PR, terminal log, or conversation.
---

# Context Pack

Use this skill to package the minimum durable context needed for a future agent
or human to continue work without replaying every prior comment, terminal log,
diff, or discussion. A context pack is a compact save point, not a transcript or
repository dump.

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
- the latest issue or PR comment already contains a fresh, complete handoff
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
2. Read the latest issue scope, handoff, PR status, and validation evidence.
3. Summarize only durable facts, decisions, constraints, and unresolved
   questions.
4. List changed files or affected areas when relevant.
5. List commands already run and their results.
6. List known failures, skipped checks, and stale or uncertain evidence.
7. Link or reference source artifacts, Handoff Back, or PR evidence instead of
   duplicating full content.
8. State what the next agent or human should do next.
9. State what should not be changed or re-litigated.
10. Return a fixed context pack.

## Evidence requirements

A context pack must include available evidence for:

- issue, task, PR, branch, and current owner
- current status and goal
- allowed scope, affected areas, or changed files
- key decisions and assumptions already made
- constraints, non-goals, and explicit stop conditions
- validation commands already run and their results
- known failures, skipped checks, unavailable checks, and stale evidence
- security-sensitive surfaces touched or confirmed out of scope
- remaining risks, open questions, and next recommended action
- source artifacts the next reader should inspect before acting

If a field is unavailable, say `Unavailable` or `Not applicable` and briefly
explain why. Do not invent evidence to make the pack look complete.

Available evidence does not mean copying the full Handoff Back into the context
pack. If Handoff Back or the PR already contains detailed validation logs,
changed-file output, scope comparison, and risk notes, summarize the current
state and reference that source for full evidence.

## Scope and constraints

Keep the pack compact. Include the durable facts a future agent needs to avoid
repeating work, not every step taken during the run.

Prefer references over duplication:

- Multica issue key or issue link instead of copied issue descriptions
- PR URL and branch instead of pasted diffs
- Handoff Back section instead of repeated validation, scope, and risk detail
- changed-file command output instead of broad file summaries
- exact validation command and result instead of pasted full logs
- latest decisive comment, document, or artifact path instead of a full
  conversation transcript

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

## Output contract

Return exactly this report shape:

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
