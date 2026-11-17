# agent-room: npm → pnpm assessment, and the worktree dependency gap

Session 2026-11-17. Project: `agent-room` (Node ≥20, 5 deps, single package, no workspaces).
The user proposed npm → pnpm, then clarified the real driver: workers work in Git worktrees and the
hope was pnpm would make creating those worktrees easier.

## Evidence gathered (exact file:line)

- `package.json` deps: `@lydell/node-pty`, `branch-graph`, `ghostty-web`, `marked`, `ws`.
- `src/host-shell.mjs:63` — reads ghostty-web from a hardcoded relative path:
  `join(dirname(fileURLToPath(import.meta.url)), '..', 'node_modules', 'ghostty-web', 'dist', 'ghostty-web.js')`.
  `readFileSync` follows symlinks, so pnpm's symlinked `node_modules/ghostty-web` still resolves — low risk.
- `src/host-shell.mjs:111` — loads the native module via dynamic import: `(await import('@lydell/node-pty')).default`.
  `@lydell/node-pty` ships prebuilt per-platform binaries as optional deps
  (`@lydell/node-pty-darwin-arm64`, etc.), so no `node-gyp` compile is expected — but under pnpm the
  build-script allowlist still needs the package approved, and a real load test is required.
- `src/ui.mjs:2661-2673` — `ensureWorktree` does a **bare** `git worktree add` (`worktree add` or
  `worktree add -b …`). It provisions no `node_modules` and no dependency install.
- `src/ui.mjs:11` — `linkSync` is **imported but never called** (only `unlinkSync` is used anywhere).
  Strong signal the intended dependency-provisioning path was never wired up.
- No `npm install` / `npm ci` anywhere in the repo; the worker rulebook
  (`README-for-worker-agents.md:45`) only tells the worker "run the project's tests (`npm test`, if it
  has them)". So a fresh worktree cannot run tests until the worker improvises an install.

## Conclusion reached

The user's pnpm rationale (content-addressed store makes per-worktree install fast) is *correct in
principle* but misdiagnoses the actual gap: worktrees get **no** node_modules at all, so the problem
is provisioning, not install speed. The direct fix is to symlink the root's `node_modules` into each
worktree in `ensureWorktree` — same filesystem (worktrees live at `<repo>.workers/<name>/`, a sibling
of the root), gitignored so never committed, and worker branches are always fast-forwarded onto `main`
(see `catchUp`, `src/ui.mjs:2722`) so the symlink always yields the right dependency set.

The npm → pnpm migration would additionally require: `pnpm.onlyBuiltDependencies` for `@lydell/node-pty`,
a sweep of `npm start`/`npm test` strings embedded in source system-prompts (`src/ui.mjs` ~31-36,
508-509, 3040), UI strings (`src/docs.mjs` 9, 2456), the Dock launcher
(`scripts/dock-launcher.applescript:40` — `npm start -- --open` + a PATH check that omits pnpm),
README.md/AGENTS.md, and lockfile replacement. Net-negative for a 5-dep project unless the branches
genuinely need divergent dependency versions.
