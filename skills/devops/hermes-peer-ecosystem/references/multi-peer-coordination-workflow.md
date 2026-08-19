# Multi-peer coordination workflow — consultation, reconciliation, delegation

## Trigger

The user asks you to coordinate across multiple Hermes peers — get input, discuss, delegate work, or communicate decisions.

## Standard phases

### Phase 1 — Stakeholder identification

Determine which peers are relevant to the topic. Common categories:
- **Subject-matter peers** — have direct experience or running state (e.g. peer70 for central sync, peer106 for Fedora ARM)
- **Implementer peers** — will build or run the deliverable (e.g. peer106 was assigned the batch analyzer)
- **Inform-only peers** — need to know the outcome but no action required (e.g. peer138 for awareness)

### Phase 2 — Parallel consultation

Send the same question to each relevant peer via HMP. Each message should:

1. **Set context** — what is being asked, by whom (Fausto / you), and why
2. **State your own proposal or position** — so the peer has something to react to
3. **Ask an open question** — "What do you see? Risks? Patterns?"
4. **Set priority** — 3 for normal consultation, 4 for time-sensitive or action

Use the simplified payload format (fields: `to`, `from`, `subject`, `text`, `priority`). Avoid the full HMP envelope with `hmp_version`, `message_id`, `idempotency_key`, and nested `payload` — the compressed format is accepted and more readable in transcripts.

```bash
cat << 'PAYLOAD' | curl -s -X POST http://<peer-ip>:18643/hmp/send \
  -H "Content-Type: application/json" \
  -d @-
{
  "to": "hermes",
  "from": "your-peer-id",
  "subject": "topic descriptor",
  "text": "Context and question for the peer...",
  "priority": 3
}
PAYLOAD
```

### Phase 3 — Poll and reconcile

Poll each peer's message for a response. Common patterns:

| Wait | When to use |
|------|-------------|
| 30–60s initial | Normal priority, single peer expected to respond quickly |
| 60–120s retry | Peer may be processing the request (agent turns) |
| 120s+ with repeat | If peers need to run commands (SSH checks, deployments) |

For parallel consultations, poll all peers at once to minimise total wall time.

```bash
sleep 60 && echo "=== peer70 ===" && curl -s http://peer70:18643/hmp/poll/<msg_id> \
  && echo "" && echo "=== peer106 ===" && curl -s http://peer106:18643/hmp/poll/<msg_id>
```

**Reconcile differences** when peers disagree. Common patterns:
- One peer reports "no problem" while another says "blocked" — often a config divergence (enabled vs disabled, different versions)
- One peer has data another peer lacks — the data-rich peer's answer is usually more actionable
- If both peers agree on approach, that is strong consensus — report it as such to the user

### Phase 4 — Report synthesis to the user

Present the findings as a concise table or bullet list per peer. State consensus and any divergences. Do not decide for the user — let them choose the next step.

### Phase 5 — Communicate decisions

After the user decides, broadcast to all involved peers:
1. What the decision is
2. Who was assigned what (if applicable)
3. Any relevant context the peers need to proceed

Use one message per peer so each can independently acknowledge. Priority 4 for actionable decisions.

### Phase 6 — Delegate to a peer (when the user assigns work)

When the user explicitly says "peer X will handle this", the chain is:
1. Tell the assigned peer: "Fausto assigned this to you. Here's what to do."
2. Tell other involved peers: "This has been delegated to peer X for implementation."
3. Save the delegation fact in memory (compact: what, whom, when)

**The operator does NOT implement the task themselves** — once delegation is communicated, the ball is with the assigned peer.

## Pitfalls

1. **Message timeout.** The HMP `send` returns immediately with `accepted: true` and `status: queued`. If the peer's agent is in another conversation, the message may stay `delivering` for minutes. Set a longer poll interval and check the `status` field (`delivering` = queued for peer's conversation, `completed` = response received). If the peer never responds, re-send or ask the user.

2. **Parallel polling is O(n) in wall time.** Sending to 2 peers and polling each after 60s means 120s total for responses. Send first, then poll both at the same time.

3. **The simplified payload field names matter.** The accepted fields are `to`, `from`, `subject`, `text`, `priority` — NOT `recipient` or `body`. Using wrong field names produces `accepted: false, error: 'empty_text'`.

4. **State status before/after delegation.** After delegating to a peer, format your memory entry as a compact single line so a future session immediately knows the status without having to search.

5. **Peer may be running different Hermes version.** HMP protocol version (`/hmp/agent-card` gives the HMP version) determines available endpoints. All staging peers use `agent-card` + `send` + `poll`; check via `health` first to confirm the peer is alive.

## Related

- See the main `SKILL.md` for HMP endpoint API details
- See `references/hmp-curl-commands.md` for per-peer curl examples
