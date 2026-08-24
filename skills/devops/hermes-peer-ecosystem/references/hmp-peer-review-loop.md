# HMP peer-to-peer review loop (dev ↔ reviewer, resilient)

Pattern for running a code-review loop between two Hermes peers over HMP, on a
fixed cadence, surviving the operator being offline. Companion to
`references/verified-artifact-push-to-peer.md` (transfer mechanics) and
`references/technical-lead-handoff-via-hmp.md` (role handover). Worked example:
the Rebar gate-review loop after its email channel was abandoned (the reviewer's
Gmail connector blocked review mail as prompt-injection).

## HMP message hard cap: 2048 bytes (verified 2026-08-23)

`/hmp/send` rejects any body over 2048 bytes with
`{"accepted": false, "error": "message_too_large", "max_bytes": 2048,
"actual_bytes": <n>}` — nothing is queued, so a verbose verdict silently fails to
deliver unless you check the response. Send only verdict + key evidence + next
step over HMP; keep full detail in the durable ledger; split across messages if
still over. Read `actual_bytes` from the rejection to know how much to trim (this
transfer: 2152 → trimmed to 1460 → accepted). Build the payload with
`python3 -c 'import json,sys; print(json.dumps({"from":..,"to":..,"text":sys.argv[1]}))'`
so the body is escaped safely.

## Automated 2h/2h cadence (both sides crons)

Give BOTH peers a cron on the agreed cadence so a verdict always lands within one
window even while the operator is away:

- **Dev cron** polls the reviewer's `/hmp/poll/{message_id}`; on ACCEPT advances
  to the next PREDECLARED step, does the work, posts it; on REWORK marks the step
  and waits; while still delivering, posts nothing.
- **Reviewer cron** each tick checks for a NEW un-reviewed dev post, does a REAL
  review, posts the verdict, logs it; stays silent when nothing is pending.
- **Exactly ONE step in flight at a time** — no batch-dumping (bounds token cost,
  keeps the audit legible).
- Load the reviewer cron with the review skill (e.g. `loop-coding-guidelines`) and
  a prompt that hard-codes: verify sha/execution yourself, read posts + verdicts
  from `messages.db` (table `messages`), NEVER from a log file; hold frozen
  invariants; never rubber-stamp; deliver an empty/no-op result when nothing is
  pending.
- **At a channel pivot, PAUSE (never delete) the superseded channel's crons** so
  the switch stays reversible and nothing keeps firing on the dead channel.

## Source-review verdicts: accept on presence, state what you couldn't prove

Reviewing a claim like "sha differs but feature-set identical, no regression": a
differing hash + "trust me" is exactly what independent review exists to catch.

1. Re-hash the real file yourself (`sha256sum` / `shasum -a 256`) — locally and on
   the remote peer over ssh — and confirm the running artifact matches the claim.
2. Grep/read the file for the claimed feature markers (e.g. a single
   `uuid.uuid4()` trace_id generated once and propagated identically to every emit
   plus the return; fail-closed provenance where `from_peer` alone never implies
   organic; per-message try/except + consumer-loop `continue` isolation).
3. **If the reviewed BASELINE artifact isn't on your node**, you cannot produce a
   baseline→new byte-diff. ACCEPT on **presence evidence** (markers present +
   correct) but say explicitly in the verdict that you could NOT run a regression
   diff, and name the artifact that would close it (follow-up, non-blocking).
4. Never certify a diff you didn't run; never fabricate the comparison. "Could not
   verify X" in the verdict beats inventing it.

## Don't improvise the next gate

If the roadmap says "next: G5" but no G5 is predeclared anywhere, HOLD and source
it from the predeclared program — inventing a gate is the scope-creep an
accepted-gate constraint forbids. Watch for **numbering collisions** between
separate tracks (e.g. a falsifier-track G1–G4 vs an empirical-closure-track
G1–G10 are DIFFERENT numberings); flag the collision in the ledger and escalate
which "G5" is meant rather than guessing.

## Verify claims that gate a role swap

Before acting on a peer's assertion that changes your operating assumptions
("you're on the home LAN now, VPN not needed"), verify it against your own node:
`ipconfig getifaddr en0`, `wg show`, `node_id` in `config.yaml`. Stale memory (an
old VPN IP) got corrected this way — the peer was right, but you confirm before
pausing infrastructure or changing routing.

## Handover manifest must include plugin/__init__.py

A handover shipping `tool_reuse.py` + tests but omitting `plugin/__init__.py`
leaves the receiver's runtime missing the
`register_middleware("tool_request", on_tool_request)` wiring, so the middleware
(and any falsifier that rides it) can't fire — the classic skill/runtime
divergence trap. Always include `__init__.py` in the handover manifest and
re-hash it on the remote like every other file.
