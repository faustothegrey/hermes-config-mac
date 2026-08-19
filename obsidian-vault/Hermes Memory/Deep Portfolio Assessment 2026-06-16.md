# Deep Portfolio Assessment 2026-06-16

Source: Claude Code delegated exploratory assessment, orchestrated by Hermes.
Root reviewed: `/Users/fausto/Software`
Related notes: [[Software Projects Review 2026-06-16]], [[Cross-Project Patterns 2026-06-16]], [[Projects]]

Hermes role for this note: manager/curator. Claude Code performed the substantive assessment. Hermes only checked glaring inconsistencies before storing the result.

## Hermes correction / caveat

Claude's final report contained one wording inconsistency around CasaSpese git state:

- Verified by Hermes: `/Users/fausto/Software/CasaSpese/.git` does **not** exist.
- Verified by Hermes: `/Users/fausto/Software/CasaSpese/casa-spese-ui/.git` **does** exist.
- Therefore, the accurate framing is: CasaSpese root is not a git repo, while the UI subproject is a git repo.
- The UI repo `.gitignore` protects `token.json`, `.env*`, `.DS_Store`, `*.csv`, and `data/transactions.json` inside `casa-spese-ui`.
- Remaining risk: parent-level files such as `/Users/fausto/Software/CasaSpese/credentials.json`, if present, are outside the UI repo and still plaintext local credential files. This note stores filenames only, not secret contents.

## Portfolio-wide summary from Claude

- CasaSpese is the most mature project and has the most immediate value, but also the most important hygiene/data-risk work.
- WebElementChat remains the most novel/high-upside project and should become actually usable by wiring a real default backend and improving virtualized table handling.
- ScienceClick2 is the best-engineered project and should export its reusable multi-agent skills-sync pattern.
- scripts-ai is a practical utility cluster that should become a single `ai-quota` command and feed agent backend choices.
- SpreadGit is a clean reusable primitive that should be consumed by CasaSpese rather than remaining orphaned.
- MyAppScriptSidebar is best treated as a reference/template asset.
- ScrapeCircolari2 is a useful one-off that should be documented, de-vendored, and possibly scheduled/summarized.
- CertiCPIAHtml should be finalized rather than over-engineered.
- `scripts` should be archived after checking for live credentials.
- `scripts_and_conf` is empty and could either be deleted or repurposed as a shared toolkit home.

## Ranked portfolio roadmap — top 10 moves

1. **Secrets/data hygiene sweep across the portfolio.**
   - Create/verify ignore rules before any new repo initialization.
   - CasaSpese root should protect `credentials.json`, `token.json`, financial JSON, CSVs, `.env*`, `.DS_Store`.
   - WebElementChat `state/` should be treated as sensitive runtime data.
   - Check `scripts/db_conn_conf.py` before sharing or archiving.

2. **Wire WebElementChat to a real agent by default.**
   - Reuse CasaSpese's `agentapi` subscription backend or default to `scripts/hermes-agent.sh`.
   - Goal: make the most novel project usable without manual environment setup.

3. **Extract a shared toolkit.**
   - Candidate home: `scripts_and_conf/` or a new `shared/` folder.
   - Include ScienceClick2's `sync-skills.py` pattern.
   - Include scripts-ai's PATH-resilient command resolution / subprocess runner pattern.
   - Avoid over-building a service; start as shared scripts/functions.

4. **Make CasaSpese use SpreadGit for Google Sheets writes.**
   - Replace or supplement ad-hoc range writes with minimal structured deltas.
   - This aligns with CasaSpese's deterministic/versioned/auditable design.

5. **Add tests to pure cores.**
   - CasaSpese: `classificaWith`, `findMatchingRuleIds`, `suggestKeyword`.
   - SpreadGit: `computePatch` and patch application logic.
   - These should be cheap, high-confidence tests.

6. **Unify scripts-ai into one `ai-quota` command.**
   - Add `--provider all` and JSON output.
   - Later, expose quota status to CasaSpese/WebElementChat backend selectors.

7. **Decompose CasaSpese's monolithic page.**
   - Claude observed `casa-spese-ui/src/app/page.tsx` as around 1098 lines.
   - Extract components/hooks and add a rule-coverage view.

