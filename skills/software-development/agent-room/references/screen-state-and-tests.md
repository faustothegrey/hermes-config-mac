# The browser screen: state, read-only views, and its unit tests

## Where the browser program lives

The room page's client code is a template literal in `src/docs.mjs` (the `SCREEN` string, served at
`/__room`). Its top-level `let` variables are browser-globals: `viewing`, `peeking`, `localMessages`,
`localInput`, `localThinking`, `yourTurn`, `localWorking`, `replica`, `doc`, etc.

## The read-only "view" pattern (mirror it for any new read-only chat view)

- `viewing` (received-peer "View chat") is the reference read-only mode. `updateReplicaView()` is the
  single function that decides what is hidden: it gates `$('composer')`, `box`, `$('attach-row')`,
  `$('talk-settings')`, `$('summary')`, `$('reload')`, `$('new-discussion')`, and renders the
  `#remote-view` notice (with the Back button). `talkStatus()` returns `'read-only'` while `viewing`;
  `message(m)` and `setThinking()` return early while `viewing` so live turns don't leak into the view.
- A LOCAL read-only view (the `/peek` command: `screen.peek` server-side → browser `peeking`, added
  2026-11) reuses this exact shape: `const readOnly = !!(viewing || peeking)` in `updateReplicaView()`, a
  `peeking`-specific `#remote-view` panel with its own Back button, and `message`/`setThinking`/`talkStatus`
  gated on `viewing || peeking`. When a discussion becomes the one in use, `switchTo()` clears `screen.peek`.
- Two UNRELATED things are both named "peek" — don't confuse them:
  1. `peek` in `docs.mjs` = the Explorer's click-the-name file view (`{ kind: 'local'|'received', ... }`,
     browser-local, orange `.peek-banner`).
  2. `screen.peek` / `peeking` / `/peek <name>` = the read-only chat+notes view of a closed discussion
     (server-side state, carried on the `reset` event's `peek` field).

## The reset event

`resetEvent(screen)` (exported) is the full page snapshot sent on SSE connect and on discussion switches.
It maps `screen.transcript` through `messageView()` into `messages`. The `/peek` feature made it
peek-aware: when `screen.peek` is set, `messages`/`doc` come from the peek and a `peek` field is added.
`messageView(m)` turns a transcript entry `{ speaker, text, ... }` into
`{ speaker, html: md.parse(text), error, pass, hidden? }`.

## Closed discussions keep their full conversation in the checkpoint

`closeNamedDiscussion` writes `{ ...checkpoint, sessions: [] }` — it drops the agent/worker sessions but
PRESERVES `state.transcript`. So `readCheckpoint(ctx, name).state.transcript` is a read-only source of a
closed discussion's chat (this is what `/peek` reads). Checkpoints are keyed by the bare discussion `name`
(not its `archive/`/`deferred/` section); the closed lifecycle is separate, marked by
`closedDiscussions(ctx)`/`setClosed` via files under `<checkpoint-dir>/closed/<sha256(name)>`.

## Unit-testing the browser script — the `new Function` harness gotcha

The unit tests don't run a browser; they `eval` slices of `src/docs.mjs` via
`new Function(param1, param2, ..., body)(arg1, arg2, ...)`. Browser-globals not declared in the harness
body's own `let ...` line are supplied as PARAMETERS. `viewing` is already a parameter; a newly added
global (e.g. `peeking`) is NOT, so the first test run fails with `ReferenceError: peeking is not defined`.

Fix = thread the new name through EVERY harness that evals code referencing it:
- add `'peeking'` to the `new Function(...)` parameter string (shared anchor `'viewing', 'renderAutoDev'`), and
- add a `null` argument in the matching position (shared anchor `null, () => {}, (cb) => cb()`).

The anchors are identical across most harnesses, so `patch` with `replace_all` works — but check the
exceptions: a harness that STUBS the function (e.g. `function updateReplicaView(){ updateReplicaHeader(); }`
in the "room header" test) must NOT gain the extra parameter, or its positional args silently shift
(`renderAutoDev is not a function`). Replace the two anchors separately, then revert the stub harness.
`test/ui.test.mjs`'s `talkStatus` harness has its own param list
(`'tab', 'localWorking', 'room', 'viewing', 'localThinking', 'yourTurn'`) needing the same treatment.

Find every affected harness with: `grep -n "'viewing'" test/*.test.mjs`.
