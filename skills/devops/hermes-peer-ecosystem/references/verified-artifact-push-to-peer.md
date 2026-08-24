# Checksum-verified artifact push to a peer (over SSH/rsync)

Use when handing code/artifacts to another peer as part of a dev/reviewer role
swap or any transfer where byte-identity matters (frozen baselines, reviewed
hashes). "I rsynced it" is a self-report; the remote re-hash is the verifiable
handle. Never tell the requester "pushed + verified" without step 4.

## Recipe

1. **Pre-verify locally against known/frozen hashes** before sending.
   `shasum -a 256 <file>` each artifact and confirm it matches the source of
   truth (e.g. a ledger's frozen sha). Filename + size is NOT identity — hash it.
   (Prior trap: a zip named `-v2.4.3` whose internal files declared 2.4.1.)

2. **Build a SHA256 manifest** of exactly the files you will send, excluding
   `__pycache__`/`*.pyc`. Ship a copy alongside the payload (e.g.
   `REBAR-HANDOVER.SHA256SUMS`) so the receiver can `sha256sum -c` independently.

3. **rsync** with pycache excluded, to LITERAL remote absolute paths:
   ```bash
   rsync -az --exclude='__pycache__' --exclude='*.pyc' <src>/ \
     fausto@<peer-ip>:/home/fausto/.hermes/skills/hermes/<skill>/<dir>/
   ```

4. **Re-hash on the remote over SSH and diff against the manifest.** Only report
   "verified" when the diff is empty:
   ```bash
   ssh -o BatchMode=yes fausto@<peer-ip> "cd <remote-skill> && sha256sum <files> > /tmp/rh.txt"
   # normalize any absolute plugin path back to the manifest's relative prefix:
   #   sed 's#/home/fausto/.hermes/plugins/<skill>/#plugin/#' /tmp/rh.txt
   # then: diff <(sort MANIFEST) <(sort /tmp/rh-normalized.txt) && echo MATCH
   ```

## Pre-flight reachability (do before any push)

- `nc -z -G 4 <ip> 22` and `ping -c2 <ip>` — port + network.
- Confirm `~/.ssh/known_hosts` has the peer and a key is present.
- `ssh -o BatchMode=yes -o ConnectTimeout=6 <peer> 'echo SSH_OK; hostname; ls -d <target dirs>'`
  — proves non-interactive key-auth AND that the target dirs exist. Never rsync
  into a host you have not proven you can auth to non-interactively.

## SSH `~` expansion trap (bit this transfer)

`~` inside a double-quoted `ssh host "... ~/path ..."` expands on the LOCAL
machine before SSH sends the string. Pushing from macOS (`/Users/fausto`) to a
Linux peer (`/home/fausto`), `mkdir -p ~/.hermes/...` failed with
`mkdir: cannot create directory '/Users': Permission denied`. **Fix:** use
literal remote absolute paths (`/home/fausto/.hermes/...`) in every remote
command and rsync target when local and remote home directories differ. The same
applies to `scp`/`rsync` destination specs.

## Reviewer-independence governance guard (dev != reviewer)

When the transfer is part of a review loop, the reviewer MUST be a different
party from the code's author. If asked to review code you authored, REFUSE
self-review and escalate the direction decision — do not manufacture an ACCEPT on
your own work (it launders author confidence as independent validation). Present
the clean role options and let the human/peer pick which side reviews. Worked
example: peer128 authored gates G1–G4, so it could not independently verdict its
own G4; resolution was that peer136 (non-author) reviews G4, peer128 reviews
everything peer136 develops from there on.

## Cross-check: memory batch-edit can silently drop content

`memory` has no plain read action (calling it with no action errors). A long
`replace` can truncate content and leave a dangling fragment. After any
non-trivial memory replace, read `~/.hermes/memories/MEMORY.md` (and `USER.md`)
directly and re-add anything the edit dropped.
