# Worked example: Rebar Phase-1 feasibility falsification (2026-08-19)

Concrete instance of the 12 principles, from authoring + reviewing the Rebar feasibility
falsification program and its implementation plan. Rebar = the capability-reuse project
(user-owned skill `capability-reuse`): check the actual proposed generic tool operation for a
compatible admitted harness before execution, prefer it when safe, surface the decision.

## Artifacts
- `REBAR_FEASIBILITY_FALSIFICATION_PROGRAM.md` — Phase 1 "Can we even do it?" (feasibility only).
- `REBAR_FALSIFICATION_PROGRAM_REV4.md` — earlier fuller version (both phases).
- Implementation plan: `~/.hermes/plans/2026-08-19_rebar-phase1-feasibility-implementation.md`
  (maps 1:1 to the program; execute via subagent-driven-development; Group A blocked until the §2
  pre-declaration is human-signed).

## The five falsifiers (structure worth reusing)
- **A1** — is the real substrate present? Sample organic proposals, mechanically score
  normalizability against a rubric, second-rater check, decision bands. THE ONLY cheap pre-build
  kill; everything else needs built machinery.
- **Gate 1** — does the mechanism reject what it must? Deterministic fake server + 5 falsifiers
  (timeout semantics, effect semantics, duplicate-safety, registry-binding authenticity, policy
  monotonicity), each asserting the *specific* enforcement point.
- **DEMO** — outcome agreement can't prove semantic equivalence (ready-vs-health coincidental match).
- **A5** — can the evidence loop converge? Material-change log + one stable window.
- **A6** — is the admitted capability more reliable than regeneration? Comparator calibration +
  verified-shadow reliability matrix + pre-declared stop rule.

## How each principle showed up as a concrete blocker
- **P2/P3** (value vs feasibility; report-vs-gate): `effective_reuse_surface = coverage ×
  normalizability` was first written as a *gate* ("A1 INCOMPLETE unless surface accepted") — that
  reintroduced the deferred value question. Fixed to **report-only**; bands apply to normalizability
  only.
- **P4** (inconclusive state): `<30` in-family after 300 ⇒ `INSUFFICIENT_ORGANIC_EVIDENCE`. The
  three-verdict exit (FEASIBLE/NARROW/NOT-FEASIBLE) had no home for it ⇒ added a 4th terminal state
  `INCONCLUSIVE — PHASE 1 REMAINS OPEN`.
- **P5/P6** (producer vs consumer; synthetic ≠ evidence): the plan had a reliability *matrix* (R2,
  consumer) but no *pair producer*. Added R0, then split R0a (fake HMP qualifies machinery, pairs
  NOT counted) vs R0b (real eligible conditions supply the 50 counted pairs; can't do safely ⇒
  A6=INCOMPLETE).
- **P7** (identity evidenced not stamped): first plan "stamp each historical record with the active
  proposal-generation identity" — invalid since models were swapped 3× in one session. Fixed to
  contemporaneous-identity eligibility + fresh single-identity window default; no pooling.
- **P8** (equivalence criterion): "same environmental state" softened to a declared criterion (same
  target / observable deploy-schema-config identity / bounded temporal separation / no known change;
  else discard the pair).
- **P9** (human judgment): `rubric_score.py` → `rubric_aggregate.py`; validates/aggregates human
  labels, never assigns property states.
- **P10** (real ordering): G6 policy monotonicity changed from "real middleware where possible" to
  MUST exercise real pinned policy ordering, else NOT passed.
- **P11** (change-log timing): A5 material-change log MUST start before the first
  normalizer/capability/comparator commit — no retrospective classification.
- **P12** (slots ≠ defaults): Gate S dropped the mandatory "+2 families"; `hmp_healthcheck` is the
  only required family, more are a human sign-off decision that changes A1's denominator.

## Grounding lesson
The plan was much stronger after checking ACTUAL code state (`plugin/tool_reuse.py`, retriever,
dispatcher, conformance suite already existed) rather than planning from memory — it reframed the
work from "greenfield build" to "wire falsifiers around existing machinery + run A1."

## Working relationship (Fausto)
Reviews iteratively and precisely: item-by-item checklist sign-off, blocks on specific numbered
issues with proposed replacement text, distinguishes design-level from implementation-plan-level
(fix the latter without reopening the former). States "I would not sign off yet" then enumerates
exact blockers. Apply the proposed text closely; deliver the edited doc as a MEDIA path each round.
