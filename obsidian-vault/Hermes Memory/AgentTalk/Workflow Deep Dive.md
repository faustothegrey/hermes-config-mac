# AgentTalk — Workflow Deep-Dive (Understanding the Loop)

## The 8-Step Collaboration Loop

From `collaboration-workflow.md` §4 — the boot sequence for any macro unit of work:

```
DRAFT (Author)
  → REVIEW (Reviewer)
  → VERIFY (Reviewer runs tools, reproduces findings)
  → CONSOLIDATE CAVEATS (tag BLOCK/RESOLVE/NOTE)
  → REVISE (Author answers point-by-point in docs)
  → RE-ASSESS (Reviewer maps each caveat → RESOLVED/OPEN)
  → READINESS GATE → IMPLEMENT (phased, smoke-tested)
```

**After implementation (M07+ refinement):**
- **Implementer** records each phase outcome as a claim row in `<milestone>-implementation.md`
- **Reviewer** runs it → fills verdict column → `VERIFIED ✅ / REFUTED ❌ / PARTIAL ⚠️ / BLOCKED ⛔`
- Tasks are on individual branches (`<epic>-t<N>-<slug>`)
- **Only the reviewer merges** — and only when all rows are VERIFIED

---

## The Per-Epic Document Pair

Every milestone/epic gets two docs:

| Doc | Owner | Volatility | Content |
|-----|-------|------------|---------|
| `<name>-plan.md` | Architect | Stable, changes only on design change | Scope, decisions, acceptance criteria, **Definition of DoD** |
| `<name>-implementation.md` | Implementer + Reviewer | Volatile, status ledger | Claim/verdict table + append-only log |

**Key structural device — the Claim/Verdict table:**
```
| DoD item | Implementer claim | Reviewer verdict | Evidence |
|----------|-------------------|------------------|----------|
| <item>   | done / wip / —    | VERIFIED ✅ /    | command + output / file:line |
|          |                    | REFUTED ❌ /     |           |
|          |                    | PARTIAL ⚠️ /    |           |
|          |                    | BLOCKED ⛔       |           |
```

Implementer fills claim → Reviewer fills verdict **only after running it** with evidence. Two columns coexist until the reviewer flips — prevents silent overwrite.

---

## The Primer Handshake (AGENT.md FIRST ENTRY POINT)

Every session, turn 1:

```
1. Identify your role → open your eligible primer (`<role>-primer.md`)
2. Read the `key:` in the primer header
3. Read your private key store (`consumed: [...]`)
4. If key ∉ consumed → primer is fresh → report and STOP (cold start)
5. If key ∈ consumed → benign re-read → proceed normally
6. Poll `node scripts/usage.mjs` for budget
7. Skim your lessons file (`design/lessons/<agent>-lessons.md`)
8. Declare your role loudly
```

**Key mechanism:** Shared primer holds a key; each agent has its own private `consumed` set. Fresh key = new assignment. Consumed key = benign re-read. This prevents re-triggering the cold-start stop on restart.

---

## Impediments & Deviations (spaces in the ledger)

Since M08, the `implementation.md` also hosts two institutional spaces:

**Impediments** — *the world got in the way* (external blockers, no code fault):
```
| ID | What blocked | Blocks (DoD row) | Status | Unblock condition |
```

**Implementer Notes & Deviations** — *the doer's voice*:
```
| ID | Type (deviation/opinion/question) | Re: (DoD row) | What & why | Reviewer disposition |
```

**Symmetry rule:** Every REFUTED gets an implementer answer; every deviation/opinion gets a reviewer disposition. Nothing open vanishes silently.

---

## The Backlog Gate (workflow §3b)

Before opening ANY new macro unit (epic/task), the architect/reviewer reviews `backlog.md` and dispositions every open item in the same pass: **promote, absorb, drop, defer, or done**. A new unit doesn't start until its backlog pass is done. The SM **convenes** the gate and sets priority; the architect/reviewer does the technical disposition.

---

## BLOCKED ⛔ vs REFUTED ❌ — Critical Distinction

| Verdict | Meaning | Can it be deferred? |
|---------|---------|---------------------|
| **REFUTED ❌** | The code is wrong | ❌ Never — must be fixed |
| **BLOCKED ⛔** | External impediment (quota, dead API, missing key) — no code fault | ✅ Yes, under all 3 conditions: (1) external only, (2) another VERIFIED row covers same behavior via different route, (3) human explicit sign-off + reopen condition recorded |

---

## What I Still Need to Clarify

1. **Primer setup for Hermes.** When I activate, I'll need: (a) a private key store (where? `~/.hermes/agenttalk-session-primer-key.json`?), (b) a `design/session-primers/hermes-primer.md` file with my key, (c) a `hermes-lessons.md` location. The primer format uses role names embedded in filenames — since my role is "Scrum Master," the file would be `scrum-master-primer.md`? Or does the primer name match the agent name (Hermes)?

2. **Channel infra timeline.** The baton conductor is being planned now. Is that enough, or does the SM need a richer channel (e.g., a sideband message bus) beyond the sequential conductor script?

3. **SM activation trigger.** Will Fausto explicitly hand me the role at a specific point (e.g., after baton conductor ships), or is it a gradual transition?

4. **First SM act.** After activation, should I immediately run a backlog gate, or wait for the current epic (baton conductor) to land first?

5. **Budget polling for Hermes.** I'm running under `deepseek/deepseek-v4-flash` on the Nous provider. The telemetry endpoint at `127.0.0.1:9899/usage` tracks per-provider figures — but that's Claude/Codex and Antigravity, not the Hermes provider. How do I budget-track my own consumption?
