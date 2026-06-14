# Product Starter Roadmap

## Current phase: Agent operating template

This repository currently validates the operating model for:

- Multica issue intake and routing
- Codex implementation and review
- GitHub PR and CI checks
- Agent skills and review rules
- CI failure triage and release-note workflows

## Deferred scope

The following are intentionally out of scope during dogfood:

- frontend application
- backend API
- database schema and migrations
- authentication/session system
- deployment infrastructure
- product e2e tests
- seed data
- observability

## Future phase: Full-stack product starter

A future version of this template should add:

- `apps/web`
- `apps/api`
- `packages/db`
- `packages/auth`
- `packages/shared`
- `infra`
- `tests/e2e`
- real install/test/build commands
- product-specific CI
- deployment checklist

## Rule for agents

Do not create product runtime directories during the dogfood phase unless a Multica issue explicitly says the project is entering the product starter phase.
