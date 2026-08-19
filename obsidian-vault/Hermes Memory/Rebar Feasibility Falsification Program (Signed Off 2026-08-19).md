# Rebar — Feasibility Falsification Program

> **Vault copy — SIGNED OFF 2026-08-19** (includes the §3.5.1 report-only + §3.5.2 insufficient-evidence amendments accepted this session). Source of record was ephemeral: `~/.hermes/cache/documents/doc_1e3f311ae44f_REBAR_FEASIBILITY_FALSIFICATION_PROGRAM.md`.
>
> Related: [[Rebar Phase 1 Feasibility Falsification 2026-08-19]] · [[Rebar Phase 1 Feasibility Implementation Plan (Frozen 2026-08-19)]] · [[Rebar Charter Alignment Checkpoint 2026-08-17]] · [[Rebar Founding Intent and Tool-Use Contract]]

**Status:** Phase 1 execution candidate  
**Question:** *Can we even do it?*  
**Purpose:** Test whether Rebar can safely and reproducibly recognize naturally occurring generic operations and substitute an admitted capability without changing requested semantics, weakening policy, or relying on evidence that cannot converge.

This document intentionally does **not** answer whether Rebar is worth deploying.

Passing Phase 1 authorizes a separate value evaluation. It does not authorize production rollout.

---

## 1. Phase 1 decision

Phase 1 asks one question:

> **Can Rebar take naturally occurring model-generated generic operations, recover enough execution-significant semantics to reason about equivalence, and substitute an admitted capability without changing the requested operation or weakening policy?**

Possible outcomes:

```text
FEASIBLE
    The core mechanism survives the falsification gates.
    Proceed to a separate Phase 2 value evaluation.

NARROW / REWORK
    The mechanism works only for a narrower family, model/runtime
    configuration, or capability shape.
    Narrow scope or fix the mechanism, then rerun the affected gate.

NOT FEASIBLE
    A premise-level gate fails in a way that undermines the core approach.
    Do not continue toward live substitution without changing the design.
```

A Phase 1 pass is **not** evidence that Rebar is economically worthwhile.

---

## 2. Pre-declaration

The following must be completed and signed **before A1 sampling begins**.

### 2.1 Proposal-generation identity

A1 measures a property of proposals produced by a specific model/runtime context, not an abstract property of Hermes.

Declare:

```text
model_id:
model_version_or_snapshot:

runtime_or_gateway_version:

system_prompt_identity_or_hash:
tool_surface_revision_or_hash:

relevant_generation_configuration:
```

The A1 sampling window MUST use one proposal-generation identity.

A material change to any proposal-shaping component invalidates the active A1 run.

Data from different proposal-generation identities MUST NOT be pooled when applying A1 thresholds.

A new proposal-generation identity requires a new declared A1 run.

### 2.2 Target operation families

Declare the target families before sampling.

```text
1. hmp_healthcheck
2. ______________________________
3. ______________________________
```

For each family, declare the **operational assignment rule**.

Family assignment must be based on the requested operation, not on whether a proposed normalizer happens to succeed.

```text
Family 1 assignment rule:
____________________________________________________________

Family 2 assignment rule:
____________________________________________________________

Family 3 assignment rule:
____________________________________________________________
```

### 2.3 Recoverability defaults

For each family, declare any execution-significant property that may be recovered from a known runtime default rather than explicit proposal syntax.

A default may count as recoverable only if declared here before sampling.

```text
Family:
Property:
Declared runtime default:
Evidence/source of default:
```

Do not invent defaults during labeling to rescue a proposal.

### 2.4 Not-applicable properties

If an execution-significant property is genuinely not applicable to a family, declare it before sampling.

```text
Family:
Property:
Reason NOT_APPLICABLE:
```

`NOT_APPLICABLE` MUST NOT be assigned post hoc to improve the normalizability score.

### 2.5 Sampling exclusions

Predeclare known Rebar-development sessions or other traffic that would distort the organic workload sample.

```text
Excluded sessions / windows:
____________________________________________________________
```

Excluded observations must not be selectively replaced based on their labels.

### 2.6 Sign-off

```text
Declared by: ______________________

Date: _____________________________

Sampling begins only after this block is complete.
```

---

## 3. A1 — Is the real substrate present?

### Assumption

Naturally occurring model-generated generic operations expose enough explicit, recoverable semantics to map into stable operation families at a useful rate.

This is the only Phase 1 test that can falsify the premise before substantial additional Rebar engineering.

It therefore runs first.

### 3.1 Sampling

