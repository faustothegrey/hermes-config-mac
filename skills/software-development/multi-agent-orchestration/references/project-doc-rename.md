# Project Doc Rename Workflow

When a project's task/milestone naming convention changes (e.g. `MT1` → `M11-T3`, `MT2` → `SP1`), the rename must be applied consistently across all documentation while preserving historical text.

This is a Scrum Master / orchestrator workflow used during multi-agent development project maintenance.

## Workflow

### 1. Understand the current state

Before proposing anything, read the project's existing convention doc (e.g. `design/collaboration-workflow.md`) and the relevant plan/ledger/backlog files to understand:
- Current naming: how are tasks, milestones, spikes labelled?
- Origin of confusing names: e.g. `MT` prefix could mean "M11-T" or it could be a carry-over from a prior epic
- Scope: which milestones/epics are affected? Keep blast radius contained.

### 2. Propose a convention (get user buy-in first)

Do NOT start editing files until the user has agreed on the naming rules. Present a clear proposal with:
- The naming rules: epic naming, task naming, spike naming, tech-task naming
- The blast radius: which milestones are in scope
- A mapping table showing old → new for every renamed item
- Any edge cases (e.g. tasks that cross epic boundaries → keep origin in description)

### 2b. Extended scope — vocabulary conventions

Sometimes a project adopts a **vocabulary convention** alongside or independent of a doc rename — e.g. banning the word "spawn" in favor of "launch" when talking about starting agents. These follow the same workflow:

1. Understand the current vocabulary and what triggered the change (user correction, confusion, consistency)
2. Propose the rule and get user buy-in
3. Write the rule into the project's canonical convention doc (e.g. AGENT.md or collaboration-workflow.md)
4. Update the skill library if the rule affects agent behaviour (e.g. how Hermes communicates)
5. Enforce: correct violations when seen, update session primers and lessons files

Vocabulary conventions apply to all agent messages, session primers, design docs, and workflow artifacts — they are a hard naming convention, not a code detail. The tool CLI's own verb (e.g. `agentctl spawn`) is exempt; the rule applies to how we *talk* about the action.

### 3. Classify references before editing

| Type | What | Action |
|------|------|--------|
| **Active** | Current plan task lists, ledgers, backlog promotion records, sequencing, decisions tables | Rename |
| **Historical** | Git commit descriptions (git show output), archived analysis from prior milestones, closed docs | Leave as-is |
| **Origin** | Descriptions that explain where a task came from | Preserve as `origin: <old-name>` |

This distinction is critical: rewriting historical text falsifies the record. Only update text that describes the current/forward-looking state.

### 4. Document the convention in the canonical workflow doc

Add the naming rules to the project's workflow/conventions document (e.g. `design/collaboration-workflow.md`). Cover:
- Scope: which milestones the convention applies to
- Epic/milestone naming: e.g. `M<N>`
- Feature task naming: `<epic>-T<N>` (numbered by execution position)
- TECH/refactoring tasks: `<epic>-TECH<N>` (separate namespace for infrastructure work)
- Spikes: `SP<N>` (global, independent of any epic)
- Branch naming: `<epic>-t<N>-<slug>`, `sp<N>-<slug>`
- Origin preservation: when a task crosses epic boundaries, note `origin:` in description

### 5. Apply the rename across files

Order by dependency (most authoritative first):
1. **workflow doc** — the convention itself (done in step 4)
2. **plan.md** — task headers, decisions tables, sequencing, DoD, open items
3. **implementation.md** — task ledger, finding sections, reviewer verdicts, gate outcomes
4. **backlog.md** — promotion records, deferred items that reference current tasks
5. **session primers** — planner, reviewer, implementer primers
6. **lessons files** — agent-specific lessons that reference old names

For each file, update:
- Task names in headers, tables, and prose descriptions
- Sequencing flows and dependency chains
- Reviewer verdicts and gate outcomes (when they reference active tasks)
- Open items and next-step instructions

Leave untouched:
- Quoted git output (`git show`, `git log`)
- Archived analysis from closed milestones
- Backlog items recorded before the rename convention was adopted

### 6. Verify completeness

Search for old naming patterns across the rename scope (e.g. `MT[123]`, `\\bT3\\b`) in the affected docs. Classify each hit as:
- Already updated ✓
- Historical record — leave as-is
- Missed reference — update now

### 7. User-preference embedding

The user is thorough about documentation: when agreeing a new convention, they expect it formalized in the canonical workflow doc AND applied across all affected files (plan, ledger, backlog, primers, lessons) in the same session. Do not stop after updating one file — push through the full set.

## Pitfalls

- Do NOT start editing files before the user has agreed on the convention. The naming rules themselves need iteration.
- Do NOT rewrite historical text (git commit descriptions, archived milestone docs) — it falsifies the record.
- Old naming may appear in active files inside git-command output quotes (`git show --oneline`). Leave those as-is.
- When a task name changes epics (deferred M10-T3 → M11-T1), keep the origin in the task description so the lineage is traceable.
- Blast radius is important — avoid touching earlier milestones.
- After all edits, run `search_files` for old patterns to catch anything missed.