8. **Add WebElementChat scroll-and-collect plus streaming chat.**
   - Virtualized grids are central to the intended Google Workspace/Admin use case.
   - Streaming matters for UX when agent responses are long.

9. **Harden ScienceClick2 result/match stores.**
   - Prepare for concurrent classroom use.
   - Add Sheets export of results if it becomes operationally useful.

10. **Archive/de-vendor legacy utilities.**
   - Move/archive stale `scripts` after checking for credentials.
   - Replace ScrapeCircolari2 committed venv with `requirements.txt` and ignored venv.

## Project: CasaSpese

Detailed note: [[CasaSpese]]
Path: `/Users/fausto/Software/CasaSpese`
UI path: `/Users/fausto/Software/CasaSpese/casa-spese-ui`
Priority: high
Confidence from Claude: high

### Identity

CasaSpese is a deterministic personal-finance reconciliation system built as a Next.js 16 / React 19 app. It ingests bank statement CSVs, categorizes transactions through explicit versioned rules, syncs with Google Sheets, models recurrences/cash items, and includes a `consulente` AI advisor backed by local subscription CLIs.

### Evidence Claude read

- `casa-spese-ui/src/lib/rules.ts`
  - Pure rule classification functions such as `classificaWith`.
  - Rule versioning via `RULES_VERSION = "2026.06"`.
  - First-match-wins deterministic classification.
  - Seed rules such as X-01 / R-001 through R-051.
- `casa-spese-ui/src/lib/rules-store.ts`
  - User rules are prepended.
- `casa-spese-ui/src/lib/consulente/manager.ts`
  - Spawns `~/.local/bin/agentapi server` per backend.
  - Backends: Claude, Codex, Antigravity.
  - Strips selected API-key environment variables to prefer subscriptions rather than paid APIs.
  - Claude gets context via `--append-system-prompt`.
- `casa-spese-ui/src/lib/consulente/context.ts`
  - Builds the advisor context.
  - Reads selected Obsidian notes from a CasaSpese vault path.
  - Tells the agent not to use tools, reducing permission prompts.
- `casa-spese-ui/src/lib/google-auth.ts`
  - OAuth/token handling.
- API routes for `rules`, `recurrences`, `transactions`, `archive`, `sheets`, and `consulente`.
- Pages: home, `investimenti`, `pro`, `consulente`.

### Strengths to preserve

- Deterministic, versioned, pure-function classification.
- Explicit “no black-box ML” position for financial reconciliation.
- Subscription-CLI-as-backend pattern via `agentapi`.
- Context injection into the AI advisor without letting the advisor use arbitrary tools.
- Working OAuth / Google Sheets integration.

### Weaknesses, risks, gaps

- CasaSpese root is not a git repo, while `casa-spese-ui` is a sub-repo. Hygiene must be handled at the root before any root repo is created.
- Parent-level credential files are not protected by the UI repo’s `.gitignore`.
- `page.tsx` is large/monolithic.
- Some portfolio/investment data appears hardcoded in source.
- Pure rule engine currently lacks the tests it naturally invites.
- Categories may be partly hardcoded and personally specific.

### Quick wins

- Add/verify a CasaSpese-root `.gitignore` before any root `git init`.
- Add unit tests for `classificaWith`, `findMatchingRuleIds`, and `suggestKeyword`.
- Move categories/config out of code where practical.

### Medium bets

- Add a rule-change audit log: which rule version classified which transaction and when.
- Add a rule-coverage view: percent auto-classified vs `DA_DECIDERE`.
- Decompose the large home page into components/hooks.
- Replace ad-hoc Sheets writes with SpreadGit-style minimal diffs.

### Ambitious/product directions

- Extract a deterministic ledger/reconciliation library.
- Add multi-bank/multi-account CSV adapters.
- Add advisor explanations for classifications using the existing `consulente` context.

### Cross-project leverage

- Consume SpreadGit for Sheets writes.
- Donate the `agentapi`/env-strip backend pattern to WebElementChat and scripts-ai.
- Reuse the Vault-as-context pattern more broadly.

## Project: ScienceClick2

Detailed note: [[ScienceClick2]]
Path: `/Users/fausto/Software/ScienceClick2`
Priority: medium
Confidence from Claude: high for engineering/skills, medium for runtime stores

