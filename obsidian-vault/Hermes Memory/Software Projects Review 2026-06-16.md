# Software Projects Review 2026-06-16

Source file: `/Users/fausto/Software/PROJECTS_REVIEW.md`
Review date in source: 2026-06-16
Captured into Hermes second-order memory: 2026-06-16
Related index: [[Projects]]

## High-level portfolio picture

The `/Users/fausto/Software` folder is the top-level directory for Fausto's software projects.

The review identified 10 directories:

- 5 substantial active projects.
- 2 small utilities.
- 3 script/config collections.

The strongest throughline is practical tooling for an Italian educator/administrator, especially CPIA Pisa / school-register / Google Workspace contexts, with increasing AI assistance and a strong privacy/local-first instinct.

The review's strongest cross-project interpretation:

- Fausto is building practical tools for his own administrative and educational workflows.
- Several projects orbit local/private AI-assisted workflows rather than cloud-first SaaS.
- The portfolio has an emerging coherent theme: personal AI infrastructure plus school/admin automation.

## Most promising projects to push on

The review names these as the two strongest projects to prioritize:

1. [[WebElementChat]]
   - Most novel idea.
   - Privacy-first UX.
   - Fills a real gap: point at a browser element and say “this” to an AI agent.
   - Especially relevant for Workspace admins and data-table-heavy admin pages.

2. [[CasaSpese]]
   - Most advanced / mature.
   - Has real personal value.
   - Has a principled deterministic design position that may be productizable.

The review also highlights [[ScienceClick2]] as the best-engineered repository and suggests its skill-versioning/sync approach is reusable across other AI-assisted projects.

## Active projects

### CasaSpese — personal finance reconciliation

Path: `/Users/fausto/Software/CasaSpese`
UI codebase: `/Users/fausto/Software/CasaSpese/casa-spese-ui`
Detailed note: [[CasaSpese]]

Review classification:

- Most advanced project.
- Mature, multi-feature, actively worked in June.
- Real OAuth and Google Sheets integration.

Purpose and domain:

- Next.js app for processing bank statements, especially `Movimenti.csv`.
- Turns statements into a categorized expense system.
- Handles reconciliation against Google Sheets.
- Handles recurrences and cash transactions that have no bank trace.

Important design philosophy:

- Deterministic, versioned rules.
- No black-box / ML reconciliation.
- This stance is valuable because it preserves auditability and user trust.
- The review sees this as a defensible product position: deterministic finance reconciliation is increasingly rare and credible.

Mentioned API / feature surface:

- `rules`
- `recurrences`
- `transactions`
- `archive`
- Google Sheets sync
- OAuth
- `consulente` / advisor feature with message history

Security / hygiene note:

- Review warns that `credentials.json` and `token.json` are sitting in the project tree.
- README says to keep them local and not commit them.
- At review time, the review believed there was no git repo protecting them.
- If this project ever becomes or already is a git repo, ensure `.gitignore` exists before any commit and explicitly excludes credentials/token files.

Product/architecture idea:

- CasaSpese could benefit from SpreadGit's minimal-diff Google Sheets patching primitive.
- A deterministic, versioned-rules finance system naturally wants careful diffs and auditability.

### ScienceClick2 — drag-and-drop educational scenes

Path: `/Users/fausto/Software/ScienceClick2`
Dedicated detailed note created from this review: [[ScienceClick2]]

Review classification:

- Best-engineered project.
- Active git history with thoughtful commits.
- Most disciplined repository structure among the reviewed projects.

Technology:

- Next.js 16.
- React 19.

Purpose:

- Teachers place labels on an image.
- Students drag terms to the correct spots.
- Designed for educational scenes and interactive labeling tasks.

Features mentioned in review:

- Spectator mode.
- Results store.
- i18n.
- 4 populated scene categories:
  - biology
  - everyday
  - jobs
  - universe

Engineering notes:

- Has a real `PROJECT.md`.
- Has a unified multi-agent skills system.
- The skill system uses `skills/` as source and syncs to `.claude`, `.codex`, and `.agents`.
- Has worktree conventions.
- Review specifically mentions thoughtful commits around touch interaction, a “nails/hanging paintings” drop-target metaphor, and dead-code removal.

Current caution:

- Uncommitted `future-scenes/` was sitting untracked at review time.

Reusable idea:

- The skill-versioning/sync approach should be reused across other AI-assisted projects.
- This may be a pattern for keeping Claude/Codex/agent instructions consistent without duplicated drift.

### WebElementChat — point-at-element AI chat

