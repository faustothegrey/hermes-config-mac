# Rebar — Founding Intent and Tool-Use Contract

**Status:** Canonical project charter  
**Applies to:** Capability-Reuse / Rebar, Observe Channel, harness registry, generic tool execution  
**Authority:** This document defines the product intent. Tests and implementations that conflict with it are incomplete, even if they pass their existing suites.

**Agreed implementation plan:** [`rebar-charter-alignment-agreed-plan-2026-08-17.md`](rebar-charter-alignment-agreed-plan-2026-08-17.md) — peer128/peer141 consensus for the plugin-first G0b tracer and reseal gates.

## 1. Origin

Rebar began with a concrete observation about Hermes using HMP.

Whenever the model needed to send an HMP request, it often rebuilt the entire operation as a fresh shell command: it selected `terminal`, composed a complete `curl` invocation, repeated the endpoint and headers, handled quoting again, and embedded a new payload. The transport procedure was already known and largely invariant, but the model regenerated it from scratch on every use.

That is wasteful and fragile. It spends model effort recreating solved operational knowledge and introduces avoidable variation in quoting, flags, endpoint selection, authentication handling, timeout behavior, provenance markers, and error handling.

The better design is a standard, reviewed HMP harness—for example, a stable curl wrapper or script—with a small typed interface. The reusable transport procedure remains fixed; each invocation changes only the legitimate variables, such as destination, session identifier, message text, provenance, and payload fields.

In short:

> **Do not regenerate a known operation when a reviewed, parameterized harness can execute it.**

HMP/curl is the founding example, not the limit of the project. The same principle applies whenever the model is about to recreate a known terminal command, Python program, API sequence, validation routine, deployment procedure, document pipeline, or other operational pattern.

## 2. Core problem

Generic tools such as `terminal` and `execute_code` are universal escape hatches. They can perform almost anything, but they encourage the model to solve repeated tasks by generating a new procedure each time.

Rebar exists to insert a reuse decision before that generic execution:

> **Before Hermes executes a proposed generic tool operation—especially shell or generated Python—it must check whether a specialized, task-specific harness or registered capability already performs that operation.**

This check is about the **specific intended operation**, not merely the tool name and not merely the original user prompt.

Examples:

- `terminal(curl ... /hmp/send ...)` should be recognized as “send an HMP message,” then compared with an HMP-send harness.
- Generated Python that polls an HMP message should be compared with an HMP-poll harness.
- A shell health probe should be compared with an HMP-healthcheck harness.
- An unrelated one-off shell inspection should not be forced into an HMP harness merely because it uses `terminal`.

## 3. Non-negotiable execution contract

For each decision-capable generic tool call, Rebar must perform the following sequence:

1. **Observe the proposed operation**
   - Inspect the actual tool name and arguments.
   - Derive an operation signature: intent, effect class, target, required permissions, inputs, and expected result.

2. **Retrieve specialized harnesses**
   - Query the capability/harness registry using that operation signature.
   - Prefer exact, versioned, reviewed capabilities over generated shell or Python.

3. **Evaluate compatibility and safety**
   - Verify input and output contracts.
   - Preserve requester, processor, target, and collector identities.
   - Check effect class, permissions, availability, trust state, and whole-request coverage.
   - Fail closed on read-only versus mutating mismatches and partial coverage.

4. **Choose explicitly**
   - **Reuse:** a compatible harness exists; invoke it with only the variable parameters.
   - **Reject candidate:** a related harness exists but is unsafe, incompatible, unavailable, or incomplete; state the reason and continue only under the normal policy.
   - **No harness:** no suitable reusable capability exists; allow the generic tool path and record a capability-gap signal when appropriate.

5. **Surface the decision**
   - Emit exactly one short, non-blocking Observe bubble before execution.
   - The bubble is evidence that the reuse check occurred; it is not the purpose of Rebar.

6. **Execute and correlate**
   - Execute the selected harness or authorized generic fallback.
   - Correlate preview, decision, dispatch, result, and telemetry with stable identifiers.

## 4. Required Observe semantics

Observe is tied to **tool-use decisions**, not to every conversational turn.