Collect consecutive organic generic-tool proposals through the normal Hermes gateway.

Rules:

- Do not generate proposals for the experiment.
- Do not prompt the model toward parseable output.
- Do not alter the declared proposal-generation identity during the run.
- Do not select only HMP-looking requests.
- Apply the predeclared exclusions.
- Preserve collection order.

Initial checkpoint:

```text
100 generic proposals
```

Sample-sufficiency limits:

```text
minimum in-family observations = 30
maximum total generic proposals = 300
```

At 100 proposals:

- coverage is an **interim** result;
- if at least 30 in-family proposals exist, the run may close;
- otherwise continue consecutive eligible sampling until:
  - at least 30 in-family proposals exist, or
  - 300 total proposals are reached.

Final coverage is calculated across the entire completed sampling window.

Record the calendar span of the window.

If 300 consecutive organic proposals still produce fewer than 30 observations from the predeclared target families, that is itself a major coverage finding.

### 3.2 Mechanical recoverability rubric

A proposal is `fully_normalizable` only if every execution-significant property that applies to the family is recoverable without guessing.

Score these properties individually:

```text
target
mutation / effect
payload meaning
timeout behavior
retry behavior
permissions
authentication
idempotency
side effects
output expectations
```

Allowed property states:

```text
R_EXPLICIT
    Explicitly recoverable from the proposed operation.

R_DEFAULT
    Recoverable from a runtime default declared in Section 2
    before sampling.

NOT_APPLICABLE
    Declared non-applicable to this family in Section 2
    before sampling.

NOT_RECOVERABLE
    Safe recovery would require guessing, inference not justified
    by the proposal/runtime contract, or information not present.
```

Rules:

- `R_DEFAULT` may only use a predeclared default.
- `NOT_APPLICABLE` may only use a predeclared family rule.
- Neither may be assigned post hoc to improve results.
- Any applicable property scored `NOT_RECOVERABLE` means the proposal is **not** `fully_normalizable`.

Headline proposal labels:

```text
fully_normalizable
    Every applicable execution-significant property is
    R_EXPLICIT, R_DEFAULT, or predeclared NOT_APPLICABLE.

partially_normalizable
    At least one relevant semantic property is recoverable,
    but at least one applicable property is NOT_RECOVERABLE.

not_normalizable
    The proposal cannot be mapped safely enough to the family
    to support substitution reasoning.

not_relevant_to_reuse
    Outside the predeclared target families.
```

The per-property results must be retained so A1 reports **why** normalizability failed, not only how often.

### 3.3 Second-rater check

A1 remains human-labeled before the normalizer exists, so rubric reliability must itself be tested.

A second labeler independently scores at least 20% of in-family proposals.

Selection rule:

```text
every 5th in-family proposal in collection order
```

The second labeler should not see the first labeler's scores before completing their own classification.

Report:

```text
per-property disagreement rate
headline-label disagreement rate
```

Disagreements are adjudicated against the predeclared family rules, defaults, and `NOT_APPLICABLE` declarations.

An unresolved disagreement that changes whether a proposal belongs in the `fully_normalizable` numerator invalidates the A1 run.

Do not negotiate such a disagreement away after seeing the resulting percentage.

### 3.4 Metrics

Report all three:

```text
target_family_coverage =
    proposals in predeclared target families
    ----------------------------------------
    all eligible generic proposals


normalizability =
    fully_normalizable in-family proposals
    ---------------------------------------
    all in-family proposals


effective_reuse_surface =
    target_family_coverage × normalizability
```

Also report:

```text
per-property NOT_RECOVERABLE rates
second-rater disagreement rates
sampling-window calendar span
proposal-generation identity
raw numerator / denominator counts
```

Treat the result as a decision band, not as a precision estimate.

### 3.5 A1 decision bands

Apply these bands only when at least 30 in-family observations exist:

```text
normalizability ≥ 80%
    CONTINUE

normalizability 60–79%
    INVESTIGATE BEFORE FURTHER INVESTMENT

normalizability < 60%
    STOP OR FUNDAMENTALLY NARROW THE TARGET FAMILIES
```

A sub-60% result does not prove Path B is mathematically incapable of reuse.

It means Path B failed the predeclared viability bar as the primary reuse mechanism for the declared families under the tested proposal-generation identity.

Possible responses include:

```text
narrow the target families
change the normalization approach
evaluate whether typed Path A should become primary
stop the current approach
```

Coverage has no universal kill threshold in Phase 1.

