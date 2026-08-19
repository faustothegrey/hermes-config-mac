# Peer Onboarding — adding a new peer to the fleet

## Full workflow

When the user tells you about a new peer ("there's a new peer, peerXX, on 192.168.178.XX"):

### 1. Test connectivity

```bash
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new fausto@<ip> 'hostname && whoami'
```

- If it succeeds → skip to step 4 (verification)
- If it asks for password or says "Permission denied" → continue to step 2

### 2. Check SSH keys

Check what keys are available:

```bash
ls ~/.ssh/id_*
```

If the Mac's `id_rsa` is present, the peer needs to accept it.

### 3. Install public key (interactive password)

**Important: run ssh-copy-id FROM the Mac (peer128), not ON the target peer.**

```bash
ssh-copy-id -o StrictHostKeyChecking=accept-new fausto@<ip>
```

Launch with:
- `background=true`
- `pty=true`
- `timeout=30`

Then use `process(action='poll')` to check for the password prompt, then `process(action='submit', data='<password>')` to send it, then `process(action='wait', timeout=15')` for completion.

Exit code 0 = key installed. Confirm with the success message "Number of key(s) added: 1".

### 4. Verify connection and collect identity info

Determine the correct user first — the user ON the peer may not be `fausto`. Check existing peers for clues (peer84 is `root`, peer105 is `root`, peer70 is `fausto`). If unsure, try `fausto` first, then `root`, then whichever the peer's admin mentioned.

```bash
ssh -o ConnectTimeout=5 <user>@<ip> 'hostname && uname -a && whoami && cat /etc/os-release | head -6 && echo "---UPTIME---" && uptime && echo "---MEM---" && free -h | head -3 && echo "---DISK---" && df -h /'
```

### 5. Add to SSH config via sshm (sshtmux)

Once SSH key works, add the peer to the managed SSH config using sshtmux:

```bash
sshm host create peerXX -p Hostname <ip> -p User fausto -p IdentityFile /Users/fausto/.ssh/id_rsa -g lan-peers -f -i "Hermes peer"
```

If the host gets created as `lan-peers-peerXX` instead of `peerXX`, rename it:

```bash
sshm host rename lan-peers-peerXX peerXX
sshm host set peerXX -p Hostname <ip> -p User <user> -p IdentityFile /Users/fausto/.ssh/id_rsa
```

**Important:** `sshm host rename` strips all parameters (Hostname, User, IdentityFile). The `sshm host set` immediately after is mandatory — the host will be unusable without it.

Caveats:
- Use PascalCase SSH param names: `Hostname`, `User`, `IdentityFile` (not lowercase)
- `IdentityFile` requires an expanded absolute path — `os.path.exists()` doesn't expand `~`
- `sshm host rename` strips parameters; always follow with `sshm host set`
- `sshm host create` may prefix `lan-peers-` to the hostname when the group is specified; rename fixes it
- If `sshm` is not in PATH, symlink it: `ln -sf /Library/Frameworks/Python.framework/Versions/3.10/bin/sshm ~/.local/bin/sshm`

### 5b. Extract Hermes API key

After SSH is working, read the peer's Hermes API key from its `.env`:

```bash
ssh <user>@<ip> 'cat /root/.hermes/.env 2>/dev/null | grep API_SERVER_KEY'
```

The key is the `API_SERVER_KEY` value. **Do not confuse with `hsk-` prefixed keys** — those are Hyperbolic provider keys for LLM routing, not the Hermes API server key. The Hermes API server at `:8642` authenticates with `API_SERVER_KEY`.

Save to fact_store with tags `peer, api-key, ssh`.

### 5c. Verify Hermes API

```bash
curl -s -H "Authorization: Bearer <key>" http://<ip>:8642/v1/chat/completions \
  -d '{"model":"deepseek/deepseek-v4-flash","messages":[{"role":"user","content":"hi"}]}'
```

Expect 200 with a response. 401 = wrong key (check if it's a Hyperbolic `hsk-` key by mistake).

### 6. Save to memory

Save a compact entry (memory chars are limited to ~2,200):
```
peerXX: 192.168.178.XX (OS, arch) user via key.
```

Also save to fact_store with appropriate tags.

### 7. (Optional) Save password to fact_store

The password is needed only as fallback for `ssh-copy-id` on future peers that share the same password. Save without the IP so the fact is reusable:

```
General SSH password for fausto@<domain>: <password>.
```

### Pitfalls

1. **Do NOT use foreground terminal** for `ssh-copy-id` — the password prompt can't be answered interactively in foreground mode.
2. **Run ssh-keygen + ssh-copy-id from the client machine (Mac), not the target.** A common mistake is running these ON the target peer, which generates the wrong key pair.
3. **Memory is limited (~2,200 chars).** Consolidate peer entries into one line when adding new ones — merge with existing peer info, drop outdated detail from other entries.
4. **known_hosts may already exist** from prior connections — `StrictHostKeyChecking=accept-new` handles this gracefully.
5. **SSH key may not be authorized for root.** Always try the user's primary user first (`fausto`), then root, then whichever the existing peers use.
6. **Raspberry Pi / SBC peers** may have aarch64 architecture and lower resources (3-4GB RAM). Document this when found.
7. **`sshtmux` / `sshm` is installed via pip but may not be in PATH.** The binary lives at `/Library/Frameworks/Python.framework/Versions/3.10/bin/sshm`. Default bash/zsh on macOS do not include that in PATH. Create a symlink in `~/.local/bin/`.
8. **SSH verbose debug** — when a key is refused, run `ssh -v user@host` and look for "Offering public key:" to see which key was tried. The server lists accepted algorithms in `server-sig-algs=<...>`.
9. **sshtmux TUI bug: key-based auth false timeout.** The NormalConnection class runs SSH in a tmux pane then waits for "password:" in the output. With SSH key auth, there's no prompt -- the loop never breaks and raises "Timeout reached!" (10s default). The connection **succeeded** -- press t (attach tmux) after the notification to enter the remote shell. Increase TMUX_TIMEOUT_COMMANDS = 30 in config.toml to reduce false timeouts.
10. **sshm hosts display artifact.** After sshm host set, param:hostname and param:user columns may appear blank even though SSH config is correct. Verify with sshm host show or cat ~/.ssh/config.
11. **SSH param case sensitivity.** sshm uses PascalCase (Hostname, User, IdentityFile). Lowercase forms confuse sshm's SSH_COMMAND. Always set via sshm host set with PascalCase.
12. **sshm host rename strips all parameters.** Always follow with sshm host set to restore Hostname, User, IdentityFile.
