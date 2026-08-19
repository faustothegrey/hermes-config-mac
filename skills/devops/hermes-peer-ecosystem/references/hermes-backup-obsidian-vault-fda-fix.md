# Obsidian Vault FDA Fix for Cron Backups

## Problem

The `generate-backup.py` script copies `~/Documents/Obsidian Vault` via `shutil.copytree()`.
When run from a cron job (or any process without **Full Disk Access**), this raises:

```
PermissionError: [Errno 1] Operation not permitted: '/Users/fausto/Documents/Obsidian Vault'
```

With `set -euo pipefail` in the calling shell script (`backup-hermes.sh`), this crashes
the entire backup. The cron job then times out (120s default) and no backup is created.

## Diagnosis

- Cron jobs and launchd services on macOS **do not inherit** Full Disk Access.
- `shutil.copytree(src, dst)` fails at `os.scandir(src)` before creating `dst`.
- The error propagates as an unhandled exception → Python exits with code 1 → `set -e` catches it.

## Fix (two changes)

### 1. Wrap the Obsidian vault copy in try/except

In `generate-backup.py`, replace the bare vault-copy block with:

```python
# Obsidian vault (may be inaccessible to cron/background without FDA)
obsidian_excludes = (
    ".trash",
    ".git",
    "*.tmp",
    "*.lock",
    "*.log",
    ".DS_Store",
)
if OBSIDIAN_VAULT.exists():
    try:
        copy_tree(OBSIDIAN_VAULT, REPO_DIR / "obsidian-vault", exclude=obsidian_excludes)
        redact_copied_configs(REPO_DIR / "obsidian-vault" / ".obsidian")
        print(f"  obsidian-vault: OK ({OBSIDIAN_VAULT})")
    except PermissionError:
        print(f"  obsidian-vault: SKIPPED (no Full Disk Access — expected in cron)")
        skipped_dir = REPO_DIR / "obsidian-vault"
        skipped_dir.mkdir(parents=True, exist_ok=True)
        (skipped_dir / ".SKIPPED-NO-FDA").write_text(
            f"Skipped at {datetime.now(timezone.utc).isoformat()}: "
            f"Full Disk Access required for {OBSIDIAN_VAULT}\n",
            encoding="utf-8",
        )
```

Key detail: call `skipped_dir.mkdir(parents=True, exist_ok=True)` *before* writing
the marker file, because `copy_tree` never got to create the directory.

### 2. (Optional) Delete stale vault dir on subsequent runs

If `remove_managed_dirs()` in `generate-backup.py` already includes `"obsidian-vault"`
in its `MANAGED_DIRS` list, old vault content is cleaned up before each run. Verify:

```python
MANAGED_DIRS = ["config", "skills", "cron", "profiles", "plugins", "memories", "hooks",
                "obsidian-vault", "inventory", "secrets"]
```

If `"obsidian-vault"` is listed, stale files from a previous successful vault copy
are removed before the next backup attempt, so no extra cleanup is needed.

## Verification

After the fix, run:

```bash
cd ~/Backups/hermes-config && bash scripts/backup-hermes.sh
```

Expected output should include:
```
  obsidian-vault: SKIPPED (no Full Disk Access — expected in cron)
Regenerated sanitized Hermes backup from ...
Encrypted secrets bundle updated.
git push → master -> master
```

Total time: ~30-40 seconds (was timing out at 120s before the fix).

## Full Disk Access as alternative

To give the cron job FDA (not recommended — security risk):

1. `System Settings → Privacy & Security → Full Disk Access`
2. Add `/usr/sbin/cron` or the specific launchd binary
3. Restart the service

The try/except approach above is preferred — it's resilient regardless of FDA.
