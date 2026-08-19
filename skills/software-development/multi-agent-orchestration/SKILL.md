---
name: multi-agent-orchestration
title: Multi-agent development session orchestration
description: "Hermes as Scrum Master / orchestrator for multi-agent dev cycles: relay discipline, communication patterns, vocabulary conventions, and the 3-role cycle (plan → implement → review). Also covers Antigravity CLI delegation patterns — readiness, trust prompts, commit misinterpretation, and agentctl operations."
version: 2.0.0
---

# Multi-Agent Development Session Orchestration

When Hermes acts as Scrum Master / orchestrator for a multi-agent dev cycle, the following patterns govern how work flows between agents and how Hermes communicates.

## Session Entry Protocol — MANDATORY (turn 1 of every session)

**This is NOT optional. The user will catch you if you skip it and will tell you to go back and do it properly.** Do not try to shortcut by relying on memory or a prior session's context window — every project is on `git` that may have moved since you last looked.

Before ANY orchestration work begins on a new session, run the full entry sequence in order:

1. **Read the project's canonical instructions** — open AGENT.md, AGENTS.md, or CLAUDE.md (whichever the project uses) and read the FIRST ENTRY POINT section verbatim. **Read via `read_file` on the canonical file path in the repo, NOT via session_search extracts.** A session_search snippet is a fragment that may lack critical context (symlink warnings, vocabulary notes, role maps). Reading the file directly is fast, cheap, and authoritative. **Check for symlinks:** some projects have multiple filenames (AGENTS.md, CLAUDE.md) symlinked to one canonical file. Read the canonical one only; never edit the symlink targets — `read_file` on the canonical path.

2. **Run the primer handshake** — check all role-primer keys (`design/session-primers/*-primer.md`). Report `key: none` (nothing fresh), or consume + STOP if a fresh key is found.

3. **Poll the usage meter** — run `node scripts/usage.mjs` or equivalent project-specific meter. Note the readings in your start-up report.

4. **Skim your own lessons file** — read `design/lessons/<agent>-lessons.md` so past lessons compound (write-only rots).

5. **Read the active epic's implementation ledger** — check what's done, what's next, and verify against git state (ground truth, not just doc claims).

6. **Run the backlog gate (SM duty 1)** — open `backlog.md` and confirm every open item is dispositioned before starting new work.

7. **Sweep git** — `git log --oneline -5` and `git status --short` to confirm working tree state and last-milestone anchor.

8. **Know and declare your role, loudly.** End the ritual by stating your current role explicitly (e.g. "Current role: Scrum Master"). **The SM is a pipeline role, not a meta-layer — you are one of the actors in the project, not the narrator of it.** Declaring your role is the guardrail that prevents you from speaking and acting as an external narrator instead of a participant. When you catch yourself framing the SM role as "above" the project, correct yourself. **The user WILL call you out if you say "I'm not one of the pipeline roles" — the SM is just as much a pipeline role as planner, reviewer, or implementer.**

9. **Read the workflow doc.** The project may have a `design/collaboration-workflow.md` or `workflow.md` that defines the full method — how the 3 roles interact, where gates sit, what artifacts carry decisions. Read it as a numbered step, not an afterthought. The user will ask "did you read the workflow?" if you skip it.

Do NOT skip to task work until this sequence is complete. The user's question "did you do the dev session start rituals?" is a signal you missed one or more steps — stop, go back, and run the full sequence. If the user asks "did you do the rituals?" and you haven't, stop and run them before proceeding.

## Epic Inception Flow (precedes the execution cycle)

Some projects use a formal inception phase before the 3-role execution cycle begins. This involves a **fourth role — the Architect** — who is distinct from both the PO and the Planner.

### Proven flow (as executed 2026-07-01 for M12)

