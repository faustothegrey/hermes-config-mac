# Cross-Project Patterns 2026-06-16

Source: Claude Code delegated exploratory assessment, orchestrated by Hermes.
Root reviewed: `/Users/fausto/Software`
Companion source review: [[Software Projects Review 2026-06-16]]

Hermes role for this note: curator/manager. Substantive exploratory assessment came from Claude Code. Hermes only verified a few glaring claims before writing, especially the CasaSpese gitignore/repo inconsistency and package-version similarity.

## Executive summary

- The strongest convergence is not just “AI-adjacent tooling”; it is a subscription-CLI-as-AI-backend pattern. Projects drive local agent CLIs such as Claude, Codex, and Antigravity as subscription resources rather than paid APIs.
- [[CasaSpese]] is part of the AI infrastructure cluster, not just a finance app. Its `consulente` backend manager launches Claude/Codex/Antigravity through `agentapi`, strips API-key env vars where needed, and repairs PATH for reduced shells.
- [[WebElementChat]], [[CasaSpese]], and scripts-ai are the clearest AI-backend / quota / local-bridge cluster.
- [[CasaSpese]] and [[ScienceClick2]] have near-identical Next.js stacks: Next.js 16.1.6, React 19.2.3, Tailwind 4, TypeScript 5, eslint-config-next 16.1.6. This suggests an implicit personal Next.js starter/template.
- CasaSpese, SpreadGit, and MyAppScriptSidebar all touch Google Sheets / Workspace. SpreadGit’s minimal-diff patching is directly relevant to CasaSpese’s Google Sheets sync.
- [[ScienceClick2]] has a reusable multi-agent skills compiler pattern: source skills in `skills/` sync to `.claude`, `.codex`, and `.agents`.
- Local-first/privacy principles show up as code-level behavior: localhost-only bridge, explicit selection, no full-page capture, deterministic no-ML finance rules, and subscription-CLI usage.
- The prior portfolio review had two notable caveats: it understated CasaSpese’s AI role, and its “no git repo / nothing protecting secrets” statement for CasaSpese was inaccurate for `casa-spese-ui`.

## Pattern: Subscription CLI as AI backend

Projects involved:

- [[CasaSpese]]
- [[WebElementChat]]
- scripts-ai

Evidence:

- `/Users/fausto/Software/CasaSpese/casa-spese-ui/src/lib/consulente/manager.ts`
  - Defines backends: `claude`, `codex`, `antigravity`.
  - Uses `~/.local/bin/agentapi`.
  - Launches real local agent CLIs.
  - Comments explicitly say the PTY/subscription route makes usage count against subscriptions rather than APIs.
  - Strips `OPENAI_API_KEY` for Codex and `GEMINI_API_KEY` / `GOOGLE_API_KEY` for Antigravity.
  - Repairs PATH by prepending `~/.local/bin:/usr/local/bin`.
- `/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh`
  - Runs Hermes as a local one-shot agent command for WebElementChat.
- scripts-ai, per review and Claude assessment:
  - Quota monitors for Claude Code, Codex, and Antigravity.
  - Same three backend families used by CasaSpese.

Why it matters:

- This is the most coherent cross-project AI infrastructure thesis.
- Fausto is not merely calling AI APIs; he is treating local agent CLIs and subscriptions as reusable local compute resources.
- The same operational needs recur: locate binaries, strip API keys to avoid paid API fallback, launch safely, monitor readiness, and track quota.

Possible next step:

- Extract a shared `local-agent-runner` or equivalent contract:
  - resolve binary;
  - repair PATH;
  - strip provider API keys when subscription use is desired;
  - launch PTY/agentapi or one-shot command;
  - expose health/status;
  - optionally expose quota metadata from scripts-ai.

Confidence: high.

## Pattern: Personal Next.js stack

Projects involved:

- [[CasaSpese]]
- [[ScienceClick2]]

Evidence verified by Hermes:

- `/Users/fausto/Software/CasaSpese/casa-spese-ui/package.json`
- `/Users/fausto/Software/ScienceClick2/package.json`

Shared versions and tools:

- `next`: `16.1.6`
- `react`: `19.2.3`
- `react-dom`: `19.2.3`
- `eslint-config-next`: `16.1.6`
- Tailwind 4 via `tailwindcss` and `@tailwindcss/postcss`
- TypeScript 5
- ESLint 9
- `@types/node` 20
- React 19 type packages

Difference noted:

- ScienceClick2’s `dev` and `start` scripts load `.env` manually before running Next.
- CasaSpese uses `next dev --webpack` for dev.

Why it matters:

- There is already an implicit “Fausto Next starter” across projects.
- A template or documented starter could reduce future setup work and drift.

Possible next step:

- Create a portfolio-level note or starter template with pinned versions, standard scripts, lint commands, Tailwind/PostCSS setup, and environment-loading choice.

Confidence: high.

## Pattern: Google Sheets and Workspace as shared layer

