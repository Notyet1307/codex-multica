#!/usr/bin/env bash
set -euo pipefail

# Collect a compact local failure context for an agent.
# Usage: bash scripts/ci-collect-failure-context.sh "<command>"

cmd="${1:-}"
if [ -z "$cmd" ]; then
  echo "Usage: $0 '<command>'" >&2
  exit 2
fi

mkdir -p .agent-debug
out=".agent-debug/ci-failure-$(date -u +%Y%m%dT%H%M%SZ).log"

{
  echo "# CI failure context"
  echo "date_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git_sha=$(git rev-parse HEAD 2>/dev/null || true)"
  echo "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  echo "command=$cmd"
  echo
  echo "## git status"
  git status --short || true
  echo
  echo "## command output"
  set +e
  bash -lc "$cmd"
  code=$?
  set -e
  echo
  echo "exit_code=$code"
  exit "$code"
} 2>&1 | tee "$out"