Path: `/Users/fausto/Software/WebElementChat`
Detailed note: [[WebElementChat]]

Review classification:

- Most novel idea.
- One of the two most promising projects to push on.

Purpose:

- Chrome MV3 extension plus localhost Python bridge.
- User clicks any DOM element, then chats about “this” with an AI agent.
- Captures selector, XPath, and visible table rows automatically.

Privacy posture:

- 127.0.0.1 only.
- No full-page capture.
- No credentials.
- Explicit selection before sending context.
- This privacy posture is part of what makes the concept credible.

Review state at time of review:

- Working bridge, extension, and tests.
- Review says real agent integration was still a stub requiring `WEBELEMENTCHAT_AGENT_COMMAND`.
- Review says streaming and virtualized-grid scroll-collect were unimplemented.

Important reconciliation with existing memory:

- Existing [[WebElementChat]] memory from 2026-06-13 says `WEBELEMENTCHAT_AGENT_COMMAND` had already been wired to Hermes via `/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh` and smoke-tested with `/chat` returning `mode=agent`.
- Therefore, preserve the review's statement as a source observation, but prefer the newer/verified detailed [[WebElementChat]] note for current operational status unless rechecked.

Why it matters:

- “Point and say this to an AI” is a real UX gap.
- Especially useful for Google Workspace admins drowning in data tables.
- Natural next step in the review: wire to an actual Claude/MCP backend; existing scripts-ai work could feed this.

Suggested next technical directions from review and existing memory:

- Streaming responses.
- Scroll-collect for virtualized grids.
- Better extraction for Google Admin / Workspace custom table DOMs.
- Real backend/session continuity if not already current.
- Possible MCP layer later, but not before UX is solid.

### ScrapeCircolari2 — school notice-board scraper

Path: `/Users/fausto/Software/ScrapeCircolari2`

Purpose:

- Scrapes Nettuno PA registro elettronico / albo pretorio.
- Login flow was reverse-engineered from a HAR.
- Includes a large crawler `list.py` of around 30 KB.
- Has rate limiting and a “slow dump” mode.

Review classification:

- Functional one-off tooling.
- Sept 2025 timeframe.
- Purely utilitarian.
- No docs.
- Fine as-is for personal use.

Ethics/behavior:

- Polite user agent.
- Randomized delays.
- Review characterizes it as responsible scraping.

### CertiCPIAHtml — digital-skills exam landing pages

Path: `/Users/fausto/Software/CertiCPIAHtml`

Purpose:

- Static HTML for CPIA 1 Pisa’s DigComp 2.2 / EDSC test-center accreditation.
- Institutional landing-page / communication material.

State:

- Design-iteration stage.
- Multiple versions / layouts:
  - `progetto_v1`
  - `v2`
  - `page3`
- Institutional blue styling.
- Clean, lightweight.
- Still needs final layout selection.

## Small utilities

### scripts-ai — AI quota monitors

Likely path from review: `/Users/fausto/Software/scripts-ai`

Purpose:

- CLI tools for reporting AI quota/usage across multiple providers/tools.
- Wrap a shared `ai_quota_lib.py` of around 24 KB.

Providers/tools mentioned:

- Claude Code.
- Codex.
- Antigravity.

Reported data:

- 5-hour window.
- Session usage.
- Weekly usage.
- Percent remaining.

Review state:

- Recently active in June.
- Genuinely useful because provider limits often bite.

Product/consolidation idea:

- Create a unified `ai-quota` dashboard across Claude Code, Codex, and Antigravity instead of three separate scripts over one shared library.
- Could be part of a broader “Fausto's AI toolkit” theme together with WebElementChat and ScienceClick2’s skills sync.

### SpreadGit — git-style patches for Google Sheets

Path: `/Users/fausto/Software/SpreadGit`

Purpose:

- Small library for applying git-style / JSON diff patches to Google Sheets rows.
- Uses `jsondiffpatch` deltas.
- Applies changes via Google Sheets API v4.

Review classification:

- Small, clean library.
- Well-documented README.
- Clear API.
- Tidy reusable primitive.

Strategic idea:

- CasaSpese already does Google Sheets sync.
- SpreadGit's minimal-diff patching is exactly what a versioned-rules finance system wants.
- Consider merging SpreadGit into CasaSpese as a dependency rather than leaving it orphaned.

### MyAppScriptSidebar — Apps Script sidebar template

Path: `/Users/fausto/Software/MyAppScriptSidebar`

Purpose:

- Reference / learning template for Google Sheets Apps Script sidebars.
- Sidebar form appends rows to a sheet.

