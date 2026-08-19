# Hermes Memory

This folder is an agent-managed second-order memory store for Hermes.

Use this space for durable context that is useful across sessions but too detailed for the main Hermes memory injection. Keep the main MEMORY compact; keep richer notes here.

## Current organization

Keep the structure flat for now. Add folders only when a cluster of notes becomes large enough to justify one.

Suggested note types:

- `Environment.md` — stable local setup facts, paths, tools, conventions.
- `Projects.md` — active or recurring project context that may matter later.
- `User Preferences.md` — durable user interaction, voice/language, and memory-organization preferences.
- `Workflows.md` — reusable procedures that are not formal Hermes skills yet.
- `Decisions.md` — durable decisions, rationale, preferences, and tradeoffs.
- `Scratch.md` — temporary notes worth capturing but not yet organized.
- Topic/project notes such as `WebElementChat.md`, `CasaSpese.md`, and `Omnigent.md` — detailed context linked from `Projects.md`.

## What belongs here

Good candidates:

- Stable project context that would clutter MEMORY.
- Long explanations, rationale, or historical context.
- Environment details with evidence or commands used to verify them.
- Workflows that may later become Hermes skills.
- Notes that should be searchable in Obsidian but not injected into every chat.

Avoid:

- Secrets, API keys, tokens, private credentials.
- Short-lived task progress, PR numbers, commit SHAs, transient TODOs.
- Anything that will likely be stale within a week unless it is clearly marked as temporary.

## Operating rule

When Hermes learns something durable but verbose, store it here and keep only a compact pointer or summary in main MEMORY if future automatic recall is important.
