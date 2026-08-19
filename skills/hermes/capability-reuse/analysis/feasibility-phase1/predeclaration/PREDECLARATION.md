# Rebar Phase 1 — A1 Pre-Declaration (Gate S)

> **BLOCKING.** `collect_proposals.py` MUST refuse to run until every `____` below is filled
> and the sign-off block carries a name + date. This block is completed and signed
> **before any A1 data is inspected** (program §2). Post-hoc edits after data inspection
> invalidate the run.

---

## 2.1 Proposal-generation identity (single identity for the whole A1 window)

```
model_id:                        ____
model_version_or_snapshot:       ____
runtime_or_gateway_version:      ____
system_prompt_identity_or_hash:  ____
tool_surface_revision_or_hash:   ____
relevant_generation_config:      ____   (temperature, tool-choice mode, decoding params that shape proposals)
```

**Identity-evidence source** (how each field above is established from *contemporaneous* metadata — NOT stamped after the fact):
```
____
```

- A material change to any proposal-shaping component **voids the active A1 run** (fresh-window mode: `A1RunInvalid`).
- Data from different proposal-generation identities MUST NOT be pooled.

Collection mode (pick one):
```
[ ] FRESH single-identity window  (default/recommended)
[ ] HISTORICAL events.jsonl        (admissible ONLY per-record where complete identity was captured at generation time)
```

---

## 2.2 Target operation families

`hmp_healthcheck` is the required initial family. Additional families are OPTIONAL and are a human
decision here — each one changes A1's denominator.

```
Family 1: hmp_healthcheck
    operational assignment rule (based on requested operation, NOT normalizer success):
    ____

Family 2 (optional): ____
    operational assignment rule: ____

Family 3 (optional): ____
    operational assignment rule: ____
```

---

## 2.3 Recoverability defaults (per family)

A property may be labeled `R_DEFAULT` only if its default is declared here first, with source.

```
Family:            ____
Property:          ____
Declared default:  ____
Evidence/source:   ____
```
*(repeat as needed)*

---

## 2.4 NOT_APPLICABLE properties (per family)

`NOT_APPLICABLE` may only be assigned from a rule declared here before sampling.

```
Family:              ____
Property:            ____
Reason NOT_APPLICABLE: ____
```
*(repeat as needed)*

---

## 2.5 Sampling exclusions

Rebar-development sessions / windows / traffic to exclude (must not be selectively replaced by label):
```
____
```

---

## 2.6 Second-rater rule

```
Base selection: every 5th in-family proposal in collection order.
Floor:          if count < ceil(0.20 × N), add deterministic tail items (collection order) to reach ceil(0.20 × N).
Blinding:       second labeler does not see first labeler's scores before completing their own.
Invalidation:   an unresolved disagreement that flips fully_normalizable numerator membership voids the run.
Second labeler (independent of program design):  ____
```

---

## Sign-off

```
Declared by: ____                     Date: ____
Reviewer (optional, independent):  ____   Date: ____

Sampling begins only after this block is complete and signed.
```