```
  SM (Hermes)
    │  1. Backlog gate: surface next work item, get PO direction
    │  2. Baton to Architect: epic goal + key questions
    ▼
  Architect (Claude)
    │  3. Reads codebase, verifies F1-F5 ground truth
    │  4. Produces design/<epic>-plan.md (technical analysis, tasks, risk, DoD)
    ▼
  PO (Fausto)
    │  5. Answers open questions (recorded as table in the plan doc)
    │  6. Also answers Planner POV findings (folded into same section)
    ▼
  SM batons Planner POV to Architect
    │
    ▼
  Architect (Claude)
    │  7. Updates plan: new filename, PO decisions table, refinements from Planner POV
    │  8. Commits to master
    ▼
  Planner (Codex)
    │  9. Produces design/<epic>-implementation.md (task breakdown + claim/verdict ledger)
    ▼
  Reviewer (Claude — different hat)
    │  10. Gate 1: verifies cited code ranges, examines breakdown
    │  11. Records verdict in ledger, commits
    ▼
  [3-Role Execution Cycle]  Planner→Gate1→Implementer→Gate2→Merge
```

**Key timings from the first run:**
- Architect analysis + plan: ~5 min (2 min reading code, 3 min writing)
- PO Q&A: ~5 min (4 questions one-by-one)
- Architect update: ~3 min
- Planner breakdown: ~2-3 min
- Reviewer gate 1: ~4 min (with detailed code citation verification)

### Architect vs Reviewer independence nuance

When the same agent (Claude) holds both the **Architect** seat (epic inception) and the **Reviewer** seat (gate 1 on the task breakdown), a legitimate independence question arises. Resolution:

- **Reviewing the Planner's breakdown IS in-bounds** because it's a distinct artifact authored by a different agent (Codex). The Reviewer is not self-reviewing.
- **But the Reviewer must NOT re-bless its own architectural findings** as if independently verified. Instead: verify the cited code ranges **fresh** (Reviewer Rule 1: verify by running/reading, not by remembering).
- **What the Reviewer CAN do:** verify Codex's breakdown-level decisions (scope fences, retry budgets, DoD wording), verify code citations against actual source lines, flag gaps in the task spec.
- **What the Reviewer should avoid:** stating "F1-F5 confirmed" or "Architecture is sound" — those are the Architect's findings and should be accepted as given unless new evidence contradicts them.
- If the Reviewer is uncomfortable, they should flag it explicitly (as Claude did) and get PO confirmation before proceeding.

This is not a hard block — it's a professional boundary that the agent should self-monitor.

```
  PO (Fausto)                                    defines epic goal (product direction)
    │
    ▼
  Architect (Claude, default)                    technical analysis: feasibility, resources, risks
    │  produces design/<epic>-plan.md
    │
    ▼
  PO + Architect                                 PO answers open questions, confirms scope decisions
    │
    ▼
  Planner (Codex, default)                       advisory (non-binding) POV on feasibility/risk/effort
    │  — independent second read, not a gate
    │
    ▼
  PO decides                                     epic open/go, or refine/abandon
    │
    ▼
  [3-Role Execution Cycle begins]                planner breakdown → reviewer gate 1 → implement → reviewer gate 2 → merge
```

### Rules

