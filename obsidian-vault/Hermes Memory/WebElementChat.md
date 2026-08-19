# WebElementChat

Updated: 2026-06-13 11:52:01 CEST

## One-line purpose

WebElementChat is a local-first Chrome extension plus localhost bridge that lets the user select a specific DOM element in the browser and chat with Hermes about that exact element from a Chrome side panel.

## Why this project exists

The user wants a browser-based exploratory analysis workflow where they can visually point at a page element, especially in Google Workspace / Gmail / Google Admin pages, and then ask the agent about “this” without manually describing the element, taking screenshots, or knowing the underlying API.

The key UX requirement is:

> User clicks/selects a page element visually → extension captures structured DOM/context → sidebar chat lets the user ask about that selected element → Hermes receives the selected-element context automatically.

## Project location

```text
/Users/fausto/Software/WebElementChat
```

Primary README:

```text
/Users/fausto/Software/WebElementChat/README.md
```

Chrome extension folder:

```text
/Users/fausto/Software/WebElementChat/extension
```

## Current architecture

Components:

1. Chrome MV3 extension
   - Side panel UI for selection preview and chat.
   - Background service worker for opening the side panel, injecting the picker, and passing messages.
   - Content script for page-level element picking and DOM extraction.

2. Local Python bridge server
   - Runs on `127.0.0.1:8765`.
   - Stores latest selected element and histories under the project `state/` directory.
   - Provides `/chat`, which either returns a stub or shells out to a configured agent command.

3. Hermes wrapper script
   - `/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh`
   - Reads the composed prompt from stdin.
   - Runs Hermes as a quiet one-shot agent call:

```bash
hermes chat -Q --source webelementchat -q "$prompt"
```

## Current server command

To start the bridge with real Hermes responses:

```bash
cd /Users/fausto/Software/WebElementChat
WEBELEMENTCHAT_AGENT_COMMAND=/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh python3 server.py
```

Server URL:

```text
http://127.0.0.1:8765
```

Health endpoint:

```text
http://127.0.0.1:8765/health
```

As of this note, the server was verified running and `/chat` returned `mode=agent` after the wrapper was configured.

## HTTP endpoints

```text
GET  /health
GET  /selected
POST /select
POST /chat
GET  /chat/history
```

Behavior:

- `POST /select`: content script sends selected element JSON to the bridge.
- `GET /selected`: returns latest selection from `state/last_selection.json`.
- `POST /chat`: combines user message with selected element context and sends it to the configured local agent command.
- `GET /chat/history`: returns chat records from `state/chat_history.jsonl`.

## Important files

```text
/Users/fausto/Software/WebElementChat/server.py
/Users/fausto/Software/WebElementChat/selection.py
/Users/fausto/Software/WebElementChat/picker.js
/Users/fausto/Software/WebElementChat/bookmarklet.txt
/Users/fausto/Software/WebElementChat/open-chrome.sh
/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh
/Users/fausto/Software/WebElementChat/tests/test_server.py
```

Extension files:

```text
/Users/fausto/Software/WebElementChat/extension/manifest.json
/Users/fausto/Software/WebElementChat/extension/background.js
/Users/fausto/Software/WebElementChat/extension/content.js
/Users/fausto/Software/WebElementChat/extension/sidepanel.html
/Users/fausto/Software/WebElementChat/extension/sidepanel.js
/Users/fausto/Software/WebElementChat/extension/sidepanel.css
/Users/fausto/Software/WebElementChat/extension/README.md
```

State files:

```text
/Users/fausto/Software/WebElementChat/state/last_selection.json
/Users/fausto/Software/WebElementChat/state/history.jsonl
/Users/fausto/Software/WebElementChat/state/chat_history.jsonl
/Users/fausto/Software/WebElementChat/state/google-admin-subscriptions.csv
```

## Chrome extension installation / reload

Install unpacked extension from:

```text
/Users/fausto/Software/WebElementChat/extension
```

Chrome steps:

1. Open `chrome://extensions/`.
2. Enable Developer Mode.
3. Click “Load unpacked”.
4. Select `/Users/fausto/Software/WebElementChat/extension`.
5. After code changes, click the extension reload/refresh button.
6. If Chrome requests new site permissions, approve them.

The extension name is currently `WebElementChat`.

## Chrome permissions decision

