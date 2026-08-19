# Interactive CLI/TUI quota probes

Session-derived pattern for CLIs that expose useful state only inside an interactive TUI command such as `/usage` or `/status`.

## Durable technique

When a CLI has no documented non-interactive quota API but the TUI shows the data:

1. Verify the TUI behavior manually once with a tracked pseudo-terminal.
   - Start a fresh temporary directory.
   - Initialize git if the CLI has trust/workspace prompts.
   - Run the CLI under `tmux` with a wide/tall pane.
   - Send the slash command (`/usage`, `/status`) and capture the pane.
2. Parse the captured screen text, not log files, when the screen is the authoritative source.
3. Keep the parser tolerant:
   - Strip ANSI/control characters.
   - Locate a semantic marker such as `Model Quota` before parsing rows.
   - Parse percentages from the progress-bar line following a model/section label.
   - Treat absent reset text as optional.
4. Wrap the probe in a script with both human and `--json` output.
5. Verify with all of:
   - syntax/compile check,
   - parser smoke test using a representative captured snippet,
   - live JSON run,
   - live human-readable run.
6. Clean up tmux sessions and temporary directories in `finally` blocks.

## Antigravity-specific observation

`agy` 1.0.7 exposes quota via interactive `/usage`. The observed screen is a 5-hour `Model Quota` window with per-model remaining percentages, e.g. Gemini, Claude, and GPT-OSS labels followed by progress bars and status text such as `Quota available`. It does not show weekly/monthly usage in that TUI.

Do not fall back to old language-server quota scraping if the user says the CLI now exposes `/usage`; prefer the interactive slash-command source and state that it is the 5h window only.

## Pitfalls

- Do not encode "CLI does not expose quota" as a durable rule after discovering a new slash command; update the probe.
- Ignore deprecated/archived scripts when the active directory has current top-level scripts, unless the user explicitly asks for legacy integration.
- Avoid brittle exact-box drawing matches; parse labels and percentages semantically.
