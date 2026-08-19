# User Preferences

Durable user preferences and interaction conventions that are useful across Hermes sessions but too detailed for first-level MEMORY.

## Browser and visual analysis workflows

- The user wants browser-based exploratory analysis workflows where they can visually select or click a specific web page element and have the agent automatically receive structured context about that element.
- The motivation is to avoid manual screenshots, long natural-language descriptions, and fragile copy/paste when asking about a precise part of a web page.
- This preference is closely related to the [[WebElementChat]] project.

## Voice and language

- The user wants Hermes voice responses to be audible via TTS, not just text replies, when voice mode is enabled.
- The user may use voice input in Italian and expects spoken output when voice mode is enabled.
- Preferred Hermes CLI voice/TTS default: enabled by default, spoken in Italian.
- Preferred Edge TTS voice: `it-IT-ElsaNeural`.
- Voice input should be interpreted as English or Italian by default; other languages are unlikely unless explicitly indicated.

## Memory organization

- The user calls Hermes main injected memory “first level memory” or `Memory.md`.
- Preference: keep first-level Hermes memory compact and high-signal.
- Store richer durable context in Obsidian under `/Users/fausto/Documents/Obsidian Vault/Hermes Memory`.
- If there is uncertainty about what to preserve or remove from first-level memory, ask rather than guessing.

## Communication preference inferred from requests

- The user values practical, forward-looking project discussions and wants promising technical ideas preserved for future conversation.

## Delegation and second-opinion boundary

- For exploratory project-assessment work, the user wants Hermes to act primarily as manager/curator rather than analyst.
- Default approach: delegate exploratory and assessment work to external agent lanes, especially Claude Code and, when useful, Antigravity CLI.
- Hermes should maintain first-level memory and the Obsidian vault, organize delegated findings, and keep an eye only for glaring inconsistencies.
- Hermes should not add a full independent second opinion unless the user asks directly for one.
- Before delegating to any external agent lane, Hermes should run a brief readiness/auth/availability check. If that candidate is unavailable, Hermes should report the candidate unavailable and continue with another delegate if available; if no delegate is available, stop and report delegation failure.
- This applies especially to portfolio/project-review directions such as discovering cross-platform similarities, reusable patterns, convergence opportunities, and project-assessment themes.
- Exception: for the Hermes Agent ecosystem — config, tools, skills, plugins, troubleshooting, development, or anything directly or indirectly part of it — and for managing system services, the user wants Hermes to do the work directly rather than delegating to Claude Code, unless explicitly instructed otherwise. For all other software development, Hermes acts as delegating editor.
