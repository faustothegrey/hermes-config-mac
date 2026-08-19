# Source guard example — init-claude.sh

This file demonstrates the portable source guard pattern for a script that is both:
1. An executable command (`init-claude.sh [path]` — copies `.claude` settings to a directory)
2. Sourceable from `.zshrc` (defines the `init_claude` function without auto-executing)

## Full source

```bash
#!/usr/bin/env bash
#
# init-claude.sh — creates a .claude folder in the target directory
# and copies settings from a fixed source location.
#

# Capture the script path for portability (bash: BASH_SOURCE, zsh: $0)
_THIS_FILE="${BASH_SOURCE[0]-$0}"

init_claude() {
  # Shell options scoped INSIDE the function — not at top level.
  set -euo pipefail

  SRC="/Users/fausto/Software/scripts/settings-ai/claude"

  FORCE=0
  DEST_DIR="$PWD"
  for arg in "$@"; do
    case "$arg" in
      -f|--force) FORCE=1 ;;
      -h|--help)
        grep '^#' "$_THIS_FILE" | sed 's/^# \\{0,1\\}//'; return 0 ;;
      *) DEST_DIR="$arg" ;;
    esac
  done

  # --- validation ---
  if [[ ! -d "$SRC" ]]; then
    echo "Error: source not found: $SRC" >&2
    return 1    # <-- return, not exit!
  fi

  TARGET="$DEST_DIR/.claude"
  mkdir -p "$TARGET"

  # --- copy ---
  shopt -s dotglob    # bash-specific but safe inside the guard
  for item in "$SRC"/*; do
    name="$(basename "$item")"
    cp -R "$item" "$TARGET/$name"
  done
  shopt -u dotglob

  echo "Done: $TARGET"
}

# --- Source guard (portable) ---
if [ -z "${ZSH_VERSION-}" ] && [ "${BASH_SOURCE[0]-}" = "${0}" ]; then
  init_claude "$@"
  exit $?   # propagate the function's return code
fi
unset _THIS_FILE
```

## Key design decisions

1. **All side-effect code goes in a function**, not at the top level.
2. **Shell options (`set -euo pipefail`) inside the function**, not at the top level — prevents polluting the global shell when sourced from zsh.
3. **`_THIS_FILE` captured at top level** using `${BASH_SOURCE[0]-$0}` so `grep` for `--help` works correctly in both bash and zsh invocation contexts.
4. **`return` everywhere inside the function**, **`exit $?` in the guard**. This is the critical distinction:
   - When sourced, `return` returns control to the shell prompt.
   - When executed as a script, the guard's `exit $?` ensures the correct exit code propagates to the OS.c5. **`unset _THIS_FILE`** at the end to avoid polluting the shell namespace.

## How the guard works across contexts

| Context | `ZSH_VERSION` | `BASH_SOURCE[0]` vs `$0` | Result |
|---|---|---|---|
| Sourced from zsh (`.zshrc`) | Set | N/A (unset) | ❌ Skip |
| Sourced from bash | Unset | Not equal | ❌ Skip |
| Executed as bash script (`./script.sh`) | Unset | Equal | ✅ Execute |
| Sourced from another script | Depends | Not equal | ❌ Skip |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Function runs at shell startup | Source guard using `case "$0"` — zsh sets `$0` to file path | Switch to `ZSH_VERSION` + `BASH_SOURCE` guard |
| **Shell crashes (closes) when calling function from prompt** | Function uses `exit` instead of `return` | Replace all `exit` calls with `return` inside the function body |
| `shopt: command not found` when calling function from zsh | `shopt` is bash-only | Move `shopt` calls inside the source-guarded function |
| `HOSTS: parameter not set` error at shell startup | `set -u` (nounset) at top level pollutes global scope | Move `set -euo pipefail` inside the function body |
| `grep: scriptname: No such file or directory` on `--help` | `$0` is `zsh` when function is called from prompt | Use `_THIS_FILE="${BASH_SOURCE[0]-$0}"` captured at top level |
| Script runs but always exits with code 0 | Guard calls `return` instead of `exit $?` when executed | Use `exit $?` after the function call in the guard |
| `_THIS_FILE` shows up in `set` output | Variable leaked into shell namespace | Add `unset _THIS_FILE` at end of script |