A low-coverage family may still matter disproportionately, but the decision must be made explicitly from the observed number rather than assumed.

### 3.5.1 Effective reuse surface — report, do not gate feasibility

Report:

```text
effective_reuse_surface =
    target_family_coverage × normalizability
```

This metric describes the observed opportunity surface under the
declared proposal-generation identity.

It MUST be recorded with the A1 result because it is important input
to any later value evaluation.

However, Phase 1 does not define a minimum acceptable
effective_reuse_surface.

A low effective reuse surface MUST NOT by itself cause A1 to fail
technical feasibility.

Its interpretation is deferred to Phase 2, where the value of the
covered operations can be considered alongside frequency, latency,
reliability benefit, operational cost, and maintenance burden.

### 3.5.2 Insufficient organic evidence

If, after the maximum 300 consecutive organic proposals, fewer than
30 in-family observations exist, the A1 decision bands MUST NOT be
applied to the undersized denominator.

Do not manufacture a 60/80 decision from insufficient data. Report:

```text
A1_NORMALIZABILITY = INSUFFICIENT_ORGANIC_EVIDENCE

with:
    target_family_coverage
    raw in-family count
    sampling-window calendar span
```

This is a coverage/evidence finding, not a feasibility failure. It
does not declare Rebar technically impossible. The project owner then
decides whether to narrow scope, extend sampling, or commission a
separately designed family-specific feasibility test.

---

## 4. Gate 1 — Can the mechanism reject what it must reject?

Gate 1 failures are implementation defects.

Use one small deterministic fake HMP server.

Suggested endpoints:

```text
GET  /health
POST /health
GET  /slow-health
GET  /ready
GET  /messages/next
POST /admin/state
```

The point of each test is to assert the **specific enforcement point**.

A test does not pass merely because Rebar rejected the request for some unrelated reason.

### 4.1 Timeout semantics

Fixture:

```text
GET /slow-health
    deliberate 2-second delay
```

Compare:

```text
original:
    curl --max-time 0.2 .../slow-health

candidate:
    hmp_healthcheck(timeout=5)
```

Expected:

```text
candidate retrieved
whole_request_covered = false
reason = timeout_semantics_mismatch
substitution = none
```

If Rebar substitutes, it is matching intent labels rather than full operation semantics.

### 4.2 Effect semantics

The fake server deliberately makes these return similar-looking results:

```text
GET  /health
POST /health
```

but `POST /health` mutates state.

Input:

```text
curl -X POST .../health -d '{}'
```

Expected:

```text
effect_mismatch
no substitution
```

The test must assert that effect compatibility caused the rejection.

### 4.3 Duplicate-safety enforcement

This test requires its own **test-only admitted capability** so the request reaches the duplicate-safety gate.

Test capability:

```text
test_next_message()

operation semantics:
    matches GET /messages/next

effect_class:
    read_only

duplicate_execution_safe:
    false
```

Fake endpoint:

```text
GET /messages/next
    returns AND consumes the next queued item
```

Expected:

```text
candidate semantically compatible
effect compatible
whole request covered

VERIFIED_SHADOW refused specifically because:
    duplicate_execution_safe = false
```

A rejection for `no_capability`, family mismatch, or another earlier reason does **not** pass this test.

### 4.4 Registry-binding authenticity

Test the binding, not only the artifact hash.

Start with:

```text
authenticated registry:
    hmp_healthcheck → artifact hash A
```

Tamper the registry snapshot:

```text
hmp_healthcheck → artifact hash B
```

without legitimate re-authentication.

Expected:

```text
registry_authenticity_failure
no capability dispatch
```

If Rebar verifies artifact B against attacker-supplied hash B, artifact hashing has not established trust.

Artifact-file tampering should remain a secondary integrity test.

### 4.5 Policy monotonicity

Policy:

```text
peer-blocked may not be contacted
```

Original proposal:

```text
curl .../peer-blocked/health
```

Without substitution:

```text
blocked
```

Rebar candidate:

```text
hmp_healthcheck(peer="peer-blocked")
```

Required invariant:

```text
blocked(original)
MUST NOT become
allowed(rewritten execution)
```

unless an explicit policy rule authorizes that transition.

The test must prove the policy layer sees enough of:

```text
original proposed operation
Rebar decision
resulting execution plan
```

to preserve or strengthen the original policy outcome.

A rewrite that changes the tool shape and thereby bypasses the original policy is a Phase 1 failure.

---

## 5. Structural demonstration — outcome agreement cannot prove equivalence

This is a demonstration, not a standalone falsifier before Spec G exists.

