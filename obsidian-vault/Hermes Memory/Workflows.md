# Workflows

Reusable procedures and operational notes that are not formal Hermes skills yet.

## Delegated project exploration

User preference:

- For exploratory project assessment, pattern discovery, and portfolio-direction work, delegate exploration and assessment to external agent lanes by default.
- Preferred lanes: Claude Code and Antigravity CLI. Claude Code remains a good default for deeper codebase assessment; Antigravity CLI is also available for independent exploration or second-lane comparison.
- Hermes' role is orchestration, memory curation, vault organization, and checking only for glaring inconsistencies.
- Do not provide a separate Hermes second opinion unless the user explicitly requests it.
- Important exception: for the Hermes Agent ecosystem (config, tools, skills, plugins, troubleshooting, development, or anything directly or indirectly part of it) and for managing system services, Hermes should do the work directly unless the user explicitly asks for delegation. For all other software development, Hermes acts as delegating editor.

Antigravity CLI details:

- Working executable: `/Users/fausto/.local/bin/agy`.
- Non-interactive delegation command: `agy --print '<bounded prompt>' --print-timeout 5m`.
- Verified on 2026-06-16 with a simple print-mode prompt returning `ANTIGRAVITY_DELEGATION_OK`.
- Stale/broken symlink: `~/.antigravity/antigravity/bin/agy` points into the GUI app bundle and should not be used.
- There is also an Antigravity IDE binary, but that is the GUI/editor CLI; for delegation use `agy`.

Suggested workflow:

1. Before any long delegation, run a short readiness/auth/availability ping for the candidate delegate. This is a general rule, not just an Antigravity rule.
   - If the candidate returns the expected readiness response, continue.
   - If the candidate prompts for login, times out, errors, or gives a non-answer, treat that delegate as unavailable.
   - When a delegate is unavailable, report that candidate as unavailable and continue with another suitable delegate if available; if no delegate is available, stop and report the delegation failure rather than waiting uselessly.
2. Prepare context for the delegate. Do NOT embed full documents verbatim in the delegation prompt. Instead, use absolute file paths as pointers and rely on the delegate reading the canonical source.
3. Ask the delegated agent to return structured findings with evidence paths, confidence, and suggested vault-note updates.
4. Hermes reads the result, checks only obvious contradictions against known vault memory/current files, and writes durable findings into Obsidian.
5. For broader or more contentious assessments, run Claude Code and Antigravity CLI as independent lanes, then reconcile only the concrete evidence and recurring themes.
6. Keep first-level MEMORY compact: store only the persistent delegation preference and pointers, not detailed findings.

### Sharing context with delegated agents (prefer file pointers over inline text)

**The problem.** Embedding full documents (multi-thousand-word critiques, specs, transcripts) directly in the delegation prompt wastes tokens, risks truncation, and creates a fragile copy where the prompt text and the canonical source can drift.

**The rule.** Give the delegate absolute file paths to canonical documents and let it read them itself. Keep the delegation prompt compact — a one-paragraph summary + pointers.

**Where documents live.** There are two categories:

- **Project design artifacts** (specs, critiques, replies, reviews, implementation notes): the canonical home is the project repo under `design/`. These evolve with the code and are only meaningful in the context of that repo. Copy to vault only if the synthesis is cross-project-significant.
- **Cross-project synthesis** (portfolio assessments, comparative analyses, convergence tables, durable decisions): the canonical home is the vault. These span multiple projects and should be searchable in Obsidian. Bridge-copy to a project repo only when that specific project needs the context for delegation.

**Pattern for the delegation prompt:**

```
Context documents (read from whichever path is reachable):
- Repo (canonical): design/some-document.md
- Vault (copy): ~/Documents/Obsidian Vault/Hermes Memory/Some Document.md
Start by reading the context document, then proceed with the task below.
```

**When to create a bridge copy.** Delegated agents (Claude Code, Antigravity) are sandboxed to their working directory and may not reach `~/Documents/Obsidian Vault/`. Therefore:

- **Project design docs are written to the repo first** — they're already reachable by delegates working in that repo. No bridge needed.
- **Cross-project synthesis** (vault notes) may need a bridge copy into the project repo for delegation. Use `design/` as the bridge location. The bridge copy is temporary convenience — the vault remains canonical for synthesis.

Always give both paths in the prompt so the delegate can try whichever is reachable.

**Step-by-step delegation prep:**

1. Write any new project design documents to the repo `design/` directory first.
2. If the document is cross-project synthesis from the vault, check whether it's reachable from the delegate's working directory. If not, copy it as a bridge: `cp ~/Documents/Obsidian\ Vault/Hermes\ Memory/Document.md <project>/design/document.md`
3. In the delegation prompt, list both paths and a one-line summary of what each document contains.
4. Delegate. The prompt body should be task instructions + pointers only — do not paste full document text.

**Recurring reference documents.** For documents that will be referenced across multiple delegation sessions within the same project, keep them in the project repo under `design/`. For documents referenced across multiple projects, keep them in the vault with bridge copies as needed.

**Post-delegation cleanup.** After the delegation round concludes, remove stale bridge copies from the repo if the vault is the canonical home. Do not remove repo-native design docs — those are permanent project artifacts.

**Verification.** After the delegate completes, Hermes should check whether the delegate successfully read the context documents by skimming the delegate's output for references to the document content. If the delegate clearly didn't access the context, flag this as a delegation quality issue.


## WebElementChat operation

Detailed project memory: [[WebElementChat]].

### Start bridge with Hermes agent enabled

```bash
cd /Users/fausto/Software/WebElementChat
WEBELEMENTCHAT_AGENT_COMMAND=/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh python3 server.py
```

### Reload extension after file changes

1. Open `chrome://extensions/`.
2. Find `WebElementChat`.
3. Click the reload/refresh button.
4. Approve new site permissions if Chrome asks.

### Verify project quickly

```bash
cd /Users/fausto/Software/WebElementChat
python3 -m unittest discover -s tests -v
python3 -m py_compile server.py selection.py
python3 -m json.tool extension/manifest.json >/dev/null
node --check extension/background.js
node --check extension/content.js
node --check extension/sidepanel.js
bash -n open-chrome.sh
bash -n scripts/hermes-agent.sh
curl -sS http://127.0.0.1:8765/health
```

### If side-panel chat returns a stub

The server was started without `WEBELEMENTCHAT_AGENT_COMMAND`. Stop it and restart with:

```bash
WEBELEMENTCHAT_AGENT_COMMAND=/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh python3 /Users/fausto/Software/WebElementChat/server.py
```

### If picker injection fails with host permission error

Check that `extension/manifest.json` includes broad host permissions:

```json
"http://*/*",
"https://*/*"
```

Then reload the extension in Chrome and approve the permission request.

