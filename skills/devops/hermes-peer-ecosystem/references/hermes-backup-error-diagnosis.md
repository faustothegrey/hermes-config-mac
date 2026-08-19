# Diagnosing Hermes Config Backup Errors

## Symptoms

The cron job `b763d78565da` reports `last_status: error` via `hermes cron list`.

## Diagnosis technique

Cross-reference cron job status with git history to locate where the failure occurs:

1. **Check cron job status:**
   ```
   hermes cron list  → look for job b763d78565da's last_status and last_run_at
   ```

2. **Check git history:**
   ```
   cd ~/Backups/hermes-config && git log --oneline --format="%ci %s" | head -10
   ```

3. **Compare timestamps:**
   - If the latest commit timestamp matches `last_run_at` ± few seconds: commit succeeded
   - If commit is older than `last_run_at`: commit failed (error in generate-backup.py)
   - If commit matches but status is error: failure happened *after* commit (push or encryption)

## Common failure modes

### 1. git push fails (most common)

The `backup-hermes.sh` script uses `set -euo pipefail`. `git push` returns non-zero
on failure, killing the entire script. The commit still exists locally but isn't pushed.

**Check:** `ssh -T git@github.com` — if SSH auth fails:
```
ssh-add -l        # check loaded keys
ssh -T git@github.com  # test auth
```

**Fix:** `ssh-add ~/.ssh/id_rsa` or verify the SSH key is registered on GitHub.

### 2. SSH key not found at ~/.ssh/id_rsa.pub

The encryption step checks for `$SSH_PUBLIC_KEY` (defaults to `~/.ssh/id_rsa.pub`).
If missing, it prints to stderr and skips encryption — the script continues, so
this alone doesn't cause the error status. But a missing key may indicate the
`ssh-agent` is also unloaded, which would break git push.

**Check:** `ls -la ~/.ssh/id_rsa.pub`

### 3. Obsidian vault FDA error (already mitigated)

The `generate-backup.py` script wraps the vault copy in `try/except PermissionError`.
If the vault is skipped due to missing Full Disk Access, a `.SKIPPED-NO-FDA` marker
file is created. This is a soft failure — the backup continues.

**Check:** `ls -la ~/Backups/hermes-config/obsidian-vault/.SKIPPED-NO-FDA`

### 4. Secrets tar/encryption timeout (SIGTERM)

The `backup-hermes.sh` script copies sensitive files (`.env`, `auth.json`, `state.db`,
`google_token.json`, etc.) into a temp directory, then runs:

```
tar -C "$tmpdir" -czf "$tmpdir/hermes-secrets.tar.gz" hermes-secrets
openssl enc -aes-256-cbc -salt -pbkdf2 -in "$tmpdir/hermes-secrets.tar.gz" ...
```

When `state.db` is large (40-50 MB), the `tar -czf` step can hang for 60+ seconds
while compressing the bundle. If the cron job timeout (or an interactive terminal
timeout) kills the process, `tar` receives SIGTERM.

**Symptom in script output:**
```
./scripts/backup-hermes.sh: line 42: ##### Terminated: 15    tar -C "$tmpdir" -czf "$tmpdir/hermes-secrets.tar.gz" hermes-secrets
```
Or simply a timeout with exit code 124 (from terminal timeout) or a stuck cron job
that never completes.

**Impact:** The script uses `set -euo pipefail`. When tar is killed, the entire script
exits with error BEFORE `git add`, `git commit`, and `git push` run. The backup
commit is NOT made — the working tree has uncommitted changes from a partial
`git add` (if the generate-backup.py stage ran first).

**Diagnosis:** Run the script manually and watch for timeout:
```
timeout 30 bash scripts/backup-hermes.sh 2>&1
```
If it exits with 124 (timeout) or shows "Terminated: 15" on the tar line, this
is the failure mode.

**Cross-reference:** The `last_run_at` on the cron job may show a time that matches
no git commit — because the script died before reaching `git commit`.

**Workarounds:**
1. **Increase cron job timeout:** The default cron job timeout may be too short
   for 40-50 MB state.db + encryption. The script needs 2-3 minutes to complete.
   Check `hermes cron list` for any timeout settings.

2. **Exclude large files from secrets:** If `state.db` is the only large file,
   consider excluding it from the encryption block and backing it up separately.
   Modify the `for item in ...` loop in `backup-hermes.sh` to drop `state.db`.

3. **No-compression tar:** Use `tar -C "$tmpdir" -cf` (no -z) to avoid the gzip
   CPU overhead, saving 30-60s at the cost of larger encrypted files.

4. **Manual recovery after timeout:** If `git add` ran before the timeout,
   the working tree has staged/unstaged changes. Recover with:
   ```
   cd ~/Backups/hermes-config && git add . && git commit -m "backup: manual recovery $(date '+%Y-%m-%dT%H:%M:%S%z')"
   ```
   Then verify with `git push`.

### 5. State.db too large (conceptual overlap with #4)

