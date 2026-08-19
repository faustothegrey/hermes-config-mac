# AgentTalk

Project path: `/Users/fausto/Software/AgentTalk`
Design docs (canonical): `design/` in the project repo

## Design documents

The canonical design chain lives in the repo under `design/`. Vault copies below are kept for Obsidian search only; if they differ, the repo is authoritative.

| Round | Document | Repo (canonical) | Vault (search copy) |
|-------|----------|-------------------|---------------------|
| 1 | Agy's revised spec | `design/agy-revised-protocol-spec.md` | [[Antigravity AgentTalk Revised Protocol Spec 2026-06-16]] |
| 2 | Claude's critique | `design/claude-critique-of-agy-spec.md` | [[Claude Critique of Antigravity AgentTalk Revised Protocol Spec 2026-06-16]] |
| 3 | Agy's reply | `design/agy-reply-to-claude-critique.md` | [[Antigravity Reply to Claude Critique 2026-06-17]] |
| 4 | Claude's review of reply | `design/claude-review-of-agy-reply.md` | [[Claude Review of Antigravity Reply 2026-06-17]] |

**Convergence table** (from Claude's review, round 4): most items settled. Remaining gaps: dynamic-schema re-scoping (as prompt optimization, not correctness mechanism), serialized transition queue, `versionToken` restart semantics, pre-DISCUSSION phase failure handling, and Milestone 03 behavior-change sign-offs.

## Assessments and synthesis (vault — canonical)

- [[Claude AgentTalk Assessment 2026-06-16]]
- [[Antigravity AgentTalk Assessment 2026-06-16]]
- [[AgentTalk Comparative Synthesis 2026-06-16]]
- [[Claude AgentTalk Historical Runs Failure Analysis 2026-06-16]]
- [[Antigravity AgentTalk Historical Runs Failure Analysis 2026-06-16]]
- [[AgentTalk Historical Runs Failure Synthesis 2026-06-16]]
- [[AgentTalk Protocol-Adherence Thesis Discussion 2026-06-16]]
- [[Projects]]

## Current design stance / resume point

The two-lane review process (Agy ↔ Claude, four rounds) has converged. Adopt the control-plane spine: proposal IDs, unified PlanningSessionState, single-writer floor lock, deterministic version-token fencing, unified budgets, failure taxonomy, replay harness. Dynamic per-turn schemas are re-scoped as prompt optimization (not correctness). Deferred: cross-model failover, N-planner scaling. Three items still need resolution before implementation: serialized transition queue, versionToken restart/persistence, pre-DISCUSSION phase failure handling. Three behavior changes (hard cutover, submit_plan override removal, infra-fault pause/backoff) need Fausto's explicit Milestone 03 sign-off.

## Identity

AgentTalk is a local-first multi-agent orchestration/control-plane project. Its main purpose is to coordinate multiple CLI agents such as Claude, Gemini, and Codex so they can investigate a task, discuss, reach consensus, submit an implementation-ready plan, and then delegate execution reliably.

The project is ambitious because its value depends on consensus/protocol reliability rather than a simple app feature. It is about making agent collaboration safer and more deterministic before code is changed.

## Why it matters in the portfolio

AgentTalk appears to be the strategic core of Fausto's emerging local AI infrastructure stack:

- [[WebElementChat]] can provide browser/DOM-selected context.
- AgentTalk can provide the multi-agent reasoning and consensus runtime.
- scripts-ai can provide quota/usage awareness.
- [[ScienceClick2]] provides a reusable skills/instructions sync pattern that AgentTalk could adopt.
- [[CasaSpese]] remains the mature real-world app/value anchor, but AgentTalk/WebElementChat/scripts-ai form the strongest AI-infrastructure cluster.

## Architecture snapshot

Main areas identified by delegated assessments:

- `apps/orchestrator`: Express/WebSocket backend, agent/team management, scenario/runtime control.
- `apps/web`: React/xterm dashboard for real-time output, planning status, usage, scheduler/drive views.
- `packages/runtime-core`: core engine, registry, team coordinator, conversation coordinator, process adapter/parser, provider runtime, executor runtime.
- `packages/contracts`: shared types/protocol payloads.
- `packages/runtime-scenarios`: declarative scenario runner/scheduler.
- `packages/observability`: session recording/playback and usage history.
- `packages/integration-google-drive`: Google Drive resource integration.
- `scripts/llm-agent.mjs`: agent-side harness for local CLI providers.

## Protocol / reliability themes

Important concepts from assessments:

- Fact collection → discussion/opinion → proposal → endorsement → submit plan → implementation/delegation.
- Phase-ranked planning state machine.
- Structured JSON response envelope for agent replies.
- Regression/violation handling.
- Failure propagation on agent error/idle timeout.
- Watchdogs and timeouts for long agent workflows.
- Plan-quality gate intended to reject vague/exploratory plans.
- Read-only planning agents plus worker execution after consensus.

## Strengths

- Clear and ambitious purpose: reliable multi-agent consensus before implementation.
- Strong local-first/control-plane alignment with Fausto's other projects.
- Formal planning protocol and explicit Milestone 03 behavior rules.
- Multiple tests around orchestrator/team behavior.
- Scenario and recording/playback infrastructure for observability.
- Potentially powerful bridge between WebElementChat's context capture and local agent execution.

## Main risks / next-work themes

- Protocol/state complexity is high; `team-coordinator.ts` is a likely refactor target but should be changed only with regression tests.
- Runtime boundary enforcement is not yet as strong as the prompt-level rules; worktree/sandbox behavior should be verified by code before trusting autonomous implementation.
- Process spawning and permissive agent modes need careful local-only assumptions; no hosted/shared use without auth and sandboxing.
- Live state appears substantially in-memory; crash/restart recovery may be a medium-term reliability issue.
- UI surface appears less tested than backend orchestration.
- Secrets/transcripts/planning runs are local and ignored, but still sensitive local artifacts.
- Historical run artifacts in `transcripts/` and `planning_runs/` show 49/49 persisted planning tasks with `status=interrupted`; delegated failure analysis points to Gemini quota exhaustion plus Codex protocol/payload/state desynchronization as the dominant causes. See [[AgentTalk Historical Runs Failure Synthesis 2026-06-16]].
- Fausto's central diagnosis of the historical failures: the main issue is lack of agent adherence to a rigid protocol schema that leaves no room for ambiguity; agents drift into ambiguous payloads, stale phase assumptions, and logic loops. Hermes' view is that this is likely the unifying product/research problem, while provider quota exhaustion is a separate infrastructure failure.

## Verified local facts

- `.git` exists at the AgentTalk root.
- `AGENTS.md` says Milestone 03 is reached and requires preserving behavior, explicit confirmation for behavior changes, minimal diffs, and regression tests.
- `.gitignore` includes `transcripts/`, `planning_runs/`, `recordings/`, `persistence/`, `google-oauth-client.json`, `google-drive-token.json`, and `credentials.json`.
- `credentials.json` exists at root; contents were not inspected or stored.
- `apps/orchestrator/src/__tests__/` contains 25 test files.
