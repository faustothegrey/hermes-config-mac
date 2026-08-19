# Rebar — Phase 1 Feasibility Falsification (2026-08-19)

Status: **feasibility program SIGNED OFF · implementation plan SIGNED OFF & FROZEN · next artifact = Gate S pre-declaration, then A1 evidence**

Related:
- [[Rebar Founding Intent and Tool-Use Contract]]
- [[Rebar Charter Alignment Checkpoint 2026-08-17]]
- [[Rebar Rebrand Decision 2026-07-27]]
- [[Rebar Phase 1 Feasibility Implementation Plan (Frozen 2026-08-19)]]

## What this is

Two documents were reviewed to sign-off over this session, both scoped to **"Can we even do it?"** feasibility only — the "**is it worth it?**" value question is deliberately deferred to a separate **Phase 2**.

1. **Feasibility Falsification Program** — vault: [[Rebar Feasibility Falsification Program (Signed Off 2026-08-19)]]; ephemeral source `~/.hermes/cache/documents/doc_1e3f311ae44f_REBAR_FEASIBILITY_FALSIFICATION_PROGRAM.md` (signed off).
2. **Phase 1 Implementation Plan** — frozen copy in vault; source at `~/.hermes/plans/2026-08-19_rebar-phase1-feasibility-implementation.md`.

Predecessor (broader, Phase 1+2): `REBAR_FALSIFICATION_PROGRAM_REV4.md` (same cache dir).

## Core principle established

Falsification only ever says **"not dead yet," never "alive."** Passing every gate = *failed to falsify*, not proof it works. And the feasibility program is deliberately narrow: it tests whether the mechanism can be made **trustworthy** (recognizable substrate + safe rejection + convergent evidence + reliable-vs-regeneration), **not** whether it is worth operating.

Phase boundary:
- **Phase 1** — Can the mechanism be made trustworthy?
- **Phase 2** — Is the resulting trustworthy mechanism worth operating? (hot-path latency, SPOF cost, reuse frequency, Path A vs B economics — all deferred.)

## The five Phase-1 falsifiers

- **A1** — is the real substrate present? (organic proposals expose recoverable semantics at a useful rate.) **The only cheap pre-build kill.** Human-labeled with a mechanical rubric + second-rater.
- **Gate 1** — can the mechanism reject what it must reject? Five falsifiers (timeout, effect, duplicate-safety, registry authenticity, policy monotonicity) against a deterministic fake HMP server.
- **Structural DEMO** — outcome agreement cannot prove semantic equivalence (a *demonstration*, not a falsifier).
- **A5** — can the evidence loop converge? (one stable window where normalizer × capability × comparator are materially unchanged.)
- **A6** — can the admitted capability behave more reliably than regeneration? Comparator calibration + verified-shadow reliability matrix + stop rule.

## Key design decisions won during review

These are the load-bearing corrections Fausto extracted across the review rounds — they define what "correct" means for this work:

