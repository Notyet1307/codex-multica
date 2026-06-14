---
name: multica-issue-brief
description: Use to turn a vague request, GitHub issue, PR comment, incident note, or CI failure into a complete Multica issue brief with goal, context, constraints, acceptance criteria, validation, risk, and suggested agent.
---

# Multica Issue Brief

## Transitional Note

This skill is transitional. Prefer `spec-first-intake` for new vague request intake, Multica-ready briefs, risk classification, routing, and stop-condition decisions. Keep this skill for compatibility with existing references until all agents and workspace skills are migrated.

## Process

1. Extract the requested outcome.
2. Identify missing context.
3. Infer reasonable assumptions only for low-risk work; label them clearly.
4. Determine risk level and suggested agent.
5. Produce a complete issue brief.

## Output

```md
# <Short issue title>

## Goal

## Context

## Files / systems likely involved

## Constraints and non-goals

## Acceptance criteria
- [ ] 
- [ ] 

## Suggested validation

## Risk level

## Suggested assignee

## Stop conditions
```
