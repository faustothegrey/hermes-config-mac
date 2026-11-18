---
name: agent-room
description: Use when developing or modifying the agent-room codebase.
---

# agent-room

A collaboration platform for a human and several AI agents around a shared document/drawing; domain-agnostic
(a "room" is any folder). Agents run through the installed Claude Code / Codex / agy CLIs. The repo is at
`~/Software/agent-room` (Node.js, ~9 source modules, 5 deps). Its own `AGENTS.md` and `README.md` are the
canonical source map and are auto-loaded as project context — this skill records only what is NOT obvious
from those.

## Hot-reload module contract (critical — read before adding any module)

agent-room hot-reloads on `/reload` (and dev mode `--dev` watches `src/` + `rulebooks/`) by re-importing
every local module with a version tag: `import(\`./room.mjs?v=${Date.now()}\`)`. A bare static
`import './foo.mjs'` inside one of those modules resolves to the un-versioned (cached) URL and **never**
picks up edits.

To add a shared module without breaking reload, use the default-parameter pattern — static-import it once
as a fallback default, and have `load()` dynamic-import it with the version tag and pass it down (or store
it on `ctx`). See `references/reload-contract.md` for the exact recipe.

## File-name and layout gotchas

- `AGENT.md` is the real file; `AGENTS.md` and `CLAUDE.md` are **symlinks** to it. Editing "AGENTS.md"
  (or "CLAUDE.md") writes `AGENT.md`. This is why a patch whose path is `AGENTS.md` reports `AGENT.md` in
  its diff.
- `AGENTS.md` is a PROTECTED agent-instruction file: writing to it requires an explicit user approval, and
  an unanswered approval prompt blocks the write with "silence is not consent". Do not retry or route
  around it without the user's explicit go-ahead.
- The two agent system-prompt "rulebooks" live in `rulebooks/` (`brainstorming.md`, `worker.md`) — renamed
  from `README-for-*.md` in 2026-11. They are sent verbatim as system instructions and re-read on Reload.
- `src/instructions.mjs` is the single source of truth for every prompt sent to agents. The runtime imports
  its builders, and the "Instructions" tab reads the same `instructionSets` registry (via `/__instructions`),
  so the panel cannot drift from what is actually sent. Each registry piece carries `intent`, `when`, and
  `content` (or a `ref` to a rulebook file).

## Worker worktrees

Created lazily by `ensureWorktree` (`git worktree add`), one per discussion at `<repo>.workers/<name>/` on
`worker/<name>` (or `<repo>.worker/` on `worker/main` before the first message). `linkDeps` symlinks the
room's `node_modules` into the worktree (same filesystem) so it needs no reinstall, and ignores the link via
the worktree's local `info/exclude`.

## Test runner

`npm test` (fast suite), `npm run test:slow`, `npm run test:all`. New tests are auto-assigned to
`test/fast.txt` or `test/slow.txt` by first-run timing. Never hand-edit those lists or `test/.timings.json` —
just run the suite. A passing fast-list test that runs >1s three times in a row is moved to slow by the
suite itself.

## Philosophy and commit style

Small diffs; ask the owner before changing behaviour they rely on; report real test output (never claim a
pass without reading it). Commit subjects are terse and descriptive, e.g. "Worker worktrees: link the
room's node_modules, so code and tests run without reinstalling".

## Pitfalls

- A `.gitignore`/`info/exclude` pattern with a trailing slash (`node_modules/`) matches directories only:
  git `lstat`s the final component, so a symlink-to-directory is a symlink and the `dir/` rule never
  matches — `git status` shows `?? node_modules`. Write the pattern WITHOUT the slash (`node_modules`) to
  ignore the symlink; a real directory (e.g. `.worker-notes/`) still needs the slash.
- Do not hand-patch the worker-dispatch prompt strings in `ui.mjs` with the patch tool: the inline template
  literals contain literal `\n` escape sequences, and the patch tool's `\n` means newline, so matching them
  needs error-prone `\\n`. Use a Python anchor-slice (find two unique markers, replace only the span) — see
  `references/reload-contract.md`.

## References

- `references/reload-contract.md` — the version-tagged import mechanism, the default-parameter recipe, and
  the Python anchor-slice replacement technique.