1. **`effective_reuse_surface` is report-only, NOT a feasibility gate** (§3.5.1). It's opportunity-size = coverage × normalizability — a *value* question. Gating A1 on it re-imports Phase 2. A low surface MUST NOT by itself fail A1.
2. **Insufficient evidence ≠ failure** (§3.5.2 + Gate X). `<30` in-family after 300 proposals → `A1_NORMALIZABILITY = INSUFFICIENT_ORGANIC_EVIDENCE`. Never forced into NARROW/REWORK or NOT-FEASIBLE.
3. **Gate X has FOUR terminal states**, not three: FEASIBLE / NARROW-REWORK / NOT-FEASIBLE / **INCONCLUSIVE — PHASE 1 REMAINS OPEN**. *A premise that could not be tested is not a premise that failed.*
4. **A1 proposal-generation identity must be pinned & contemporaneously evidenced** — post-hoc stamping the active identity onto old records is NOT identity evidence. Default: fresh single-identity window. A mid-window identity change **voids the run** (`A1RunInvalid`), not skip-and-continue (preserves the consecutive-organic property).
5. **The rubric stays human.** `rubric_aggregate.py` validates & aggregates human property labels; it must NOT algorithmically decide recoverability (that's the judgment the second-rater exists to check).
6. **G6 policy monotonicity MUST exercise the real pinned policy/guardrail ordering** (original → Rebar rewrite → guardrail → dispatch). A unit test of compatibility logic cannot falsify a rewrite-induced bypass. If real ordering can't be exercised, G6 is NOT passed — not downgraded.
7. **A6 needs a pair PRODUCER, not just a matrix consumer** — the biggest hole caught. Split:
   - **R0a** — qualify the machinery (fake HMP permitted); its pairs MUST NOT count.
   - **R0b** — acquire the 50 feasibility pairs under **real eligible execution conditions** (natural original + exact admitted capability, same Rebar decision). Synthetic pairs never count. If safe real pairing is impossible → **A6 = INCOMPLETE**, not "passed on the fake server."
8. **Environmental-equivalence criterion is declared & frozen (versioned hash) BEFORE the 50-pair window**, applied uniformly, sealed in evidence. No deciding after a disagreement that "that pair wasn't equivalent." Same-target / same observable deployment-schema-config identity / bounded temporal separation / no known intervening state change → else discard the pair.
9. **Gate R-A candidate admission blocks R0b.** "Already exists / active / previously validated" is NOT admission. `hmp-healthcheck@1.0.0` must have: approved admission record, exact contract + implementation versions, verified artifact_hash, authenticated registry binding (→G5), approved effect_class, `duplicate_execution_safe=true`, duplicate constraints (→G4). Not established ⇒ R0b must not start. (Minimum architecture-mandated admission, not all of Spec A.)
10. **A5 is not a precondition R waits for** — A6's evidence window IS the window through which A5 convergence is demonstrated. The comparator is inside the identity triple, so it can't be frozen before R1 builds it. M1 (material-change logging) starts BEFORE the first relevant normalizer/capability/comparator commit — no retrospective classification.

## Frozen sequencing

```
Gate S  — §2 pre-declaration filled + human-signed   [BLOCKS group A]
Group A — A1 (only true pre-build kill; runs FIRST)
Group G — Gate 1 fake server + 5 falsifiers + DEMO
Group M — A5 logging STARTS before any relevant commit
Group R-prep — F0 discover · R0a qualify producer · R1 build/calibrate comparator
FREEZE IDENTITIES — normalizer · capability · comparator
OPEN A5/A6 WINDOW
Group R-evidence — Gate R-A admission · R0b real pairs · R2 first 50
M2 — confirm A6 window was uninterrupted A5-stable window
Gate X  — 4-state verdict, seal evidence + SHA256SUMS
```

## Artifacts on disk

- Frozen plan (source): `~/.hermes/plans/2026-08-19_rebar-phase1-feasibility-implementation.md`
- Gate S skeleton: `~/.hermes/skills/hermes/capability-reuse/analysis/feasibility-phase1/predeclaration/PREDECLARATION.md`
- All Phase-1 harnesses will live under `~/.hermes/skills/hermes/capability-reuse/analysis/feasibility-phase1/` (isolated from plugin runtime + existing evidence bundles).
- Feasibility program: `~/.hermes/cache/documents/doc_1e3f311ae44f_REBAR_FEASIBILITY_FALSIFICATION_PROGRAM.md`

## Open human decisions (Gate S)

- **§2.1** pin proposal-generation identity + collection mode (recommend FRESH single-identity window).
- **§2.2** whether any family joins the required `hmp_healthcheck` (optional; each changes the A1 denominator).
- **§2.6** name a second labeler independent of the program's design.

## Governance reminder (from charter checkpoint)

peer128 = implementation owner · peer141 = independent testing/evidence review **when available** (not always reachable — if unavailable, do not block; note it skipped and proceed to the `loop-coding-guidelines` external verdict) · peer70 = coordinator/phase authority. Formal Phase 1B + fleet rollout remain unauthorized. Passing Phase 1 authorizes a Phase 2 value evaluation only — **not deployment.**
