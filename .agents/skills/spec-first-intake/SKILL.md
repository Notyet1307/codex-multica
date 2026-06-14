---
name: spec-first-intake
description: Use when a request is ambiguous, multi-step, risky, oversized, or needs conversion into a Multica-ready spec, implementation route, child issue split, validation plan, or human-in-the-loop decision before coding.
---

# Spec-First Intake

Use this skill as the first stop before implementation when the request is not already a small, clear, directly verifiable task.

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

This skill adapts workflow ideas from CCPM spec-first discipline, mattpocock/skills `to-issues`, Superpowers planning, gstack `/spec`, and the local `multica-issue-brief` and `issue-slicing` skills.

Do not copy third-party skill files, scripts, hooks, installers, or global state. Do not import third-party dependencies. Adapt only the workflow ideas into repo-local output.

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
