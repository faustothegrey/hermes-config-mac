# Antigravity AgentTalk Historical Runs Failure Analysis 2026-06-16

Source: Antigravity CLI delegated read-only forensic analysis.
Project path: `/Users/fausto/Software/AgentTalk`
Artifacts reviewed via factual digest from:

- `/Users/fausto/Software/AgentTalk/transcripts`
- `/Users/fausto/Software/AgentTalk/planning_runs`

Related notes: [[AgentTalk]], [[Claude AgentTalk Historical Runs Failure Analysis 2026-06-16]], [[AgentTalk Historical Runs Failure Synthesis 2026-06-16]]

## Delegation note

Antigravity readiness was verified first with a short ping:

- Command: `/Users/fausto/.local/bin/agy --print 'Readiness ping: reply with exactly READY and nothing else.' --print-timeout 30s`
- Result: `READY`

A first full artifact review run timed out before producing a final report. Antigravity had started inspecting the same files and source-code paths but returned only progress narration. Hermes then reran a narrower digest-only delegation, which completed successfully. The analysis below comes from the completed digest-only Antigravity run.

## Executive diagnosis

Antigravity agreed that all 49 recorded historical planning runs failed or stopped with `status=interrupted`.

It identified two bottlenecks:

1. Infrastructure/provider bottleneck: Gemini planner agents hit hard API quota/resource exhaustion.
2. Logic/protocol bottleneck: Codex agents violated or desynchronized from the planning protocol state machine.

Antigravity's bottom line was that AgentTalk was failing at both the external-agent substrate layer and the internal coordination-protocol layer.

## Evidence inventory

Antigravity cited the following evidence from the digest:

- 49 of 49 files in `planning_runs/` showed `status=interrupted`.
- Some runs were interrupted almost instantly, with `createdAt` and `updatedAt` only milliseconds apart.
- Other runs lasted much longer, from minutes to around twenty-plus minutes, suggesting timeout, protocol regression, or stalled coordination rather than immediate process failure.
- Gemini planner logs showed explicit quota failures:
  - `planner-gemini-pro-a-1775765889459.log`
  - `planner-gemini-pro-b-1775765889459.log`
  - `TerminalQuotaError`
  - HTTP 429
  - `QUOTA_EXHAUSTED`
  - capacity exhausted with reset after roughly 13 hours
- Codex-related logs showed validation and schema/protocol failures:
  - `Unexpected agreement_proposal: a different proposal is already pending endorsement`
  - `Invalid agreement_acceptance: proposal text is required`
  - `Unexpected agreement_acceptance: proposal does not match pending proposal`
- Codex-related logs also showed team/task lifecycle routing failures:
  - `Agent agent-codex-... is not part of any active team`
  - `Planning task is not active for team team-...; cannot route planning messages.`
- Protocol regression was explicit in logs:
  - `received "submit_plan" but planning had advanced to "opinion"`

## Failure taxonomy

### Category A: external API / quota failures

Symptom:

- `QUOTA_EXHAUSTED` / HTTP 429 / Gemini process exit.

Consequence:

- Planner process exits immediately and cannot contribute to planning.
- This can produce instant interruption or repeated scheduled failures until quota resets.

### Category B: agent protocol violations

Symptoms:

- Missing required proposal text in `agreement_acceptance`.
- Proposal text not matching the pending proposal.
- A new `agreement_proposal` arriving while another proposal is still pending endorsement.

Consequence:

- Orchestrator rejects the protocol call.
- The planning flow falls back or stalls.
- Repeated violations eventually interrupt the task.

### Category C: dynamic desynchronization / stale planning state

Symptom:

- The orchestrator falls back to a previous phase, but one or more agents continue as if the newer phase is still active.
- Agents submit `submit_plan` while the orchestrator expects `opinion` or `agreement_proposal`.

Consequence:

- Protocol regression is detected.
- The planning task is interrupted.

### Category D: routing and lifetime de-registration

Symptoms:

- Messages arrive after the team/task is no longer active.
- Agents are no longer considered members of active teams.

Consequence:

- Later protocol messages cannot be routed.
- The session cannot recover once deactivated.

## Ranked likely root causes

1. API quota / rate limits — high confidence for planner runs.
   - Direct evidence: 429 / `QUOTA_EXHAUSTED` / process exit.
   - Antigravity considered this unambiguous for Gemini planner failures.

2. LLM-agent instruction or prompt mismatch on protocol payload requirements — high confidence for Codex runs.
   - Direct evidence: repeated missing/mismatched proposal text in acceptance messages.
   - Antigravity suggested that Codex agents were either not given sufficiently strict payload requirements or did not follow them reliably.

3. Orchestrator fallback stale-state desynchronization — medium-high confidence.
   - When fallback returns the orchestrator to discussion/opinion, agents can remain mentally or locally in a later phase and send stale events.
   - This explains `submit_plan` arriving when the orchestrator expected `opinion` or `agreement_proposal`.

4. Premature team/task termination or aggressive lifecycle cleanup — medium confidence.
   - `Agent is not part of any active team` and `Planning task is not active` suggest that once an error occurs, the lifecycle closes quickly.
   - Ambiguity remains: this may be expected safety behavior rather than a bug.

## Missing or ambiguous evidence

Antigravity called out missing details:

- Exact turn limits and timeout thresholds used by the runs.
- Full chronological state-transition timelines for each task.
- Whether these runs happened before or after Milestone 03 failure-propagation changes.
- Whether team/task de-registration is expected safety semantics or an unintended lifecycle bug.
- Whether some failures were caused by slow responses rather than malformed responses.

## Questions Antigravity suggested for Fausto

- What rate limits or plan/tier backed the Gemini key used for planner agents?
- Should AgentTalk implement exponential backoff or local rate limiting before spawning planner agents?
- How are Codex agents instructed about the `agreement_acceptance` payload shape?
- Can local schema validation catch bad protocol payloads before sending them to the orchestrator?
- Were these runs generated before or after the Milestone 03 failure-propagation changes?
- What exact rule or timeout marks a planning task inactive?
