# Claude-delegated project assessment for Fausto

Session source: 2026-06-16 conversation about `/Users/fausto/Software` portfolio review and cross-project convergence.

## Durable user workflow preference

For exploratory project-assessment work, especially portfolio reviews, cross-project pattern discovery, convergence analysis, and reusable-component assessment:

- Hermes should act primarily as manager, curator, and memory/vault maintainer.
- Delegate substantive exploratory and assessment work to Claude Code by default.
- Hermes should not provide a parallel independent second opinion unless the user directly asks for it.
- Hermes should only check Claude's output for glaring inconsistencies before preserving it.
- Hermes should write durable findings into the Obsidian second-order memory vault and keep first-level MEMORY compact.

**Broader delegation boundary (updated 2026-06-17):** Hermes acts as delegating editor for all software development outside the Hermes Agent ecosystem and system service management — not just exploratory assessment. Hermes works directly only for: (a) the Hermes Agent ecosystem (config, tools, skills, plugins, dev, anything directly or indirectly part of it); (b) system service management. See also `delegation-readiness-checks` skill.

## Recommended workflow

1. Load `agent-second-order-memory`, `obsidian`, and the relevant delegation skill/tooling context such as `claude-code`.
2. Give Claude Code a bounded, read-only prompt with:
   - root path(s),
   - existing review or source note path(s),
   - exact assessment dimensions,
   - output structure suitable for vault import,
   - explicit instruction not to print or inspect secret contents.
3. Ask Claude for evidence-backed findings, not generic brainstorming.
4. Hermes performs only a light consistency pass:
   - verify a few claims that would materially alter memory;
   - check obvious contradictions against existing vault notes or current files;
   - avoid adding Hermes' own full analysis unless requested.
5. Write a curated vault note that clearly labels Claude Code as the substantive assessor and Hermes as curator/manager.
6. Patch index/project notes with links and compact takeaways.
7. Store only the operating preference or a pointer in first-level MEMORY, not the full assessment.

## Example output note language

> Source: Claude Code delegated exploratory assessment, orchestrated by Hermes.
> Hermes role for this note: curator/manager. Substantive exploratory assessment came from Claude Code. Hermes only verified glaring inconsistencies before writing.

## Pitfalls

- Do not silently replace Claude's assessment with Hermes' own full second opinion.
- Do not turn the vault note into a raw transcript dump; curate findings into stable project memory.
- Do not preserve secret contents. Mention credential filenames or hygiene risk only when needed.
- Do not over-fragment into one-session-one-skill entries; keep this as a class-level workflow under second-order memory / vault curation.