### Identity

ScienceClick2 is a Next.js 16 / React 19 educational tool where teachers create image-based labeling scenes and students drag words onto correct targets. It includes spectator mode, result/match stores, i18n, and multiple scene categories.

### Evidence Claude read

- Scene pages and APIs under `src/app/scenes/[id]/...`.
- Editor components such as `Canvas.tsx`, `WordList.tsx`, `PracticePanel.tsx`, `HeaderBar.tsx`.
- Libraries such as `scenePaths.ts`, `i18n.ts`, `resultsStore.ts`, `matchStore.ts`.
- Scene data under `public/scenes/<category>/<scene>/`.
- Source materials under `sources/{matter,geology,biology}`.
- Multi-agent skill source: `skills/create-scene/{skill.md,config.json}`.
- Skill compiler: `scripts/sync-skills.py`.
- Project guidance: `CLAUDE.md`, `PROJECT.md`, AGENTS guidance.

### Strengths to preserve

- Best-engineered repo structure in the portfolio.
- Clean source-of-truth skill compilation workflow.
- Good code/content separation with scenes as data.
- Disciplined project docs and worktree conventions.

### Weaknesses, risks, gaps

- `future-scenes/` was observed as untracked in prior review.
- File/JSON-backed stores may not survive concurrent classroom use or deployment.
- Match/result logic likely needs automated tests.

### Quick wins

- Commit or intentionally ignore `future-scenes/`.
- Extract/document the `sync-skills.py` pattern for use elsewhere.
- Add a few new scenes using the existing create-scene skill.

### Medium bets

- Harden results/match stores for classroom concurrency.
- Add Google Sheets export for results if useful.
- Add teacher analytics such as per-term error rates.

### Ambitious/product directions

- Shareable scene packs.
- Hosted multi-classroom mode.
- Prompt-assisted scene generation with a human review loop.

### Cross-project leverage

- Source of the multi-agent skills-sync pattern for CasaSpese, WebElementChat, scripts-ai, and future projects.
- Could consume a shared Google Sheets export layer.

## Project: WebElementChat

Detailed note: [[WebElementChat]]
Path: `/Users/fausto/Software/WebElementChat`
Priority: high
Confidence from Claude: high

### Identity

WebElementChat is a local-first Chrome MV3 extension plus Python bridge on `127.0.0.1:8765`. The user selects a DOM element and chats about that exact element with structured context such as selector, XPath, attributes, bounding box, and table rows.

### Evidence Claude read

- `server.py`
- `selection.py`
- `picker.js`
- `bookmarklet.txt`
- `open-chrome.sh`
- `extension/manifest.json`
- `extension/background.js`
- `extension/content.js`
- `extension/sidepanel.js`, `.html`, `.css`
- `scripts/hermes-agent.sh`
- `tests/test_server.py`
- Runtime state files under `state/`

### Strengths to preserve

- Most novel concept in the portfolio.
- Strong privacy posture: localhost, explicit selection, no full-page capture, no credentials/cookies/storage, truncation.
- Clean HTTP contract and test coverage.
- Agent layer is pluggable through stdin/stdout.

### Weaknesses, risks, gaps

- Agent integration may still depend on environment setup rather than working by default.
- Runtime `state/` data can contain sensitive real Workspace/Admin information.
- Broad host permissions are practically useful but expand the extension’s attack surface.
- No streaming yet.
- Virtualized grids are the central use case but only partly handled.

### Quick wins

- Ensure `state/` is ignored/treated as runtime sensitive data.
- Make the default agent path work out of the box via `scripts/hermes-agent.sh` or an `agentapi` backend.
- Turn the privacy constraints into a prominent project doctrine / extension listing text.

### Medium bets

- Add streaming `/chat`.
- Add scroll-and-collect for virtualized grids.
- Add multi-turn session continuity.

### Ambitious/product directions

- MCP tool layer exposing the selected element to any MCP client.
- Packaged/distributed extension.
- Select table → export/patch to Sheets via SpreadGit.

### Cross-project leverage

- Adopt CasaSpese’s `agentapi` backend pattern.
- Feed selected tables into SpreadGit or CasaSpese-style reconciliation flows.
- Continue linking with Hermes/Obsidian memory via `--source webelementchat`.

