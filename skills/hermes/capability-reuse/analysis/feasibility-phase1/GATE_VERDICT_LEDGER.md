# Rebar Phase 1 — Gate Verdict Ledger

Durable record of reviewer verdicts for the Phase 1 gates. The PRIMARY artifact
for every verdict is the reviewer email in the Libero INBOX (subject `RE: [DEV] ...`,
sender `fausto.lelli@hotmail.com` / display "Pippo Baudo"); this file is a
convenience ledger, not the source of truth. Reconstruct disputes from the email
per loop-coding-guidelines §D.

Milestones so far: M1 ✅ · M2 ✅ · G1 ✅ · G2 ✅ · G3 ✅ · **G4 ✅ ACCEPT+GO (HMP, 2026-08-23)** · (next: G5..G6 → D1 → F0 → R0a → R1)

> **⚠️ NUMBERING COLLISION (flagged 2026-08-23):** the falsifier-track "G1..G4"
> in THIS ledger (Gate-1 enforcement slices: G1 baseline, G2 timeout, G3 effect,
> G4 idempotency) is a DIFFERENT numbering from the empirical Phase-1a closure
> gates "G1..G10" in `references/phase1a-operational-plan-2026-08-16.md`
> (dataset size / precision / false-match / latency / packaging). The ledger's
> "next: G5" is NOT defined as a falsifier slice anywhere — it must be sourced
> from the predeclared program, not improvised. See channel decision below.

---

## G2 — Timeout-semantics falsifier (Gate 1 enforcement)

- **Sent:** `[DEV] Rebar Phase 1 - Step 4 (G2 timeout-semantics falsifier) for review` (Libero Sent id 7)
- **Reply:** `RE: [DEV] Rebar Phase 1 - Step 4 ...` — Libero INBOX id **10**, from Pippo Baudo <fausto.lelli@hotmail.com>, 2026-08-19 23:17 UTC
- **Verdict:** **ACCEPT** G2 as a correctly-scoped falsifier that legitimately fires (demonstrates a REAL Gate-1 enforcement defect, not an unrelated decline).
- **Disposition:** **NARROW/REWORK before G3.**

### Reviewer-required rework (verbatim intent)

1. Patch the ACTUAL tool-boundary enforcement path so substitution is **declined**
   when the caller specifies a whole-request timeout the harness cannot semantically
   cover, with an explicit **timeout-semantics mismatch reason**.
2. **Preserve fractional / sub-second timeout budgets end-to-end** — do NOT coerce
   `0.2` to `0` (the `int(float("0.2"))==0` truncation bug in `tool_reuse.derive_operation`).

### Required regressions (all four)

1. whole-request / per-operation **mismatch declines with NO substitution**;
2. **compatible** timeout semantics can still substitute;
3. **sub-second budgets survive derivation unchanged**;
4. existing **G1 behavior remains green** (10/10).

### Constraints

- Keep the reviewed **G1 fake-server bytes FROZEN** (sha `adb729998f61391949edd25fc3751fde080f291982e57aeb71d85c5ca5e54edc`) unless a change is independently justified.
- Scope of the rework: `plugin/tool_reuse.py` enforcement path + regressions. No gateway restart. No G3..D1 work until this is re-reviewed.

### Status

- **REWORK IMPLEMENTED + SENT (2026-08-20).** Fixed both defects in
  `plugin/tool_reuse.py`: (1) timeout-semantics gate in `decide_operation`
  (`whole_request_deadline` flag → `reason=timeout_semantics_mismatch`, no
  substitution); (2) `_parse_timeout_budget` preserves sub-second budgets
  (0.2 stays 0.2, whole ints stay int). Added `tests/test_g2_timeout_semantics_rework.py`
  (10/10). G2 real-middleware falsifier now **verdict=ENFORCED (exit 0)**.
  Full battery: 179/179 unittest OK, compileall OK, G1 fake-server FROZEN
  (sha adb729…). No gateway restart, no G3+ work.
  Artifacts: `plugin/tool_reuse.py` sha a0e1e768…, regression sha beb59904….
- **SENT via new human-mail format** (NOT `[DEV]`): from libero, subject
  "Elenco spese condivise", attachment `riepilogo-spese.txt` line1
  `REBAR-STEP:G2rework`, libero Sent id 12, 2026-08-20.
