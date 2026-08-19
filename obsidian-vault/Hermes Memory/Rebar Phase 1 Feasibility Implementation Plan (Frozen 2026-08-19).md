# Rebar — Phase 1 Feasibility Falsification: Implementation Plan

> **For reviewers (Fausto + peer70/peer106 + external):** this plan implements the falsifiers defined in
> `REBAR_FEASIBILITY_FALSIFICATION_PROGRAM.md` (Phase 1, "Can we even do it?"). It does **not** decide whether
> Rebar is worth operating (Phase 2). It is written for execution via `subagent-driven-development` with two-stage
> review, but **Task group A cannot start until the §2 pre-declaration is human-signed** — see Gate S below.

**Goal:** Stand up and run the Phase-1 falsifiers (A1, Gate 1, the structural DEMO, A5, A6) against the *already-built*
Rebar tool-boundary plugin, and reach one of the program's **four** terminal states (FEASIBLE / NARROW-REWORK /
NOT-FEASIBLE / INCONCLUSIVE-PHASE-1-OPEN) with pre-declared, reviewable evidence.

**Architecture:** Reuse the existing `capability-reuse` skill/plugin. Add a new isolated subtree
`analysis/feasibility-phase1/` for the falsification harnesses, fixtures, pre-declaration record, and evidence —
so falsification artifacts never contaminate the plugin runtime or the existing evidence bundles.

**Tech stack:** Python stdlib only (no new deps), `unittest` for Gate 1 falsifiers, a local `http.server` fake HMP
server, JSONL/CSV for logs. Matches the rest of the skill.

---

## Current context / assumptions (verified 2026-08-19)

**Already exists (do NOT rebuild):**
- `plugin/tool_reuse.py` (+ runtime copy `~/.hermes/plugins/capability-reuse/tool_reuse.py`) — Rebar founding loop at the real generic-tool boundary: operation signature from `terminal.command`/`execute_code`, exact harness lookup, tool-level safety decision per `tool_call_id`, single-fire Observe (reused/rejected/no_harness).
- `plugin/retriever.py` — `_extract_request_effect()` with EN+IT mutating/read/composite classification (T5a).
- `plugin/dispatcher.py` — deterministic read-only executor for `hmp-healthcheck@1.0.0`; PEER_MAP targets.
- `plugin/protocol.py`, `plugin/event_store.py` (schema 1.3, correlation envelope), `plugin/compatibility.py`, `plugin/registry.py`.
- `scripts/conformance-suite.py` (15/15), `scripts/batch-reuse-analyzer.py`, `tests/` (169-suite).
- Live shadow harvesting: `~/.hermes/data/reuse-observer/events.jsonl` is the canonical organic proposal source.

**Gaps Phase 1 must fill:**
- No pre-declaration record artifact (families / defaults / NOT_APPLICABLE / exclusions / **proposal-generation identity pin**).
- No A1 sampling + mechanical recoverability rubric scorer + second-rater tooling + metrics (coverage / normalizability / effective_reuse_surface, reported not gated).
- No `INSUFFICIENT_ORGANIC_EVIDENCE` guard (<30 in-family after 300).
- No deterministic **fake HMP server** with the §4 endpoints, and no five Gate-1 falsifier tests asserting the *specific* enforcement point.
- No structural DEMO (ready-vs-health coincidental agreement).
- No A5 material-change log + convergence-window gate.
- No A6 comparator calibration fixtures + verified-shadow reliability matrix + stop rule. (Comparator identity must be pinned; confirm whether a comparator exists or is new — see Task F0.)

**Assumptions (flag if wrong):**
1. A1 labeling is human, per the program (§11). Code assists scoring; it does not decide recoverability.
2. Phase-1 work lives on Charon/peer70 primary + one peer for second-rater independence; no gateway restart required for A1 (offline analysis of `events.jsonl`).
3. No new production behavior ships in Phase 1. `hmp-send` stays mutating/unsafe/not-active. Active path stays limited to `hmp-healthcheck@1.0.0`.