Review state:

- Good `DEPLOYMENT.md`.
- Essentially a starter/snippet rather than an active product.

## Script collections and legacy/config folders

### scripts

Path: `/Users/fausto/Software/scripts`

Review state:

- Old scripts from 2021–2022.
- RethinkDB and MySQL population/query scripts.
- References local databases.
- Stale.
- Archive candidate.

### scripts_and_conf

Path: `/Users/fausto/Software/scripts_and_conf`

Review state:

- Empty or near-empty placeholder.
- `bin/` has nothing.

## Cross-cutting observations

### 1. Secrets hygiene gap

The review’s most urgent hygiene warning is CasaSpese:

- `credentials.json` and `token.json` present in tree.
- Ensure `.gitignore` before committing or pushing.
- Consider a broader sweep for secrets across all projects before putting anything online.

Related general habit:

- `.DS_Store` files are present in multiple places.
- Harmless locally, but a global gitignore habit would reduce noise.

### 2. Google Sheets projects should converge

There are at least two Google Sheets-related projects:

- [[CasaSpese]]: Sheets sync consumer for finance/reconciliation.
- SpreadGit: minimal-diff patching primitive for Sheets rows.

The review suggests these are solving adjacent problems independently and should talk to each other.

Possible concrete direction:

- Use SpreadGit-style deltas inside CasaSpese sync to support auditability, minimal writes, safer reconciliation, and versioned changes.

### 3. AI tooling convergence

The review identifies a coherent personal AI tooling ecosystem emerging from:

- scripts-ai: quota/usage monitoring for AI tools.
- [[WebElementChat]]: browser element selection → local agent bridge.
- [[ScienceClick2]]: multi-agent skills sync for coding/education project workflows.

Possible umbrella concept:

- “Fausto's AI toolkit” or “personal AI infrastructure.”
- Local-first, privacy-aware, tool-augmented workflows for school/admin/software work.

### 4. Best candidates for next work

From the review:

- Push [[WebElementChat]] because it is novel and has a real UX gap.
- Push [[CasaSpese]] because it is mature, useful, and has a principled deterministic design.
- Reuse [[ScienceClick2]]'s skills-sync pattern in other projects.

## Follow-up assessment

See [[Cross-Project Patterns 2026-06-16]] for a Claude-delegated follow-up assessment of cross-project similarities and convergence opportunities.

Important corrections/caveats from that follow-up:

- The original review understated CasaSpese's role in the AI-tooling cluster. CasaSpese's `consulente` launches Claude/Codex/Antigravity via `agentapi`, matching scripts-ai's quota-monitoring focus.
- The original review's “no git repo / nothing protecting secrets” framing for CasaSpese was inaccurate for `casa-spese-ui`: `/Users/fausto/Software/CasaSpese/casa-spese-ui/.git` exists and its `.gitignore` protects `token.json`, `.env*`, `.DS_Store`, `*.csv`, and `data/transactions.json`.
- Remaining hygiene caveat: plaintext credential files in parent/project folders should still be handled carefully; this vault note intentionally does not store secret contents.

## Raw source review preserved

