---
name: spec-first-intake
description: Use when a request is ambiguous, multi-step, risky, oversized, or needs conversion into a Multica-ready spec, implementation route, child issue split, validation plan, or human-in-the-loop decision before coding.
---

# Spec-First Intake

Use this skill as the first stop before implementation when the request is not already a small, clear, directly verifiable task.

The scoper is responsible for context stewardship before implementation begins. Context stewardship means verifying current state before delegating, separating facts from assumptions, preserving decisions already made, defining allowed scope and stop conditions, defining expected worker output, and writing the handoff into durable Multica issue comments or PR text instead of relying on hidden chat context.

## Use when

- A rough request needs to become an agent-ready Multica brief or spec.
- Current state must be verified before planning or coding.
- The work may need splitting, routing, risk classification, or human input.
- The likely implementation is multi-step, oversized, risky, or ambiguous.

## Do not use when

- The issue already has clear scope, acceptance criteria, validation, and assignee.
- The task is a narrow mechanical edit with obvious validation.
- The user explicitly asks for implementation and the issue is already agent-ready.

## Design References

This skill adapts workflow ideas from the Multica Squad model, CCPM spec-first discipline, Open SWE manager/programmer separation, agent handoff patterns, the MUL-11 dogfood failure, mattpocock/skills `to-issues`, Superpowers planning, gstack `/spec`, and the former local intake and issue-slicing workflows.

Adapted workflow ideas:

- Multica Squad model: the scoper acts as leader and context steward before delegating work.
- CCPM: context must be durable and traceable through spec, issue, branch, PR, and validation.
- Open SWE: keep manager/planner responsibilities separate from programmer execution; do not let implementation start before context and plan are clear.
- Agent handoff patterns: prevent lost state, weak escalation, and unclear uncertainty signals by using persistent state, approval gates, risk signals, and handoff artifacts.
- MUL-11 dogfood failure: missing allowed files and stop conditions caused scope expansion, so handoff fields must be durable and copy-safe.

Do not copy third-party project files, prompts, skills, scripts, hooks, installers, dependencies, or global state. Do not add external tools. Adapt only the workflow ideas into short repo-local instructions.

## Intake Workflow

1. Read the source request, issue, PR comment, incident note, or plan.
2. Verify current state from durable sources before making claims:
   - issue description and comments
   - linked PRs or branches
   - relevant files, docs, scripts, CI logs, screenshots, or attachments
3. Separate known facts from assumptions. Mark assumptions as low, medium, or high confidence.
4. Define scope and non-goals.
5. Draft acceptance criteria that can be checked by a human or command.
6. Classify execution:
   - AFK: an agent can complete the work without human input.
   - HITL: a human decision, access grant, design review, security review, production action, or manual validation is required.
7. Identify risk and stop conditions.
8. Recommend validation commands or manual checks.
9. Decide routing:
   - one implementation route when the work is small enough for a single agent-ready issue
   - child issues when the work is large, serial, or independently reviewable
10. Preserve traceability from request/spec to issue, branch, PR, and validation result. Include the Multica issue key in suggested branch and PR text.
11. For non-trivial implementation delegation, write a Context Handoff before assigning a worker and require a Handoff Back before review.

## Context Handoff

The scoper must produce a Context Handoff before delegating non-trivial implementation. Keep it proportional to task risk, but do not delegate if required scope boundaries are missing.

Required fields:

- Source of truth
- Verified current state
- Decisions already made
- Known facts
- Assumptions
- Allowed files or allowed areas
- Explicit non-goals
- Stop conditions
- Worker assignment
- Expected output
- Validation required
- Handoff back requirement

Suggested output shape:

## Context handoff

### Source of truth

- Multica issue:
- GitHub PR:
- Branch:
- Related docs:

### Verified current state

- ...

### Decisions already made

- ...

### Known facts

- ...

### Assumptions

- ...

### Allowed files or allowed areas

- ...

### Explicit non-goals

- ...

### Stop conditions

Stop and ask a human if:

- ...

### Worker assignment

- Agent:
- Reason:

### Expected output

