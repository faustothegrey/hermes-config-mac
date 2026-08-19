# Fausto Antigravity CLI verification — 2026-06-16

Session learning captured from a Hermes conversation about using Antigravity as a delegation lane in addition to Claude Code.

## User intent

Fausto asked whether Hermes could also use Antigravity, alongside Claude, for delegation. He clarified that he meant the Antigravity CLI, not the Antigravity IDE/editor launcher.

## Verified CLI shape

The usable headless agent CLI is `agy`.

Relevant help output observed:

```text
Usage of agy:
  --add-dir                       Add a directory to the workspace (repeatable)
  -c                              Short alias for --continue
  --continue                      Continue the most recent conversation
  --conversation                  Resume a previous conversation by ID
  --dangerously-skip-permissions  Auto-approve all tool permission requests without prompting
  -i                              Short alias for --prompt-interactive
  --log-file                      Override CLI log file path
  --model                         Model for the current CLI session
  -p                              Short alias for --print
  --print                         Run a single prompt non-interactively and print the response
  --print-timeout                 Timeout for print mode wait (default 5m0s)
  --prompt                        Alias for --print
  --prompt-interactive            Run an initial prompt interactively and continue the session
  --sandbox                       Run in a sandbox with terminal restrictions enabled

Available subcommands:
  changelog       Show changelog and release notes
  help            Show help for subcommands
  install         Configure environment paths and shell settings
  models          List available models
  plugin          Manage plugins
  update          Update CLI
```

## Smoke test performed

Command pattern:

```bash
agy --print 'Reply with exactly: ANTIGRAVITY_DELEGATION_OK' --print-timeout 60s
```

Observed result:

```text
ANTIGRAVITY_DELEGATION_OK
```

Conclusion: `agy --print` is suitable for bounded non-interactive delegation from Hermes.

## Practical guidance for future sessions

- Use `command -v agy` first rather than assuming a fixed install path.
- If the user says “Antigravity CLI,” do not substitute the IDE launcher.
- For assessment tasks, ask Antigravity for structured evidence and confidence, then let Hermes curate into memory/vault notes.
- For edits, verify changed files and tests independently before telling the user the work is done.
- If CLI setup is missing, capture the setup/fix command, not a persistent negative rule that Antigravity is unavailable.