It should appear when Hermes is about to perform a decision-capable operation, especially through:

- `terminal`;
- `execute_code` or generated Python;
- generic web/API calls that duplicate a registered operational harness;
- other configurable generic execution surfaces.

Expected messages include:

- `✅ hmp-send reused`
- `✅ hmp-healthcheck reused`
- `⛔ hmp-send rejected · mutating mismatch`
- `⛔ candidate rejected · partial coverage`
- `🔍 checked · no specialized harness`

Observe must be:

- single-fire per underlying tool decision;
- informational and non-blocking by itself;
- fail-open as a display channel;
- truthful about whether a harness was reused, rejected, or absent;
- emitted before execution, not reconstructed afterward;
- absent on ordinary conversation when no tool execution is proposed.

A bubble that merely displays the highest-scoring prompt-level candidate—even when irrelevant or rejected—does not satisfy this contract.

## 5. HMP reference pattern

The canonical HMP pattern separates stable procedure from variable payload.

### Stable harness responsibilities

A reviewed HMP-send harness owns:

- HTTP method and endpoint construction;
- standard headers;
- serialization and shell quoting;
- connection and request timeouts;
- response parsing;
- error normalization;
- provenance/test markers;
- requester/processor/target/collector identity handling;
- retry and idempotency policy;
- secret-safe logging and redaction.

### Per-call variables

The model supplies only fields such as:

- destination peer;
- session or correlation ID;
- message text;
- traffic/provenance class;
- approved optional payload fields.

The model should not rewrite the complete curl/bash envelope on every request.

Conceptually:

```text
hmp_send(
  peer="peer70",
  session_id="...",
  text="...",
  provenance="operator_solicited"
)
```

is preferred over freshly generating:

```text
curl -X POST ... -H ... --data-binary '...'
```

The harness may internally use curl. Rebar's point is not to ban curl; it is to stop regenerating the same curl procedure as new model-authored code.

## 6. Why this matters

Reusing a specialized harness provides:

- **Consistency:** identical operational behavior across invocations.
- **Safety:** reviewed effect classification, permissions, redaction, and error handling.
- **Efficiency:** fewer generated tokens and less reasoning spent on solved mechanics.
- **Reliability:** less quoting drift, malformed JSON, missing flags, or endpoint variation.
- **Auditability:** stable capability versions, contracts, traces, and outcomes.
- **Maintainability:** transport changes are fixed once in the harness instead of rediscovered in prompts.
- **Learning:** repeated generic fallbacks reveal which new harnesses are worth creating.

## 7. What Rebar is not

Rebar is not:

- a bubble shown for every user message;
- a generic “use tools” notification;
- a prompt-only semantic search detached from the proposed tool call;
- a ban on terminal or Python;
- permission to force a partial or unsafe harness onto a request;
- proof of reuse merely because a similarly named capability scored highest;
- a reason to hide fallback execution or fabricate successful dispatch.

Generic tools remain valid when no compatible harness exists. Rebar makes that fallback deliberate and observable rather than automatic and invisible.

## 8. Acceptance criteria

An implementation satisfies the founding intent only if it can demonstrate all of the following:

1. A proposed hand-built HMP curl send is detected at the pre-tool boundary.
2. The HMP-send harness is retrieved using the actual proposed operation.
3. A compatible harness receives only variable payload fields; the model-authored curl is not executed.
4. A read-only request cannot be redirected to a mutating harness, or vice versa.
5. A partially covering harness is rejected with an explicit reason.
6. When no harness exists, the generic tool may proceed and Observe reports `no specialized harness`.
7. Exactly one truthful decision bubble appears before each decision-capable tool execution.
8. Ordinary no-tool conversation produces no Rebar bubble.
9. Preview, decision, dispatch, and result share exact correlation identifiers.
10. Tests exercise the real gateway/tool-dispatch path, not only a local controller mock.

## 9. Product invariant

> **Rebar is procedural memory at the point of action: before the model regenerates an operation through a generic tool, it checks for a reviewed reusable harness, prefers that harness when compatible, and makes the decision visible.**

This invariant is the standard against which future architecture, tests, reviewer verdicts, and phase gates must be judged.