If `state.db` is 40-50 MB, encryption + commit + push may take longer than the
cron job timeout (default 120s). Check total backup time from `last_run_at` to
the next commit.

### 6. Wrapper script timeout after successful backup (false-positive error)

The cron wrapper `hermes-config-backup-nightly.sh` calls `./scripts/backup-hermes.sh`.
On some runs the underlying script finishes in 90-100 seconds, close to the
cron job's 120-second timeout. The wrapper script then gets killed by the
timeout after `backup-hermes.sh` already completed its git commit and push.

**Symptom:**
- `hermes cron list` shows `last_status: error`
- The output directory's `.md` file reads `Script timed out after 120s`
- BUT `git log -1 --format="%ci %s"` shows a matching commit within minutes
  of (or before) `last_run_at`
- `git status --short` is clean
- The remote already has the commit (`git fetch origin && git log origin/main -1`)

**Diagnosis:** Cross-reference cron `last_run_at` with git commit timestamps:
```
cd ~/Backups/hermes-config && \
  echo "Last cron run: $(hermes cron list 2>/dev/null | grep -A 5 b763d78565da | grep last_run_at)" && \
  echo "Last commit: $(git log -1 --format='%ci %s')" && \
  echo "Remote: $(git log origin/main -1 --format='%ci %s')"
```

If the commit timestamp is within 2 minutes BEFORE the cron `last_run_at`,
the backup actually succeeded — the wrapper timed out during its final
cleanup printf.

**Impact:** None. The backup is intact, pushed to GitHub. The cron status
is misleading. No action needed except possibly increasing the cron timeout
or accepting the false positive as harmless.

**Fix (optional):** No fix needed — backup is fine. To suppress the false
positive in future, the wrapper script can be made faster by reducing
`backup-hermes.sh` overhead (skip gzip on secrets, exclude `state.db`).
Alternatively, increase the cron timeout if the Hermes cron system
supports it.

## Quick triage command

```
cd ~/Backups/hermes-config && \
  echo "=== CRON STATUS ===" && \
  hermes cron list 2>/dev/null | grep -A 5 b763d78565da && \
  echo "=== LAST 3 COMMITS ===" && \
  git log -3 --oneline --format="%ci %s" && \
  echo "=== TOTAL COMMITS ===" && \
  git rev-list --count HEAD
```

Use this to determine the real state:

```
cron last_status  | git commit matches last_run_at? | interpretation
------------------+--------------------------------+-----------------
error             | yes, ±1min                     | wrapper script timeout (backup OK) — failure mode #6
error             | no (commit is older)            | backup died before commit — failure modes #1-4
ok                | yes                             | normal, happy path
ok                | no (commit is way older)        | git push failed last time, recovered by manual run
```

## Run counter

The cron system doesn't expose total run count. Use the cron output directory
for the authoritative total (ALL runs — success + failure):

```
ls ~/.hermes/cron/output/b763d78565da/ | wc -l
```

Use git commit count as success-only subset:
```
cd ~/Backups/hermes-config && git rev-list --count HEAD
```

Each successful run produces exactly one commit. The delta between
`ls | wc -l` and `git rev-list --count HEAD` is the number of partial or
total failures (runs that died before reaching `git commit`).

**When answering `run_totali`:** Always use the output directory count.
The git commit count under-reports. Cross-reference with `last_status`
**When answering `run_totali`:** Always use the output directory count (or jobs.json repeat.completed). The git commit count SIGNIFICANTLY under-reports — expect 20-40% fewer commits than actual runs due to failures, manual tests, and timeouts. Cross-reference with `last_status` to explain the delta.

**Real-world data (July 2026):** The backup cron job accumulated ~44 git commits over ~20 days of operation. The actual run count (including failures, manual tests, setup runs) is substantially higher. The output directory or jobs.json `repeat.completed` is the authoritative source.

## Fix: full manual run to collect errors

```
cd ~/Backups/hermes-config && bash scripts/backup-hermes.sh 2>&1
```

Watch for error output after "git push" line. If push fails, the last lines should
contain the SSH/git error.

## Partial-success pattern

If you see:
1. A git commit matching the cron `last_run_at` timestamp
2. `last_status: error` on the cron job
3. Uncommitted changes in the working tree (`git status --short` shows M/D files)

This means the script ARRIVED at `git commit` (so generate-backup.py worked),
but the `set -euo pipefail` killed the script at a later step (secrets encryption
or git push). The commit exists locally but may not be pushed to remote.

**Alternative partial-success (no visible damage):**
1. A git commit timestamped SLIGHTLY BEFORE the cron `last_run_at`
2. `last_status: error` with "Script timed out after 120s"
3. Clean `git status`
4. Remote has the commit (`git log origin/main -1` matches local)

This means `backup-hermes.sh` completed successfully (commit + push), but
the wrapper script was killed by the cron job timeout before it could
print its completion message and exit. The backup is fully intact — the
error is a false positive. See failure mode #6.