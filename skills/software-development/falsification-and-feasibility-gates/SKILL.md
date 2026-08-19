---
name: falsification-and-feasibility-gates
description: Design/review fail-fast feasibility-gate programs.
version: 1.0.0
metadata:
  hermes:
    tags: [falsification, feasibility, review, decision-gates, evidence, fail-fast]
---

# Falsification & Feasibility Gates

Use this when the task is a **premise-level decision program**: pre-registered tests
whose job is to KILL a project/approach cheaply and early ("fail fast"), or a review of
someone else's such program. Distinct from `systematic-debugging` (root-causing a known
bug) and `plan` (how to build). This is about *whether to build at all*, and how to
structure evidence so the answer is trustworthy.

Applies to: falsification programs, feasibility gates, go/no-go criteria, spike/POC
acceptance bars, "is this premise strong enough to justify the machinery?" reviews.

## The 12 principles (each one is a real sign-off blocker if violated)

1. **Falsification says "not dead yet," never "alive."** Passing every gate = *failed to
   falsify* = still unproven. Never present a clean pass as proof the thing works.

2. **Separate feasibility ("can we do it") from value ("is it worth it").** Push value
   questions (latency, cost, SPOF, frequency, economics, savings) to a later phase. A value
   judgment wearing a feasibility gate's clothes is a scope regression — the single most
   common defect in these programs.

3. **Report-vs-gate discipline.** Opportunity-size / value-shaped metrics are *reported, not
   gated* in a feasibility phase. Gating completion on "someone accepts the size" with no
   declared threshold smuggles the value question back in. Gate only the technical property.

4. **Insufficient evidence is its own terminal state.** Below-threshold sampling ⇒
   INCONCLUSIVE / "phase remains open", NOT a pass/rework/fail verdict. "A premise that could
   not be tested is not a premise that failed." Any exit gate offering only pass/rework/fail
   is missing this fourth state.

5. **Evidence PRODUCER vs CONSUMER.** A thing that *judges* evidence (matrix, scorer, comparator)
   is worthless without a defined thing that *creates legitimate evidence*. Specify the producer
   — with all identity/isolation fields — before writing the consumer. This is the easiest hole
   to miss and often the biggest.

6. **Synthetic substrate qualifies MACHINERY, never supplies EVIDENCE.** Split the producer:
   a fake/deterministic fixture may prove the harness works; the *counted* feasibility evidence
   must come from real eligible conditions. N perfect runs on a fake can pass while real
   endpoint/auth/schema/transport assumptions are stale. Can't get real evidence safely ⇒
   INCOMPLETE, not "passed on the fake."

7. **Identity EVIDENCED, not STAMPED.** When a sample's validity depends on how it was generated
   (model/config/version), copying the current identity onto old records is not evidence. Admit
   historical data only where identity was captured contemporaneously; else open a fresh, bounded,
   single-identity window. Never pool across identities.

8. **"Same state" is unprovable for a live target — declare an equivalence CRITERION.** Same
   target; same observable deployment/schema/config identity; bounded temporal separation; no
   known intervening change. Criterion fails ⇒ discard the sample, don't fake simultaneity.

9. **Human judgment stays human.** Tooling for a human-labeled rubric VALIDATES and AGGREGATES
   labels; it MUST NOT algorithmically decide the labels, or it mechanizes the very judgment a
   second-rater check exists to test.

10. **Runtime-placement assertions need the REAL ordering — no "where possible."** An
    ordering-dependent property (e.g. rewrite-induced policy bypass) MUST run the real pipeline
    ordering or a proven-identical harness. Can't run it ⇒ the gate is NOT passed, not downgraded
    to a unit test.

11. **Anti-gaming spine:** pre-declare families/thresholds/exclusions BEFORE inspecting data;
    one-way materiality ratchet (upgrade non-material→material, never downgrade to rescue a
    window); invalidate on any second-rater disagreement that flips a numerator; two-sided
    calibration (positive AND negative controls) before the evidence window; a voided/restarted
    window does NOT launder already-observed negatives; start the change-log BEFORE the first
    commit that could join an evidence window (no retrospective classification).

12. **Declaration slots are scope, not defaults.** Providing N declaration slots does not require
    filling N. Requiring extra scope as an implementer default silently changes the denominator.
    Extra scope is a human sign-off decision.

## Review stance
When reviewing such a program, look specifically for where it lets the project LIVE when it
shouldn't — the comfortable test, the value question hidden in a feasibility gate, the missing
producer, the fake-substrate pass. Sign off with an explicit item-by-item checklist; block on
specific numbered issues with proposed replacement text; distinguish design-level from
implementation-plan-level issues and fix the latter without reopening the former.

## References
- `references/feasibility-falsification-program-and-plan-2026-08-19.md` — worked example: the
  Rebar Phase-1 feasibility falsification program + its implementation plan, and the specific
  edits each review round demanded (all 12 principles in action).