```markdown
# Software Projects Review

_Review date: 2026-06-16_

## Overview

You've got **10 directories**: 5 substantial active projects, 2 small utilities, and 3 script/config collections. The throughline is clear — you're an Italian educator/administrator (CPIA Pisa, school registers) building practical tools, increasingly AI-assisted, with a strong privacy/local-first instinct.

---

## Active projects

### 🏠 CasaSpese — *Personal finance reconciliation* (most advanced)
A Next.js app for processing bank statements (`Movimenti.csv`) into a categorized expense system. The interesting part is the **design philosophy** (per the README's vault pointer): deterministic, **versioned rules, no black-box/ML** reconciliation — plus handling for recurrences and cash transactions with no bank trace. The API surface is rich: `rules`, `recurrences`, `transactions`, `archive`, Google Sheets sync, OAuth, and a `consulente` (advisor) feature with message history.
- **State:** Mature, multi-feature, actively worked (June). Real OAuth + Sheets integration.
- **⚠️ Note:** `credentials.json` and `token.json` are sitting in the tree. The README says "keep local, do not commit" — but there's no git repo here, so nothing's protecting them. If this ever gets a repo, you need a `.gitignore` *first*.
- **Idea:** The "deterministic versioned rules, no ML" stance is genuinely valuable and increasingly rare. That's a defensible product position.

### 🎓 ScienceClick2 — *Drag-and-drop educational scenes* (best-engineered)
Next.js 16 / React 19 app where teachers place labels on an image and students drag terms to correct spots. Has a spectator mode, results store, i18n, and 4 populated scene categories (biology, everyday, jobs, universe).
- **State:** Active git history with thoughtful commits (touch interaction, "nails/hanging paintings" drop-target metaphor, dead-code removal). This is the most disciplined repo — it has a real `PROJECT.md`, a **unified multi-agent skills system** (`skills/` source → synced to `.claude`/`.codex`/`.agents`), and worktree conventions.
- **Note:** Uncommitted `future-scenes/` is sitting untracked.
- **Idea:** The skill-versioning/sync approach here is reusable across all your other AI-assisted projects.

### 🌐 WebElementChat — *Point-at-element AI chat* (most novel idea)
Chrome MV3 extension + localhost Python bridge: click any DOM element, then chat about "this" with an AI agent — selector/XPath/visible table rows captured automatically. Strong privacy constraints (127.0.0.1 only, no full-page capture, no credentials, explicit selection).
- **State:** Working bridge + extension + tests, but the **real agent integration is still a stub** — requires `WEBELEMENTCHAT_AGENT_COMMAND`. Streaming and virtualized-grid scroll-collect are unimplemented.
- **Idea:** This is the most genuinely interesting concept of the bunch. "Point and say *this* to an AI" is a real UX gap, especially for Workspace admins drowning in data tables. The clear privacy posture makes it credible. The natural next step is wiring it to an actual Claude/MCP backend — your `scripts-ai` work could feed this.

### 📜 ScrapeCircolari2 — *School notice-board scraper*
Scrapes the Nettuno PA registro elettronico / albo pretorio (login flow reverse-engineered from a HAR, plus a 30KB `list.py` crawler with rate-limiting and a "slow dump" mode).
- **State:** Functional one-off tooling (Sept 2025). Polite UA, randomized delays — responsible scraping.
- **Note:** Purely utilitarian; no docs. Fine as-is for personal use.

### 📋 CertiCPIAHtml — *Digital-skills exam landing pages*
Static HTML for CPIA 1 Pisa's DigComp 2.2 / EDSC test-center accreditation. Multiple iterations (`progetto_v1`, `v2`, `page3`) — institutional blue styling, clean.
- **State:** Design-iteration stage, picking a final layout. Lightweight.

---

## Small utilities

### 🔧 scripts-ai — *AI quota monitors* (recently active, June)
CLI tools wrapping a shared `ai_quota_lib.py` (24KB) to report usage for **Claude Code, Codex, and Antigravity**. Returns the 5h window, session/week usage, percent-remaining.
- **Idea:** A unified `ai-quota` dashboard across all three providers would be a nice consolidation — right now they're three separate scripts over one lib. Genuinely useful given how often these limits bite.

### 📊 SpreadGit — *git-style patches for Google Sheets*
Small, clean library: `jsondiffpatch` deltas applied to Sheets rows via Sheets API v4. Well-documented README with a clear API.
- **Idea:** This is a tidy reusable primitive. **CasaSpese already does Sheets sync** — SpreadGit's minimal-diff patching is exactly what a versioned-rules finance system wants. Consider merging it in as a dependency rather than leaving it orphaned.

### 📝 MyAppScriptSidebar — *Apps Script sidebar template*
A reference/learning template: Google Sheets sidebar form → row append. Good `DEPLOYMENT.md`. Essentially a starter/snippet.

---

## Script collections (legacy/config)

- **scripts** — Old (2021–2022) RethinkDB + MySQL population/query scripts. Stale; references local DBs. Archive candidate.
- **scripts_and_conf** — Empty (`bin/` has nothing). Just a placeholder.

---

## Cross-cutting observations

1. **Secrets hygiene gap.** CasaSpese has live `credentials.json`/`token.json` with no git protection. Worth a sweep before any of these become repos.
2. **Two Sheets projects that should talk.** SpreadGit (patching primitive) and CasaSpese (Sheets sync consumer) are solving adjacent problems independently.
3. **AI-tooling convergence.** scripts-ai (quota), WebElementChat (agent bridge), and ScienceClick2 (skills sync) all orbit the same theme — you're building personal AI infrastructure. There's a coherent "Fausto's AI toolkit" hiding here.
4. **Most promising to push on:** **WebElementChat** (novel, privacy-first, just needs a real backend) and **CasaSpese** (mature, real value, principled design).
5. **`.DS_Store` files everywhere** — harmless but worth a global gitignore habit.
```
