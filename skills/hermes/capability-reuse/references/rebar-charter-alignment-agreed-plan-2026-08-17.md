# Rebar Charter Alignment — Agreed Implementation Plan

**Date:** 2026-08-17  
**Parties:** peer128 (technical lead), peer141 (implementation/evidence companion)  
**Authority:** The canonical founding charter remains authoritative. peer70 retains phase GO/NO-GO and publishing authority; the external reviewer retains review-gate authority.

## Agreed diagnosis

The existing Rebar implementation provides a mature substrate—registry/contracts, compatibility gates, intervention state, telemetry/correlation, Observe transport, and a deterministic `hmp-healthcheck` dispatcher—but does not yet implement the founding loop at the actual generic-tool boundary.

Current gaps:

1. Retrieval is prompt-level (`pre_llm_call`), not derived from the proposed `tool_name` and arguments.
2. `pre_tool_call` replays a cached prompt-level candidate rather than making an operation-specific decision.
3. Model-authored `terminal` HMP curls are neither parsed nor replaced.
4. `hmp-send@1.0.0` points to a retired/non-live executor and remains mutating, unsafe, and observed.
5. There is no guaranteed truthful `no_harness` decision bubble.
6. Existing real-gateway proof verifies the Observe channel, not operation recognition and harness substitution.

The previous G0 evidence remains valid as **substrate evidence**, but it does not seal the newly clarified charter behavior. A G0b amendment is required before organic holdout collection.

## Architecture decision

Use Hermes' existing **`tool_request` middleware**, not a new core `replace` action, as the baseline substitution seam.

Verified ordering on Hermes 0.20.1:

```text
model tool proposal
  → apply_tool_request_middleware(tool_name, original_args)
  → run_tool_execution_middleware(...)
  → _authorized_dispatch(rewritten_args)
      → pre_tool_call hooks / Observe
      → guardrails and approval
      → normal tool execution
```

For an exact safe reusable operation, middleware rewrites only `args["command"]` from model-authored shell to a fixed reviewed harness CLI invocation. All other arguments (`workdir`, `timeout`, `background`, etc.) remain unchanged. The normal authorization and execution path remains intact.

The decision is stored by `tool_call_id`; `pre_tool_call` consumes it exactly once, emits the authoritative `harness_decision` event and one truthful Observe bubble, and suppresses the old cached prompt-level bubble for that call.

A per-core `replace` action is a fallback only if the real integration gate proves middleware cannot preserve result semantics, correlation, or one-bubble behavior.

## Safety invariants

1. **No behavior change in Phase A.** Detection and decisions are shadow-only.
2. **Production reuse begins with `hmp-healthcheck@1.0.0`**, which is read-only, trusted, and allowlisted.
3. **`hmp-send` remains non-dispatchable in production** while it is mutating/unsafe/observed.
4. Production HMP-send proposals produce `rejected(mutating_not_trusted)`, keep original args unchanged in shadow mode, and emit one truthful rejection bubble.
5. HMP-send substitution is exercised only against a fake server under an explicit test-target override; test/calibration evidence is never organic evidence.
6. Unknown operations fail open: original tool runs and Observe reports `no_harness`.
7. Unsafe, partial, effect-mismatched, untrusted, or unavailable candidate reuse fails closed: no substitution.
8. Harness payloads are passed through mode-0600 files, never interpolated inline into a rewritten shell command.
9. Rewritten middleware output preserves all tool arguments except `command`.
10. The original model-authored curl bytes must never execute in a successful reuse case.

## Ordered TDD plan

### Phase A — Operation-specific shadow decision

No tool substitution yet.

1. **T1 — Operation signature**
   - Add a pure `tool_signature` component.
   - Recognize exact HMP health and send shapes from `terminal.command` and supported generated-Python equivalents.
   - Extract normalized operation, target, method, endpoint, payload reference, and effect.
   - Include hard negatives: SSH, package management, Git, unrelated curl, composite/multi-step commands, unsupported endpoints, and trailing side effects.
   - **Gate:** complete fixture table; zero false positives in the declared hard-negative set.

2. **T2 — Exact harness lookup**
   - Map operation signature to exact `capability_id@version`.
   - Check that the declared executor is actually live.
   - Outcomes: exact candidate, `executor_not_live`, or `no_harness`.
   - **Gate:** healthcheck resolves exactly; current HMP-send is identified but rejected as executor-not-live/untrusted; unknown operations return `no_harness`.