Projects involved:

- [[CasaSpese]]
- SpreadGit
- MyAppScriptSidebar
- [[WebElementChat]] for Workspace/Admin Console read-side workflows

Evidence from Claude assessment:

- CasaSpese:
  - `casa-spese-ui/src/app/api/sheets/route.ts`
  - `casa-spese-ui/src/lib/google-auth.ts`
  - Uses Sheets v4 operations such as values reads/updates and row insertion.
- SpreadGit:
  - `SpreadGit/src/sheetPatch.js`
  - `SpreadGit/README.md`
  - Uses `googleapis` and `jsondiffpatch` for minimal-diff row updates.
- MyAppScriptSidebar:
  - `MyAppScriptSidebar/Code.js`
  - Apps Script sidebar form appends rows.
- WebElementChat:
  - Can inspect Google Workspace/Admin Console pages and captured a subscriptions table into CSV in prior project memory.

Why it matters:

- The original review correctly said SpreadGit and CasaSpese should talk, but Claude’s assessment expands this to a three/four-project Google Workspace pattern.
- CasaSpese’s finance reconciliation wants auditability and minimal writes; SpreadGit’s structured deltas fit that design.

Possible next step:

- Evaluate whether SpreadGit can become a dependency or internal module for CasaSpese’s Sheets route.
- Consider a shared Google OAuth helper extracted from CasaSpese’s `google-auth.ts`.

Confidence: high for SpreadGit ↔ CasaSpese, medium for broader shared OAuth helper.

## Pattern: Multi-agent skills compiled from one source

Projects involved:

- [[ScienceClick2]] as producer/source pattern.
- [[CasaSpese]] and [[WebElementChat]] as possible consumers.
- scripts-ai as possible portfolio-level home.

Evidence:

- `/Users/fausto/Software/ScienceClick2/scripts/sync-skills.py`
- `/Users/fausto/Software/ScienceClick2/skills/`
- ScienceClick2 repository guidance says not to edit `.agents/skills`, `.claude/skills`, or `.codex/skills` directly; edit source templates in `skills/` and run `./scripts/sync-skills.py`.

Why it matters:

- This solves a real maintenance problem for a workflow involving multiple coding agents.
- It pairs naturally with the subscription-CLI backend pattern: if Claude, Codex, and Antigravity are all first-class tools, they need consistent but target-specific instructions.

Possible next step:

- Promote the skill sync script/pattern to a reusable portfolio-level utility.
- Consider adopting it in CasaSpese and WebElementChat after documenting the pattern.

Confidence: high.

## Pattern: Local-first and privacy-aware by design

Projects involved:

- [[WebElementChat]]
- [[CasaSpese]]
- scripts-ai / local agent tooling

Evidence:

- WebElementChat runs a bridge on `127.0.0.1:8765`.
- WebElementChat design avoids full-page capture and requires explicit element selection.
- WebElementChat memory documents not collecting cookies, passwords, auth headers, localStorage, sessionStorage, or browser profile data.
- CasaSpese uses deterministic no-ML/versioned-rules reconciliation rather than black-box classification.
- CasaSpese `consulente` launches subscription CLIs and strips API keys for some backends, reducing accidental paid API usage / external API routing.

Why it matters:

- This is not only a design preference but a product/positioning principle.
- It could be explicitly named as part of Fausto’s personal software philosophy: local-first, privacy-aware, inspectable automation.

Possible next step:

- Create or expand a principles note in the vault.
- Use this principle to guide WebElementChat and CasaSpese decisions.

Confidence: medium-high.

## Pattern: Tabular/admin data reconciliation

Projects involved:

- [[CasaSpese]]
- ScrapeCircolari2
- [[WebElementChat]]
- CertiCPIAHtml / CPIA administrative context
- MyAppScriptSidebar / SpreadGit via rows/sheets

Evidence from review and Claude assessment:

- CasaSpese processes bank rows such as `Movimenti.csv`.
- ScrapeCircolari2 works with Nettuno registro elettronico / albo pretorio data and CSV-like dumps.
- WebElementChat captured Google Admin subscription table data into CSV in a prior real-world use.
- Google Sheets tools revolve around row append/update/diff.

Why it matters:

- Many projects reduce messy admin/education data into rows, reconcile them, and present or sync them.
- CSV/row normalization may become a reusable utility, though lower priority than AI backend and Sheets convergence.

Possible next step:

- Track recurring row-normalization patterns before extracting anything.
- Avoid premature abstraction until at least two call sites need the same code.

Confidence: medium.

## Reusable opportunity: `local-agent-runner`

Source projects:

- CasaSpese `consulente/manager.ts`
- scripts-ai quota/command resolution
- WebElementChat agent command bridge

Opportunity:

- Extract the shared mechanics of local agent execution:
  - backend names;
  - command resolution;
  - subscription-vs-API environment handling;
  - PATH normalization;
  - agentapi or one-shot wrapper;
  - health/status;
  - quota awareness.

