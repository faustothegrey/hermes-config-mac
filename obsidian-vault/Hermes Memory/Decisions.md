# Decisions

Durable decisions, rationale, preferences, and tradeoffs.

## Hermes second-order memory

- Use Obsidian as Hermes' second-order memory store instead of cluttering the main Hermes MEMORY / first-level memory.
- Keep `/Users/fausto/Documents/Obsidian Vault/Hermes Memory` as flat as possible initially.
- Organize iteratively over time only when the amount of material justifies additional structure.
- Hermes may manage this folder directly.
- The main Hermes MEMORY should retain only compact pointers and high-signal facts; verbose details belong in Obsidian notes.
- The user explicitly refers to main Hermes MEMORY as “first level memory” or `Memory.md`.

## User preferences

Detailed preference memory: [[User Preferences]].

- Browser element workflows: user wants to visually select/click a specific page element and have Hermes receive structured context automatically.
- Voice/TTS: user wants audible Hermes TTS when voice mode is enabled, preferably Italian via `it-IT-ElsaNeural`.
- Voice language defaults: interpret input as English or Italian unless another language is explicitly indicated.

## WebElementChat design decisions

Detailed project memory: [[WebElementChat]].

- Use a Chrome MV3 extension with side panel as the main UX, because the user wants to visually select browser elements and chat in the context of the page itself.
- Keep the bridge local-first on `127.0.0.1:8765` because Google Workspace/Gmail/Admin data may be sensitive.
- Prefer selected-element DOM/text/table context over screenshots as the primary handoff format.
- Keep the bookmarklet only as a lightweight fallback for simple pages; Gmail/Google Workspace often block bookmarklet injection via CSP/Trusted Types.
- Use a Chrome extension content script for Gmail/Workspace because extension scripting is more reliable on authenticated Google pages.
- Use broad `http://*/*` and `https://*/*` host permissions for now because Chrome side-panel-triggered injection failed with `activeTab` alone. Mitigate with explicit user activation and data minimization.
- Use `WEBELEMENTCHAT_AGENT_COMMAND` as the local agent integration seam; current wrapper calls Hermes via `/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh`.
- Treat Google Admin/Workspace tables as custom/virtualized and expect extraction failures where `table.rows` is empty but useful table-like data exists in selected text.

