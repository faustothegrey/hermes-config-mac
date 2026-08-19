---
name: agent-second-order-memory
description: Manage an agent-owned second-order memory store in Obsidian or markdown notes without bloating Hermes main MEMORY.
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [memory, obsidian, notes, knowledge-management, persistence]
    related_skills: [obsidian]
---

# Agent Second-Order Memory

## Purpose

Use this skill when the user wants Hermes to keep richer durable context outside the always-injected main MEMORY store, especially in Obsidian or another markdown note vault.

The goal is a two-tier memory system:

1. **Main Hermes MEMORY**: compact, high-signal facts that should be injected into future sessions.
2. **Second-order memory**: richer notes, rationale, workflows, environment context, project background, and longer explanations that should be searchable and manually browsable but not injected into every turn.

## When to use

Use this skill when:

- The user asks to use Obsidian, markdown notes, or a vault as persistent agent memory.
- Durable context is too verbose for main MEMORY.
- A complex task produced useful detail, but not enough to justify a formal reusable skill.
- The user wants a browsable memory layer they can inspect or edit directly.
- You need to keep a compact pointer in MEMORY while storing the full detail elsewhere.

Do not use this for:

- Secrets, API keys, OAuth tokens, or credentials.
- Short-lived task state, transient TODOs, PR numbers, commit hashes, or one-off logs.
- Claims that will likely be stale within a week unless clearly marked as temporary.
- Procedures that are mature and reusable enough to become a formal Hermes skill; create or patch a skill instead.

## Workflow

### Standard second-order memory capture

1. **Load the storage-specific skill first.**
   - For Obsidian vaults, load `obsidian` and follow its filesystem-first instructions.
   - Resolve the concrete vault path before file operations. Do not pass `$OBSIDIAN_VAULT_PATH` directly to file tools.

2. **Find or create the agent-managed memory area.**
   - Prefer an existing user-approved folder if main MEMORY has a pointer to it.
   - Otherwise ask only if the location choice is genuinely consequential.
   - A good default inside an Obsidian vault is `Hermes Memory/`.

3. **Keep the initial structure flat.**
   - Start with a small number of top-level notes rather than many nested folders.
   - Add folders only when note volume makes the flat structure painful.
   - Suggested starter notes:
     - `README.md` — operating rules and boundaries.
     - `Environment.md` — stable local setup facts and conventions.
     - `Projects.md` — recurring project context.
     - `Workflows.md` — reusable procedures not yet promoted to skills.
     - `Decisions.md` — durable choices and rationale.
     - `Scratch.md` — temporary or not-yet-organized items.

4. **Write concise, durable notes.**
   - Prefer summaries, decisions, commands that verified facts, and rationale.
   - Use Obsidian wikilinks when they improve navigation.
   - Avoid dumping raw transcripts unless a concise excerpt is genuinely valuable.

5. **Keep main MEMORY lean.**
   - Store at most a compact pointer such as the folder path and operating convention.
   - Do not duplicate the entire note content in main MEMORY.

6. **Review before finalizing.**
   - Verify the files exist after creating or editing notes.
   - Report paths plainly so the user can open them in Obsidian.

### Claude-delegated exploratory assessment into Obsidian

Use this flow when the user wants exploratory project assessment, portfolio review, cross-project pattern discovery, convergence analysis, or reusable-component assessment preserved in the vault.

For Fausto's preferred workflow, Hermes should act primarily as manager/curator and delegate substantive exploratory assessment to Claude Code by default. Hermes should maintain first-level MEMORY and Obsidian notes, perform only light checks for glaring inconsistencies, and avoid adding a parallel independent second opinion unless the user explicitly asks for it.

Recommended steps:

1. Delegate the assessment to Claude Code with a bounded, self-contained, preferably read-only prompt.
2. Require evidence-backed findings with file paths and a vault-friendly structure.
3. Instruct Claude not to inspect or print secret contents; filenames and hygiene risk are enough.
4. Hermes lightly verifies only claims that would materially change memory or contradict existing notes.
5. Write a curated Obsidian note that labels Claude Code as the substantive assessor and Hermes as curator/manager.
6. Patch index/project notes with compact links and takeaways.
7. Keep first-level MEMORY compact: store the delegation preference/pointer, not the detailed assessment.

Detailed reference: `references/claude-delegated-project-assessment.md`.

### Compacting Hermes first-level MEMORY into Obsidian

Use this flow when the user asks to compact, slim, or "compactify" Hermes main MEMORY / first-level memory while preserving details elsewhere.

1. Treat "first-level memory", `Memory.md`, and "main MEMORY" as the always-injected Hermes memory/user-profile layer.
2. Write or enrich Obsidian notes first, before removing or replacing first-level memories.
3. Store verbose durable detail in topic/class notes such as `User Preferences.md`, `Projects.md`, `Decisions.md`, `Environment.md`, or a project/topic note linked from `Projects.md`.
4. Patch index notes with wikilinks so the relocated information is discoverable later.
5. Verify the Obsidian files exist/read correctly.
6. Then compact main MEMORY and USER PROFILE into short declarative pointers/summaries.
7. Remove duplicate first-level entries after their content has been preserved in Obsidian.
8. Ask only if there is real uncertainty about whether a first-level entry should be removed or whether content is sensitive.

Detailed reference: `references/first-level-memory-compaction.md`.

## Pitfalls

- Do not turn second-order memory into a hidden junk drawer. If a note grows stale or unstructured, consolidate it.
- Do not create deep folder hierarchies prematurely. Start flat and evolve by pressure.
- Do not store user secrets or raw credentials in Obsidian notes.
- Do not treat Obsidian notes as automatically injected context. Use main MEMORY for small pointers that must be remembered automatically.
- Do not patch bundled or hub-installed skills to encode user-specific Obsidian memory conventions; create or update an agent-owned umbrella skill like this one instead.

## References

- `references/fausto-obsidian-hermes-memory.md` — user-specific setup and conventions from the initial Obsidian second-order memory setup.
- `references/first-level-memory-compaction.md` — workflow for compacting Hermes main MEMORY / first-level memory into Obsidian while preserving details.
