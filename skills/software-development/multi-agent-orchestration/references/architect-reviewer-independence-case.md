# Architect vs Reviewer Independence — Concrete Case (M12, 2026-07-01)

## What happened

Claude held the **Architect** seat for M12 (cross-provider consensus epic). It produced `design/milestone12-cross-provider-consensus-plan.md` with:
- Ground-truth architecture findings (F1-F5)
- Task breakdown with C1 discovery
- Risk assessment
- Open questions for the PO

After PO decisions and the Planner's (Codex) advisory POV, Codex produced a task breakdown at `design/milestone12-cross-provider-consensus-implementation.md`. The Reviewer for gate 1, by default role assignment, was **Claude** — the same agent who held the Architect seat.

## The concern Claude raised

> "Reviewing Codex's breakdown-level decisions is in-bounds; I should not re-bless my own architectural findings as if independently verified — I'll verify the cited code ranges fresh instead (which is Reviewer Rule 1 anyway)."

Claude asked the SM whether to proceed or flag the independence issue.

## Resolution

The PO confirmed: proceed. The reasoning:

1. **Reviewing the Planner's breakdown IS in-bounds** — it's a distinct artifact authored by Codex, not Claude. No self-review.
2. **But fresh verification of code citations is required** — the Reviewer must independently read the cited source ranges, not rely on memory from the Architect phase.
3. **The Reviewer should focus on:** scope fences, retry budgets, DoD wording, code citation accuracy, gaps in the spec — things the Planner produced.
4. **The Reviewer should explicitly NOT state:** "Architecture confirmed" or "F1-F5 verified" — those are the Architect's findings.
5. **If uncertain, flag it.** Claude asked — the right move. The PO confirmed, and gate 1 proceeded.

## Lesson

When the same agent holds both Architect and Reviewer on the same epic:
- Gate 1 on the Planner's breakdown is fine (distinct author, distinct artifact)
- Apply fresh code-reading discipline (no reliance on Architect-phase memory)
- If in doubt, ask the PO for explicit confirmation before proceeding
- The independence guard is behavioral, not structural — the agent self-monitors

## Full commit trail

- `edc6a3b` — Architect plan + PO decisions
- `c009072` — Planner task breakdown
- `ab93517` — Reviewer gate 1: VERIFIED with F-G1-1 clarification