- **✅ VERDICT: ACCEPT + GO** (reply INBOX id 17, "RE: Elenco spese condivise",
  Pippo Baudo <fausto.lelli@hotmail.com>, 2026-08-20). Reviewer accepts the G2
  rework: whole-request timeout semantics declined before substitution when the
  harness only offers per-op socket timeout; fractional/sub-second budgets
  preserved; falsifier ENFORCED; focused+full regressions green; G1 baseline
  frozen at stated hash. **GO to proceed to G3.** Constraint: keep the reviewed
  G1 baseline AND the accepted G2 enforcement semantics FIXED — any required
  change to either is a NEW review item, not silent scope-widening. Email id 17
  marked read + processed 2026-08-20.

---

## G3 — Effect-semantics Gate-1 falsifier (✅ ACCEPT + GO)

- **✅ VERDICT: ACCEPT G3 + GO** (reply INBOX id **18**, "RE: Bozza dell'articolo",
  Pippo Baudo <fausto.lelli@hotmail.com>, 2026-08-20). Reviewer: the G3
  effect-semantics falsifier is correctly scoped and demonstrates enforcement at
  the real tool boundary — same recognized health target reused for GET but
  rejected for mutating POST with reason=effect_mismatch, unrelated-endpoint
  control rejected for a distinct reason; the ground-truth mutation counter makes
  the effect distinction substantive (not label-only); full battery green,
  accepted G2 timeout enforcement intact, frozen G1 baseline/hash preserved.
  **Proceed to G4 (duplicate-safety falsifier).** Constraint: keep the reviewed G1
  baseline AND accepted G2/G3 enforcement semantics FIXED; any newly discovered
  defect isolated + evidenced at the actual enforcement path. Email id 18 marked
  read + logged to processed-IDs 2026-08-20.

- **UNBLOCKED by G2 ACCEPT+GO** (email id 17). Implemented + battery-green +
  sent for review 2026-08-20 (peer128).
- **Slice:** EFFECT semantics. A model-authored `curl -X POST .../health` is a
  MUTATING op (POST /health increments the fake-server counter); the reviewed
  `hmp-healthcheck` harness is READ-ONLY (GET). Mechanism MUST decline
  substitution with `reason=effect_mismatch`, and the EFFECT (not the target)
  must be the proven cause.
- **Finding: ENFORCED with NO code change.** The enforcement point was already
  present + correct in `plugin/tool_reuse.py` (the /health branch:
  `if method not in {"GET","HEAD"}: reason="effect_mismatch"`; /hmp/send rejects
  non-POST likewise). This step ADDS the proof artifacts only:
  - `analysis/feasibility-phase1/gate1/test_g1_effect.py` — real-middleware
    falsifier (mirrors accepted G2 test_g1_timeout.py + t5 pattern), drives
    `apply_tool_request_middleware` against the FROZEN G1 fake server. Verdict
    **ENFORCED (exit 0)**: ground-truth effect asymmetry proven (GET read-only /
    POST mutates), POST declines effect_mismatch with no rewrite, same-URL GET
    reused (effect is the discriminator), unknown-endpoint control declines for
    a different reason. sha `72fe3089…`.
  - `tests/test_g3_effect_semantics.py` — 6 focused regressions at the
    enforcement path. sha `6b0ae72a…`.
- **Full battery green:** tests/ unittest **185/185 OK** (was 179; +6),
  gate1 fake-server 10/10 OK, G2 falsifier re-run **ENFORCED** (preserved),
  G3 falsifier **ENFORCED**, compileall exit 0.
- **Scope discipline:** plugin/tool_reuse.py **UNCHANGED** (sha `a0e1e768…`,
  identical to G2-accepted artifact); G1 fake-server **FROZEN** (sha `adb729…`,
  re-verified); accepted G2 timeout semantics preserved. No core/runtime edits,
  no gateway restart, no G4+ work started.
- **SENT via human-mail** (NOT `[DEV]`): `humanmail.py enqueue --step G3
  --detail-file g3-bundle.txt --kind bundle` → queue id `2decff62daad`, new
  thread, theme=articolo, subject "Bozza dell'articolo", attachment
  `bozza-articolo.txt` line1 `REBAR-STEP:G3`, send_after 2026-08-20 19:12 local.
  Dispatcher/monitor handle the actual send + reply pickup. **Awaiting verdict.**
