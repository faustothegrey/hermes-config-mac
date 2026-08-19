# Verifying a fluid project state on an authoritative peer

Use when the user says one peer contains the latest state and asks you to rerun tests rather than trust reports.

## Workflow

1. **State the connection target before connecting.** Name the peer, IP, transport, and reason in one short sentence, e.g. “Connecting read-only over SSH to peer70 (`192.168.178.70`) because it holds the latest artifacts.” This prevents an unexplained SSH attempt from surprising the user.
2. **Separate four states:** live files on the authoritative peer; latest independently reviewed artifact; historical review baseline; deployed state on each peer. Never treat a dated review summary as the current ceiling when the user says development is fluid.
3. **Inspect the authoritative peer directly.** Read version fields, artifact hashes, manifests, test entry points, and runtime/source paths from disk. Peer self-reports are pointers, not proof.
4. **Run the tests on that peer.** Prefer the project’s recorded interpreter and exact harness commands. Capture command, working directory, exit code, pass/fail counts, and evidence scope.
5. **Do not overclaim conformance.** A local-controller harness passing does not establish pinned gateway, delegated-agent, fleet-wide, or formal holdout conformance unless those surfaces were actually exercised.
6. **Report inconsistencies as status.** Typical examples: runtime manifest version differs from code version; source and runtime plugin trees hash differently; a temporary cohort passed while the official cohort was not exercised.
7. **No mutation by implication.** Test reruns do not authorize deployment, restarts, manifest edits, or sync. Ask separately before those actions.

## Harness argument pitfall

Bundle validators often accept the **bundle root**, then append component paths internally. Read the script’s `BUNDLE`/`PLUGIN_DIR` construction before invoking it. If the script computes `PLUGIN_DIR = BUNDLE / "capability-reuse"`, pass the parent bundle root (`.`), not `capability-reuse`; otherwise it silently looks under `capability-reuse/capability-reuse`. The same applies to HMP validators that append `plugins/hmp`.

A failed run caused solely by a wrong harness root is an invocation error, not a product failure. Correct the invocation and rerun; report only the corrected result as the product status, while noting the invocation correction if relevant.
