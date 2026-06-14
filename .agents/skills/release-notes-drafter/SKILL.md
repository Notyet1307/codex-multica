---
name: release-notes-drafter
description: Use to draft release notes from merged PRs, Multica issues, Git history, or milestone content. Groups changes by user impact, security, fixes, migrations, and breaking changes.
---

# Release Notes Drafter

## Process

1. Identify release range: previous tag to current HEAD, milestone, or date range.
2. Collect merged PRs and linked issue IDs.
3. Exclude internal-only noise unless it matters operationally.
4. Group by category:
   - Features
   - Fixes
   - Security
   - Performance
   - Breaking changes
   - Migrations
   - Internal maintenance
5. Add upgrade and rollback notes where needed.
6. Flag missing information rather than guessing.

## Output

```md
# Release <version/date>

## Highlights

## Features

## Fixes

## Security

## Breaking changes

## Migrations and operations

## Internal changes

## Known issues
```
