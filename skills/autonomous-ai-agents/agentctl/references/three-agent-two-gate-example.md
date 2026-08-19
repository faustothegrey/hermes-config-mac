# Worked Example: M11-T2 Active Re-prompting (Full 3-Agent 2-Gate Cycle)

This is a verbatim trace of a real session (2026-07-01) for AgentTalk's M11-T2 task
using the 3-agent pipeline: Codex (planner + reviewer, resource-scarcity fallback),
Gemini/agy (implementer), Hermes (SM). Use this as a concrete map of timing,
baton shape, and gate rhythm.

## Overview

M11-T2 was a bounded implementation task: update the correction prompt in
`team-coordinator.ts` to include the rejected action, current phase, legal action
set, and a `consensus_respond` resend instruction. DoD was 5 rows (D1-D5).

Total wall clock: ~1 hour for a 236-line breakdown + 212-line implementation + tests.

## Step-by-step

### Step 1 — SM briefs planner (Codex)

**SM writes** a self-contained baton to `/tmp/m11-t2-brief.md`, then:
```
agentctl send codex "$(cat /tmp/m11-t2-brief.md)"
```

**Baton shape:**
- Opens with role-to-role pass ("SM Hermes → Planner (Codex)")
- Names the task and its M11-T1 vocabulary dependency
- Lists exact file/line scope from the plan
- Lists DoD items
- Lists explicit DO-NOT-TOUCH fences
- Points to artifacts: plan + ledger (does NOT restate them)
- States current role assignment (Codex holds planner + reviewer)

**Wait:** 60s for the first capture (the agent reads the baton, loads context)

**Typical breakdown size:** 200-300 lines (this one: 236 lines)

### Step 2 — SM commits breakdown, requests reviewer gate 1

```
git add design/m11-t2-...-breakdown.md + ledger
git commit -m "docs: M11-T2 task breakdown"
```

**SM writes reviewer gate 1 brief** pointing to the breakdown artifact:
```
agentctl send codex "$(cat /tmp/m11-t2-review-brief.md)"
```

**Reviewer gate 1 evidence requirements:**
- `git rev-parse --short HEAD` confirms grounding commit
- `wc -l` confirms cited file/line ranges exist
- Read protected ranges to confirm they are untouched
- Run one happy-path test to confirm regression
- `git diff --check` for whitespace issues
- `node scripts/usage.mjs` for budget reading

**Verdict:** VERIFIED ✅ with evidence. Recorded in ledger.

**SM commits** gate 1 verdict: `git commit -m "docs: record M11-T2 reviewer gate 1 VERIFIED"`

### Step 3 — Send implementer baton to agy

**SM spawns agy first** (if not already running):
```
agentctl spawn agy --workdir /path/to/project
wait 15s for trust prompt + init
```

**First message carries copilot advisory:**
```
⚠️ I'm copiloting — Fausto is the real gate until explicit handoff.

[Human] Implement M11-T2 — Active re-prompting...
```

**Baton points to artifacts, restates only what can't be derived:**
- Points to the task breakdown as the spec
- States the exact file/line ranges
- States the branch name to create
- States the DoD in short form
- Lists DO-NOT-TOUCH fences
- Tells agy to "claim rows in the ledger, don't self-verify" (implementer records claims, reviewer verifies)

**Wait:** 60-90s before first capture. Then re-poll every 60s.

**Typical implementer duration:** 3-8 minutes (multiple read-edit-test cycles)

### Step 4 — Implementer commits, SM verifies

Agy completes and reports:
- Files changed (team-coordinator.ts + new test file)
- Commands run and results (tsc clean, 249/249 tests)
- Claims recorded in ledger

**SM verifies** by running independently:
```
tsc -b
git diff --stat HEAD
npx vitest run .../team-protocol-correction.test.ts
npm test
```

**SM commits** the branch and pushes:
```
git add ... && git commit -m "feat(m11-t2): ..."
git push origin m11-t2-active-reprompting
```

### Step 5 — Reviewer gate 2

**SM briefs Codex** to review the committed branch:
```
agentctl send codex "$(cat /tmp/m11-t2-gate2-brief.md)"
```

**Gate 2 evidence requirements:**
- `git switch <branch>` and resolve HEAD
- `npx vitest run <focused-test>` — D1-D3 assertions pass
- `npx vitest run <happy-path-test>` — D4 regression green
- `tsc -b` — clean
- `npm test` — 43 files, 249 tests, all passed
- `git diff --stat master...<branch>` — confirms scope
- `git status --short --branch` — no dirty files
- `git worktree list --porcelain` — zero pollution
- `git diff --check -- <changed-files>` — clean
- `node scripts/usage.mjs` — budget reading

**Verdict:** VERIFIED ✅ with steelman + attack sections. Recorded in ledger.

### Step 6 — SM merges (human-authorized)

Human says "Please merge":
```
git checkout master
git merge --no-ff <branch> -m "feat(m11-t2): ... (merged, gate 2 VERIFIED ✅)"
git push origin master
```

**Cleanup:**
```
git branch -d <branch>
git push origin --delete <branch>
```

**Ledger update:** mark task row as **DONE** ✅ merged to master.

## Timing summary

| Phase | Wall clock |
|-------|-----------|
| Planner produces breakdown | ~5 min |
| Reviewer gate 1 | ~3 min |
| SM commits + briefs implementer | ~1 min |
| Implementer builds + tests | ~5 min |
| SM verifies + commits + pushes | ~2 min |
| Reviewer gate 2 | ~3 min |
| SM merges + cleanup | ~1 min |
| **Total** | **~20 min active** (some wait time overlapping) |