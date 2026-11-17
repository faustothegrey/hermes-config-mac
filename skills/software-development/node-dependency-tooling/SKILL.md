---
name: node-dependency-tooling
description: Use when assessing a package-manager or dependency change.
---

# Node dependency tooling: migrations, native modules, worktree provisioning

How to assess a change to a Node.js project's dependency/package-manager setup *against the actual
codebase*, not just the tool's marketing page. Covers npm ↔ pnpm ↔ yarn migrations, native-module
build risks, and getting dependencies into per-branch Git worktrees.

## Trigger conditions
- Someone proposes switching npm → pnpm (or pnpm → npm/yarn), or "should we adopt X package manager".
- A Node project uses Git worktrees (or frequent fresh checkouts) and installs deps slowly or not at all in them.
- A dependency change might break a native module (`node-gyp`, `node-pty`, `better-sqlite3`, etc.).

## The checklist — verify these against the code before answering

1. **Native modules / lifecycle build scripts.** This is the highest-risk item. pnpm v9+ blocks
   transitive lifecycle scripts; v10 blocks *all* build scripts by default and requires
   `pnpm.onlyBuiltDependencies` (or `neverBuiltDependencies`) to allow them. If a package falls back
   to a `node-gyp` build at install time, that build silently never runs under pnpm and the module
   fails to load at runtime with no obvious install error. Distinguish *prebuilt-binary* packages
   (shipped as per-platform optional deps, e.g. `@lydell/node-pty` + `@lydell/node-pty-darwin-arm64`)
   — those usually work — from packages that must compile. Always require a real load test of the
   native module after the switch, not just a successful install.

2. **Hardcoded relative paths into `node_modules`.** Grep for
   `node_modules/` inside string literals (e.g.
   `readFileSync(join(...,'node_modules','pkg','dist','x.js'))`). Under pnpm's isolated layout,
   `node_modules/<pkg>` is a symlink into the content-addressed store. `readFileSync`/`require` follow
   symlinks, so this *usually* works for a **direct** dependency — but verify it is a direct dep
   (pnpm hoists only direct deps by default), and confirm no code does `realpath`-based path
   comparison that a symlink would break.

3. **Scattered command-string references.** Find every `npm start` / `npm test` / `npm run` string:
   in source (especially **system prompts sent to subagents/workers**), rulebooks read by agents,
   launcher scripts (AppleScript, plist, shell), CI config, and docs. These are *behavioral*, not
   cosmetic — an agent told "run `npm test`" will run the wrong command after the switch and may
   reinstall with the old tool. List them all; a migration is only done when this list is fully swept.

4. **Lockfile churn.** `package-lock.json` ↔ `pnpm-lock.yaml`. Note the current lockfile's dirty state
   in git — you're replacing one tracked artifact with another.

5. **Prerequisite install.** Is the new manager even installed on the machine (and in any fixed-PATH
   launcher)? `corepack enable` or a global install is itself a new requirement for everyone who
   clones/builds.

## The meta-check — is the migration even the right fix?

Before recommending any migration, ask what problem it is *actually* solving, and whether a cheaper,
direct fix exists. Common case (see `references/agent-room-worktree-provisioning.md`): "workers create
many Git worktrees and each needs dependencies installed." Two separate things are being conflated:

- pnpm's content-addressed store (`~/.local/share/pnpm/store`) does make a per-worktree `install`
  near-instant (hardlinks, no re-download/extract) and near-zero-disk. That part of the rationale is real.
- **But** if the worktree is created with a bare `git worktree add`, it has *no* `node_modules` at all
  (node_modules is gitignored) and nothing installs it — the migration doesn't fix that gap; it only
  makes the still-missing install faster.

**The direct fix is usually a symlink, not a package-manager swap.** The root checkout and its
worktrees are on the same filesystem, and `node_modules` is gitignored so a symlink is never committed:

```js
// after 'git worktree add <wt> <branch>', before the worker runs anything:
symlinkSync(join(root, 'node_modules'), join(wt, 'node_modules'), 'dir');
```

Node resolves modules and prebuilt native binaries through the symlink fine (no `--preserve-symlinks`
involved). This holds only when the worktree's branch tracks the root's dependency set — which is the
common case when worktree branches are always fast-forwarded onto `main`. If branches genuinely need
*different* dependency versions, a symlink is wrong and a per-worktree install (where pnpm's store
then helps) is justified.

## Pitfalls
- Don't answer a package-manager question with only "disk space / install speed / strictness" — those
  are near-irrelevant for a small (5-dep, single-package, no-workspaces) project. Weigh the real
  migration cost (checklist items 1–5) against the actual benefit.
- `linkSync` imported-but-unused is a strong hint the intended provisioning was never wired up — check
  whether the symlink/copy is actually called, not just present in the import list.
- Grep must include non-`*.mjs` files: rulebooks (`.md`), launcher scripts (`.applescript`), CI. The
  agent-facing ones matter most because a wrong command string there causes real misbehavior.

## References
- `references/agent-room-worktree-provisioning.md` — the concrete agent-room investigation: exact
  file:line evidence (bare `git worktree add`, unused `linkSync`, hardcoded ghostty-web path, native
  `@lydell/node-pty`), and the symlink fix.
