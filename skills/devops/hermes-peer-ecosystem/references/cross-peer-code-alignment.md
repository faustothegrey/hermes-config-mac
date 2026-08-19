# Cross-peer code alignment and verification

Use when one peer is declared the fast-moving source of truth and the local node must be aligned without trusting status reports.

## Scope first

Align distributable code and reviewed artifacts, not node-local identity/state. Typical code surfaces:

- skill source tree;
- runtime plugin tree;
- coupled transport/runtime plugin tree;
- target-specific integration bundle or core patch.

Do not copy telemetry, message databases, cohort/node identity, credentials, local cursors, or deployment state merely to make two nodes “identical.” Core patches are target-version-specific: use the bundle prepared for the local core version rather than copying the coordinator's installed core files.

## Procedure

1. **Inspect both nodes directly.** Read live version fields and compute hashes from the actual source-of-truth filesystem. Treat summaries and review notes as snapshots.
2. **Rerun tests on the source peer.** Include compilation, full unit discovery, conformance, integration harnesses, and an explicitly non-organic live smoke when available. Preserve the suite's evidence scope: local-controller conformance is not gateway or delegated-agent conformance.
3. **Back up locally before synchronization.** Copy each destination tree and save the local core diff in one timestamped backup directory.
4. **Dry-run synchronization.** Review additions, changes, and deletions. For exact source-tree alignment, use `rsync -a --delete` only after the backup. Exclude `__pycache__/` and `*.pyc`.
5. **Synchronize coupled surfaces together.** A runtime plugin, transport adapter/core, and their integration bundle may be an atomic compatibility set. Do not sync only one file from such a set.
6. **Verify bytes independently.** Cross-platform `rsync -c` may report checksum drift even when SHA-256 bytes match. Compute a deterministic tree digest on both nodes: for every sorted regular file, excluding caches, hash `relative_path + NUL + bytes + NUL`. Require equal file counts and aggregate digests.
7. **Verify patch state without applying it twice.** `git apply --reverse --check <patch>` succeeding means the exact patch is already applied. A simultaneous forward-check failure is expected in that state. Keep unrelated local edits outside the patch untouched.
8. **Rerun the complete validation locally.** Test the synchronized source and the installed runtime separately. A frozen bundle test alone does not prove the live installation.
9. **Check a live endpoint.** Confirm the local adapter/card version and, when safe, run a clearly marked `test` or `operator_solicited` request so it cannot enter organic evidence.
10. **Report known inconsistencies faithfully.** Byte alignment can reproduce an upstream metadata mismatch (for example, manifest version differing from implementation fields). Do not silently “fix” it and then claim exact alignment.

## Useful verification snippets

### Deterministic tree digest

```python
from pathlib import Path
import hashlib

root = Path("/path/to/tree")
h = hashlib.sha256()
count = 0
for p in sorted(root.rglob("*")):
    if not p.is_file() or "__pycache__" in p.parts or p.suffix == ".pyc":
        continue
    rel = p.relative_to(root).as_posix()
    h.update(rel.encode())
    h.update(b"\0")
    h.update(p.read_bytes())
    h.update(b"\0")
    count += 1
print(count, h.hexdigest())
```

### Non-portable test harnesses

A copied Python harness may hardcode a Linux plugin path such as `/home/<user>/.hermes/plugins`. On macOS, do not edit the reviewed harness just to run it. Execute from the expected repository directory with `PYTHONPATH` containing the local plugin and skill-plugin roots, then report the portability defect separately.

## Interpretation rules

- “All tests pass” is an engineering-health statement, not formal phase closure.
- A live file hash newer than the hash named in a closure report requires explicit review coverage for the newer bytes.
- Trace correlation by shared `trace_id` does not prove every required correlation field is populated; inspect fields such as `retrieval_event_id`, provenance, requester/processor/target/collector identities, and eligibility reason.
- When the project is fluid, timestamp the alignment claim and re-check the source peer before each release or deployment decision.
