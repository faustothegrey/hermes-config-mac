# AgentTalk — Project Overview

**Location:** `~/Software/AgentTalk/`
**Canonical doc:** `AGENT.md` (single source → `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` are symlinks)
**Repo:** Monorepo, TypeScript (Node.js, `tsc -b`, vitest, npm workspaces)
**Purpose:** Multi-agent AI orchestration engine — manages lifecycle, consensus, and execution of LLM-based agents (API-backed and externally-launched MCP-attached).

---

## Architecture (high-level)

```
Node orchestrator → child_process → agent (LLM MCP process)
```

- **Orchestrator** (`apps/orchestrator/`) — Node.js server with Express + WebSockets
- **Web UI** (`apps/web/`) — React dashboard + xterm.js terminal views
- **Registry** (`packages/runtime-core/src/registry/`) — central agent lifecycle, status tracking, conversation/team management
- **TeamCoordinator** (`packages/runtime-core/src/registry/team-coordinator.ts`) — task lifecycle, consensus protocol brain, failure handling
- **InProcessAgentDriver** — drives API-backed agents (prompt→parse→lifecycle loop)
- **MCP transport** — externally-launched agents connect via `agentalk-mcp-client` repo over WebSocket/MCP

**Protocol:** `[AgentTalk]:TYPE:JSON_PAYLOAD` line-based over stdio.

**Agent statuses:** `creating → starting → ready → busy → error → terminated`
**TeamTask statuses:** `idle → planning → in_progress → awaiting_operator → awaiting_confirmation → completed → interrupted`

---

## Monorepo Structure

| Workspace | Description |
|-----------|-------------|
| `apps/orchestrator` | Server: Express, WebSockets, scenario-runner, DiagramTalk bridge |
| `apps/web` | React Web UI (Vite, xterm.js) |
| `packages/runtime-core` | Core: Registry, TeamCoordinator, AgentDriver, protocol logic |
| `packages/contracts` | TypeScript types, response schemas, wire-contract |
| `packages/llm-client` | Zero-dep leaf: `ApiCompleter`, `McpChatCompleter`, `ChatSession` |
| `packages/mcp-transport` | MCP/WebSocket transport layer |
| `packages/mcp-exec-server` | Standalone exec-only attach server for MCP clients |
| `packages/integration-google-drive` | Google Drive integration |
| `packages/observability` | Observability/logging |
| `packages/runtime-scenarios` | Test scenarios |

---

## Milestone History

| MS | Theme | Status |
|----|-------|--------|
| M03 | Agent Failure Propagation | ✅ DONE |
| M05 | MCP Attach Mode (single-agent) | ✅ DONE |
| M06 | Multi-Agent Consensus under Attach Mode | ✅ DONE |
| M07 | Centralized Brain (prompt/parse/state → server-side) | ✅ DONE |
| M08 | Transport / Lifecycle Fault Tolerance (effect-fence, tolerance) | ✅ DONE |
| M09 | MCP Vocabulary Removal (`mcp`→`api`/`mcp` rename) | ✅ DONE (history squashed @ `565ad3d`) |
| **M10** | **Graded, Stateful Protocol Brain** | **✅ ACTIVE** |

---

## Current State — M10 (Graded Protocol Brain)

**Settled decisions (Fausto):**
- **D1:** eject = fail-soft (peer-safe, task freezes)
- **D2:** retry budget N=2 (correct → retry → eject)
- **D3:** v1 = T1+T2 (T3 single-tool + T4 API enforcement deferred → done as separate tasks)

**M10 tasks completed and MERGED:**

| Task | What | Status |
|------|------|--------|
| **T1** | Peer-safe `ejectPlanner(agentId, reason)` — additive non-killing path | ✅ MERGED (`76e5b34`) |
| **T2** | Graded loop: correct → retry N=2 → eject (not dual-kill) | ✅ MERGED (`5fea20c`) |
| **T4** | API-path `tools`+`tool_choice`+strict `enum` enforcement optimization | ✅ MERGED (`d0462b6`) |
| **T4 Live Probe** | Live verification script probing OpenRouter/Google/Nous | ✅ MERGED (`461791d`) |
| **Bridge v3** | DiagramTalk overlay: `endorse` stop + `e4`, eject/correction lanes | ✅ MERGED (`53593a4`) |
| **T3** | Single tool `consensus_respond(action, payload)` | **DEFERRED** (D3) |

**Backlog gate (2026-06-27) — NEXT ITEM SELECTED:**
- ⭐ **Auto-handoff / Baton Conductor** — remove the human as manual turn-scheduler. Sequential conductor script loops `while baton != human && !done`. **Planning delegated to Codex** (Claude near weekly ceiling at ~86%).
- Branch: `master` @ `9d899fd`

---

## Consensus Protocol (simplified)

```
ack → fact_collection → discussion → proposal_pending_endorsement → submittal_pending
```

