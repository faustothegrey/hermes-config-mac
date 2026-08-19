# Fausto Obsidian Hermes Memory Setup

Session-specific detail for the agent-managed second-order memory store.

## Decision

The user wants Obsidian to act as Hermes' second-order memory layer so the main Hermes MEMORY stays compact. The user explicitly suggested keeping the structure as flat as possible and organizing iteratively over time.

## Location

Vault:

`/Users/fausto/Documents/Obsidian Vault`

Agent-managed folder:

`/Users/fausto/Documents/Obsidian Vault/Hermes Memory`

Main MEMORY contains a compact pointer to this folder.

## Initial flat structure

Created notes:

- `README.md` — operating rules for Obsidian vs main MEMORY.
- `Environment.md` — stable local setup facts and conventions.
- `Projects.md` — recurring project context.
- `Workflows.md` — reusable procedures not yet formalized as skills.
- `Decisions.md` — durable decisions, rationale, and tradeoffs.
- `Scratch.md` — temporary or not-yet-organized notes.

## Operating convention

- Use the builtin `obsidian` skill for filesystem-first vault operations.
- Keep this area flat until real note volume justifies folders.
- Store verbose durable context here, not in main MEMORY.
- Put only a compact pointer or summary in main MEMORY when automatic recall matters.
- Avoid secrets, transient task progress, PR numbers, commit SHAs, and stale operational details.

## Related note

The user also confirmed that `/Users/fausto/Software/scripts-ai/_older` was removed. Any previous memory about ignoring that deprecated folder was removed from main MEMORY and should not be reintroduced.
