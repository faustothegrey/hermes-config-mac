---
name: sshtmux-fix-normalconnection
description: Fix sshm NormalConnection timeout bug for key-based SSH auth
---

# sshtmux NormalConnection Fix

## The bug

sshm's `NormalConnection` (used when no identities are stored) sends the SSH command to a tmux pane, then loops checking for "password:" in the pane output. With **key-based SSH auth** there's no password prompt, so the loop runs until `TMUX_TIMEOUT_COMMANDS` seconds (default 10) and then calls `_check_timeout_reached()` which **kills the window** and raises `SSHException("Timeout reached!")`.

This makes the TUI unusable for any host that has key-only auth.

## The fix

Edit `/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages/sshtmux/services/tmux.py`:

In `NormalConnection.start()`, replace the `_check_timeout_reached()` call with a plain time check + `break`:

```python
while not password_prompt_found:
    if time.time() - timeout_start > settings.tmux.TMUX_TIMEOUT_COMMANDS:
        # SSH key auth succeeded — no password prompt needed.
        # Break gracefully without killing the window.
        break
    pane_output = window.attached_pane.capture_pane()
    self._check_connections_errors(window, pane_output, host)
    ...
```

This does NOT affect `IdentityConnection` (which uses stored passwords and does need password detection).

Also set `TMUX_TIMEOUT_COMMANDS = 5` in `~/.config/sshtmux/config.toml` since it no longer needs to be long.

## Locations

- **Tmux module:** `.../site-packages/sshtmux/services/tmux.py`
- **Config:** `~/.config/sshtmux/config.toml`
- **CLI:** `sshm` symlinked to `~/.local/bin/sshm` → `/Library/Frameworks/Python.framework/Versions/3.10/bin/sshm`