Each phase has a legal set of `message_type` actions. The brain:
1. Restates the *current* affordance each turn
2. Validates the agent's response against the phase
3. On invalid: correct + retry (bounded N=2)
4. On repeated failure: **eject** the offending agent, **peer-safe** (graceful, no dual-kill)

Introduced T4: API path now sends `tools`+`tool_choice:'required'` with a strict `message_type` enum for first-try compliance. Google rejects the combo (D-T4-2: declared unfit). OpenRouter/gpt-4o-mini FIT.

---

## Key Logbook Entries (LB high-signal)

| ID | What | Relevance |
|----|------|-----------|
| LB-1 | Nous endpoint is a multi-vendor aggregator | `deepseek-v4-flash` 404s |
| LB-6/7 | Gemma/Flash-Lite models hallucinate protocol transitions | Only frontier models work for consensus |
| LB-9 | Worker/consensus tests must mock `execSync` or pollute repo | Backlog gate trap |
| LB-10 | Protocol COMPLIANCE is root issue; tolerance ≠ compliance | Genesis of M10 |
| LB-11 | Token-budget calibration table | Budget tracking |
| LB-12 | `claude.md`/`agents.md` collide with auto-load on case-insensitive FS | Primer naming rule |
| LB-18/19 | DiagramTalk tooling — layout engine grain, see→fix→see loop | Visual reasoning infra |
| LB-20 | M10 Phase-1 design spike findings | Grounds M10 plan |
| LB-22/23/24 | DiagramTalk bridge v1/v2/v3 | Live protocol visualization |
| LB-43/44 | Scrum Master role refinement (3 duties + comms channel) | Defines AI-SM |
| LB-45 | Per-agent lessons-learned files | Hermes file ready, empty |
| LB-46 | Live probe: Google rejects strict tools combo | D-T4-2 declare-unfit |
| LB-47 | Backlog three-layer staleness | Ground-truth discipline |

---

## Provider Ecosystem

| Provider | Status | Notes |
|----------|--------|-------|
| **Google (Gemini)** | Quota-constrained, only 2.5-flash works | 429 across 2.5/2.0 family; rejects strict tools |
| **Nous** | Aggregator, `deepseek-v4-flash` 404s | Pick real catalog id; works with e.g. google/gemini-*-* |
| **OpenRouter** | Paid credit needed for consensus | `:free` tier flaky/429; gpt-4o-mini supports strict tools |
| **Antigravity (agy)** | Local Gemini executor | Native `--continue` for multi-turn; used by harness |
| **Claude Code** | Subscription/OAuth | For delegated tasks (Claude Pro budget) |
| **Codex (OpenAI)** | Subscription | Currently handling baton-conductor planning |

---

## Design Artifacts (canonical doc set)

| File | Role |
|------|------|
| `AGENT.md` | Everything — roles, rules, primer handshake, resource monitoring |
| `design/collaboration-workflow.md` | Working method (Scrum Master duties, adversarial review, 8-step loop) |
| `design/backlog.md` | Parking lot for work not attached to an open epic |
| `design/logbook.md` | Append-only cross-cutting findings (LB-1 through LB-47) |
| `design/lessons/<agent>-lessons.md` | Per-agent self-authored lessons (Claude, Codex, Gemini, **Hermes**) |
| `design/implementer-pitfalls.md` | Reviewer-observed anti-patterns (IP-1 through IP-4) |
| `design/<milestone>-plan.md` | Epic plan + Definition of Done |
| `design/<milestone>-implementation.md` | Status ledger (claim/verdict table) |
| `design/session-primers/<role>-primer.md` | Key-gated session briefs per role |

---

## Key Principles (from `collaboration-workflow.md`)

1. **Adversarial but constructive** — review steels, attacks, strengthens
2. **Verify, don't assert** — run the actual tools, record exact versions/commands/output
3. **Everything in durable docs** — auto-persist is default
4. **Severity- and status-tagged** — `[BLOCK]/[RESOLVE]/[NOTE]`
5. **Decide, park, or open — never silently drop**
6. **Internal consistency maintained** — cross-references fixed in the same pass
7. **Readiness gate precedes code**
8. **Step-by-step with smoke tests** — riskiest unknown first
9. **Ambiguous/non-compliant assignment escalates before execution** — to Scrum Master

---

## Agent Roles (static assignment + dynamic reassignment)

| Role | Default holder | Function |
|------|---------------|----------|
| **Human** | Fausto | Sets scope/goals, final decisions, communicates baton |
| **Scrum Master** | Fausto → **Hermes** (delegate, pending infra) | Authority for role-boundary, go/no-go, backlog, budget |
| **Planner-Reviewer** | Claude or Codex (one at a time) | Proposes designs, critiques, runs verification |
| **Implementer** | Gemini/agy | Writes code, records claims in ledger |
| **Reviewer** | Planner-Reviewer (Claude/Codex) | Verifies by running, fills verdict column, merges |

Note: roles are **dynamic**. The Scrum Master may temporarily reassign any role. Changes are stated explicitly in the relay and ledger (no-shared-memory constraint).