Fake endpoints:

```text
normal state:
    /ready  = true
    /health = true

maintenance state:
    /ready  = false
    /health = true
```

Deliberately let the normalizer propose `hmp_healthcheck` for a readiness request.

Run verified shadow only in the normal state.

Observed result:

```text
perfect output agreement
```

even though the operations are not semantically equivalent.

Conclusion:

> **No quantity of matching verified-shadow outputs can establish semantic equivalence by itself.**

Semantic equivalence review remains mandatory.

Outcome agreement is supporting evidence only.

Once Spec G exists, this demonstration gains an executable assertion:

```text
outcome agreement alone
MUST NOT satisfy the live-enablement gate
```

---

## 6. A5 — Can the evidence loop converge?

### Assumption

Enough evidence can accumulate before one of the components defining equivalence materially changes again.

The evidence identity is:

```text
normalizer
×
capability
×
comparator
```

### 6.1 Material-change log

For every Phase 0 change:

```text
date
component
    normalizer | capability | comparator

material_change
    yes | no

rationale
```

The author classifies materiality at commit time.

Materiality criteria must be declared before an evidence window opens.

A change is material if it can alter:

```text
normalizer:
    normalized operation or compatibility semantics

capability:
    applicability, effects, execution, or result semantics

comparator:
    equivalence classification
```

Review may later upgrade:

```text
non-material → material
```

Review MUST NOT retroactively downgrade:

```text
material → non-material
```

to rescue an active evidence window.

### 6.2 Convergence gate

Before live enablement, demonstrate at least one complete evidence window during which:

```text
normalizer
capability contract and implementation
comparator
```

remain materially unchanged.

If such a window cannot be achieved, the validation loop has not converged.

Permitted responses:

```text
freeze development during the evidence window
narrow the operation family
simplify the implementation
explicitly amend the later evidence policy
```

Redefining materiality until the window passes is not permitted.

---

## 7. A6 — Can the admitted capability behave more reliably than regeneration?

### Assumption

A reviewed and pinned capability can be trusted enough to replace regenerated generic execution.

This is kept in Phase 1 as a **feasibility/reliability** question.

Broader economic value remains deferred.

### 7.1 Prerequisite — calibrated comparator

Before the A6 window, calibrate the exact comparator identity that will score it.

Record:

```text
comparator_version
comparator_artifact_hash
comparison_rules_version
```

Calibration is two-sided.

#### Positive controls — known equivalent

Derive from contract-declared equivalence rules:

```text
declared volatile field differs
request_id differs
timestamp differs where declared volatile
allowed collection ordering differs
numeric difference inside declared tolerance
```

#### Negative controls — known non-equivalent

Derive from contract-declared stable semantics:

```text
healthy flips
required result field disappears
relevant status changes
semantic value changes
numeric difference exceeds tolerance
```

Calibration passes only if both control classes are correctly classified.

Do not create calibration controls that contradict the capability contract.

### 7.2 Verified-shadow reliability matrix

For each valid paired execution:

```text
                           CANDIDATE
                     succeeds          fails

ORIGINAL succeeds    outcomes agree    candidate-only failure
                     outcomes disagree

ORIGINAL fails       candidate rescues both fail
```

The dangerous state is:

```text
original succeeds
candidate succeeds
outcomes materially disagree
```

Technical success is not semantic correctness.

Correlate disagreements with known environment changes where available:

```text
environment_change_id
target_version
endpoint/schema revision
deployment timestamp
```

### 7.3 A6 evidence window

The A6 run must occur inside one uninterrupted A5-stable window.

Target:

```text
first 50 valid verified-shadow pairs
```

A material change to the:

```text
normalizer
capability
comparator
```

before the window completes voids the incomplete window and evidence accumulation restarts under the new identity.

A restart MUST NOT erase an already-observed negative finding.

For example:

```text
candidate-only failure observed
→ comparator changes
→ new window starts

The earlier candidate-only failure remains a finding.
It is not laundered by the restart.
```

### 7.4 Stop rule

Before the window opens, declare:

```text
0 trust/contract violations

STOP live-enablement work if:
    candidate uniquely fails ≥ 3 times
    where the original succeeds

OR

    any unexplained material semantic disagreement appears
```

Environment-correlated disagreements must be investigated immediately.

They MUST NOT be counted as harmless successful pairs.

A6 passes only if:

```text
comparator calibration passed
under the same comparator identity

AND

the full stable evidence window completed

AND

the stop rule did not fire
```

---