The side panel’s “Select element” button injects `content.js` into the active tab via `chrome.scripting.executeScript`. Chrome’s `activeTab` grant was not sufficient when the user gesture originated inside the side panel. The extension initially failed with:

```text
Could not activate picker: Cannot access contents of the page. Extension manifest must request permission to access the respective host.
```

Fix applied in `extension/manifest.json`:

```json
"host_permissions": [
  "http://127.0.0.1:8765/*",
  "http://localhost:8765/*",
  "http://*/*",
  "https://*/*"
]
```

Security implication: broad page host permission is currently required for reliable side-panel-triggered injection across arbitrary web pages. Data minimization remains the safety boundary: inject only after explicit “Select element”; send only selected element context and explicit chat messages; do not collect cookies, passwords, auth headers, localStorage, sessionStorage, or browser profile data.

## Captured selected-element fields

`content.js` currently captures:

- `captured_at`
- `pickerSource`
- `url`
- `title`
- `tagName`
- CSS `selector`
- `xpath`
- selected element `text`
- selected element `outerHTML`, truncated
- selected element `attributes`
- bounding `rect`
- `viewport`
- nearest `dataRegion`
  - tag name
  - selector
  - XPath
  - ARIA role
  - text
  - rect
- `table`
  - kind
  - selector
  - visible row count
  - max visible column count
  - visible rows if detected

## Current side panel behavior

The side panel includes:

- Bridge status indicator.
- “Select element” button.
- Selected element preview:
  - page title
  - URL
  - element summary
  - selector
  - text preview
  - visible table/grid preview if extracted
- Chat log.
- Chat input that posts to `POST /chat` with current `selected_element`.

The side panel receives selection updates via extension runtime messaging and also stores latest selection in `chrome.storage.local`.

## Agent integration behavior

`server.py` reads `WEBELEMENTCHAT_AGENT_COMMAND`. If unset, `/chat` returns a clear stub response explaining what would be sent. If set, `/chat` executes the configured command with the composed prompt on stdin and uses stdout as the assistant reply.

Current wrapper:

```text
/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh
```

Wrapper content at creation time:

```bash
#!/usr/bin/env bash
set -euo pipefail

prompt=$(cat)
exec /Users/fausto/.local/bin/hermes chat -Q --source webelementchat -q "$prompt"
```

Smoke test performed:

- Prompt: `Reply with exactly: bridge-agent-ok`
- `/chat` response mode: `agent`
- Response: `bridge-agent-ok`

## Verified commands

