# HMP peer-to-peer review loop — recipes + worked example (2026-08-23)

Context: the Rebar review loop moved from email (Libero/Hotmail) to HMP peer-to-peer after
the reviewer's ChatGPT scheduled-task (Gmail connector) began blocking review mail as
prompt-injection and the human-simulation email workaround still tripped Hotmail's
automated-sending flags. Dev = peer136 (192.168.178.136), reviewer = peer128 (this Mac,
192.168.178.112, on home LAN — no VPN needed).

## Transport recipes

**Send a message (verdict or dev-step):**
```bash
TEXT='...'
printf '%s' "$TEXT" | wc -c        # MUST be < 2048 before sending
curl -s -X POST http://192.168.178.136:18643/hmp/send \
  -H 'Content-Type: application/json' \
  -d "$(python3 -c 'import json,sys;print(json.dumps({"from":"peer128","to":"peer136","text":sys.argv[1]}))' "$TEXT")"
# success: {"accepted": true, "message_id": "hmp_...", "status": "queued"}
# too big: {"accepted": false, "error": "message_too_large", "max_bytes": 2048, "actual_bytes": N}
```
- 🔴 **2048-byte hard cap per message.** Keep the wire message terse (verdict + key evidence
  + next step). Put full evidence in the ledger, not on the wire.
- **Read dev-posts / verdicts from `messages.db` (table `messages`), never from a log file.**
  The DB is authoritative; logs rotate/truncate.
- Poll a specific message: `GET /hmp/poll/{message_id}`.

## Both-sides cron automation (resilient while the human is offline)

- **Dev cron** (e.g. `rebar-g0-loop-peer136`, every 2h): polls the reviewer's
  `/hmp/poll/{id}`; on ACCEPT advances to the next step, does the work, posts it; on
  REJECT/REWORK marks rework and waits; if still delivering, posts nothing (one step in
  flight).
- **Reviewer cron** (e.g. `rebar-g0-review-peer128`, every 2h, load the review skill +
  `verifying-agent-claims`): does a REAL review each tick; if nothing new is pending, stays
  silent (posts nothing). Toolsets: `terminal`, `file`. It must verify sha/execution, read
  from `messages.db`, and never rubber-stamp.

Cadence contract (Fausto): 2h dev-post max, 2h verdict max, one step in flight, no batch.

## Handover push (checksum-verified) — exact recipe

```bash
# 1. manifest of exactly what you send
shasum -a 256 <files...> > /tmp/HANDOVER.SHA256SUMS
# 2. rsync (exclude pycache), LITERAL remote paths (~ expands to LOCAL home inside ssh!)
ssh fausto@192.168.178.136 'mkdir -p /home/fausto/.hermes/plugins/capability-reuse'
rsync -az --exclude='__pycache__' --exclude='*.pyc' <files...> \
  fausto@192.168.178.136:/home/fausto/.hermes/plugins/capability-reuse/
# 3. re-hash on the REMOTE and diff vs manifest before saying "pushed"
ssh fausto@192.168.178.136 'cd /home/fausto/.hermes/... && sha256sum <files...>' \
  | diff <(sort /tmp/HANDOVER.SHA256SUMS) - && echo MATCH
```
- Include `plugin/__init__.py` in a plugin handover — it holds
  `register_middleware("tool_request", on_tool_request)`; omitting it left peer136's runtime
  unable to fire the falsifier (skill/runtime divergence trap). Add it to the manifest too.

## Worked example — G0-1 and G0-2 reviews

**G0-1 (adapter.py source-review).** Dev claimed v0.1.5 sha `6fc19e0f` "feature-set identical
to reviewed baseline `c164ba7a`, sha only differs due to minor bump". Reviewer actions:
- ssh-hashed the remote file → confirmed `6fc19e0f`, byte-identical to a local bundle copy →
  reviewed the actual bytes.
- Confirmed P0-10 by line: single `trace_id = str(uuid.uuid4())` generated once, propagated
  identically to `emit_retrieval`, `surface_execution_start`, `surface_execution_complete`,
  and the return dict; no chat_id fallback; fail-closed `_classify_traffic`.
- **Honest limitation stated in the verdict:** the baseline `c164ba7a` was NOT present on the
  reviewer node, so NO line-level baseline→0.1.5 diff was possible. Verdict = ACCEPT on
  **PRESENCE evidence** (markers confirmed present), NOT on a baseline diff; requested the
  baseline artifact for a real diff as a non-blocking follow-up.

**G0-2 (live trace_id proof).** Dev cited 5 live chains, an 18-non-organic count, a collector
event, and "30/30 PASS". Reviewer actions + findings:
- Parsed the dev's real `events.jsonl`: 5 chains all UUID v4, complete
  retrieval→start→complete, distinct, zero chat_id fallback. ✅
- Battery: bare `python3` gave "0 tests / No module aiohttp" (misleading). Re-ran with the
  gateway venv `/home/fausto/.hermes/hermes-agent/venv/bin/python` → the file is a custom
  `__main__` harness (4 fns / 30 sub-assertions) → reproduced **30 PASS / 0 FAIL**.
- **Finding the dev report OMITTED (found by independent log parsing):** a SECOND emit surface
  — the capability-reuse plugin hook (`source=hook_context.capability_reuse_provenance`,
  `producer_surface` EMPTY) — writes a DUPLICATE `retrieval_event` per trace_id that stamps
  `traffic_type=organic_peer` while its own `provenance.valid=False`. Same trace_id appeared
  once as correct `hmp_ingress/unknown` and once as bad `organic_peer/invalid`.
- **Disposition:** ACCEPT G0-2 (the finding is in a NEIGHBORING component, not adapter.py the
  subject; and `formal_holdout_validation` rejects `invalid_provenance` so nothing bad reaches
  the sealed holdout) BUT raised it as a mandatory pre-seal fix assigned to the next step
  (G0-3): apply the same fail-closed classifier on the hook, set a non-empty `producer_surface`,
  dedupe by trace_id, add a regression failing on `organic_* + valid=False`. Stated both the
  ACCEPT and the blocker plainly.

Lesson pattern: "ACCEPT this step + mandatory follow-up finding" is the right shape when the
deliverable is sound but independent inspection uncovers a real defect the report didn't
mention in an adjacent component.
