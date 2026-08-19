# Native Antigravity tmux tool pattern (2026-06-16)

Session learning: `agy --print` / `agy -p` can be a poor Hermes delegation interface for Fausto because it may ask for login frequently. `agy --prompt-interactive` inside tmux works as a more stable Claude-Code-like lane.

## Verified local readiness

- `tmux` available at `/usr/local/bin/tmux`, version `tmux 3.6b`.
- Antigravity CLI available at `/Users/fausto/.local/bin/agy`.
- Interactive readiness probe returned visible `READY` in tmux capture.

## Native Hermes tool implementation shape

A Claude-Code-like Hermes tool was added in the Hermes source checkout:

- `tools/antigravity_tool.py`
- tool name: `antigravity`
- toolset: `antigravity`
- `toolsets.py` entry for `antigravity`
- `hermes_cli/tools_config.py` entry so it appears in `hermes tools`
- tests in `tests/tools/test_antigravity_tool.py`

The tool:

1. Resolves `/Users/fausto/.local/bin/agy` before PATH `agy`.
2. Requires `tmux`.
3. Starts a detached tmux session running `agy --prompt-interactive <prompt>`.
4. Polls `tmux capture-pane` until Antigravity appears idle at the input prompt.
5. Extracts the report body from the TUI capture.
6. Returns structured JSON with `success`, `result`, `workdir`, `session_name`, `mode`, elapsed time, and timeout/error tails.
7. Kills the tmux session by default unless `keep_session: true` is passed.

## Validation commands/results

Targeted tests:

```bash
python -m pytest tests/tools/test_antigravity_tool.py tests/cli/test_cli_tools_command.py -q -o 'addopts='
```

Observed result:

```text
17 passed, 1 warning
```

Live smoke check through the tool function:

```text
prompt: Readiness ping: reply with exactly READY and nothing else.
result: READY
success: true
mode: tmux_prompt_interactive
elapsed_seconds: ~15s
```

Tool registry discovery check observed:

```text
schema True
toolset antigravity
available True
```

## Future-use notes

- Enable the `antigravity` toolset via `hermes tools`; a fresh Hermes session is required before the schema appears to the model.
- Keep `claude_code` and `antigravity` symmetric where possible: bounded prompt, workdir, timeout, optional model, explicit danger flag for permission bypass, structured JSON return, and self-side verification of external-agent claims.
- Prefer this native tool over ad-hoc tmux shell snippets once enabled.