Syntax/tests have been verified with:

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
```

Additional live checks performed:

```bash
curl -sS http://127.0.0.1:8765/health
curl -sS -X POST http://127.0.0.1:8765/select ...
curl -sS -X POST http://127.0.0.1:8765/chat ...
```

## Example real-world use: Google Admin subscriptions

The user selected a Google Admin Console subscriptions region:

```text
URL: https://admin.google.com/ac/billing/subscriptions?journey=218
Title: Abbonamenti - Console di amministrazione
Selector: div#yDmH0d > c-wiz > div > div:nth-of-type(1) > div[role="main"] > div:nth-of-type(2) > div:nth-of-type(1) > div > div:nth-of-type(2) > div > article > div:nth-of-type(3) > div > div
```

The selected text contained a subscription table, but the extractor reported:

```text
Visible table rows captured: 0
```

Reason: Google Admin’s table DOM did not match the current HTML table / ARIA grid / heuristic row extraction patterns. However, the relevant data was present in the selected element’s plain text, so Hermes manually parsed it and wrote a CSV file.

CSV saved at:

```text
/Users/fausto/Software/WebElementChat/state/google-admin-subscriptions.csv
```

CSV contents:

```csv
Nome,Tipo,Stato,Licenze,Piano di pagamento,Rivenditore,Pagamento dovuto
Google Workspace for Education Fundamentals,,Attivo,"2.358 disponibili, 142 assegnate",Prezzi per i rivenditori,tech data italy,Prezzi per i rivenditori
Google Workspace for Education Fundamentals - Utente archiviato,,Attivo,"2.499 disponibili, 1 assegnate",Prezzi per i rivenditori,tech data italy,Prezzi per i rivenditori
Google Workspace for Education Plus (Staff),Componente aggiuntivo Google Workspace,Attivo,"8 disponibili, 17 assegnate",Prezzi per i rivenditori,tech data italy,Prezzi per i rivenditori
Google Workspace for Education Plus,Componente aggiuntivo Google Workspace,Attivo,"62 disponibili, 38 assegnate",Prezzi per i rivenditori,tech data italy,Prezzi per i rivenditori
Utente solo Gmail di Google Workspace for Education,,Attivo,"2.500 disponibili, 0 assegnate",Prezzi per i rivenditori,tech data italy,Prezzi per i rivenditori
```

This revealed an important next improvement: support Google Admin’s custom table/list DOM by using stronger row heuristics and/or parsing structured text as fallback.

## Known limitations and next improvements

1. No streaming responses yet.
   - `/chat` is synchronous.
   - Long Hermes responses block until complete.

2. No persistent side-panel conversation session yet.
   - Current Hermes wrapper uses one-shot `hermes chat -q`.
   - Future improvement: create a named/resumable WebElementChat session so sidebar chat has continuity.

3. Google Workspace / Google Admin virtualized tables are imperfect.
   - DOM often contains only visible rows.
   - Some tables are custom components and not `<table>` or obvious ARIA grids.
   - Current extractor may return `table.kind = none` even when selected text clearly contains table-like data.

4. No element screenshot capture yet.

5. No scroll-and-collect yet.

6. Broad host permissions are currently used for practical side-panel injection.
   - Future improvement may use per-site optional permissions or another Chrome API pattern.

## Suggested next technical tasks

- Improve `extractHeuristicRows()` in `extension/content.js` for Google Admin tables.
- Add fallback text-to-table parsing when `table.rows` is empty but selected/data-region text contains repeated tabular blocks.
- Add a “Download CSV” button in the side panel when table-like data is present.
- Add `/export/csv` endpoint or client-side CSV export.
- Add streaming responses with Server-Sent Events or fetch streaming.
- Add named Hermes session continuity for sidebar chats.
- Add screenshot-of-selected-element capture.
- Add scroll-and-collect for virtualized grids.
- Consider a proper MCP layer later, but avoid premature MCP complexity until side panel UX is solid.

## 2026-06-16 Portfolio Review Notes

Source: [[Software Projects Review 2026-06-16]]

The portfolio review classified WebElementChat as the most novel idea in `/Users/fausto/Software` and one of the two strongest projects to push on.

Review takeaways:

- “Point and say this to an AI” is a real UX gap.
- Especially useful for Workspace admins drowning in data tables.
- Clear privacy posture makes the project credible:
  - localhost / `127.0.0.1` only;
  - no full-page capture;
  - no credentials;
  - explicit selection before sending context.
- Review state said bridge, extension, and tests were working, while real agent integration was still a stub requiring `WEBELEMENTCHAT_AGENT_COMMAND`.
- Note: this review-state line conflicts with this note's earlier verified status from 2026-06-13, where `WEBELEMENTCHAT_AGENT_COMMAND` had been configured and `/chat` returned `mode=agent`. Prefer live verification/current note for operational state.
- Review said streaming and virtualized-grid scroll-collect were still unimplemented.
- Review suggested scripts-ai work could feed WebElementChat as part of a larger personal AI toolkit.

## Deep portfolio assessment notes

Source: [[Deep Portfolio Assessment 2026-06-16]]

Claude's deeper project review keeps WebElementChat as a high-priority project because it has the highest novelty/upside and a relatively small gap to day-to-day usefulness.

Key development directions from that assessment:

- Treat `state/` as sensitive runtime data and keep captured real Workspace/Admin data out of versioned project state.
- Make the default agent path work out of the box via `scripts/hermes-agent.sh` or a CasaSpese-style `agentapi` backend.
- Add streaming `/chat` for long agent responses.
- Add scroll-and-collect for virtualized grids, especially Google Workspace/Admin tables.
- Add multi-turn session continuity.
- Longer-term: expose selected-element context through an MCP tool layer, but only after the basic backend/streaming/scroll-collect UX is solid.

Cross-project leverage:

- Adopt CasaSpese's subscription-CLI backend pattern.
- Use SpreadGit/Sheets ideas for selected-table → Sheet export or patch workflows.

## Related notes

- [[Projects]]
- [[Software Projects Review 2026-06-16]]
- [[Cross-Project Patterns 2026-06-16]]
- [[Deep Portfolio Assessment 2026-06-16]]
- [[Workflows]]
- [[Decisions]]
- [[Environment]]