- **Architect is a PO-assigned seat, default Claude.** Only the PO assigns/reassigns it per epic. The Architect must differ from that epic's Planner so the Planner's POV stays an independent second opinion.
- **Architect produces the epic `*-plan.md`** — technical analysis (scope, tasks, risk, resources), not implementation code.
- **PO answers open questions** from the Architect plan. Decisions are recorded in the plan doc as a PO-decisions table.
- **Planner gives an advisory (non-binding) POV** — the second, independent read on feasibility/risk/effort. PO and Architect weigh it but need not follow it.
- **The Architect has no cold-start primer** (it's a PO-assigned, epic-inception seat, not a primer-keyed handshake role).
- **After PO go, the normal 3-role execution cycle takes over.** The Architect's plan becomes the spec for the execution cycle tasks.
- **The Architect role is orthogonal to the SM** (technical authority vs process authority). Both serve the PO.

## The 3-Role Cycle

Canonical pattern for projects with role-primed agents (e.g. AgentTalk's primer protocol):

```
  Hermes (SM/orchestrator)
    ├── agentctl send codex "Plan: <task>"       # planner
    ├── agentctl capture codex                     # read plan
    ├── agentctl send codex "Review: <task>"       # reviewer (gate 1)
    ├── agentctl capture codex                     # read verdict
    ├── agentctl send agy "Implement: <task>"      # implementer
    ├── agentctl capture agy                       # read results
    └── agentctl send codex "Review: <task>"       # reviewer (gate 2)
```

**Workflow rules:**
1. Planner writes plan first. Review does NOT begin until a plan exists.
2. Gate 1 (reviewer approves plan) must pass before implementer starts.
3. Implementer builds on a task branch, commits claim-only (no self-close, no DoD ticking).
4. Gate 2 (reviewer verifies by running) must pass before merge.
5. The same actor may hold multiple roles (resource-scarcity) but keeps each role's gate and discipline separate.
6. Never modify the same file from two agents simultaneously.

## Relay Discipline (critical)

**Do NOT duplicate content in relay messages.** When passing work from one agent to another:

- Point to the artifact that already has the content (task breakdown, plan, ledger, commit)
- Keep your relay message lean — just the baton handoff and what's expected next
- The artifact IS the single source of truth; restating it in the message creates drift risk

**Bad:** "The implementer edited mcp-tools.ts:12-125 to replace the five old planning tool definitions with one consensus_respond tool. They also updated registry.ts:336-464 to add dispatch..."

**Good:** "M11-T1 implementation on branch m11-t1-consensus-respond. tsc clean, 247/247 suite, v6 contract lockstepped. Verify by running it."

The artifact (task breakdown, plan, ledger) contains the detailed scope. The relay message only needs the baton state + current evidence.

### Baton format by receiver temperature

A baton's verbosity depends on whether the receiver is cold or warm:

- **Cold receiver** (first message to a freshly launched tmux session): self-contained — include the full task scope, artifact paths, DoD, and non-goals. The receiver has zero context from this session. Use the copilot advisory as the first line.

- **Warm receiver** (ongoing chat, already familiar with the project): pointers-only — name the branch, the artifact, and what's expected next. The receiver can read the artifacts themselves.

- **Mid-session relay** (same agent, same session, next turn): [Hermes] tag + one-line instruction + artifact pointer.

When in doubt, ask yourself: does this receiver have this session's project context loaded? If no, write self-contained. If yes, write pointed.

## Copilot First-Message Protocol

The first message to any agent MUST carry the copilot advisory:

```
⚠️ I'm copiloting — Fausto is the real gate until explicit handoff.

[Human] <task instruction>
```

This applies to every first message in a session, even if the agent was already running. Prefix operational/process instructions with `[Hermes]` after the initial advisory.

## Origin Tag Protocol

- `[Human]` prefix = binding instruction from the PO (Fausto). Use for task assignments, scope decisions, merge instructions.
- `[Hermes]` prefix = orchestration/coordination from the SM (Hermes). Use for handoffs, status checks, process instructions, relay messages.
- No tag on a first message defaults to `[Human]` context (the copilot advisory establishes this).

After the first message (which carries `[Human]` for the task), subsequent relay and coordination messages use `[Hermes]`:

```
agentctl send codex "[Hermes] Reviewer gate 2 — verify M11-T1 on branch m11-t1-consensus-respond"
```

## Vocabulary Conventions

- Never use the word "spawn" when talking about starting agents — use "launch" instead.
- This applies to all agent messages, session primers, design docs, and workflow artifacts.
- Tool CLI verbs (e.g. `agentctl spawn`) are exempt — the rule applies to how we talk about the action, not the command name.
- Violations should be corrected when seen.

This is a hard naming convention, not a code detail. It goes in the project's AGENT.md or equivalent convention doc.

### Project doc & vocabulary renames

When a project's task/milestone naming convention or vocabulary changes (e.g. `MT1` → `M11-T3`, or banning "spawn"), apply the rename consistently using the workflow in `references/project-doc-rename.md`. Key rules: classify references as active vs historical before editing, get user buy-in before acting, and never rewrite git history or archived docs.

## Polling, Not Waiting

Do NOT wait passively for agent output. The pattern is:

1. Send the instruction via `agentctl send`
2. Wait an appropriate amount of time (5-10s for simple, 30-60s for planning, 60-120s for implementation)
3. Poll with `agentctl capture` to check progress
4. If still working, wait and poll again
5. Report findings as soon as they're ready — don't accumulate multiple results before reporting

The user sees what you see. Report substance (task, findings, review, decisions), not process details (CLI commands, tmux sessions, tool internals).

## Telemetry on Handoff

When passing the baton from one agent to another, include a compact evidence summary:
- Build status (tsc clean / failing)
- Test results (X/Y passing)
- Contract/hash status (for wire-contract changes)
- Pollution check (branch-only / stray files)

This lets the receiving agent (or the user) pick up without re-running the full evidence chain.

## Role Assignment Degradation Handling

When the default role assignment is broken (reviewer out of budget, planner unavailable), the PO may override the default map. Two patterns have emerged:

### PO-override role reassignment (method 1)

The PO explicitly reassigns a role to a different agent. This is a **PO-level act** (not SM's) — the SM facilitates but does not reshuffle the role map. The PO says e.g. "I overrule Codex's reviewer assignment and set you (Hermes) as reviewer on this one." The SM accepts and acts as the appointed reviewer, running the full gate evidence chain (tsc, test suite, diff, pollution, live observation) and issuing a VERIFIED/REFUTED verdict in the ledger.

**When this applies:** the default agent's CLI is unavailable (e.g. out of 5h/window quota, or technical issue). The PO reassigns the seat to whoever can actually run the gate. The reassignment is **ephemeral per task** — the next task reverts to default roles unless stated otherwise.

**Key nuance (learned from M11-T3 gate 2 re-review):** a single agent may exhaust BOTH its 5h window AND its weekly quota, AND its default reviewer may still be on pre-reset budget. In that case there are TWO unavailable reviewers (Codex at 5h 100%, Claude pre-reset at 92% weekly) — neither CLI is available. The PO then reassigns to the only agent with available credits who can run the gate (Hermes). **This is not a workflow violation — it is the PO exercising its apex authority when both default and fallback reviewers are unavailable.** The same agent may hold SM + Reviewer together for one task, declared loudly.

**Recording requirement:** the SM must document the reason in a durable artifact (the ledger or logbook) — e.g. "Codex at 5h 100%, Claude pre-reset at 92% weekly — PO reassigned reviewer to Hermes for M11-T3 gate 2 re-review."

### Resource-scarcity fallback (method 2)

When multiple agents share a provider (e.g. Claude and Codex both use OpenAI's budget) and one is exhausted, one agent may hold several roles — typically planner AND reviewer. The no-self-review default is **consciously suspended** for this window. The actor must:
- Declare both roles loudly on startup
- Keep each role's gate and discipline separate
- The assignment auto-lapses when the exhausted agent's credits return

### When to use which

- **Resource-scarcity fallback** — use when the same provider budget limits a distinct agent but their CLI is still available. Suitable for same-provider pairings.
- **PO-override reassignment** — use when the default agent's CLI is unavailable (out of 5h/window quota) or the PO wants a different evaluator. The reassigned agent must be capable of running the full gate independently.

### Important: merger role constraints

Even with these overrides, the **core workflow gates remain intact**:
- Gate 1 still precedes gate 2 (plan approved before code)
- Gate 2 requires verify-by-running (not diff-reading)
- Merge stays human-gated unless PO explicitly delegates it
- The reviewer (whoever holds the seat) records evidence in the ledger

## Handling REFUTED Verdicts

**At gate 1 (plan review):**
- Read the blocker list carefully. The reviewer identifies specific out-of-scope surfaces, missing DoD items, or unsupported claims.
- Feed back to the planner with the exact required fix — don't just forward the verdict. Summarise what must change and (if the reviewer provided one) include the recommended approach.
- After the planner corrects the breakdown, resubmit for re-review at gate 1.
- Fixes are usually narrow: remove an unauthorised range, tighten wording, add a missing cleanup path.

**At gate 2 (implementation review):**
- Three blocker classes may appear:
  1. **Scope creep** — the implementer changed something outside the approved edit surfaces. This is the most common blocker. The fix is reverting the out-of-scope change and re-applying only the in-scope work.
  2. **Deterministic failures** — test fails, whitespace, lint, typecheck. Straightforward fix: patch and re-run.
  3. **Missing evidence** — the plan required live observation that wasn't performed. Options: (a) run the live gate, or (b) request PO deferral if the observation is infeasible (quota, unavailable provider).
- Triaging: separate blocker (1) from blockers (2) and (3). Scope creep goes back to the implementer; whitespace/lint can be fixed directly; live observation requires a decision.
- A REFUTED at gate 2 does NOT mean the whole task is wrong — it means the branch isn't ready for merge. The reviewer will note what IS verified (e.g. "D3 VERIFIED ✅, D5 REFUTED ❌") — use that to scope the rework.

**General principles:**
- The same agent wearing both hats will still catch its own scope creep — trust the gate, don't override it.
- Every REFUTED identifies a concrete, preventable issue in the next cycle.
- Do not treat a REFUTED as a personal failure or a system bug — it is the gate doing its job.

## Session Close Protocol — MANDATORY (before killing agent sessions)

**This is NOT optional.** Killing agents without the session close protocol is a process violation. Each agent owns:
- Its own lessons file (`design/lessons/<agent>-lessons.md` — self-authored, per-agent)
- Its own private key store (`consumed[]` — tracking which primer keys have been consumed)

These cannot be written after the tmux session is terminated. The lessons files are per-agent self-authored — the SM cannot write them for another agent.

### Sequence

1. **Send each active agent a session-close baton:**
   ```
   agentctl send codex "Session close — write your lessons to design/lessons/codex-lessons.md, update your private key store (consumed list), and confirm when done."
   agentctl send claude "Session close — write your lessons to design/lessons/claude-lessons.md, update your private key store (consumed list), and confirm when done."
   agentctl send agy "Session close — write your lessons to design/lessons/antigravity-lessons.md, update your private key store, and confirm when done."
   ```

2. **Wait and capture each agent's confirmation:**
   ```
   sleep 15
   agentctl capture codex
   agentctl capture claude
   agentctl capture agy
   ```
   Look for explicit confirmation ("done", "lessons written", "key store updated", "handing back the baton"). Re-poll after 15-30s if still working.

3. **SM writes own artifacts:**
   - Append entry to `design/lessons/hermes-lessons.md` (session summary, what worked, what didn't)
   - Update all role-primers (`planner-primer.md`, `reviewer-primer.md`, `implementer-primer.md`) to `key: none` with updated body text reflecting this session's state
   - If M12/etc. active, primer body describes where the epic is and what's next
   - Stage and commit all session-close changes

4. **Kill only after all agents confirm:**
   ```
   agentctl kill codex && agentctl kill claude && agentctl kill agy
   ```

5. **Final push** to origin — all session-close commits (primers, lessons, ledger updates, any outstanding changes) reach master before the window closes.

6. **Verify:** run `git status --short --branch` — should show clean master, no dirty files.

### Timing

- Each agent gets ~15s after the close baton to respond
- If an agent was deeply engaged in complex work, it may need 30-60s to process the close instruction and write its lessons
- Re-poll rather than guessing — look for a completion summary, not activity lines
- If an agent doesn't confirm after 2 re-polls, log it and kill anyway — better to lose one agent's lessons than hold the session open indefinitely

### Real failure (2026-07-01)

I terminated all three agents (Codex, Claude, agy) with `agentctl kill` without giving them a session close baton. Claude had been acting as Architect, Reviewer, and had deep insights about the M12-T4 blocker. Codex had just produced the PF/T4 re-plan. Both had uncommitted lessons, unwritten key store entries, and unrecorded insights. The lessons files are per-agent self-authored — I cannot write them for another agent. The data is permanently lost. On the next cold start, these agents will find primers with keys they've already consumed, triggering false fresh-primer stops. This exact sequence is designed to prevent that.

## Multi-Agent Timings

| Step | Wait before capture | Typical duration |
|------|-------------------|------------------|
| Simple query/confirmation | 5-10s | 3-5s API |
| File read + analysis | 15-25s | 10-20s API |
| Code search + investigation | 20-40s | 15-30s API |
| Planning a task breakdown | 30-90s | 45-120s API |
| Complex implementation | 60-180s | 2-5min API |
| Full test suite | 60-120s | 5-15s (fast suites) |

## Antigravity CLI Delegation

Use this section when the user asks Hermes to delegate work to the Antigravity CLI (`agy`), or when comparing Antigravity with Claude Code / Codex / OpenCode as delegation lanes.

### When to use Antigravity vs Claude Code

Use Antigravity when: the user explicitly asks for it, you want a second independent external-agent lane alongside Claude Code, or the task is exploratory/project-assessment where Hermes should act as curator. Prefer Claude Code when the built-in `claude_code` tool integration, JSON metadata, or max-turn controls are needed.

For contentious assessments, run both agents as separate independent lanes and reconcile only concrete evidence and clear disagreements.

### Core command — agentctl interface (preferred)

```bash
agentctl spawn agy                          # start
agentctl send agy "<bounded prompt>"         # send task
sleep 10                                    # wait for generation
agentctl capture agy                         # read output
agentctl kill agy                            # stop
```

`agentctl send` handles Escape (to exit TUI), sleep, and Enter automatically. Use `agentctl spawn agy --workdir <path>` to set the working directory.

### Direct agy CLI (fallback)

Use only for quick, bounded one-shots where agentctl overhead isn't worth it:
```bash
agy --print '<bounded prompt>' --print-timeout 5m
agy --print '<bounded prompt>' --print-timeout 10m --dangerously-skip-permissions
```

### Readiness check (before long delegation)

```bash
# Preferred — agentctl health check
agentctl health --json
# Look for anomaly_count == 0 and agy count >= 1 with orphan_count == 0

# Fallback — direct agy ping
/Users/fausto/.local/bin/agy --print 'Readiness ping: reply with exactly READY and nothing else.' --print-timeout 30s
```

Treat visible `READY` in the output as usable. If it prompts for auth or times out, report Antigravity unavailable and try another delegate or stop.

### Prompt shape

Give Antigravity a self-contained, bounded prompt. Include: repository path, exact task and non-goals, whether it may edit files, expected output format, evidence requirements, and a time/turn boundary. Template:

```text
You are an independent agent lane working for Hermes.

Task: <specific task>
Target path: <absolute path>
Mode: <read-only assessment | edits allowed within scope>
Non-goals: <what not to touch>

Return a concise structured report:
- Summary
- Evidence: file paths and commands inspected
- Findings, with confidence
- Suggested next actions
- If edits were made: exact files changed and verification commands/results

Do not ask follow-up questions. If context is missing, state assumptions and proceed conservatively.
```

### Key Antigravity-specific pitfalls

**Trust prompt blocks first spawn.** When spawning into a directory Antigravity hasn't accessed before, it shows a "Do you trust this folder?" TUI selection menu (↑/↓ Navigate · enter Confirm). `agentctl send` can't handle TUI menus. Fix:

```bash
agentctl spawn agy --workdir ~/Software/Project
sleep 8
tmux send-keys -t <session_name> Enter        # accept trust (raw tmux)
sleep 10
agentctl send agy "<real prompt>"              # now send the real message
```

After trust is accepted once for a directory, subsequent spawns skip the prompt.

**agy may leave implementation uncommitted, citing phantom "rule restrictions."** After completing work, agy sometimes says "I have left the changes uncommitted as per your rule restrictions" even when no such restriction was set. Explicitly state "commit your changes after each completed step" in the initial instruction. If discovered after the fact:

```bash
agentctl send agy "Commit all your changes on the branch with a descriptive message."
sleep 30 && agentctl capture agy
```

**agy orphans (PPID=1) can survive terminal close.** If agy was started in a bare iTerm window and the window was closed, the process becomes orphaned and may consume 30-60% CPU. `agentctl health --json` detects these via `orphan_count`.

### Copilot first-message protocol (Antigravity)

The first message to agy must carry the copilot advisory:

```bash
agentctl send agy "⚠️ I'm copiloting — Fausto is the real gate until explicit handoff.

[Human] task: <instruction>"
```

Use `[Hermes]` tag for subsequent coordination messages.

### Origin tag protocol

- `[Human]` — binding instruction from Fausto. Treat as if spoken directly.
- `[Hermes]` — orchestration or coordination from the orchestrator. Informative.
- No tag — direct human terminal input (binding).

**Related references:**
- `references/antigravity-fausto-antigravity-cli-2026-06-16.md` — session-specific verification and local command notes.
- `references/antigravity-fausto-antigravity-readiness-and-digest-fallback-2026-06-16.md` — readiness ping, unavailable-candidate fallback, digest-only retry pattern.
- `references/antigravity-fausto-agenttalk-spec-delegation-2026-06-16.md` — successful pattern for asking Antigravity to turn prior critique into a detailed architecture/spec proposal.
- `references/antigravity-native-antigravity-tmux-tool-2026-06-16.md` — implementation pattern and verification notes for the native Hermes `antigravity` tmux tool.

## Pitfalls

- **Do NOT restate the task breakdown in relay messages.** Point to the file. Keeping the breakdown only in the artifact prevents drift and keeps messages readable.
- **Codex sometimes blocks at the `›` prompt** and ignores long messages. Fix: send a very short command (2-3 words) to wake it up, then the real instruction.
- **agy trust prompt and other Antigravity quirks** — see the [Antigravity CLI Delegation](#antigravity-cli-delegation) section above for full detail on trust prompt handling, commit misinterpretation, orphan detection, readiness checks, and copilot protocol.
- **Between send and capture, the agent may still be "Generating..."** — wait the appropriate time for the task type before capturing.
- **The copilot advisory goes on the FIRST message only.** Subsequent messages in the same session use `[Hermes]` or `[Human]` as appropriate.
- **Keep responses substance-only.** The user does not want to hear about tmux, agentctl commands, or how you orchestrated — only the task outcome: what was found, decided, built, or reviewed.
- **agentctl send with backtick-heavy messages can break.** When using `agentctl send <agent> "$(cat /tmp/file)"`, bash interprets backticks (`` ` ``) inside the file content as command substitution, causing bash errors. Two solutions: (a) avoid backticks in the file content by using plain apostrophes or `code` formatting without backticks; (b) use a heredoc (`agentctl send <agent> << 'EOF'`) instead of `$(cat ...)`. Prefer sending the file content via a temp file with minimal special characters, or pipe through `tee`.

## References

- `references/gate2-refuted-case-m11t3.md` — concrete case study of a REFUTED gate 2 verdict with three blocker classes (scope creep, whitespace, missing live observation) and what was VERIFIED despite the rejection.
- `references/architect-reviewer-independence-case.md` — the full case study from M12 when the same agent (Claude) held both Architect and Reviewer seats on the same epic. When to flag, how to resolve.
- `references/cross-provider-consensus-reframing.md` — the insight that replaced the old "Nous + Google" assumption with the simpler "use existing MCP agents" approach for mixed-provider consensus.
- `references/codex-bridge-websocket-blocker.md` — the Codex dual-WebSocket connection conflict discovered during M12-T4 live run.
- `references/antigravity-fausto-antigravity-cli-2026-06-16.md` — antigravity CLI session-specific verification.
- `references/antigravity-fausto-antigravity-readiness-and-digest-fallback-2026-06-16.md` — readiness ping and fallback patterns.
- `references/antigravity-fausto-agenttalk-spec-delegation-2026-06-16.md` — successful spec-delegation to antigravity.
- `references/antigravity-native-antigravity-tmux-tool-2026-06-16.md` — native Hermes antigravity tmux tool.

> **Package integrity note:** The `antigravity-cli` skill has been absorbed into this umbrella. Its content is now in the "Antigravity CLI Delegation" section above. Reference files are preserved in `references/antigravity-*.md`. The original skill directory has been moved to `.archive/`.
