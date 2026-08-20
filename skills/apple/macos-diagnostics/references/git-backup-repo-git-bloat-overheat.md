# Runaway `git pack-objects` from backup-repo `.git` bloat (Mac overheating)

Session: 2026-08-19. Belongs under §1 "System Resource Diagnostics" (companion to
§1.5 gateway memory spike). Add a §1.6 pointer to this file when the SKILL.md is
next editable.

## Symptom

- Fans at max, sustained high load (1-min ≥ 20 on an 8-core), user asks
  "perché scalda tanto?" / "why is it so hot?".
- `ps -Ao pcpu,comm -r | head` shows **`git-core/git pack-objects`** at 400%+ CPU
  — one process saturating several cores. (Observed: 481% CPU, 22 min elapsed,
  load 23.33 on 8 cores.)

## Trace it

```bash
# find the hot git process, its parent, and which repo it's working in
ps -Ao pid,ppid,pcpu,etime,command | grep "[g]it-core/git"
GITPID=<pid>
ps -o pid,command -p $(ps -o ppid= -p $GITPID | tr -d ' ')   # who launched it
lsof -p $GITPID 2>/dev/null | grep cwd                        # which repo dir
du -sh <repo>/.git                                            # is .git absurdly large?
git -C <repo> ls-files <dir> | head                          # what's tracked in the suspect dir
```

Observed: parent was the Hermes gateway (running the nightly config-backup cron),
cwd `~/Backups/hermes-config`, `.git` = **13GB**.

## Root cause — un-deltable artifact committed every run

A backup/config repo commits a large file that is **byte-different on every run**,
so git can't delta-compress it and appends a full new copy to history each time.

Concrete cause here: `backup-hermes.sh` built an encrypted secrets bundle with a
**fresh random AES key every night**:

```bash
openssl rand 32 > aes.key                       # new key each run
openssl enc -aes-256-cbc ... -in secrets.tar.gz -out hermes-secrets.tar.gz.enc
git add . && git commit && git push
```

The plaintext (which included `state.db`, the ~525MB conversation DB) was
identical night to night, but the ciphertext was 162MB of totally different bytes
each time. `.gitignore` even had a `!secrets/*.enc` rule *forcing* it in.
162MB × ~80 nights → **13GB `.git`**. Every push/gc re-packed it → `pack-objects`
frying the CPU.

## Fix (ask before each destructive step)

1. **Immediate relief** — `kill <GITPID>`. Kills only that pack; frees cores in
   ~30-60s (load 23 → 6 observed); outbound backup just retries next cycle. No
   data lost. Gateway parent untouched.
2. **Stop the bleed** — `.gitignore` the volatile dir so it stays on disk for
   local restore but is never versioned:
   ```
   secrets/
   ```
   Then `git rm -r --cached secrets/`. Also untrack small companion files the
   generator recreates (`MANIFEST.json`, `README.md`) or `git add .` re-adds them.
3. **Reclaim the bloat** — fresh history + hard GC:
   ```bash
   git checkout --orphan fresh && git add -A && git commit -m "fresh root"
   git branch -M fresh master
   git reflog expire --expire=now --all && git gc --prune=now --aggressive
   git push --force origin master        # rewrites remote — confirm with user first
   ```
   Result: **13GB → 160MB**.
4. **Prevent recurrence** — gate the expensive step behind an opt-in switch so the
   nightly run doesn't re-encrypt a 525MB DB it won't push:
   ```bash
   if [ "${BACKUP_SECRETS:-0}" != "1" ]; then
     echo "Skipping encrypted secrets bundle (local-only)."
   elif ...  # original encrypt block
   ```
   Backup dropped from 22 min (frying CPU) to **~15s**.

## Lesson: don't blame the obvious-but-innocent

The Obsidian vault (508KB) *looked* like the culprit and the user initially asked
to exclude it — but it was 0.004% of the problem. Always check `du -sh .git` and
`git ls-files <dir>` against real on-disk sizes before deciding what to exclude.
Escluding the vault would have "fixed" nothing.
