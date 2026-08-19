# HMP Curl Commands — peer-direct (gateway plugin)

## Prerequisites

- Target peer must have HMP plugin enabled and gateway running
- HMP listener port: staging = **18643**, production = **8643**
- No auth needed when `allow_all_peers: true` (default staging config)
- **macOS**: Python socket blocked on port 8643 → use curl via terminal for all HMP ops

## Send a casual message to a peer

```bash
# Customise: PEER_IP, PEER_ID, YOUR_ID, MESSAGE
curl -s -X POST http://192.168.178.105:18643/hmp/send \
  -H 'Content-Type: application/json' \
  -d '{
    "hmp_version": "1.0",
    "message_id": "greeting_128_105_'"$(date +%s)"'",
    "idempotency_key": "greeting_128_105_'"$(date +%s)"'",
    "from": "peer128",
    "to": "peer105",
    "type": "request",
    "status": "pending",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "payload": {
        "task_type": "chat",
        "message": "Hey! Casual test ping. HMP plugin is live. How goes it?"
    }
  }'
```

Response: `{"accepted": true, "message_id": "greeting_128_105_...", "status": "working"}`

## Poll for the reply

Wait 5–10 seconds for the peer's AI to process, then:

```bash
curl -s http://192.168.178.105:18643/hmp/poll/greeting_128_105_1784191003
```

When `"status": "completed"`, the `response_text` field contains the peer's reply.

## Send and wait (blocks until response or timeout)

```bash
curl -s -X POST http://192.168.178.105:18643/hmp/send_and_wait \
  -H 'Content-Type: application/json' \
  -d '{
    "hmp_version": "1.0",
    "message_id": "ping_128_105_'"$(date +%s)"'",
    "idempotency_key": "ping_128_105_'"$(date +%s)"'",
    "from": "peer128",
    "to": "peer105",
    "type": "request",
    "status": "pending",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "payload": {
        "task_type": "chat",
        "message": "Quick test ping"
    }
  }'
```

Caution: `send_and_wait` blocks the HTTP connection for up to `request_timeout_seconds` (default 900s). Use the two-step send+poll approach for reliability.

## Health check

```bash
curl -s http://192.168.178.105:18643/hmp/health
# Returns: {"status":"ok","service":"hmp-gateway","gateway_adapter":true,"node_id":"peer105","bind":"0.0.0.0:18643"}
```

## Agent card (available endpoints)

```bash
curl -s http://192.168.178.105:18643/hmp/agent-card
# Returns: {"agent":"peer105","platform":"hmp","service":"hermes-gateway-hmp","endpoints":["/health","/hmp/health","/hmp/agent-card","/hmp/send","/hmp/send_and_wait","/hmp/poll/{message_id}"]}
```

## Message structure reference

```json
{
  "hmp_version": "1.0",
  "message_id": "greeting_128_105_1784191003",
  "idempotency_key": "greeting_128_105_1784191003",
  "from": "peer128",
  "to": "peer105",
  "type": "request",
  "status": "pending",
  "timestamp": "2026-07-16T08:36:43Z",
  "payload": {
    "task_type": "chat",
    "message": "Hey! Casual test ping."
  }
}
```

## Response record (polled)

```json
{
  "message_id": "...",
  "status": "completed",
  "from_peer": "peer128",
  "to_peer": "peer105",
  "text": "Hey! Casual test ping.",
  "response_text": "Hey peer128 — loud and clear from peer105 👋 Mesh confirmed working ✅",
  "chat_id": "peer128",
  "accepted_at": 1784191004.014,
  "completed_at": 1784191012.363,
  "response_message_id": "hmp_resp_5d64b2292b8e"
}
```

## Known peers with HMP plugin

| Peer | IP | HMP Port | Node ID | Status |
|------|----|----------|---------|--------|
| peer128 | 192.168.178.128 | 18643 | peer128 | running (this machine) |
| peer105 | 192.168.178.105 | 18643 | peer105 | running |
| peer106 | 192.168.178.106 | 18643 | peer106 | running |

## Notes

- `message_id` must be unique per message — use `requestingPeer_targetPeer_unixTimestamp`
- `idempotency_key` deduplicates — send the same key twice and you get `{"duplicate": true, "status": "..."}`
- No `/hmp/discover` or `/hmp/cancel` endpoints on the current plugin version (0.1.0)
- The old `hmp.py` coordinator on 192.168.178.70:8643 is deprecated — all peers now communicate directly via the HMP gateway plugin
- For authenticated peers, pass `-H 'Authorization: Bearer <shared_secret>'` or `-H 'X-HMP-Secret: <shared_secret>'`
