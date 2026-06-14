#!/usr/bin/env bash
set -euo pipefail

# Helper for sending a generic JSON payload to a Multica Autopilot webhook.
# Required env:
#   MULTICA_WEBHOOK_URL
# Optional env:
#   EVENT_NAME
#   EVENT_PAYLOAD_JSON

: "${MULTICA_WEBHOOK_URL:?MULTICA_WEBHOOK_URL is required}"
EVENT_NAME="${EVENT_NAME:-manual.agent_event}"
EVENT_PAYLOAD_JSON="${EVENT_PAYLOAD_JSON:-{}}"

jq -n \
  --arg event "$EVENT_NAME" \
  --argjson payload "$EVENT_PAYLOAD_JSON" \
  '{event: $event, eventPayload: $payload}' \
| curl -fsS -X POST "$MULTICA_WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    --data-binary @-
