# AgentTalk Historical Runs Failure Synthesis 2026-06-16

Sources:

- [[Claude AgentTalk Historical Runs Failure Analysis 2026-06-16]]
- [[Antigravity AgentTalk Historical Runs Failure Analysis 2026-06-16]]
- Hermes factual extraction from `/Users/fausto/Software/AgentTalk/transcripts` and `/Users/fausto/Software/AgentTalk/planning_runs`

Related notes: [[AgentTalk]], [[Claude AgentTalk Assessment 2026-06-16]], [[Antigravity AgentTalk Assessment 2026-06-16]], [[AgentTalk Comparative Synthesis 2026-06-16]]

## Bottom line

Both Claude and Antigravity independently converged on the same diagnosis: the recorded AgentTalk sessions appear to have failed for two different classes of reasons at once.

1. Some runs failed because the external provider/agent substrate was unavailable or exhausted, especially Gemini planner quota exhaustion.
2. Other runs failed because the consensus protocol was too brittle for the actual LLM-agent behavior: agents sent malformed, incomplete, stale, or out-of-phase protocol messages.

Hermes' factual extraction found 49 planning-run JSON files and all 49 had `status=interrupted`. This confirms Fausto's memory that the runs overwhelmingly, possibly entirely, ended in failure/interruption.

The most important nuance: `interrupted` may be the correct safety terminal state under AgentTalk's failure-propagation semantics. The artifact result can therefore be both a failure of the historical experiment and a sign that the orchestrator refused to continue unsafe/incoherent consensus flows.

## Artifact facts verified by Hermes

- `transcripts/` contained 12 filesystem entries, including 10 `.log` files, one `conversations.json`, and `.DS_Store`.
- `planning_runs/` contained 50 filesystem entries, including 49 `.json` planning task files and `.DS_Store`.
- All 49 planning-run JSON files had top-level `status=interrupted`.
- Planning-run JSON files used top-level fields such as:
  - `taskId`
  - `teamId`
  - `composition`
  - `description`
  - `status`
  - `plan`
  - `plannerAgentId`
  - `members`
  - `transcript`
  - `createdAt`
  - `updatedAt`
  - `persistedAt`
- Some tasks had millisecond-scale lifetimes, indicating immediate interruption.
- Some tasks lasted minutes to tens of minutes, indicating longer planning/protocol/timeout failure modes.
- Gemini planner logs contained explicit quota/resource failure signals.
- Codex agent logs contained explicit protocol validation and phase-regression errors.

## Consensus diagnosis from Claude and Antigravity

### 1. Provider quota exhaustion was a real direct failure mode

Both delegates highlighted Gemini planner failures:

- `TerminalQuotaError`
- HTTP 429
- `QUOTA_EXHAUSTED`
- messages indicating model capacity was exhausted and reset would occur after roughly 13 hours
- Gemini process exit code 1

Likely implication:

- For runs using Gemini planners, AgentTalk could not even begin or complete planning because the planner process itself failed.
- If a scheduler/soak loop kept retrying every ~30 minutes, many runs would fail mechanically until quota reset.
- AgentTalk likely needs provider-readiness checks, backoff, and failover before treating a provider-backed planner as available.

### 2. The Codex consensus protocol repeatedly desynchronized

Both delegates highlighted the same Codex protocol problems:

- `agreement_acceptance` rejected because proposal text was required.
- `agreement_acceptance` rejected because the proposal did not match the pending proposal.
- `agreement_proposal` rejected because a different proposal was already pending endorsement.
- `submit_plan` arrived when the orchestrator had advanced or reverted to `opinion` / `agreement_proposal` expectations.

Likely implication:

- The agents were often semantically aligned but structurally noncompliant.
- They could discuss the right idea but not satisfy the exact machine contract.
- The protocol required exact proposal text and exact state transitions; the LLMs tended to provide rationale, approximations, or stale next steps.

### 3. Fallback behavior may have worsened stale-state confusion

The orchestrator sometimes returned to discussion after missing required endorsement events. Logs included messages such as:

- `agreement_acceptance was not provided; returning to discussion phase (2/2 allowed fallback(s))`

Both delegates interpreted this as a key desynchronization point:

- The orchestrator legally reverts to discussion/opinion.
- One or more agents still behave as if proposal/acceptance/submit is the current step.
- A later `submit_plan` is then treated as a protocol regression.

This suggests a design issue around how phase changes are communicated and enforced. If the authoritative state moves backward, agent-side context and pending intentions must be reset strongly enough that stale actions are impossible or harmless.

### 4. Task/team deactivation errors are probably cascade symptoms

Logs included errors like:

- `Agent ... is not part of any active team`
- `Planning task is not active for team ...; cannot route planning messages.`

Delegates agreed these may not be primary causes. They can happen after the orchestrator has already interrupted a task, while late agent messages continue arriving. This still matters because the system must handle late messages gracefully, but the real cause may be the earlier quota/protocol/fallback failure.

### 5. Strict failure propagation made every local error terminal

Under Milestone 03-style behavior, an agent entering error/idle/failure state can interrupt the active team task. This is probably intentional safety behavior, but it means:

- one provider failure can end the whole run;
- one malformed protocol call can end or poison the planning cycle;
- one stale message after fallback can become a terminal protocol regression;
- persisted history will show a uniform `interrupted` population even if underlying causes differ.

## Failure taxonomy

### A. Provider or substrate unavailable

Direct signs:

- Gemini 429 / quota exhaustion.
- Planner process exits.
- Runs interrupt immediately or near-immediately.

Likely fix category:

- Provider readiness checks.
- Backoff on quota exhaustion.
- Do not schedule repeated runs during a known reset window.
- Fail over to another planner or mark the run as `provider_unavailable` instead of generic `interrupted`.