3. **T3 — Tool-level safety and decision record**
   - Reuse existing effect, trust, allowlist, permission, availability, idempotency, and partial-coverage gates against the derived operation.
   - Store one decision per `tool_call_id`.
   - Outcomes: `reused`, `rejected(reason)`, `no_harness`.
   - **Gate:** zero HMP-send `reused` outcomes in production configuration while trust remains observed.

4. **T6/T7 — Truthful Observe behavior**
   - `reused` → existing `matched` kind;
   - `rejected` → existing `rejected` kind;
   - `no_harness` → existing `generic` kind.
   - Tool-level decision supersedes cached prompt-level Observe for that call.
   - **Gate:** exactly one bubble and one `harness_decision` event per decision-capable tool call; no bubble for no-tool chat.

5. **T8 — Single feedback source**
   - Ensure dummy `harness-feedback` is disabled on the test node before measurement.
   - peer128 already has only `hmp` and `capability-reuse` enabled; peer141 must remove its dummy before evidence runs.
   - **Gate:** only Capability-Reuse emits Rebar decision bubbles.

### Phase B — Trusted read-only production tracer

6. **T4 — Stable harness CLI**
   - Build a reviewed CLI wrapper for `hmp-healthcheck@1.0.0` with file-based inputs where applicable.
   - Test both in-process logic and CLI subprocess behavior against a fake HTTP server.
   - **Gate:** contract-conformant input/output/error behavior.

7. **T5 — Real `tool_executor` integration**
   - Register Capability-Reuse `tool_request` middleware.
   - Rewrite only the exact compatible healthcheck command to the stable harness invocation.
   - Carry middleware trace `{source: capability-reuse, reason: harness_reuse, name: hmp-healthcheck@1.0.0}`.
   - Exercise the actual Hermes tool pipeline.
   - **Gate:**
     - original generic command bytes never execute;
     - harness receives only normalized parameters;
     - fake server receives exactly one request from the harness;
     - rewritten args pass normal hooks, guardrails, approval, and execution;
     - exactly one bubble;
     - complete correlated decision → invocation → completion chain;
     - sequential and concurrent paths each apply middleware exactly once;
     - middleware failure remains fail-open.

### Phase C — Founding HMP-send case, sandbox only

8. Build and source-review the new live `hmp-send@1.0.0` harness; replace the retired contract entrypoint only after review.
9. Exercise exact single-peer HMP-send curl recognition and substitution against a fake HMP server using an explicit test-target override.
10. Verify idempotency/deduplication, per-target partial-effect accounting, Unicode/quoting safety, unsupported fields, composite command rejection, and zero production dispatch.
11. Produce calibration/evaluation evidence only; never label these tests `organic_live`.

**Phase C gate:** the original curl is suppressed in sandbox, one harness POST occurs, normalized fields match the contract, and production configuration still yields `rejected(mutating_not_trusted)` with no rewrite.

## Cross-cutting correctness checks

- Derive the decision from `original_args` even if another plugin later rewrites the command.
- Record actual executed args in post-tool telemetry so the chain remains truthful.
- Verify middleware availability and ordering separately on peer70's Hermes 0.17.x before any rollout; do not assume 0.20.1 parity.
- Preserve requester, processor, target, and collector identities.
- Preserve request-unique `trace_id`, cohort label, provenance, and traffic type.
- Do not count fake-server or operator-solicited traffic as organic holdout.
- Sync skill source and runtime plugin only after focused tests pass; keep per-core patches outside general skill sync.

## G0b reseal gate

G0b may be proposed to peer70 and the reviewer only when:

1. Phase A and Phase B gates pass on pinned peer141 runtime.
2. The real tool-dispatch test demonstrates operation → lookup → safety → rewrite → Observe → harness → result.
3. All three outcomes are evidenced: reused, rejected with canonical reason, and no harness.
4. Exactly-one bubble/event behavior holds under sequential and concurrent paths.
5. No read-only↔mutating false match is observed in the hard-negative battery.
6. Fail-open and fail-closed boundaries match the charter.
7. Runtime and source copies are synchronized and hashed.
8. The evidence bundle contains the reviewed artifact hash, tests, traces, provenance labels, and non-empty gates.
9. peer70 and the external reviewer accept the G0b amendment and sealed bytes.
10. Only then does clean organic holdout accumulation begin.

## Explicit agreement

peer141 independently inspected the current 0.20.1 middleware ordering and accepted this plugin-first baseline. Both peer128 and peer141 agree:

- Phase A: plugin-only shadow decisions;
- Phase B: trusted read-only healthcheck substitution through `tool_request` middleware;
- Phase C: HMP-send sandbox substitution with zero production auto-dispatch;
- add a per-core `replace` action only if the T5 integration gate proves the existing middleware insufficient.

No implementation was authorized or started during planning.