## Project: ScrapeCircolari2

Path: `/Users/fausto/Software/ScrapeCircolari2`
Priority: low-medium
Confidence from Claude: medium

### Identity

ScrapeCircolari2 is a scraper for Nettuno PA / registro elettronico / albo pretorio content. It includes login handling and a polite crawler for listing publications and downloading PDFs.

### Evidence Claude read

- `login.py`
- `list.py`
  - Base domain: `albopretorio.nettunopa.it`.
  - Descriptive user agent.
  - `ThrottledClient` with delay, jitter, retry, backoff.
  - PDF download toggle.
  - `--archivio=storico` support.
- Bundled virtual environment under `scrapecircolari2/`.

### Strengths to preserve

- Responsible scraping behavior: identifying UA, rate limiting, jitter, single-request-at-a-time, backoff.
- Useful one-off for school notice data.

### Weaknesses, risks, gaps

- No README/docs.
- Feature toggles are in source rather than CLI/config.
- Bundled virtualenv bloats the tree.
- Reverse-engineered login flow may be brittle.

### Quick wins

- Add `requirements.txt`.
- Ignore/remove committed venv.
- Add a short README.
- Promote toggles to CLI flags.

### Medium bets

- Schedule it to detect new notices and notify.
- Dedupe/index downloaded PDFs.

### Ambitious/product directions

- AI digest of new school notices via local subscription backend.
- Feed useful institutional content into Obsidian or a CPIA knowledge base.

### Cross-project leverage

- Reusable polite HTTP client pattern.
- Outputs could feed Hermes/Obsidian ingest or CertiCPIAHtml content.

## Project: CertiCPIAHtml

Path: `/Users/fausto/Software/CertiCPIAHtml`
Priority: low
Confidence from Claude: medium

### Identity

CertiCPIAHtml contains static/near-static HTML iterations for CPIA 1 Pisa digital-skills exam / EDSC test-center communication pages.

### Evidence Claude read

- `progetto_v1.html`
- `pages/progetto_v2.html`
- `pages/page.html`
- `pages/page3.html`
- `pages/page.js`
- `pages/banner.html`

### Strengths to preserve

- Lightweight, easy to host.
- Multiple design variants available for comparison.
- Institutional styling already present.

### Weaknesses, risks, gaps

- Version sprawl: v1/v2/page/page3/banner with no canonical final.
- Possible duplicated markup.
- Accessibility/responsive quality unknown.

### Quick wins

- Choose a canonical final version.
- Move old versions into `drafts/` or archive.
- Run an accessibility/contrast pass.

### Medium bets

- Extract shared header/banner into a small template.
- Deploy to a stable URL.

### Ambitious/product directions

- Small content-managed CPIA test-center info site.
- Use ScrapeCircolari2 or Obsidian as a content feed only if genuinely useful.

### Cross-project leverage

- Could share CPIA-facing visual language with other institutional artifacts.

## Project: scripts-ai

Path: likely `/Users/fausto/Software/scripts-ai`
Priority: medium
Confidence from Claude: high

### Identity

scripts-ai contains AI CLI quota monitors for Claude Code, Codex, and Antigravity, built over a shared `ai_quota_lib.py`.

### Evidence Claude read

- `ai_quota_lib.py`
  - `resolve_command` searches normal PATH plus `~/.local/bin`, `~/bin`, and nvm locations.
  - `run` wraps subprocess execution with timeout and return code capture.
  - `parse_ts` and quota-time parsing helpers.
- Thin executables such as `claude-quota`, `codex-quota`, `antigravity-quota`.

### Strengths to preserve

- PATH-resilient command discovery is broadly reusable.
- Shared library with thin provider-specific wrappers is good factoring.
- Solves a real pain point: subscription limits.

### Weaknesses, risks, gaps

- Three separate commands over one library.
- Some parsing of interactive `/status` screens may be brittle as CLIs change.
- No consolidated dashboard/status view.

### Quick wins

- Add one `ai-quota` command with `--provider all`.
- Add JSON output.

### Medium bets

- History logging and burn-rate trends.
- Hermes routine warning before quota limits hit.
- UI/status-bar/menu-bar widget.

### Ambitious/product directions

- Local dashboard for Claude/Codex/Antigravity usage.

