# Rebar Phase 1 — Gate Verdict Ledger

Durable record of reviewer verdicts for the Phase 1 gates. The PRIMARY artifact
for every verdict is the reviewer email in the Libero INBOX (subject `RE: [DEV] ...`,
sender `fausto.lelli@hotmail.com` / display "Pippo Baudo"); this file is a
convenience ledger, not the source of truth. Reconstruct disputes from the email
per loop-coding-guidelines §D.

Milestones so far: M1 ✅ · M2 ✅ · G1 ✅ · G2 ✅ · G3 ✅ · **G4 → see below (sent, awaiting verdict)** · (next: G5..G6 → D1 → F0 → R0a → R1)

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

## G4 — Duplicate-safety Gate-1 falsifier (SENT, AWAITING VERDICT)

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
- **SENT via human-mail** (NOT `[DEV]`): `humanmail.py enqueue --step G4
  --detail-file g4-bundle.txt --kind bundle` → queue id `108f1600caf5`, new
  thread, theme=corso, subject "Note della lezione di ieri", attachment
  `appunti-corso.txt` line1 `REBAR-STEP:G4`, send_after 2026-08-20 22:22 local.
  Dispatcher/monitor handle the actual send + reply pickup. **Awaiting verdict.**

---

## Note — email format fix (2026-08-20, out of gate sequence)

Reviewer confirmed (INBOX id 15) the new Hotmail-friendly email format
(text/plain body + text/plain attachment) arrives in INBOX and the attachment is
readable. Format fix validated end-to-end. See loop-coding-guidelines §A.
