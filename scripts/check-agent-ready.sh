#!/usr/bin/env bash
set -euo pipefail

missing=0

require_file() {
  if [ ! -f "$1" ]; then
    echo "MISSING: $1"
    missing=1
  else
    echo "OK: $1"
  fi
}

require_file AGENTS.md
require_file docs/agents/code-review.md
require_file docs/agents/security-review.md
require_file docs/agents/issue-tracker.md
require_file .github/pull_request_template.md
require_file .github/codex/prompts/review.md
require_file .github/scripts/deepseek_pr_review.py
require_file .github/workflows/deepseek-pr-review.yml

python3 .github/scripts/deepseek_pr_review.py --self-test

if [ -d .agents/skills ]; then
  find .agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
else
  echo "MISSING: .agents/skills"
  missing=1
fi

if [ "$missing" -ne 0 ]; then
  echo "Agent readiness check failed."
  exit 1
fi

echo "Agent readiness check passed."
