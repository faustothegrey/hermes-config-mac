# Hermes config backup — .git bloat from nightly random-AES-key secrets (2026-08-19)

## Symptom

Mac overheated (load 23 on 8 cores, fans max). `ps -Ao pcpu,comm -r` showed a single
`git-core/git pack-objects` at **481% CPU for 22+ minutes** (cwd = `~/Backups/hermes-config`,
parent = hermes gateway, launched by the nightly backup cron).

Root-cause chain:

```
backup-hermes.sh  (lines 34-35)
  ├── openssl rand 32 > aes.key        # NEW random key EVERY night
  ├── openssl enc -aes-256-cbc ...     # encrypt state.db (~525MB) + secrets → 162MB .enc
  └── git add . && git commit && push  # bundle byte-different EVERY night
                                        #   → git cannot delta it
                                        #   → +162MB of "new" objects per night
                                        #   → .git  → 13 GB
                                        #   → next push/gc: pack-objects at ~500% CPU
```

The vault was NOT the cause (only 508K). The `!secrets/*.enc` line in `.gitignore`
was FORCING the encrypted bundle into version control.

## Fix (applied, peer128 2026-08-19)

1. **`.gitignore`**: replace the `!secrets/*.enc` / `!secrets/*.pub` / `!secrets/MANIFEST.json` /
   `!secrets/README.md` force-include block with a plain `secrets/` ignore. Bundle stays on
   disk (local restore works), never versioned.
2. **Untrack**: `git rm -r --cached secrets/` (files remain on disk).
3. **Fresh history** (recovers the disk):
   ```bash
   git checkout --orphan fresh_root
   git add -A
   git commit -m "backup: fresh root — secrets local-only"
   git branch -M fresh_root master
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   # .git: 13 GB → ~160 MB
   ```
4. **Push** (one-time, WITH user approval — force rewrite of remote history):
   `git push --force origin master`
5. **Opt-in switch** in `backup-hermes.sh`: guard the whole encryption block with
   `if [ "${BACKUP_SECRETS:-0}" != "1" ]; then echo "skipping secrets bundle"; elif ... fi`.
   Default off — the 525MB state.db re-encryption is pure wasted CPU when the result is gitignored.
6. Verify: `git ls-files secrets/ | wc -l` → 0; backup full dry-run completed in ~15s
   (was 22+ min of CPU burn).

## Numbers

| Metric | Before | After |
|--------|--------|-------|
| Load 1-min | 23.33 | ~3.0 |
| `.git` size | 13 GB | 161 MB |
| secrets tracked in git | yes (162MB/night) | 0 |
| backup runtime | 22+ min CPU-burn | ~15 s |

## If secrets must go off-site again

`BACKUP_SECRETS=1` re-enables the bundle, but `.git` will regrow (same random-key cause).
Better alternatives: deterministic encryption (same key until the secret content actually
changes, so git can delta), or a separate snapshot repo / object store for the encrypted
bundle — never the config git history.

## Lesson for other backup repos

Any pipeline that regenerates an artifact with fresh randomness each run (encryption salts,
timestamps inside compressed files, nonce prefixes) produces byte-different outputs that git
stores as new objects. If the artifact is large, `.git` grows unboundedly and pushes/gcs
become CPU monsters. Either gitignore the artifact, or make regeneration deterministic.