Why it matters:

- WebElementChat can benefit from a more robust backend without inventing another runner.
- CasaSpese already contains a working implementation.
- scripts-ai already knows quota state for the same providers.

Confidence: high.

## Reusable opportunity: SpreadGit as CasaSpese Sheets layer

Source project:

- SpreadGit

Target project:

- [[CasaSpese]]

Opportunity:

- Replace or supplement manual Google Sheets row update logic with SpreadGit-style structured deltas.

Why it matters:

- CasaSpese’s deterministic/versioned finance design aligns with minimal diffs and auditability.
- SpreadGit is currently a clean but orphaned primitive.

Confidence: high.

## Reusable opportunity: ScienceClick2 skills sync as portfolio tool

Source project:

- [[ScienceClick2]]

Target projects:

- [[CasaSpese]]
- [[WebElementChat]]
- scripts-ai
- Future agent-assisted projects

Opportunity:

- Turn `sync-skills.py` and its source-template structure into a reusable portfolio convention.

Why it matters:

- Avoids duplicated, divergent instructions across Claude/Codex/other agent directories.

Confidence: medium-high.

## Reusable opportunity: Unified AI quota dashboard

Source project:

- scripts-ai

Potential consumers:

- CasaSpese consulente backend selector
- WebElementChat side panel / bridge status
- Hermes-adjacent workflows

Opportunity:

- Consolidate per-provider quota scripts into one `ai-quota` command or endpoint.
- Surface quota state where agent backend selection happens.

Why it matters:

- The same Claude/Codex/Antigravity limits affect multiple projects.
- Quota visibility is useful at the moment of choosing a backend.

Confidence: medium.

## Reusable opportunity: Shared Google OAuth helper

Source project:

- [[CasaSpese]]

Potential consumers:

- SpreadGit
- Any future Google Workspace/Sheets tooling

Opportunity:

- Extract the OAuth/token-refresh path from CasaSpese into a reusable helper.

Caveat:

- MyAppScriptSidebar uses Apps Script’s implicit auth model, so not every Sheets-related project needs the same OAuth layer.

Confidence: medium.

## Glaring inconsistencies and caveats from the original review

### CasaSpese git/secrets framing correction

Original review statement:

- `credentials.json` and `token.json` are sitting in the tree.
- “There’s no git repo here, so nothing’s protecting them.”

Claude flagged this as inaccurate, and Hermes verified the core correction.

Verified facts:

- `/Users/fausto/Software/CasaSpese/casa-spese-ui/.git` exists.
- `/Users/fausto/Software/CasaSpese/casa-spese-ui/.gitignore` includes:
  - `token.json`
  - `.env*`
  - `.DS_Store`
  - `*.csv`
  - `data/transactions.json`
- Therefore, if `token.json` is inside `casa-spese-ui`, it is protected from that repo by `.gitignore`.

Remaining hygiene concern:

- If `credentials.json` is in the parent `/Users/fausto/Software/CasaSpese` folder outside the git repo, it may not be committed by `casa-spese-ui`, but it is still a plaintext local credential file worth handling carefully.
- This note does not contain secret contents.

### AI convergence list should include CasaSpese

Original review emphasized scripts-ai, WebElementChat, and ScienceClick2 as the AI-tooling convergence cluster.

Correction:

- CasaSpese’s `consulente` is one of the strongest AI-infrastructure examples because it actively launches Claude/Codex/Antigravity through `agentapi`.
- Future summaries should include CasaSpese in the AI convergence cluster.

### ScienceClick2 permissions caveat

Claude reported that ScienceClick2 has looser local Claude permissions than the general privacy/principled posture might imply.

Hermes did not independently inspect this in detail during this pass, so treat it as a caveat to verify before acting.

### Existing review observations that remain plausible

- `scripts_and_conf/bin` as empty/placeholder.
- `scripts/` as stale 2021–2022 RethinkDB/MySQL scripts.
- `.DS_Store` files as general hygiene issue.
- `future-scenes/` in ScienceClick2 as untracked at review time.

## Suggested note structure from Claude

Claude suggested a richer structure:

- Cross-project map / MOC.
- Pattern note for Subscription-CLI AI Backend.
- Pattern note for Personal Next.js Stack.
- Pattern note for Google Sheets & Workspace Layer.
- Pattern note for Multi-Agent Skills Sync.
- Pattern note for Local-First Privacy Principles.
- Opportunities / convergence backlog.
- Review corrections note.
- Hygiene / secrets and repo state note.

Hermes chose a flatter initial implementation in this note to match the existing Hermes Memory style. Split into separate notes later if this grows.

## Related notes

- [[Projects]]
- [[Software Projects Review 2026-06-16]]
- [[CasaSpese]]
- [[WebElementChat]]
- [[ScienceClick2]]
- [[Workflows]]
- [[User Preferences]]