### B. Protocol payload contract mismatch

Direct signs:

- Missing proposal text.
- Proposal text mismatch.
- Agreement/proposal calls rejected by orchestrator.

Likely fix category:

- Make protocol payloads machine-generated from orchestrator state where possible.
- Avoid asking LLMs to copy exact proposal strings manually.
- Use structured schemas with explicit fields, and preflight validation before sending protocol RPCs.
- Use proposal IDs/hashes instead of exact text matching if possible.

### C. Phase/state desynchronization

Direct signs:

- `submit_plan` sent while orchestrator expects `opinion` or `agreement_proposal`.
- Fallbacks to discussion after missed endorsement.
- Agents continue with stale planned actions.

Likely fix category:

- Every agent turn should include an authoritative current state block generated by the orchestrator.
- The agent wrapper should discard or reject stale actions before they reach the protocol layer.
- After fallback, pending proposal/endorsement intent should be reset explicitly.
- Consider a simpler linear protocol before allowing general multi-agent negotiation.

### D. Late messages after task termination

Direct signs:

- inactive team/task routing errors.
- messages from agents after the planning task is no longer active.

Likely fix category:

- Late-message absorption with clear non-fatal logging.
- Distinguish root-cause error from expected cleanup noise.
- Preserve the first failure reason in the persisted planning-run JSON.

### E. Missing/empty replies and harness fragility

Direct signs:

- `No reply generated ... skipping`.
- `Message from undefined: undefined`.

Likely fix category:

- Treat empty replies as explicit typed failures with retry/backoff.
- Improve adapter parsing and error classification.
- Avoid letting undefined messages enter protocol logic.

## Ranked likely root causes across all historical runs

1. Provider quota exhaustion for Gemini planner runs — high confidence.
2. Payload-contract mismatch for agreement/proposal/acceptance in Codex runs — high confidence.
3. Agent/orchestrator phase desynchronization after fallback — high confidence.
4. Strict failure propagation turning any single-agent failure into full task interruption — medium-high confidence as an amplifier.
5. Unattended scheduled loop repeating the same failed configuration without backoff — medium confidence.
6. Startup/provisioning/lifecycle race for millisecond-lifetime runs — low-medium confidence.
7. Idle-timeout behavior for long-running interrupted tasks — low-medium confidence from current digest; needs per-task timelines.

## Most useful next technical investigation

If Fausto wants another analysis pass later, the highest-value next step is not more general review. It is classification of all 49 `planning_runs/*.json` files into exact failure buckets by reading their full `transcript`, `members`, `composition`, `plannerAgentId`, timestamps, and first failure event.

Desired output of that pass:

- task ID
- planner/agent composition
- lifetime duration
- first error event
- final persisted status
- category: quota / malformed acceptance / stale submit / fallback exhaustion / inactive team cascade / immediate startup failure / empty reply / idle timeout / unknown
- whether the failure was primary or a downstream cascade

This would turn the current qualitative diagnosis into a counted reliability report.

## Questions to ask Fausto before concluding causality

- Were these runs intended as a scheduled soak/stress test, or were they expected to complete real work?
- Did AgentTalk ever produce a successful complete planning run? If yes, which task/config should be used as the baseline?
- Were Gemini and Codex alternative planner configurations, or did they participate in the same multi-agent workflow?
- Were the runs before or after Milestone 03 failure-propagation behavior?
- Did Fausto already know the Gemini quota was exhausted, or was that accidental?
- Is exact proposal-text matching an intentional protocol invariant, or would a proposal ID/hash be acceptable?
- Does Fausto consider `interrupted` to be a failed run, a correct safety stop, or both?

## Fausto's point of view

Fausto's main interpretation is that AgentTalk's failures are fundamentally about lack of agent adherence to a rigid protocol schema. The intended protocol leaves little or no room for ambiguity, but current LLM agents drift into ambiguity, approximate payloads, stale phase assumptions, and logic loops. This is the core failure mode he wants treated as central, not merely as a superficial schema-validation bug.

Hermes' reaction: this fits the delegated evidence very well and should probably be considered the unifying diagnosis. Provider quota exhaustion explains some runs, but it is incidental infrastructure failure. The deeper product/research problem is that consensus among probabilistic agents cannot rely on natural-language compliance with a brittle exact protocol. If the protocol requires exact proposal identity, exact message type, exact phase awareness, and no stale actions, then those invariants probably need to be enforced or generated by the runtime rather than trusted to the agents.

Useful framing: AgentTalk is not failing because the consensus idea is bad; it is exposing the hard part of the idea. The system needs a translation/guard layer between free-form agent reasoning and the rigid consensus state machine.

Possible design implication:

- Agents should reason in natural language, but protocol events should be selected/generated by a deterministic wrapper when possible.
- Replace exact proposal-text copying with proposal IDs, hashes, or orchestrator-owned proposal objects.
- Make the orchestrator's current phase and allowed actions impossible to ignore, not merely present in the prompt.
- Treat stale or ambiguous agent outputs as recoverable parse/guard events, not as direct protocol messages.
- Reduce loops by making the state machine own turn-taking and by making invalid actions no-ops with diagnostic feedback unless they cross a safety threshold.
- Separate semantic agreement from protocol compliance: first infer whether agents agree, then have the runtime emit the canonical acceptance event.

## Hermes curator note

Hermes did not independently decide the final interpretation beyond checking obvious consistency and preserving delegated findings. The delegated agents strongly agree on the major causes. Fausto's personal point of view now reframes the central root cause as rigid-protocol adherence failure and ambiguity/logic-loop drift by agents.
