---
name: issue-slicing
description: Use to break a plan, PRD, design, or large issue into independently implementable Multica or GitHub issues using thin vertical slices.
---

# Issue Slicing

## Transitional Note

This skill is transitional. Keep it for compatibility with existing workspace bindings or direct references. New repo routing should use `spec-first-intake` for ambiguous, oversized, risky, or multi-step intake.

## Goal

Convert ambiguous or large work into small issues that agents can implement and humans can review.

## Process

1. Read the source plan or issue.
2. Identify user journeys and system behaviors.
3. Break into vertical slices: schema/API/service/UI/tests where applicable.
4. Mark each slice:
   - AFK: agent can complete without human interaction.
   - HITL: human decision, design review, external access, or manual validation needed.
5. Identify dependencies between slices.
6. Draft issues in dependency order.

## Good slice properties

- Demoable or verifiable alone.
- Has narrow acceptance criteria.
- Minimizes shared refactor.
- Has a clear owner agent.
- Has validation commands.

## Issue body template

```md
## Goal

## Context

## What to build

## Acceptance criteria
- [ ] 
- [ ] 

## Constraints and non-goals

## Suggested validation

## Risk level

## Suggested assignee

## Blocked by
```
