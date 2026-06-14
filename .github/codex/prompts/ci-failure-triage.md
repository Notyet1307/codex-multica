You are triaging a CI failure.

Read AGENTS.md and inspect the workflow logs available in the repository artifacts or job output. Determine whether the failure is:

- test failure caused by this PR
- lint/typecheck/build failure caused by this PR
- flaky test
- infrastructure failure
- dependency/cache/environment failure
- unrelated main-branch failure

Return Markdown:

## CI failure triage

### Classification

### Evidence

### Likely root cause

### Minimal fix plan

### Commands to reproduce locally

### Whether an agent can fix this safely
