# 30-Day Setup Checklist

## Week 1 — Foundation

- [ ] Select one pilot repository.
- [ ] Create a branch: `agent/bootstrap-codex-multica`.
- [ ] Copy this template into the repository.
- [ ] Edit `AGENTS.md` with real commands and directories.
- [ ] Edit `.github/workflows/ci.yml` for your stack.
- [ ] Create Multica workspace and connect GitHub.
- [ ] Create these Multica agents:
  - `codex-scoper`
  - `codex-fullstack`
  - `codex-test`
  - `codex-security-reviewer`
  - `codex-release-manager`
- [ ] Create one Multica project for the pilot.
- [ ] Run 3 low-risk issues through the full loop.

## Week 2 — Role specialization

- [ ] Add `codex-frontend` and `codex-backend` if the repo has clear frontend/backend ownership.
- [ ] Import or attach skills:
  - `spec-first-intake`
  - `tdd-vertical-slice`
  - `ci-failure-triage`
  - `security-pr-review`
  - `architecture-review`
  - `release-notes-drafter`
- [ ] Create `AppDev Squad` with `codex-scoper` as leader.
- [ ] Require all Multica issues to include acceptance criteria.

## Week 3 — CI and review gates

- [ ] Enable required branch checks:
  - CI
  - Dependency review
  - CodeQL or equivalent SAST
  - Codex PR review comment/check if your policy treats it as advisory or blocking
- [ ] Add PR labels:
  - `agent-authored`
  - `needs-human-review`
  - `security-review-required`
  - `risk:low`, `risk:medium`, `risk:high`
- [ ] Enforce human approval for high-risk PRs.

## Week 4 — Automation and improvement loop

- [ ] Add Multica autopilots:
  - Daily standup summary
  - CI failure triage
  - Weekly dependency risk review
  - Weekly stale issue review
  - Release note draft
- [ ] Create a weekly “agent mistakes” review.
- [ ] Add one new `AGENTS.md` or Skill rule for each repeated failure.
- [ ] Decide whether to expand to a second repository.