### Cross-project leverage

- Feed quota information into CasaSpese and WebElementChat backend selectors.
- Donate `resolve_command` to shared local-agent-runner tooling.

## Project: SpreadGit

Path: `/Users/fausto/Software/SpreadGit`
Priority: medium
Confidence from Claude: medium-high

### Identity

SpreadGit is a small JS library that applies git-style/jsondiffpatch deltas to Google Sheets rows via Sheets API v4.

### Evidence Claude read

- `README.md`
  - API: `computePatch`, `applyPatch`, `sheetValuesToObjects`, `objectsToSheetValues`, `updateSheet`, `applyStructuredPatchToSheet`.
- `package.json`
- Source file referenced: `src/sheetPatch.js`.

### Strengths to preserve

- Clean single-responsibility library.
- Well-documented API.
- Strong fit for minimal-diff/auditable Sheets writes.

### Weaknesses, risks, gaps

- Orphaned / not consumed by CasaSpese.
- Tests not visible in Claude’s pass.
- Auth integration is left to callers; good for library design but needs examples.

### Quick wins

- Add examples using CasaSpese’s authenticated Google client.
- Add unit tests around `computePatch`.

### Medium bets

- Make CasaSpese depend on it locally.
- Add conflict detection for keys matching more than one row.

### Ambitious/product directions

- “Sheets as versioned store”: commit/log/revert row deltas.

### Cross-project leverage

- CasaSpese is the canonical consumer.
- ScienceClick2 could use it for results export.
- WebElementChat could use it for selected-table → Sheet workflows.

## Project: MyAppScriptSidebar

Path: `/Users/fausto/Software/MyAppScriptSidebar`
Priority: low
Confidence from Claude: high

### Identity

MyAppScriptSidebar is a Google Apps Script sidebar template for Sheets. It adds a custom menu, shows a sidebar form, appends rows, and includes a Gemini helper.

### Evidence Claude read

- `Code.js`
  - `onOpen`
  - `showSidebar`
  - `processForm`
  - `callGemini`
  - Placeholder `YOUR_GEMINI_API_KEY`
- `Sidebar.html`
- `DEPLOYMENT.md`

### Strengths to preserve

- Good minimal Sheets-sidebar starter.
- Demonstrates a Workspace-native AI pattern.

### Weaknesses, risks, gaps

- Template only; not a current product.
- API key handling in Apps Script needs careful documentation.
- Gemini model ID may be dated.

### Quick wins

- Keep as canonical Workspace sidebar snippet.
- Add explicit key-handling caveats to deployment docs.

### Medium bets

- Turn into a configurable columns/sidebar template.

### Ambitious/product directions

- “WebElementChat-lite for Sheets”: send active Sheets selection to a local or configured agent.

### Cross-project leverage

- Overlaps with WebElementChat’s in-context AI over Workspace data.
- Overlaps with CasaSpese / SpreadGit Sheets writes.

## Project: scripts

Path: `/Users/fausto/Software/scripts`
Priority: low / archive
Confidence from Claude: medium

### Identity

Legacy RethinkDB/MySQL population/query scripts from around 2021–2022.

### Evidence Claude read

- `db_conn_conf.py` (not printed/inspected for secrets)
- `populate_rethink_db_local`
- `query_testing`
- `get_overlay`
- `default.ovl`
- Compiled `.pyc` files observed.

### Strengths to preserve

- Historical reference only.

### Weaknesses, risks, gaps

- Stale.
- May contain local DB connection details.
- Contains generated/cache artifacts.

### Quick wins

- Verify no live credentials before sharing.
- Move to archive or remove from active project view.

### Cross-project leverage

- None identified.

## Project: scripts_and_conf

Path: `/Users/fausto/Software/scripts_and_conf`
Priority: low
Confidence from Claude: high

### Identity

Empty or near-empty placeholder directory, with `bin/` effectively empty.

### Strengths / weaknesses

- Current strength: available namespace.
- Current weakness: clutter / unclear purpose.

### Further development options

- Delete it if not needed.
- Or repurpose it as the shared cross-project utilities home.

Potential shared contents:

- `sync-skills.py` extracted from ScienceClick2.
- `resolve_command` / subprocess helpers inspired by scripts-ai.
- local-agent-runner helpers.
- portfolio-wide gitignore/templates.

