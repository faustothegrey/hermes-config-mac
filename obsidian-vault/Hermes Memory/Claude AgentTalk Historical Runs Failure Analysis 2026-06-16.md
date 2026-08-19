# Claude AgentTalk Historical Runs Failure Analysis 2026-06-16

Source: Claude Code delegated read-only forensic analysis.
Project path: `/Users/fausto/Software/AgentTalk`
Artifacts reviewed via factual digest from:

- `/Users/fausto/Software/AgentTalk/transcripts`
- `/Users/fausto/Software/AgentTalk/planning_runs`

Related notes: [[AgentTalk]], [[Antigravity AgentTalk Historical Runs Failure Analysis 2026-06-16]], [[AgentTalk Historical Runs Failure Synthesis 2026-06-16]]

## Executive diagnosis

Claude's assessment was that the historical AgentTalk runs show total failure at the persisted planning-run level: all 49 planning-run JSON files had `status=interrupted`, with no completed/successful terminal state visible in the digest.

Claude separated the failures into two main families:

1. Gemini planner quota / provider failure.
2. Codex-agent protocol/state-machine churn or deadlock.

Claude emphasized that Milestone 03-style failure propagation likely amplified both families: once any agent enters an error or idle/invalid state, the whole team task becomes interrupted. Therefore the uniform `interrupted` status is probably partly a product of zero-tolerance interruption semantics, not necessarily one single root-cause bug.

## Evidence inventory

Artifact inventory from the factual digest:

- `planning_runs/`: 49 `.json` task files.
- Every planning run reported `status=interrupted`.
- Top-level fields included `taskId`, `teamId`, `composition`, `description`, `status`, `plan`, `plannerAgentId`, `members`, `transcript`, `createdAt`, `updatedAt`, and `persistedAt`.
- `transcripts/`: 10 `.log` files plus one `.json` file.
- Gemini planner logs included `planner-gemini-pro-a-1775765889459.log` and `planner-gemini-pro-b-1775765889459.log`.
- Codex agent logs included several `agent-codex-*` files around task IDs/timestamps near `177576638*` and `177576706*`.
- Several planning tasks had `createdAt` and `updatedAt` equal or nearly equal, suggesting immediate interruption during provisioning/startup.
- Other tasks ran for minutes to tens of minutes before interruption, suggesting protocol stalls, timeout, or late failure.

## Failure taxonomy

### 1. Provider quota exhaustion / planner death

Evidence in Gemini planner logs indicated hard provider exhaustion:

- `TerminalQuotaError`
- HTTP 429
- `QUOTA_EXHAUSTED`
- text indicating the model capacity was exhausted and would reset after roughly 13 hours
- `Gemini process exited with code 1`
- `Interactive gemini request failed`

Claude's interpretation: when Gemini planner capacity was exhausted, the planner process could not produce a plan at all. If the run cadence was around every 30 minutes, a single quota exhaustion window could mechanically poison many scheduled runs.

### 2. Protocol phase regression

Codex logs showed the agents and orchestrator disagreeing about the current planning phase.

Representative failure:

- `Planning interrupted because required event(s) were not received: Protocol regression: received "submit_plan" but planning had advanced to "opinion" (expected one of [opinion, agreement_proposal])`.

Claude's interpretation: the agent believed it was allowed to submit the plan, while the authoritative orchestrator had already moved or reverted to a previous protocol phase.

### 3. Agreement/proposal payload mismatch

Codex logs showed rejected protocol calls such as:

- `Invalid agreement_acceptance: proposal text is required`
- `Unexpected agreement_acceptance: proposal does not match pending proposal`
- `Unexpected agreement_proposal: a different proposal is already pending endorsement`

Claude's interpretation: agents were often putting justification/freeform reasoning in the message text instead of supplying the exact proposal text expected by the protocol. This made endorsement fail even when the agents appeared semantically aligned.

### 4. Fallback exhaustion and discussion loops

The orchestrator emitted reminders and fallback messages such as:

- `agreement_acceptance was not provided; returning to discussion phase (2/2 allowed fallback(s))`
- reminders to explicitly motivate why the selected `message_type` matched the current protocol step
- expected next message types such as `agreement_acceptance`, `opinion`, and `agreement_proposal`

Claude's interpretation: the protocol tried to recover by returning to discussion, but the LLM agents did not reliably synchronize to that state. This caused repeated loops and eventually interruption.

### 5. Team/task deactivation cascade

After interruption, logs contained routing errors such as:

- `Agent agent-codex-... is not part of any active team`
- `Planning task is not active for team team-...; cannot route planning messages.`

Claude treated these mostly as downstream cascade symptoms: once the task is interrupted, later agent messages continue arriving but can no longer be routed.

### 6. Non-responses / empty or undefined messages

Logs also contained signs of harness-level fragility:

- `No reply generated for ...; skipping`
- `Message from undefined: undefined`

Claude treated these as possible contributors to missed required events and fallback exhaustion.

## Ranked likely root causes

1. Gemini planner quota exhaustion — high confidence for Gemini-configured planner runs.
   - Direct evidence: 429 / `QUOTA_EXHAUSTED` / process exit code 1.
   - Likely explains immediate planner failures and long streaks during quota reset windows.

2. Planning protocol state-machine plus payload-contract mismatch — high confidence for Codex runs.
   - Direct evidence: missing proposal text, mismatched proposal, competing pending proposals, and out-of-phase `submit_plan`.
   - Likely design/contract issue rather than just a model quality issue: the protocol required exact structured payloads that agents did not consistently produce.

3. Zero-tolerance failure propagation — medium-high confidence as an amplifier.
   - Any single agent/provider/protocol/idle failure becomes whole-task `interrupted`.
   - Explains why persisted outcomes are uniformly interrupted.

4. Unattended scheduled loop without backoff/recovery — medium confidence.
   - Many tasks appear to have similar cadence and generic descriptions.
   - If runs repeated every ~30 minutes, provider quota failures and protocol bugs would repeat mechanically.

5. Provisioning/startup race or immediate teardown — low-medium confidence.
   - Inferred from tasks with millisecond lifetimes and paired timestamps.
   - Digest did not expose enough cause detail for a firm conclusion.

6. Idle-timeout stalls — low-medium confidence.
   - Plausible from long-running interrupted tasks and missing replies, but explicit idle-timeout strings were not prominent in the digest.

## Ambiguities and missing evidence

Claude highlighted these missing or ambiguous areas:

- There was no successful baseline run in the digest, so it is unclear whether AgentTalk regressed from a working state or had not yet reached working reliability.
- The digest did not map every planning-run JSON to a precise transcript failure mode.
- The full per-task `transcript`, `plan`, `members`, `composition`, and `plannerAgentId` fields would be needed to classify all 49 runs accurately.
- The exact cause of millisecond-lifetime interruptions was not clear.
- It was ambiguous whether Gemini and Codex were alternative configurations or roles in one combined pipeline.
- It was unclear whether `interrupted` should be interpreted as a failure label or as the expected Milestone 03 terminal state for failed/invalid agent behavior.

## Questions Claude suggested for Fausto

- Was this an unattended scheduled loop or soak/stress test?
- Did any AgentTalk run ever complete and submit a plan?
- What Gemini quota/tier was backing these runs, and was the quota exhaustion expected?
- Is `agreement_acceptance` supposed to include the exact pending proposal text or freeform justification?
- Under Milestone 03 semantics, should `interrupted` be considered a failure, a correct safety stop, or both?
- Were Gemini and Codex alternative configurations, or part of one hybrid pipeline?
- Should the next investigation quantify all 49 runs by direct failure class from their full JSON transcript arrays?