## 8. Phase 1 sequencing

```text
NOW
────────────────────────────────────────
A1
    fill and sign pre-declarations
    pin proposal-generation identity
    collect organic proposals
    measure coverage and recoverability

Do not let A1 slip.


ALONGSIDE MINIMUM NORMALIZER WORK
────────────────────────────────────────
Gate 1
    timeout semantics
    effect semantics
    duplicate-safety enforcement
    registry-binding authenticity
    policy monotonicity

Structural demonstration
    ready-vs-health coincidental agreement


THROUGHOUT PHASE 0
────────────────────────────────────────
A5
    material-change log
    prove one stable evidence window


BEFORE A6
────────────────────────────────────────
comparator calibration


DURING VERIFIED SHADOW
────────────────────────────────────────
A6
    paired reliability evidence
    inside one uninterrupted A5-stable window
```

---

## 9. Phase 1 exit

### FEASIBLE

Phase 1 may be judged feasible only if:

```text
A1 clears the declared viability decision
or produces an explicitly accepted narrowed scope

Gate 1 mechanism tests pass at their intended enforcement points

policy monotonicity holds

registry authenticity holds

duplicate-safety is enforced explicitly

one A5-stable evidence window can be completed

A6 completes without firing its stop rule

semantic equivalence remains independently required
rather than inferred from outcome agreement
```

A feasibility pass means:

> **Rebar has survived the tests required to justify evaluating it further.**

It does not mean:

```text
production-ready
worth the latency
worth the operational dependency
worth the maintenance cost
fleet-ready
economically positive
```

### NARROW / REWORK

Use when the premise survives only for a smaller family or configuration, or a mechanism defect can plausibly be corrected without changing the core design.

Rerun every affected falsification gate after the change.

### NOT FEASIBLE

Use when a Gate 0 result undermines the core approach, for example:

```text
real proposals cannot be normalized at the declared viability level

the evidence loop cannot remain stable long enough to complete

the admitted capability cannot demonstrate trustworthy replacement behavior
```

Do not convert a premise failure into another implementation task merely because work has already been invested.

---

## 10. Explicitly deferred — Phase 2 value evaluation

Phase 1 does **not** ask whether Rebar is worth operating.

Only after Phase 1 passes may a separate Phase 2 evaluate questions such as:

```text
hot-path latency
audit / registry availability cost
SPOF consequences
operational complexity
token savings
retry reduction
round-trip reduction
frequency of actual reuse
maintenance cost
net productivity
Path A versus Path B economics
```

No Phase 2 threshold is defined here.

> **Passing Phase 1 authorizes evaluation, not deployment.**

---

## 11. Known limits

A1 remains a human-labeled pre-build test.

The recoverability rubric constrains that judgment but does not mechanize it completely.

The second-rater rule exists to expose rubric instability rather than conceal it.

Therefore:

- report A1 as a decision band with raw counts;
- report disagreement rates;
- do not treat the resulting percentage as precise;
- where practical, have the final A1 interpretation performed by someone who did not participate in designing this program.

Gate 1 fixtures test failure modes we know how to imagine.

They cannot prove the absence of unknown failure modes.

A5 and A6 cannot inform the earliest build/no-build decision because they require infrastructure that does not yet exist.

That is why A1 runs first.

---

## 12. Sign-off

Signing this document does **not** assert that Rebar is feasible.

It asserts agreement on how Phase 1 will attempt to falsify feasibility.

```text
[ ] F2   proposal-generation identity declared
[ ] F2   target families and assignment rules declared
[ ] F2   defaults / NOT_APPLICABLE cases declared
[ ] F2   exclusions declared

[ ] A1   sampling and recoverability rubric accepted
[ ] A1   second-rater rule accepted
[ ] A1   viability bands accepted
[ ] A1   effective_reuse_surface reporting rule accepted

[ ] G1   timeout-semantics falsifier accepted
[ ] G1   effect-semantics falsifier accepted
[ ] G1   duplicate-safety falsifier accepted
[ ] G1   registry-authenticity falsifier accepted
[ ] G1   policy-monotonicity falsifier accepted

[ ] DEMO outcome agreement cannot establish equivalence

[ ] A5   stability-window gate accepted
[ ] A6   comparator calibration accepted
[ ] A6   stable-window reliability test accepted
[ ] A6   stop rule accepted

[ ] Phase 2 value questions explicitly deferred
```

```text
Signed: ______________________________

Date: ________________________________

Dissents / amendments:
____________________________________________________________
____________________________________________________________
```