## Things to strengthen globally

### Secrets and sensitive data

- Establish a global convention: no real data in repos, use fixtures.
- Add root `.gitignore` files before `git init` in project roots.
- Treat `state/`, financial data, credentials, tokens, CSV exports, `.env*`, and DB config files as sensitive by default.
- Keep vault notes filename-only for sensitive files; do not store secret contents.

### Engineering hygiene

- Add a global `.gitignore` habit for `.DS_Store`, `node_modules`, `__pycache__`, venvs, `.next`, `.env*`, tokens, CSV/data dumps.
- Remove vendored virtualenvs and generated caches from active project trees.
- Add `PROJECT.md` / README identity to every active project.

### Tests

- Start with pure cores:
  - CasaSpese rule engine.
  - SpreadGit patch engine.
  - ScienceClick2 matching logic.
- Avoid heavy integration tests until the core tests exist.

### Reusable templates

- Extract or document the personal Next.js starter shared by CasaSpese and ScienceClick2.
- Extract the multi-agent skills-sync pattern.
- Extract a PATH-resilient local command runner.
- Avoid building a grand framework before two projects actively use the same helper.

### Agent workflows

- ScienceClick2’s skills-sync pattern should become the canonical way to maintain Claude/Codex/agent-specific instructions.
- CasaSpese’s `agentapi` backend pattern should become the canonical way to run local subscription CLIs.
- scripts-ai quota data should inform backend selection.

### Positioning

Claude’s suggested portfolio positioning:

> Fausto’s local-first, subscription-powered AI toolkit for an Italian educator/admin.

This fits the strongest projects:

- WebElementChat: point-at-element admin assistant.
- CasaSpese: deterministic local finance reconciliation + local AI advisor.
- scripts-ai: quota/usage awareness for subscription CLIs.
- ScienceClick2: multi-agent skill authoring and educational tools.

## Ideas probably not worth doing yet

- A universal agent-backend microservice. Start with shared functions/scripts first.
- Publishing SpreadGit publicly. Make CasaSpese consume it locally first.
- Full multi-tenant/hosted ScienceClick2 or CasaSpese. Their local/single-user nature is a strength for now.
- MCP layer for WebElementChat before default agent wiring, streaming, and scroll-collect are solved.
- Rewriting ScrapeCircolari2 or CertiCPIAHtml. Document/archive/finish instead.
- A grand unified dashboard combining quota, finance, scenes, and everything else. Build small consolidations first.

## Suggested Obsidian structure from Claude

Claude suggested a richer foldered structure:

```text
Software Portfolio/
  _Index.md
  Roadmap (Top 10).md
  Patterns/
    Subscription-CLI Backend.md
    Skills Sync (sync-skills).md
    Google Sheets Layer.md
    PATH-Resilient Exec.md
    Polite Scraping.md
    Local-First / Privacy.md
  Projects/
    CasaSpese.md
    ScienceClick2.md
    WebElementChat.md
    ScrapeCircolari2.md
    CertiCPIAHtml.md
    scripts-ai.md
    SpreadGit.md
    MyAppScriptSidebar.md
    scripts (legacy).md
    scripts_and_conf.md
  Risks/
    Secrets & Sensitive Data.md
```

Hermes implementation choice for now:

- Keep the main Hermes Memory structure flat, consistent with existing vault convention.
- Use this note as the detailed assessment hub.
- Update existing per-project notes where they already exist.
- Create separate notes only when a topic becomes active enough to need one.

## Follow-up note updates to consider

- Add a dedicated `scripts-ai.md` note if the quota tooling becomes active again.
- Add a dedicated `SpreadGit.md` note before integrating it into CasaSpese.
- Add a `Secrets & Sensitive Data.md` note only if the user wants an explicit hygiene checklist; keep it filename-only.
- Add a `Local Agent Runner.md` pattern note if work begins on extracting the subscription-CLI backend pattern.

## Related notes

- [[Projects]]
- [[Software Projects Review 2026-06-16]]
- [[Cross-Project Patterns 2026-06-16]]
- [[CasaSpese]]
- [[ScienceClick2]]
- [[WebElementChat]]
- [[Workflows]]
