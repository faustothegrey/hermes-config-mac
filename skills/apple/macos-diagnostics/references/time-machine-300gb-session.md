# Time Machine Backup Size Investigation — Session 2026-06-28

## Context

Fausto reported Time Machine doing a 300GB backup. System had high load (21.96 / 15.25 / 13.86) from multiple processes. Investigation revealed APFS metadata inconsistencies on the backup volume as the likely cause.

## System State at Investigation Time

### Load
- Before any action: 21.96 (1m) / 15.25 (5m) / 13.86 (15m)
- After killing Chrome + Claude + iTerm2: 9.48 (1m)
- After gateway restart: 5.63 (1m)

### Memory
- Active pages: ~4.7GB
- Inactive: ~5.3GB
- Wired: ~3.4GB
- Free: ~1GB
- Swap: 2GB used / 3GB total

### Disk
- Internal (APFS): 466Gi total, 314Gi used, 135Gi free (70% capacity on Data volume)
- Backup disk: 1TB external (APFS via USB), ~448Gi used on "Timemachine  7" volume

## Backup Volume Structure

Multiple numbered volumes suggest the backup disk was reformatted/recreated several times:

```
/Volumes/Timemachine     (Jan 2024)
/Volumes/Timemachine  1  (Feb 2024)
/Volumes/Timemachine  2  (Feb 2024)
/Volumes/Timemachine  3  (Jul 2024)
/Volumes/Timemachine  4  (Oct 2024)
/Volumes/Timemachine  5  (Nov 2024)
/Volumes/Timemachine  6  (Dec 2024)
/Volumes/Timemachine  7  (Jun 2026 — current active)
```

Each reformat creates a new numbered entry. TM uses the latest one when the disk reconnects, but old entries persist in /Volumes/ as empty stubs.

## Local Snapshots (Internal, Last 24h)

13 snapshots from 2026-06-27 07:41 through 2026-06-28 06:59:

```
com.apple.TimeMachine.2026-06-27-074105.local
com.apple.TimeMachine.2026-06-27-084126.local
...
com.apple.TimeMachine.2026-06-28-065914.local
```

Hourly cadence — normal MacBook behavior when on battery without the backup disk connected.

## Key Log Evidence

### Metadata Type Mismatch (Smoking Gun)

```
backupd: Expected SnapshotInProgressContainer metadata type
but found APFSBackup metadata type at URL
'file:///Volumes/Timemachine%20%207/2026-05-04-122954.previous/'
```

This error appeared for **7 different backup snapshots** on the destination (May 4, May 17 `.interrupted`, Jun 9, Jun 28 `.inprogress`, May 29, Jun 3, Jun 5 `.interrupted`, May 21, Jun 17).

**Interpretation:** The APFS backup metadata on the external disk has a type mismatch. Time Machine reads the metadata for these old snapshots and expects one type (`SnapshotInProgressContainer`) but finds another (`APFSBackup`). This causes TM to distrust its own database. The safest recovery behavior is to re-copy data it can't verify, explaining the 300GB backup.

### Interrupted Backups

Two `.interrupted` snapshots found:
- `2026-05-17-104507.interrupted`
- `2026-06-05-161159.interrupted`

These indicate the backup disk was disconnected or unmounted while a backup was in progress. Each interrupted backup degrades the metadata consistency further.

### Mount Point Warning

```
Warning: disk has a mountpoint '/Volumes/Timemachine  7' that
differs from the expected mountpoint '/System/Volumes/Data/Volumes/Timemachine  7'
```

The expected path suggests TM originally expected the volume at a different location (under /System/Volumes/Data/), but the actual mount is at /Volumes/. This discrepancy can contribute to TM's confusion about what it has backed up.

## Conclusion

The 300GB backup was most likely caused by **cumulative APFS metadata corruption** on the external backup disk, originating from:
1. Multiple interrupted backups (at least 2 confirmed)
2. A mount-point path mismatch
3. A disk that was reformatted several times (Timemachine → ... → 7)

TM's response to metadata it can't parse is to **re-copy the data it can't verify**, producing the observed 300GB spike.

## Remediation Priority (from least to most destructive)

1. **Unmount/remount** — `diskutil unmount /Volumes/Timemachine\ \ 7/` then `diskutil mount disk3s2` — sometimes fixes transient metadata issues
2. **Verify volume** — `diskutil verifyVolume disk3s2` — checks the APFS container for corruption
3. **Delete local snapshots** — `tmutil deletelocalsnapshots /` — frees internal space, may reduce next backup size
4. **Repair volume** — `diskutil repairVolume disk3s2` — repairs APFS metadata (requires offline disk)
5. **Recreate backup destination** — Remove from System Settings → Time Machine → re-add — forces TM to rebuild its database from scratch
