# AgentTalk Protocol-Adherence Thesis Discussion 2026-06-16

Related notes:

- [[AgentTalk]]
- [[AgentTalk Historical Runs Failure Synthesis 2026-06-16]]
- [[Claude AgentTalk Historical Runs Failure Analysis 2026-06-16]]
- [[Antigravity AgentTalk Historical Runs Failure Analysis 2026-06-16]]
- [[AgentTalk Comparative Synthesis 2026-06-16]]

## Context

After delegated analysis of AgentTalk's historical `transcripts/` and `planning_runs/`, Fausto stated his main point:

> The main AgentTalk failure is the lack of adherence of agents to a rigid protocol schema that leaves no room for ambiguity and logic loops.

Hermes agreed that this is likely the central diagnosis behind the interesting AgentTalk failures, while Gemini quota exhaustion remains a separate infrastructure/provider issue.

Fausto then asked for other agents' point of view on this thesis.

## Readiness results for delegate follow-up

Following the new general delegation-readiness workflow:

- Claude Code readiness check passed: `READY`.
- Antigravity readiness check failed: it prompted for Google OAuth again and timed out. Hermes therefore treated Antigravity as unavailable and continued only with Claude Code.

## Claude's independent point of view

Claude partially agreed with Fausto's thesis but refined it.

Claude's key distinction:

1. Format/adherence failures.
2. Semantic/state-machine failures.

Claude argued that strict schema adherence is necessary but not sufficient, because some failures are not merely malformed output. They are stale-state, concurrency, or authority-boundary failures.

## Format/adherence failures

Examples:

- malformed messages;
- wrong field shapes;
- missing required proposal text;
- invalid `agreement_acceptance` payloads;
- agents using freeform rationale where the protocol required exact proposal content.

Claude agreed these can be improved by:

- stricter schemas;
- constrained decoding;
- function calling / tool calling;
- local validation before sending protocol events;
- schema-repair re-prompts.

## Semantic/state-machine failures

Claude emphasized that valid JSON is not enough if the event is semantically stale or invalid for the current orchestration state.

Examples:

- a syntactically valid `submit_plan` sent after the orchestrator fell back to `opinion` / `agreement_proposal`;
- competing pending proposals;
- an agent accepting an obsolete or mismatched proposal;
- agents acting on superseded phase assumptions;
- loops around proposal / endorsement / fallback.

Claude's point: a perfectly rigid schema can still permit the wrong valid event at the wrong time.

## Refined thesis

Claude's refined formulation:

AgentTalk should not rely on agents to be the protocol.

Instead:

- agents should deliberate and reason;
- the runtime/control plane should own canonical protocol state;
- deterministic wrappers or orchestrator-owned mechanisms should translate/guard/free-form agent intent into valid protocol events;
- stale or ambiguous outputs should be recoverable diagnostics rather than direct state transitions.

Hermes' synthesis of Claude's point:

> AgentTalk failed because probabilistic agents were being allowed to directly operate a rigid consensus protocol. The fix is not just stricter prompts or schemas; it is moving protocol authority out of the agents and into deterministic runtime mechanisms.

## Design implications

Claude suggested these architectural directions:

- Make the control plane the authoritative referee, not just a message relay.
- Use server-assigned proposal IDs or content-addressed proposal hashes instead of exact copied proposal text.
- Require agents to reference proposal IDs plus versions/fencing tokens.
- Add phase/version/fencing tokens so stale writes are rejected or repaired deterministically.
- Make the orchestrator the single source of truth for allowed next actions.
- Add a single-proposal-at-a-time invariant or explicit merge rule to prevent competing pending proposals.
- Separate format validation from semantic state validation.
- Add loop detection, progress metrics, and max-round convergence rules.
- Keep infrastructure/provider failures, such as Gemini quota exhaustion, in a separate telemetry/error taxonomy from protocol failures.

## Concrete experiments Claude suggested

1. Classify every historical interrupted run into failure buckets:
   - format/schema;
   - state/concurrency;
   - stale phase;
   - provider/infra;
   - timeout/idle;
   - unknown.

2. Try constrained decoding or function calling to measure whether invalid-message rates drop.

3. Replace exact proposal-text matching with server-assigned proposal IDs and measure whether `agreement_acceptance` rejection rates drop.

4. Add a single-writer proposal lock or explicit merge rule and measure competing-proposal incidence.

5. Build a deterministic replay harness for failed runs and A/B the current protocol against revised control-plane rules.

6. Add schema-repair loops so strict validation does not simply convert ambiguous output into hard rejection.

## Risks and counterarguments

Claude warned against treating rigid schema as the entire solution:

- Over-rigidity may defeat the purpose of multi-agent deliberation by turning the system into an expensive brittle rules engine.
- Rigidity can increase failures for weaker or variable models unless paired with repair loops.
- “Agent did not adhere” can hide control-plane bugs, such as too-strict acceptance predicates or false rejections.
- A full protocol rewrite would be premature without first quantifying failure classes across the 49 historical runs.
- “No room for ambiguity” is probably unattainable with natural-language agents; the system should be designed for graceful degradation, repair, and containment.

## Current resume point

The conversation should resume from this refined framing:

- Fausto's core thesis remains central: agents failed to adhere to a rigid protocol that could not tolerate ambiguity and loops.
- Claude refines it: schema adherence is necessary but not sufficient; the deeper issue is that protocol authority should not live inside probabilistic agents.
- The likely next productive direction is either:
  1. classify all 49 historical runs by failure type; or
  2. design a revised AgentTalk protocol/control-plane architecture with proposal IDs, phase fencing, deterministic event generation, and loop/progress guards.

## Open question for next session

Should AgentTalk's next design pass focus first on empirical classification of the 49 historical failures, or directly on a revised protocol architecture that assumes agents are unreliable protocol participants?
