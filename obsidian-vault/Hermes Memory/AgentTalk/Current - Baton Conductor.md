# AgentTalk — Current Active: Baton Conductor (Auto-Handoff)

> **Status:** PLANNING — Codex is writing the `*-plan.md`
> **Selected at:** Backlog gate 2026-06-27 (Fausto)
> **Repo head:** `master` @ `9d899fd` — `primer(planner-reviewer): hand to Codex — PLAN the baton conductor`
> **Budget:** Codex ~60% weekly; Claude ~86% (batoned-out by headroom)

---

## What It Is

The baton conductor removes the **human as manual turn-scheduler** — the single biggest operational bottleneck in the current workflow. Right now, after an agent finishes its work, Fausto manually reads the artifacts and decides who goes next. The conductor automates this sequential loop.

**Design seed** (from `design/backlog.md` ⭐ SELECTED NEXT):

1. **3-state baton** at the top of `implementation.md`:
   - `baton ∈ {impl, review, human}`
   - One-line reason per state
   - Lifecycle: impl does the first non-VERIFIED row → commit claim-only → `baton:review`; reviewer runs it, fills verdicts → all VERIFIED → merge + next task → `baton:impl`, else REFUTED → `baton:impl`, else scope/decision → `baton:human`

2. **Sequential conductor script** that loops:
   ```
   while baton != human && !done:
       invoke (headless) the agent named by the baton
       re-read baton
   ```
   - Human is invoked **only on `baton:human`**

3. **Guardrails:**
   - `max_rounds` per task (cap REFUTED↔fix ping-pong)
   - Keep the reviewer's **run-it verification** (the circuit breaker — non-negotiable)
   - Single human escape hatch
   - Log per-round token cost
   - **Sequential, NOT parallel worktrees** — Fausto is explicitly *not* ready for parallel agent orchestration

4. **Protocol documentation:** The baton protocol must be documented into `design/collaboration-workflow.md` before (or as part of) building the conductor.

---

## Why This Matters for Me (Hermes)

The baton conductor is the **sequential turn scheduler** that removes human relay for the normal flow.
Agent Bus (port 9901) is the **sideband channel** for SM-to-agent communication.
Together they make a delegated AI-SM operationally complete:
- `baton:` field = source of truth for "who's up next"
- Conductor script = replaces the human relay for the normal loop
- `baton:human` = escape hatch where Fausto still needs to be in the loop
- Agent Bus = SM's channel to intervene, nudge agents, or handle exceptions

---

## What Happens Next

1. **Codex writes the `*-plan.md`** (design + DoD) — currently in progress
2. **Fausto reviews and approves** the plan
3. **Implementation** by the implementer (Gemini/agy — when budget allows)
4. **Document baton protocol** into `collaboration-workflow.md`
5. **Merge + deploy**
6. **Fausto delegates SM to Hermes** (in theory — this is an open sequence; Fausto decides when)

---

## Design Constraints (from Fausto)

- Sequential only — no parallel worktrees
- Reviewer's **verify-by-running** is the circuit breaker
- `baton:human` on: scope question, decision needed, or something goes wrong
- The conductor script must be simple, deterministic, observable
- Token cost logging per round for budget tracking
- Resolves workflow open-question #2: "relay overhead — feature or bottleneck?"
