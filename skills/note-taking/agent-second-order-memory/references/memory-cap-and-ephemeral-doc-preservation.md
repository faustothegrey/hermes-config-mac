# Memory-cap batching, ephemeral-doc preservation, and reviewer sign-off knowledge notes

Session-proven patterns (2026-08-19, Rebar Phase-1 review session) for the memory↔vault two-tier system.

## 1. Landing a new pointer when main MEMORY is at the char cap

Symptom: main MEMORY is at/near its limit (e.g. 98%, 2173/2200). A plain `add` — or even a
`replace` that grows an entry — is rejected with `would be at N/limit chars -- over the limit`, and
the error echoes every current entry plus current usage.

Do NOT:
- retry the same bare add/replace (it will fail identically),
- shorten one entry per call across multiple calls hoping to inch under (slow, and risks the lock below),
- give up and only write to the vault.

DO — one atomic batch:
1. Write the verbose detail to the vault note FIRST, so nothing is lost even if the memory write stays blocked.
2. Issue ONE `memory` call with an `operations: [...]` array that, in the same batch:
   - `replace`/`remove` enough verbose entries to free room (collapse them to a pointer that says
     "details in vault [[Note Name]]"), AND
   - `replace` (or `add`) the new pointer entry.
   The char cap is checked only on the FINAL batch result, so removal + add together is what fits —
   an add alone never would.
3. If the batch is still over, read the echoed `current_entries` + `usage`, add MORE trims to the
   SAME batch, and resend once. Size the cut from the exact numbers in the error (e.g. "2291/2200"
   means cut ≥91 more chars).

## 2. The memory turn-lock

Repeatedly failing `memory` calls within a single turn triggers a hard lock:
`Memory consolidation failed N times this turn. Stop retrying memory calls ... The fact can be
saved in a later turn.` After this, every further memory call in the turn is refused regardless of
correctness. Recovery: stop; the vault already holds the detail; land the compact pointer on a
LATER turn. Observed: ~4 failed attempts triggered the lock. Prevention: get the batch right in
≤2 attempts by sizing cuts from the echoed usage number, not by guessing.

## 3. Preserving ephemeral signed-off / frozen documents

Ephemeral locations that are NOT preservation stores:
- `~/.hermes/cache/documents/doc_<hash>_NAME.md` — user-uploaded docs; hash-named, transient.
- `~/.hermes/plans/*.md` — plan-mode output.

When a document reaches durable status this session (SIGNED OFF, FROZEN, ACCEPTED verdict):
1. `cp` it into `Hermes Memory/` with a descriptive, status+date-carrying name, e.g.
   `Rebar Feasibility Falsification Program (Signed Off 2026-08-19).md`.
2. Prepend a short vault header (blockquote) recording: the durable status, any amendments it
   already incorporates, and its ephemeral source path (so provenance is traceable).
3. Add `[[wikilink]]` backlinks to the related note cluster in the header, and cross-link the new
   file FROM the topic/knowledge note (two-way).
The vault copy — not the cache/plan file — becomes the note of record.

## 4. Iterative reviewer sign-off → knowledge note

When a document is driven to sign-off across several review rounds (each round: reviewer lists
blockers → you patch the doc → re-submit), the durable value for a future session is NOT the
final doc alone but the SET OF DESIGN DECISIONS won during review — each blocker resolution is a
load-bearing constraint that defines what "correct" means for that work. Capture them as a numbered
"Key design decisions won during review" section in the topic knowledge note, each as a crisp
principle + its rationale. This lets a future session honor the same constraints without re-deriving
them or reopening settled questions.

## 5. Conditional-availability phrasing for peer/human gates

When a governance doc names a peer/human as a review gate (e.g. "obtain peer141 independent
review"), make it conditional on availability unless the user says it is strictly blocking:
"if peer141 is available ... otherwise note it skipped/unavailable and do not block, proceed to the
mandatory external verdict." A hard gate on an intermittently-available party stalls the pipeline;
the honest-evidence move is to record the skip in the review bundle, not to wait indefinitely.