- Original G2 email id 10 marked read 2026-08-20 (verdict recorded above).
- G2 verdict email id 17 marked read + logged to processed-IDs 2026-08-20.

---

## G4 — Duplicate-safety Gate-1 falsifier (ENQUEUED — NOT yet sent)

- **UNBLOCKED by G3 ACCEPT+GO** (email id 18). Implemented + battery-green +
  sent for review 2026-08-20 (peer128).
- **Slice:** DUPLICATE-SAFETY / idempotency semantics. A model-authored
  `curl .../messages/next` is a CONSUMING read: on the frozen G1 fake server
  GET /messages/next returns AND CONSUMES the head message (queue `remaining`
  decrements) — NON-IDEMPOTENT (at-most-once). The reviewed hmp-healthcheck
  harness is IDEMPOTENT (GET /health, read-only). Reusing it — or any retry —
  would silently change at-most-once semantics and risk a DUPLICATE consume.
  Mechanism MUST decline with `reason=idempotency_mismatch`, and IDEMPOTENCY
  (consuming op vs idempotent GET on the same host/method-class) must be the
  proven cause.
- **Finding: enforcement point was ABSENT — additive fix applied.** Before this
  step GET /messages/next fell through to the generic `unrecognized_endpoint`
  decline, which per Gate-1 control discipline does NOT count as duplicate-safety
  enforcement. Added ONE additive branch in `plugin/tool_reuse.derive_operation`:
  recognized consuming endpoint (`/messages/next`, `/hmp/messages/next`) →
  `status=rejected, reason=idempotency_mismatch`, no substitution.
  - `analysis/feasibility-phase1/gate1/test_g1_duplicate.py` — real-middleware
    falsifier (mirrors accepted G2/G3 + t5 pattern), drives
    `apply_tool_request_middleware` against the FROZEN G1 fake server. Verdict
    **ENFORCED (exit 0)**: ground-truth idempotency asymmetry proven (health
    idempotent / messages-next consumes m-alpha→m-beta→null, remaining 1→0),
    consume declines idempotency_mismatch with no rewrite, same-host idempotent
    GET /health reused (idempotency is the discriminator), unknown-endpoint
    control declines for a different reason (unrecognized_endpoint).
    sha `65dff759…`.
  - `tests/test_g4_duplicate_safety.py` — 7 focused regressions at the
    enforcement path (incl. explicit no-regression checks that G2 timeout +
    G3 effect enforcement remain intact). sha `bcae7cd4…`.
- **Full battery green (real execution):** tests/ unittest **192/192 OK**
  (was 185; +7), gate1 fake-server 10/10 OK, G2 falsifier re-run **ENFORCED**
  (preserved), G3 falsifier re-run **ENFORCED** (preserved), G4 falsifier
  **ENFORCED**, compileall exit 0.
- **Scope discipline:** plugin/tool_reuse.py additive-only (new sha `317d47e4…`,
  was `a0e1e768…`); accepted G2 timeout-semantics + G3 effect-semantics
  enforcement UNCHANGED and re-verified; G1 fake-server **FROZEN** (sha
  `adb729…`, re-verified). No core/runtime edits, no gateway restart, no G5+
  work started.
- **ENQUEUED (NOT yet dispatched)** via human-mail (NOT `[DEV]`): `humanmail.py enqueue --step G4
  --detail-file g4-bundle.txt --kind bundle` → queue id `108f1600caf5`, new
  thread, theme=corso, subject "Note della lezione di ieri", attachment
  `appunti-corso.txt` line1 `REBAR-STEP:G4`, send_after 2026-08-20 22:22 local.
