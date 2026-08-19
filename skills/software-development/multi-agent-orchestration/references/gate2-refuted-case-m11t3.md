# Gate 2 REFUTED Case Study — M11-T3 (Turn-budget / Referee)

**Date:** 2026-07-01
**Task:** M11-T3 — Add MAX_DISCUSSION_TURNS = 6 referee to bound discussion loops
**Branch:** `m11-t3-turn-budget-referee`

## The verdict

Codex (reviewer, same actor holding both planner+reviewer under resource-scarcity fallback) issued REFUTED ❌ at gate 2 with three blockers:

### Blocker 1: Scope creep — terminal helper refactored outside approved surface

**What happened:** The approved edit surface allowed cleanup in `team-coordinator.ts:1847-1860` and permitted a small budget-specific wrapper. The implementer refactored `interruptPlanningForMissingEvents(...)` into a shared `interruptPlanningTerminal(...)` and added a `conversation_end` protocol event to every planner for ALL missing-event interruptions — not only the new referee path. Master sent only `message_received` before requesting shutdown; the branch added `conversation_end`.

**Root cause:** The implementer generalised a helper beyond its approved scope ("make it reusable" vs "add only the referee path").

**Fix:** The shared refactor had to be undone — either revert to the original `interruptPlanningForMissingEvents` and add a separate referee terminal path, or accept the refactor only for the new referee path without changing the existing path.

### Blocker 2: Whitespace

**What happened:** `git diff --check` reported trailing whitespace in the new test file `team-protocol-referee.test.ts`.

**Fix:** Remove trailing whitespace and re-run the gate.

### Blocker 3: Missing live observation

**What happened:** The M11-T3 plan §3 DoD requires: "Required live observation is recorded in the ledger with provider, command, final status, and budget reading." The branch had deterministic tests and a successful suite, but no live observation was performed or recorded.

**Options:**
- Run a live referee observation with an available provider (requires a `test-live-gate.mjs` sibling or the existing harness)
- Request PO deferral with an explicit reopen condition (permitted by the plan: "If no provider/quota is available, stop and request reviewer/PO deferral instead of closing M11-T3")

### What was VERIFIED

Not everything was wrong. The reviewer noted:
- D3: VERIFIED ✅ — happy-path mocked MCP consensus stays green, reaches `submit_plan` before budget
- D1, D2, D4: PARTIAL ⚠️ — deterministic tests prove the 6/6 boundary and cleanup code exists, but coverage gaps need filling

## Lessons for future cycles

1. **A shared "improvement" that touches existing behavior outside the approved edit surface is still a scope creep.** Even if the refactoring makes the code cleaner, it changes behavior that previously passed review.
2. **Always run `git diff --check` before claiming done.** Whitespace is a mechanical gate that should never fail.
3. **Live observation requirements are easy to forget.** The implementer focused on deterministic tests and missed the plan's explicit live-run requirement. The baton from SM should call it out separately from the DoD rows.
4. **A single-agent dual-hat (planner+reviewer) still catches its own scope creep.** The adversarial process works when each gate is enforced independently.