---

## Sequencing (mirrors program §8)

```
Gate S  — §2 pre-declaration filled + human-signed        [BLOCKS everything in group A]
Group A — A1 sampling + rubric + second-rater + metrics    [cheapest pre-build kill; runs FIRST]
Group G — Gate 1 fake server + 5 falsifiers + DEMO         [alongside minimum normalizer work]
Group M — A5 material-change logging STARTS before any relevant normalizer/capability/comparator commit
Group R-prep — F0 discover comparator/pairing · R0a build+qualify producer · R1 build/calibrate comparator if needed
FREEZE EVIDENCE IDENTITIES — normalizer · admitted capability · comparator
OPEN A5/A6 STABLE WINDOW  ← the A6 evidence window IS the window through which A5 convergence is demonstrated
Group R-evidence — Gate R-A candidate admission · R0b acquire real-condition pairs · R2 accumulate first 50 valid pairs
M2 — confirm the completed A6 window was also an uninterrupted A5-stable window
Gate X  — Phase 1 exit verdict assembled + evidence sealed (FEASIBLE / NARROW-REWORK / NOT-FEASIBLE / INCONCLUSIVE)
```

Only Group A is a true pre-build kill. R-prep/R-evidence exercise already-built machinery (§11: they can't inform the earliest build/no-build decision). **A5 is not a precondition R waits for — A6's evidence window is the window through which A5 convergence is demonstrated.**

---

## Files likely to change / create

All new work under `~/.hermes/skills/hermes/capability-reuse/analysis/feasibility-phase1/`:
```
predeclaration/PREDECLARATION.md            (Gate S — human-filled, signed)
a1/collect_proposals.py                     (Task A1)
a1/rubric_aggregate.py                      (Task A2 — human-label validator/aggregator)
a1/second_rater.py                          (Task A3)
a1/metrics.py                               (Task A4)
gate1/fake_hmp_server.py                    (Task G1)
gate1/test_g1_timeout.py                    (Task G2)
gate1/test_g1_effect.py                     (Task G3)
gate1/test_g1_duplicate_safety.py           (Task G4)
gate1/test_g1_registry_authenticity.py      (Task G5)
gate1/test_g1_policy_monotonicity.py        (Task G6)
demo/ready_vs_health_demo.py                (Task D1)
a5/material_change_log.py + material_change_log.jsonl  (Task M1)
a5/convergence_gate.py                      (Task M2)
a6/comparator_calibration.py + fixtures/    (Task R1)
a6/pair_producer.py + pairs.jsonl           (Task R0 — verified-shadow paired-execution producer)
a6/reliability_matrix.py                    (Task R2)
evidence/                                    (sealed outputs + SHA256SUMS)
```
No edits to `plugin/*` unless a Gate-1 falsifier exposes a real defect (then: patch + regression, per program NARROW/REWORK).

---

## Gate S — Pre-declaration (BLOCKING, human)

**Objective:** Produce and sign the §2 block before any A1 data is inspected. Nothing in Group A may run first.

**Step 1:** Create `predeclaration/PREDECLARATION.md` from the program's §2 template, containing:
- proposal-generation identity: `model_id`, `model_version/snapshot`, `runtime/gateway_version`, `system_prompt_identity_or_hash`, `tool_surface_revision_or_hash`, `relevant_generation_configuration`.
- target operation families:
  - `hmp_healthcheck` is the initial **required** family.
  - additional families **MAY** be declared before sampling but are **not required** by this implementation plan. Choosing more families is a Gate-S human decision (it changes A1's denominator and can materially move coverage and normalizability), not an implementer default.
  - each declared family carries an **operational assignment rule** (based on requested operation, not on normalizer success).
- recoverability defaults per family (with source of the default).
- NOT_APPLICABLE properties per family with reason.
- sampling exclusions (Rebar-dev sessions/windows).
- second-rater sampling rule (every 5th in-family, ≥20%).
- `Declared by / Date` sign-off line.

**Step 2 (human):** Fausto + one reviewer fill and sign. **Verification:** file has no blank `____` fields and a signature/date. Until then, `collect_proposals.py` must refuse to run (assert a signed PREDECLARATION exists).

**Risk:** model was swapped 3× in one session historically → an unpinned identity makes A1 meaningless. The pin + no-pooling rule (program §2.1) is the mitigation; Task A1 enforces it mechanically.

---

## Group A — A1: is the real substrate present?

### Task A1: proposal collection harness
**Files:** Create `a1/collect_proposals.py`.

**Identity rule (normative — A1 is the only cheap premise-kill, so identity must be *evidenced*, not asserted):**
- A proposal is A1-eligible **only if its proposal-generation identity can be established from contemporaneous metadata/evidence** (identity captured *at generation time*). **Post-hoc stamping the currently-active identity onto an old record is NOT identity evidence** and disqualifies the record.
- **Default for the first A1 run:** use a **fresh, explicitly bounded, single-identity collection window** — unless historical `events.jsonl` records already contain independently verifiable *complete* proposal-generation identity (model + snapshot + runtime/gateway + system-prompt hash + tool-surface rev + generation config) captured contemporaneously. Given models were swapped repeatedly, treat historical data as ineligible unless it clears that bar per-record.
- The run header MUST contain the identity **and the evidence establishing it**, not merely a copy of the active identity.

- Step 1 (test first): `test_collect_refuses_without_signed_predeclaration` → SystemExit when PREDECLARATION has blank fields; `test_rejects_record_without_contemporaneous_identity` → a record lacking generation-time identity evidence is excluded, not stamped.
- Step 2: implement: assert signed pre-declaration; open/read the bounded single-identity window (or, for historical mode, admit only records with verifiable contemporaneous identity); select consecutive organic generic-tool proposals in collection order; apply declared exclusions; do not filter to HMP-looking requests; stop at the program's checkpoints (100 interim; continue to ≥30 in-family or 300 max).
- **Identity change VOIDS the run (fresh-window mode) — do NOT merely skip the off-identity record.** If the active window is `identity A, identity A, identity B appears`, the collector raises `A1RunInvalid`. Silently discarding B and continuing to count later A records would break the *consecutive organic proposals* property and bias the sample. ("Refuse to pool across identities" is the weaker offline-analysis rule; the live collector enforces the stricter void.)
- Step 2b test: `test_identity_change_voids_run` → a mid-window identity switch raises `A1RunInvalid`, not a skip-and-continue.
- Step 3: emit `a1/collected_proposals.jsonl` + a run header (identity, **identity-evidence source**, window span, exclusions applied).
- Verify: run on a small fixture slice; assert ordering preserved, a no-identity record is rejected, and the header carries identity evidence.

### Task A2: recoverability rubric — human-label validator/aggregator (NOT an auto-scorer)
**Files:** Create `a1/rubric_aggregate.py`.
- **A1 stays human-labeled.** This script **validates and aggregates human property labels**; it MUST NOT algorithmically decide whether `target`, `effect`, `timeout`, etc. are recoverable — otherwise it quietly mechanizes the very judgment the signed program subjects to a second rater.
- Consumes human-entered labels for the 10 execution-significant properties in `{R_EXPLICIT, R_DEFAULT, NOT_APPLICABLE, NOT_RECOVERABLE}`.
- **Validation rules it enforces (not decisions it makes):** `R_DEFAULT` only cites a pre-declared default; `NOT_APPLICABLE` only cites a pre-declared family rule; neither may be entered to improve the score (reject with error if the cited declaration is absent). Any applicable property labeled `NOT_RECOVERABLE` ⇒ headline is not `fully_normalizable`.
- Computes headline label deterministically **from the human labels** + retains per-property labels (so A1 reports *why* normalizability failed).
- Test: a single human `NOT_RECOVERABLE` correctly forces `fully_normalizable`→`partially_normalizable`; an `R_DEFAULT` citing an undeclared default is rejected; the script never assigns a property state itself.

### Task A3: second-rater support
**Files:** Create `a1/second_rater.py`.
- Selects every 5th in-family proposal, blinds first labeler's scores, records per-property + headline disagreement rates. **≥20% floor:** "every 5th" is slightly under 20% for some N (e.g. 6/31); when `count(every-5th) < ceil(0.20 × N)`, add enough **deterministic tail items** (by collection order) to reach `ceil(0.20 × N)`.
- **Invalidation rule:** an unresolved disagreement that flips numerator membership (`fully_normalizable`) voids the A1 run — must not be negotiated away after seeing the %.
- Test: a constructed numerator-flipping disagreement raises `A1RunInvalid`.

### Task A4: metrics + decision bands (report-only surface)
**Files:** Create `a1/metrics.py`.
- Computes `target_family_coverage`, `normalizability`, `effective_reuse_surface = coverage × normalizability`.
- Applies bands **only to `normalizability`** and **only when ≥30 in-family** (≥80 CONTINUE / 60–79 INVESTIGATE / <60 STOP-OR-NARROW).
- **§3.5.1 (as amended):** `effective_reuse_surface` is **reported, not gated** — a low value MUST NOT by itself fail A1; interpretation deferred to Phase 2.
- **§3.5.2:** if `<30` in-family after 300 → emit `A1_NORMALIZABILITY = INSUFFICIENT_ORGANIC_EVIDENCE` with coverage + raw in-family count + sampling span; **not** a feasibility failure.
- Also report: per-property NOT_RECOVERABLE rates, second-rater disagreement, window span, identity, raw numerator/denominator.
- Test: the 4%-coverage/95%-normalizability case → CONTINUE on normalizability, surface reported, no gate fired; the `<30` case → INSUFFICIENT_ORGANIC_EVIDENCE.

---

## Group G — Gate 1: can the mechanism reject what it must reject?

### Task G1: deterministic fake HMP server
**Files:** Create `gate1/fake_hmp_server.py` (stdlib `http.server`, fixed responses, no randomness/timestamps).
Endpoints: `GET/POST /health` (POST mutates), `GET /slow-health` (2s delay), `GET /ready`, `GET /messages/next` (returns AND consumes), `POST /admin/state`. Test: server starts, each endpoint returns its declared shape.

### Task G2–G6: the five falsifiers (each asserts the *specific* enforcement point)
- **G2 timeout semantics:** `curl --max-time 0.2 /slow-health` vs `hmp_healthcheck(timeout=5)` ⇒ expect `whole_request_covered=false`, `reason=timeout_semantics_mismatch`, no substitution. (Reject-for-unrelated-reason must NOT pass.)
- **G3 effect semantics:** `POST /health` (mutates) ⇒ expect `effect_mismatch`, no substitution; assert *effect* caused it.
- **G4 duplicate-safety:** add a **test-only** admitted capability `test_next_message()` (read_only, `duplicate_execution_safe=false`) matching `GET /messages/next`; expect candidate compatible + covered but refused specifically for `duplicate_execution_safe=false`. A `no_capability`/family-mismatch rejection does NOT pass.
- **G5 registry-binding authenticity:** authenticated registry `hmp_healthcheck→hash A`; tamper snapshot to `hash B` without re-auth ⇒ expect `registry_authenticity_failure`, no dispatch. If artifact B verifies against attacker-supplied hash B, hashing established no trust.
- **G6 policy monotonicity:** policy "peer-blocked may not be contacted"; `curl /peer-blocked/health` blocked; `hmp_healthcheck(peer="peer-blocked")` ⇒ `blocked(original)` MUST NOT become `allowed(rewritten)`. **This test MUST exercise the real pinned policy/guardrail ordering** (original proposal → Rebar rewrite → guardrail/policy → dispatch), **or** an independently demonstrated execution harness identical in the relevant ordering and policy inputs. A unit test of compatibility logic cannot falsify a rewrite-induced policy bypass, so **if the real ordering cannot be exercised, G6 is NOT passed — it is not downgraded to a local unit test.** The same principle applies to any Gate-1 assertion whose validity depends on runtime placement (notably G5 registry binding).
- Each: test-first, run against `plugin/` machinery via the real middleware path (mirror `scripts/t5-real-middleware-proof.py`); where an assertion depends on runtime ordering, the real ordering is mandatory, not best-effort.
- **If any falsifier exposes a real defect:** stop, patch `plugin/*`, add regression, rerun the affected gate (program NARROW/REWORK).

### Task D1: structural DEMO (not a standalone falsifier)
**Files:** Create `demo/ready_vs_health_demo.py`. Normal state `/ready=true /health=true`; let normalizer propose `hmp_healthcheck` for a *readiness* request; run verified-shadow in normal state only ⇒ perfect output agreement despite non-equivalence. Conclusion asserted: outcome agreement alone cannot establish semantic equivalence; equivalence review stays mandatory.

---

## Group M — A5: can the evidence loop converge?

### Task M1: material-change log — **start before the first relevant Phase-1 commit**
**Files:** Create `a5/material_change_log.py` + `material_change_log.jsonl`.
- **Timing (normative):** M1 MUST be created and begin logging **before the first Phase-1 commit that touches `normalizer | capability | comparator`** — i.e. before any change that could later participate in an evidence window. Do NOT implement M1 after several such changes and reconstruct classifications retrospectively; retrospective classification defeats the ratchet. In the execution order M1 is therefore stood up at the *start* of any work that can move those three components (including Task R0/R1 comparator work).
- For every Phase-0/1 change to `normalizer | capability | comparator`: `date, component, material(yes/no), rationale`. Materiality declared at commit time. **Ratchet:** review may upgrade non-material→material; MUST NOT downgrade material→non-material to rescue a window.

### Task M2: convergence gate
**Files:** Create `a5/convergence_gate.py`. Verifies ≥1 complete window where normalizer + capability contract/impl + comparator are all materially unchanged. If unachievable ⇒ loop not converged (permitted responses: freeze during window / narrow family / simplify / explicitly amend evidence policy — never redefine materiality to pass). Test: an in-window material change voids the window.

---

## Group R — A6: can the admitted capability behave more reliably than regeneration?

### Task F0 (spike, do first): confirm comparator identity AND verified-shadow availability
Two prerequisites, both gating:
1. **Comparator identity.** Determine whether a semantic comparator exists in the plugin or must be built minimally. Record `comparator_version`, `comparator_artifact_hash`, `comparison_rules_version`. A6 cannot start without a pinned comparator identity.
2. **Verified-shadow pairing capability.** Determine whether *verified-shadow paired execution* (original + candidate executed against the **same environmental state**) actually exists as deployed functionality. The current "Already exists" inventory does **not** list it. If it does not exist, Task R0 must build a controlled Phase-1 pairing harness before any pairs can be produced. **Gate:** A6 is not implementable until a valid pair-generation path is defined and proven.

### Task R0: verified-shadow paired-execution PRODUCER (new — the evidence-creation path A6 depends on)
**Files:** Create `a6/pair_producer.py` → `pairs.jsonl`. A matrix consumer (R2) cannot run without a producer of legitimate pairs; this is that producer. **Split into two distinct sub-tasks — qualifying the machinery is NOT the same as acquiring A6 evidence.**

Each emitted pair record MUST carry:
```
decision_id
original_execution_id
candidate_execution_id
normalizer_identity
capability_identity
comparator_identity
original_result
candidate_result
candidate_independent_timeout
candidate_provenance
original_result_isolation   (proof original result was not derived from / contaminated by the candidate)
environmental_equivalence   (the declared criterion below, evaluated per pair)
```

#### R0a — pair-producer qualification (fake HMP permitted)
Against the deterministic fake HMP server (Group G), prove the harness itself is sound: **pairing, original-result isolation, independent candidate timeout, provenance capture, audit/correlation, and same-state / state-change rejection**. This qualifies the *machinery only*. **Pairs produced here MUST NOT count toward the 50 A6 feasibility pairs.**
- Test: producer rejects a pair whose original and candidate ran at different server states; accepts a fully-formed same-state pair; refuses a replayed-historical record.

#### Gate R-A — candidate admission (BLOCKS R0b; real pairs cannot count until this passes)
"Already exists," "active," or "previously validated" is **not** admission under the frozen architecture. Before any real-condition A6 pair counts, the candidate capability (`hmp-healthcheck@1.0.0`) MUST have:
```
approved admission record
exact contract_version recorded
exact implementation_version recorded
artifact_hash verified
authenticated registry binding verified   (ties to G5)
effect_class approved
duplicate_execution_safe = true
duplicate-execution constraints satisfied  (ties to G4)
```
This does **not** mean building all of Spec A during Phase 1 — only that the first A6 capability clears the **minimum admission requirements the architecture already mandates**. **If these are not established, R0b MUST NOT start and A6 cannot accumulate feasibility pairs.** (Otherwise A6 would "prove" an experimental harness reliable and mislabel that as evidence about reviewed procedural memory.)

#### R0b — A6 evidence acquisition (real eligible execution conditions, MANDATORY)
The 50 A6 feasibility pairs MUST be acquired under **real eligible execution conditions** — because A6 asks whether the admitted capability can be trusted against regenerated execution *in current reality*. Fifty perfect pairs against a fake deterministic server can pass while the real HMP endpoint, auth, schema, transport, or artifact assumptions are stale.
- **original side:** a naturally generated generic proposal.
- **candidate side:** the exact admitted capability.
- both linked to the **same Rebar decision**.
- **Synthetic or hand-authored original calls may test the machinery (R0a) but MUST NOT count toward the 50 A6 feasibility pairs.**
- **If valid real verified-shadow pairing cannot be performed safely, A6 = INCOMPLETE — NOT "passed on the fake server."**

**Environmental-equivalence criterion (declared, per pair — replaces naive "same environmental state"):**
For a real peer we cannot prove the universe stayed identical between two requests. A pair counts only if it satisfies a **declared equivalence criterion**: same target; same relevant deployment/schema/config identity **where observable**; bounded temporal separation; and no known intervening state change. **If the criterion fails, discard the pair** rather than pretending exact simultaneity. Replayed or independently re-executed historical requests at a later environmental state are not pairs and MUST NOT be admitted.

**Freeze the criterion BEFORE the 50-pair window (anti-gaming):** `environmental_equivalence_policy` is declared and frozen as a versioned identity/hash *before any pair result is inspected*, then applied uniformly to every candidate pair — so no one can decide *after* seeing a disagreement that "actually, that pair wasn't environmentally equivalent." A material change to the policy **voids the incomplete window and restarts** it (prior negative findings remain findings). The policy identity/hash is included in the sealed A6 evidence.

### Task R1: comparator calibration (two-sided, before the window)
**Files:** Create `a6/comparator_calibration.py` + `fixtures/`.
- Positive controls (declared-volatile differences: request_id, timestamp, allowed ordering, in-tolerance numeric) → must classify equivalent.
- Negative controls (healthy flips, required field disappears, status/semantic change, out-of-tolerance numeric) → must classify non-equivalent.
- Calibration passes only if BOTH classes correct. Controls must not contradict the capability contract.

### Task R2: verified-shadow reliability matrix + stop rule
**Files:** Create `a6/reliability_matrix.py`. **Consumes valid R0b (real-condition) pairs only** — R0a fake-server pairs are excluded from the count. First 50 valid paired executions inside ONE uninterrupted A5-stable window. Flag the dangerous cell (both succeed, outcomes materially disagree); correlate disagreements with env changes. **Stop rule (pre-declared):** 0 trust/contract violations; STOP if candidate uniquely fails ≥3 where original succeeds, OR any unexplained material semantic disagreement. A material change mid-window voids the incomplete window (evidence restarts under new identity) but **already-observed negatives are not laundered**. A6 passes only if calibration passed under the same comparator identity AND the full stable window of 50 real-condition pairs completed AND the stop rule did not fire. **If 50 valid real-condition pairs cannot be safely acquired, A6 = INCOMPLETE** (not passed, not failed).

---

## Gate X — Phase 1 exit

Assemble the verdict strictly from program §9. **Four terminal states, not three** — a premise that could not be tested is not a premise that failed:
- **FEASIBLE** iff: A1 clears its declared decision (or an explicitly accepted narrowed scope); all 5 Gate-1 tests pass at their intended enforcement points; policy monotonicity holds; registry authenticity holds; duplicate-safety enforced explicitly; ≥1 A5-stable window completed; A6 completes on **real-condition pairs** without firing the stop rule; semantic equivalence remained independently required (not inferred from outcome agreement).
- **NARROW/REWORK** for narrowed premise or a correctable mechanism defect → rerun affected gates.
- **NOT FEASIBLE** for a Gate-0 premise failure → do not convert into another implementation task to protect sunk cost.
- **INCONCLUSIVE — PHASE 1 REMAINS OPEN** when required evidence was not sufficient to apply a premise gate. **No FEASIBLE / NOT-FEASIBLE claim may be made.** Triggers include:
  - `A1_NORMALIZABILITY = INSUFFICIENT_ORGANIC_EVIDENCE` (<30 in-family after 300) — MUST NOT be forced into NARROW/REWORK or NOT-FEASIBLE.
  - `A6 = INCOMPLETE` — 50 valid real-condition pairs could not be safely acquired (a fake-server pass does not substitute).
  The owner then explicitly chooses to extend collection, narrow/redeclare scope and rerun, or stop investing for practical reasons — none of which is a feasibility verdict.
- Seal `evidence/` with `SHA256SUMS`; record the interpretation by someone who did not design the program (program §11).
- **Explicitly stamp:** passing Phase 1 authorizes a Phase 2 value evaluation only — not deployment.

---

## Risks / tradeoffs / open questions

1. **A1 is human-labeled** — the rubric constrains but does not mechanize judgment (§11). Mitigation: second-rater + report as a band with raw counts, not a precise %.
2. **Only A1 is a true pre-build kill.** G/M/R need built machinery; they test *soundness*, not *build/no-build*. Don't oversell a Gate-1 pass as feasibility of the whole.
3. **Comparator may not exist yet, and verified-shadow pairing may not exist at all** (Task F0). A6 needs a legitimate *pair producer* (Task R0), not just the matrix consumer — original+candidate at the **same environmental state**, never replayed history. If the pairing harness must be built, A6 is heavier than the others — but it stays feasibility-scoped (reliability vs regeneration), value deferred.
4. **Second-rater independence** needs a genuinely separate labeler/peer, or the disagreement check is theatre.
5. **Open (Gate-S human decision):** whether to declare *any* additional family beyond the required `hmp_healthcheck`. Not an implementer default — each added family changes A1's denominator and must be declared with its assignment rule before sampling.
6. **Resolved (normative):** A1 runs against a **fresh, explicitly bounded, single-identity collection window** by default; historical `events.jsonl` is admissible only per-record where complete proposal-generation identity was captured contemporaneously (post-hoc stamping is not identity evidence).

---

## Handoff

Group A is gated on human sign-off (Gate S) and is the only pre-build kill — so the correct next action is **review this plan + fill/sign the §2 pre-declaration**, not code. Once Gate S is signed, execute via `subagent-driven-development`: fresh subagent per task, spec-compliance review then code-quality review, proceed only when both pass. Gate-1 falsifiers that expose real defects trigger patch+regression under NARROW/REWORK before continuing.