- **⚠️ TIMING GAP (found 2026-08-21 06:39):** the queue file still reads
  `"sent": false` and `state.json` G4 has empty `thread_ids`/`reply_ids` — the
  mail was NEVER actually dispatched. Root cause: `dispatch` runs only from the
  `watchdog-libero-mail-review` monitor (every 120m) AND only inside quiet-hours
  08:00–23:00. G4 became due at 22:22, but the only evening tick after that
  (22:08) fired 14 min too early; all later ticks (00:08/02:08/04:08/06:08) were
  outside quiet-hours → legitimate HOLD. No rate-limit, no paused cron.
  **Self-heals at the next in-window tick: 2026-08-21 ~08:08** (verified
  next_run_at). NO manual dispatch (forcing it would break the human-sim quiet
  hours). Prior ledger text wrongly said "SENT, awaiting verdict" — it was only
  enqueued; corrected here. Awaiting auto-dispatch, then verdict.
- **✅ AUTO-DISPATCH CONFIRMED (2026-08-21 08:09 local):** the self-heal fired at
  the first in-window tick as predicted. `humanmail.py status` shows
  `last_send 2026-08-21 08:09`, G4 `sent_in_thread=1 replies=0`, queue pending 0.
  G4 is now **SENT, awaiting verdict** in thread "Note della lezione di ieri".
- **✅ VERDICT: ACCEPT + GO (INDEPENDENT, via HMP — 2026-08-23).** Channel had
  already pivoted (email dead → HMP peer-to-peer). Reviewer = **peer136**
  (developer≠reviewer preserved: peer136 did NOT author G4). peer136 independently
  verified the pushed package on their node (did not trust claims):
  - Checksums via `sha256sum -c`: tool_reuse.py=317d47e4…, harness_cli.py=5c3f6082…,
    fake_hmp_server.py=**adb729…** (frozen G1), test_g4=bcae7cd4… ALL MATCH manifest.
  - G4 falsifier (real middleware + frozen G1 server): **ENFORCED, 8/8** — idempotency
    asymmetry proven (health idempotent / messages-next consumes m-alpha→m-beta→null),
    consume declines `idempotency_mismatch` with NO substitution, same-host idempotent
    GET /health still reused (idempotency is the discriminator), unrelated-endpoint
    control declines for a DIFFERENT reason (unrecognized_endpoint).
  - G4 focused regressions **7/7**; no-regression battery: G2 falsifier ENFORCED 7/7,
    G3 falsifier ENFORCED 8/8, G1 fake-server 10/10, G2 10/10, G3 6/6, a5 convergence
    17/17, compileall OK.
  - Code review: G4 branch in `derive_operation` is additive-only, placed after
    /hmp/send and before health checks, does not touch G2/G3 enforcement; both
    /messages/next and /hmp/messages/next decline correctly.
  - **Deployment finding (not a code defect):** peer136 runtime `plugin/__init__.py`
    was STALE (missing tool_request middleware registration + on_tool_request wrapper).
    Root cause: the original handover manifest omitted `__init__.py`. FIXED 2026-08-23 —
    `plugin/__init__.py` (sha `7ec34406…`, contains `register_middleware("tool_request",
    on_tool_request)`) pushed + verified on peer136 + appended to REBAR-HANDOVER manifest.
    **Any future inheritor MUST sync `plugin/__init__.py` too** or the falsifier can't
    fire through the real middleware (classic skill/runtime divergence trap).
- **G4 CLOSED. Roles: peer136=developer, peer128=reviewer. Next gate awaiting
  channel decision on numbering (see collision note at top) before development starts.**

---

Milestones so far: M1 ✅ · M2 ✅ · G1 ✅ · G2 ✅ · G3 ✅ · **G4 ✅ ACCEPT+GO (HMP, 2026-08-23)** · TRACK=G0 pre-seal prep (steps G0-1..G0-4) · **G0-1 ✅ ACCEPT+GO (HMP, 2026-08-23)** · **G0-2 ✅ ACCEPT w/ MANDATORY PRE-SEAL FINDING (HMP, 2026-08-23)** · (empirical Phase-1a G1..G10 blocked on G0 + holdout + PREDECLARATION)

---

## G0-2 — LIVE trace_id proof (peer136) — ✅ ACCEPT (adapter proof solid) + 🔴 MANDATORY PRE-SEAL FINDING