- Changed files:
- Validation evidence:
- PR or issue comment:
- Handoff back: required

### Required validation

- `make verify` or task-specific command

## Handoff Back

A worker agent must return a Handoff Back after implementation and before the task is considered ready for review.

Handoff Back is the detailed evidence report. It should carry the implementation summary, validation evidence, changed-file output, scope comparison, risks, and readiness decision.

The scope check must be evidence-based, not only self-reported. The worker must include the changed-file command output, compare it with the allowed files or allowed areas from the handoff, and explicitly confirm whether unexpected files changed. If unexpected files changed, mark the task not ready for review and ask for correction instead of asking for review or merge.

If a visible Context pack is also required, it should coexist with Handoff Back as a compact resume state. The Context pack may reference Handoff Back and the PR for full validation, changed-file, scope, and risk evidence instead of duplicating the evidence report.

Suggested output shape:

## Handoff back

### Work performed

- ...

### Files changed

- ...

### Validation evidence

- Command:
- Result:

### Scope check

- Changed-file command: `git diff --name-only origin/main...HEAD`
- Changed-file output:
- Compared against allowed files or areas:
- Within allowed files or areas: yes/no
- Unexpected files changed:
- No unexpected files changed: yes/no
- Unexpected behavior changes:

### Decisions made during implementation

- ...

### Remaining uncertainty

- ...

### Follow-up needed

- yes/no
- Suggested follow-up issue:

### Ready for review

- yes/no
- Reason, including whether any unexpected files require correction:

## Delegation Gate

Scoper must not delegate non-trivial implementation if any of these are missing:

- allowed files or allowed areas
- stop conditions
- validation command
- expected worker output
- risk or HITL classification

If the user request or Multica issue is missing them, scoper must first write a Context Handoff comment or ask for clarification.

## Copy Safety

Do not rely on fenced code blocks for critical scope boundaries in Multica issue text if copying may truncate later sections.

For critical instructions such as `Allowed files`, `Stop conditions`, and `Validation`, prefer bullet lists and inline command text like `make verify`.

## Scope Creep

If a worker identifies useful changes outside the allowed files, allowed areas, or approved scope, it must propose them as follow-up comments or follow-up issues. It must not implement them in the current PR without human approval.

## Split Decision

Split into child issues when any of these are true:

- The work spans independent user journeys or operational concerns.
- One part can be verified without the others.
- A human decision blocks only part of the work.
- Risk differs by part, such as docs-only work plus security-sensitive changes.
- The likely PR would be too broad to review confidently.

Keep as one route when the work has one owner, one clear validation path, and one reviewable PR.

## Stop Conditions

Stop and ask or route instead of implementing when:

- Acceptance criteria are missing for risky or user-visible behavior.
- Required access, secrets, production data, or external approvals are unavailable.
- Security, tenant isolation, PII, migrations with data-loss risk, or deployment decisions are involved.
- The request conflicts with `AGENTS.md`, docs, or an existing decision record.
- The work needs product direction, design acceptance, or architecture approval before coding.
- The implementation would require deleting or renaming old skill directories.
- The implementation would require changing files outside the explicitly allowed scope.
- The implementation would add external tools, new workflow automation, scripts, hooks, installers, global state, or third-party dependencies.
- The implementation would copy third-party skill files verbatim instead of adapting workflow ideas.

## Output

```md
# <Short Multica-ready title>

## Goal

## Verified current state
- 

## Known facts
- 

## Assumptions
- Low confidence:
- Medium confidence:
- High confidence:

## Scope
- 

## Non-goals
- 

## Acceptance criteria
- [ ] 

## AFK / HITL classification
- Classification:
- Reason:
- Human input needed:

## Risk and stop conditions
- Risk:
- Stop if:

## Suggested validation
- 

## Suggested routing
- Recommended route:
- Suggested assignee:
- Branch / PR traceability:

## Split decision
- Decision: single issue | child issues
- Rationale:

### Child issues
1. <Title>
   - Goal:
   - Acceptance criteria:
   - Validation:
   - AFK / HITL:
   - Dependencies:
```
