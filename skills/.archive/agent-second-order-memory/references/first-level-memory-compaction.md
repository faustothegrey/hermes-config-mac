# First-level Hermes MEMORY compaction into Obsidian

Use this reference when the user asks to compact, slim, or "compactify" Hermes main MEMORY / first-level memory while preserving as much detail as possible in Obsidian.

## User terminology

The user may call Hermes main injected memory:

- "first level memory"
- `Memory.md`
- "main MEMORY"

Interpret these as the always-injected Hermes memory/user-profile layer, not the Obsidian vault.

## Proven workflow

1. Load `obsidian` and `agent-second-order-memory`.
2. Resolve the Obsidian/Hermes Memory folder from main MEMORY or `OBSIDIAN_VAULT_PATH`.
3. Read or inspect the current Obsidian memory index notes enough to avoid duplicating structure:
   - `README.md`
   - `Environment.md`
   - `Projects.md`
   - `Decisions.md`
   - existing topic notes
4. Before deleting/compacting first-level entries, create or enrich Obsidian notes with the verbose durable details.
5. Prefer class/topic notes over dumping everything into one scratch note. Good targets:
   - `User Preferences.md` for style, voice, language, memory organization, and recurring interaction preferences.
   - `Projects.md` as an index of recurring projects/topics.
   - separate project/topic notes such as `WebElementChat.md`, `CasaSpese.md`, `Omnigent.md` for detail.
   - `Decisions.md` for durable rationale and memory-policy decisions.
   - `Environment.md` for stable paths and local setup facts.
6. Patch index notes so future agents can discover the new detail via wikilinks.
7. Only after verifying Obsidian notes exist, replace/remove verbose first-level MEMORY and USER PROFILE entries with compact summaries or pointers.
8. Final response should state what changed and give the important note paths plainly.

## Decision rule

Do not ask for clarification if the intent is clear and all content can be preserved safely in Obsidian. Ask only if there is uncertainty about whether a first-level memory entry should be removed or if the content may be sensitive/secret.

## What to preserve in first-level memory

Keep only high-signal automatic-recall pointers, for example:

- The Obsidian second-order memory folder path and convention.
- A compact user-preference summary that materially changes behavior across sessions.

Move verbose project, workflow, rationale, and research details into Obsidian notes.

## Pitfalls

- Do not remove first-level memory before the Obsidian copy is written and verified.
- Do not duplicate the same preference across multiple USER PROFILE entries; merge them into one compact declarative summary.
- Do not turn Obsidian second-order memory into a hidden junk drawer; create linked notes where a topic is likely to recur.
- Do not store secrets or raw credentials in Obsidian.