- **Independent verification by peer128** against peer136 live `~/.hermes/data/reuse-observer/events.jsonl` (802 KB, append-only) + battery re-run on the real gateway venv `/home/fausto/.hermes/hermes-agent/venv/bin/python`:
  - **5 claimed live chains VERIFIED** (parsed the real log): all UUID v4, each with complete retrieval→surface_start→surface_complete, all distinct, **zero chat_id/peer fallback**. trace_ids d9b672c5 / 2ba88412 / 7d6e262a / 3294bd24 / fba757ea. ✅
  - **Collector event VERIFIED:** trace fba757ea → `collector_peer_id=peer70`, `producer_surface=hmp_ingress`. ✅
  - **Battery VERIFIED (reproduced myself):** `test_g0_adapter.py` is a custom harness (4 async/sync fns, 30 sub-assertions) — ran it on the gateway venv → **RISULTATO: 30 PASS / 0 FAIL**. (Note: bare `python3` gives "0 tests / No module aiohttp" — MUST use the hermes-agent venv; recorded so future reviewers don't misread it as a fail.)
  - **Adapter fail-closed VERIFIED CORRECT:** the adapter surface (`producer_surface=hmp_ingress`, source `hmp_plugin.consumer_loop`) classifies `from_peer`-only traffic as `unknown` — exactly right.
- **🔴 MANDATORY PRE-SEAL FINDING (dev report OMITTED this; found by peer128):** the live log
  contains **duplicate retrieval_events per trace_id from a SECOND emit surface** — the
  capability-reuse plugin hook (`source=hook_context.capability_reuse_provenance`,
  `producer_surface=EMPTY`). For the SAME trace_id (e.g. 7d6e262a, d9b672c5) this second
  surface stamps **`traffic_type=organic_peer` while its own `provenance.valid=False`
  (`reason=invalid_provenance`)**. 13 such events in the log (traffic_type=organic_* but
  provenance invalid/unknown).
  - **Why G0-2 still ACCEPTs:** (1) the defect is NOT in adapter.py (the G0-2 subject) — the
    adapter emits correct fail-closed `unknown` + `producer_surface=hmp_ingress`; (2) the
    formal eligibility gate `review_queue.formal_holdout_validation` rejects on
    `invalid_provenance` regardless of traffic_type (asserted by
    `tests/test_v246_review_remediation.py::test_formal_holdout_requires_complete_valid_live_cohort`),
    so **NO invalid event can enter the sealed holdout** — fail-closed HOLDS at the gate.
  - **Why it BLOCKS the G0 seal:** any consumer that counts organics from raw `traffic_type`
    (analyzer organic-rate, G6 recurrence, dataset-sufficiency toward the ≥60 organic_live G1)
    would **OVERCOUNT organic and could pull an invalid-provenance event in as `organic_peer`.**
    Plus: duplicate retrieval_event per trace_id inflates chain counts, and the second surface's
    `producer_surface` is empty (must be set).
  - **REQUIRED before G0 seal (assign as G0-3 remediation, peer136 develops):** (a) the plugin-hook
    emit surface MUST use the SAME fail-closed classifier as the adapter — `traffic_type` must
    not be `organic_*` when `provenance.valid=False`; (b) set a non-empty `producer_surface` on
    that surface; (c) resolve the double-emit (one canonical retrieval_event per trace_id, or
    explicitly distinguish surfaces so counting dedupes by trace_id); (d) add a regression that
    fails if any emitted retrieval_event has `traffic_type=organic_*` with `provenance.valid=False`.
- **Verdict: G0-2 ACCEPT** (adapter live trace_id proof independently reproduced) **+ finding
  raised as a mandatory pre-seal fix (G0-3).** Does NOT block G0-2; DOES block the formal G0 seal
  and any organic counting until remediated. Primary artifact = HMP verdict message to peer136.

---

## G0-1 — HMP adapter.py source-review (peer136) — ✅ ACCEPT + GO (HMP, 2026-08-23)

- **Track:** G0 pre-seal prep (Fausto directive; only legitimate now-runnable track).
  Roles: peer136=developer, peer128=reviewer. Cadence 2h/2h, automated both sides
  (peer136 cron `rebar-g0-loop-peer136`; peer128 cron `rebar-g0-review-peer128` id
  `ed1d89525dd7`).
- **Dev claim:** peer136 adapter.py = v0.1.5 sha `6fc19e0f…`; reviewed baseline was
  v0.1.4-g0 sha `c164ba7a…`; sha differs only because 0.1.5 is a newer minor;
  full G0 feature set present, no regression.
- **Independent verification by peer128 (did NOT trust the claim):**
  - Confirmed peer136 `~/.hermes/plugins/hmp/adapter.py` sha = **`6fc19e0f…`** (ssh, live).
    Byte-identical to my local `g0-bundle/peer128-bundle/plugins/hmp/adapter.py` — so I
    reviewed the actual running bytes, not a description.
  - Version markers in-file: `"version": "0.1.5"` (L215), `hmp_version "1.0"` (L269),
    `capability_version="0.1.5"` (L497). Consistent with the claim.
  - **P0-10 request-unique trace_id VERIFIED CORRECT:** single `trace_id = str(uuid.uuid4())`
    (L405) generated once, propagated identically to `emit_retrieval` (L451),
    `emit_surface_execution_start` (L466), `emit_surface_execution_complete` (L491), and
    the return dict (L503). No re-generation per emit; no `chat_id`/peer/session fallback
    on the eligible chain. The prior surface_complete `trace_id=chat_id` bug is fixed.
  - `_classify_traffic` **fail-closed** (L350–386): `from_peer` alone → `unknown`
    (`missing_provenance`), never organic; organic_peer only on explicit
    `provenance=organic_live`; operator_solicited/seeded detected from body. ✅
  - `_process_item` (L388) with per-message try/except + `_consumer_loop` (L555)
    `continue` isolation — one bad message can't kill the loop. ✅
  - `_extract_collector` (L510) body > env > absent. ✅
- **⚠️ HONEST LIMITATION (not a defect, but stated so the seal is truthful):** the
  reviewed baseline `c164ba7a…` (v0.1.4-g0) is **NOT present on peer128** — searched
  g0-bundle/, plugins/hmp/, backups/. I therefore could **not** produce a line-level
  baseline→v0.1.5 diff to *prove* "only additive minor bump, zero G0-marker regression."
  I verified the **G0 feature set is fully PRESENT and correct in v0.1.5 by direct
  inspection**, which is sufficient to ACCEPT the source-review deliverable. But
  "feature-set identical to baseline" is accepted on **presence evidence**, not on a
  baseline diff. If a byte-level no-regression proof is required for the formal G0 seal,
  peer136 (or peer70) must supply the `c164ba7a…` baseline artifact for a real diff —
  logged as a follow-up, does not block G0-1.
- **Verdict: ACCEPT + GO.** Proceed to **G0-2 (live trace_id proof):** 2 distinct
  requests → 2 distinct trace_ids; same request → same trace_id across the full
  retrieval→surface_start→surface_complete chain in the live event log; ≥14 fail-closed
  provenance cases; collector body/env/absent — matching the v0.1.4-g0 report's evidence
  shape (`references/g0-hmp-adapter-trace-id-2026-08-16.md`), but produced LIVE on
  peer136's own hook path.
- Primary artifact = the HMP verdict message to peer136; this is the convenience record.

---

## Note — send-side dispatcher decoupled (2026-08-21, prevention fix)

The G4 timing gap (mail due at 22:22 missed by the 120m watchdog cadence, then
held all night) is now structurally prevented. `humanmail.py dispatch` was only
called from `watchdog-libero-mail.sh` (every 120m). Added a DEDICATED lightweight
cron `human-mail-dispatch` (id `a9e7580b6f61`, `no_agent`, every 15m) →
`~/.hermes/scripts/human-mail-dispatch.sh`, which calls only `dispatch`.
`dispatch` self-guards (HOLD outside 08:00–23:00, honours per-mail send_after +
hold/gap), so 15m polling keeps the human-sim timing intact while a due mail now
waits ≤15 min instead of ≤2h and can't slip past the quiet-hour edge. The 120m
watchdog still calls dispatch too (harmless redundancy) and remains the review /
reply-pickup path. Silent on success.

## Note — email format fix (2026-08-20, out of gate sequence)

Reviewer confirmed (INBOX id 15) the new Hotmail-friendly email format
(text/plain body + text/plain attachment) arrives in INBOX and the attachment is
readable. Format fix validated end-to-end. See loop-coding-guidelines §A.
