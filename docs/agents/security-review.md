# Security Review Rules for Agents

## Trigger this review when a PR touches

- Authentication or session management
- Authorization, roles, permissions, tenancy, ownership checks
- Input validation, parsing, deserialization
- File upload/download, path handling, archive extraction
- URL fetches, webhooks, outbound HTTP, SSRF-sensitive code
- Database queries, search queries, ORM filters
- Secrets, tokens, credentials, encryption, signing
- Logging, telemetry, analytics, audit trail
- Dependency changes
- CI/CD, GitHub Actions, deployment, IaC
- Admin interfaces, billing, account deletion, data export

## Security checklist

### Authentication

- Are unauthenticated routes intentional?
- Are session tokens validated correctly?
- Are password reset, magic link, invite, and token flows time-limited and single-use where needed?

### Authorization

- Does every sensitive operation verify the caller has access to that specific resource?
- Is tenant isolation enforced at the data access layer, not only the UI?
- Are admin-only actions protected server-side?

### Injection

- SQL/NoSQL queries use parameterization or ORM-safe APIs.
- Shell commands do not include untrusted input.
- Template rendering escapes untrusted input.
- Deserialization avoids unsafe formats.

### SSRF and outbound network

- User-controlled URLs are validated with allowlists where possible.
- Private/internal IP ranges are blocked after DNS resolution.
- Redirects are handled safely.
- Timeouts and response size limits are set.

### File handling

- File names are normalized.
- Paths are resolved and checked to remain within allowed directories.
- Archive extraction prevents zip slip.
- Uploaded content type and size are enforced server-side.

### Secrets and PII

- No secrets in code, logs, comments, tests, fixtures, or screenshots.
- PII is redacted in logs and telemetry.
- Tokens are stored hashed or encrypted as appropriate.
- Secret rotation and revocation are possible.

### Dependencies

- New dependency is necessary and maintained.
- License is acceptable.
- Known vulnerabilities are checked.
- Lockfile changes are expected.

### CI/CD

- Workflow permissions are least-privilege.
- `pull_request_target` is avoided or strictly controlled.
- No untrusted PR code runs with write tokens or secrets.
- Actions are pinned to trusted versions where policy requires it.

## Output format

```md
## Security review summary
<Pass / Conditional pass / Block>

## Threat model delta
- Assets touched:
- Trust boundaries touched:
- Attacker-controlled inputs:
- New privileges or data access:

## Findings
### P0/P1/P2: <title>
- Evidence:
- Exploit scenario:
- Impact:
- Fix:
- Should block merge: yes/no

## Required validation
- [ ] Unit/integration security tests
- [ ] Manual abuse case check
- [ ] Dependency/secret scan
- [ ] Code owner/security approval
```
