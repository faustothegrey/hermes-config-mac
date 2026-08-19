# WebElementChat prototype notes

Session-derived implementation notes for a local browser element selection workflow.

## Problem

The user wanted to point at a table/region in a live browser page and say things like "analyze this table" without manually describing which table. Screenshots were explicitly not the desired workflow; the agent needed structured context from the selected page element.

## Implemented project shape

A local project was created with this shape:

```text
WebElementChat/
├── server.py
├── picker.js
├── bookmarklet.txt
├── selection.py
├── open-chrome.sh
├── README.md
├── tests/
│   └── test_server.py
├── state/
│   ├── last_selection.json
│   ├── history.jsonl
│   └── chat_history.jsonl
└── extension/
    ├── manifest.json
    ├── background.js
    ├── content.js
    ├── sidepanel.html
    ├── sidepanel.js
    ├── sidepanel.css
    └── README.md
```

Key behavior:

- `server.py` runs a local HTTP server on `127.0.0.1:8765`.
- `POST /select` accepts JSON from the browser and saves it to `state/last_selection.json` and `state/history.jsonl`.
- `GET /selected` returns the latest selection.
- `GET /health` provides a readiness probe.
- `POST /chat` accepts `{message, selected_element?}`. If `selected_element` is omitted, it uses the latest saved selection.
- `GET /chat/history` returns persisted chat records.
- Chat history is appended to `state/chat_history.jsonl`.
- `WEBELEMENTCHAT_AGENT_COMMAND` optionally configures a real local agent command; the prompt is passed on stdin and stdout becomes the assistant response.
- If no agent command is configured, `/chat` returns a clear stub response that confirms the selected selector and visible row count.
- `selection.py` summarizes the latest selection and can export visible table rows to CSV.
- `picker.js`/`content.js` highlight the current element, capture the clicked element, extract structured context, and post it to the bridge.
- `open-chrome.sh` can launch an isolated Chrome profile with CDP enabled, but this is optional for the basic select-and-chat workflow.

## Captured element schema

Useful fields:

```json
{
  "captured_at": "...",
  "pickerSource": "chrome-extension|bookmarklet",
  "url": "...",
  "title": "...",
  "tagName": "div",
  "selector": "...",
  "xpath": "...",
  "text": "bounded inner text",
  "outerHTML": "bounded outer HTML",
  "attributes": {},
  "rect": {},
  "viewport": {},
  "dataRegion": {
    "tagName": "...",
    "selector": "...",
    "xpath": "...",
    "role": "grid",
    "text": "bounded region text",
    "rect": {}
  },
  "table": {
    "kind": "html-table|aria-grid|heuristic-rows|none",
    "selector": "...",
    "rowCountVisible": 0,
    "columnCountMaxVisible": 0,
    "rows": []
  }
}
```

## Gmail/Workspace and bookmarklets

A bookmarklet worked on ordinary Google search pages but did not work reliably on Gmail / Google Workspace pages. Likely causes: strict Content Security Policy and/or Trusted Types blocking externally loaded bookmarklet scripts.

Fix: package the picker as a Chrome MV3 extension and inject `content.js` via `chrome.scripting.executeScript` from the extension service worker.

Minimal MV3 manifest pattern for picker + side panel:

```json
{
  "manifest_version": 3,
  "name": "WebElementChat",
  "version": "0.2.1",
  "action": { "default_title": "Open WebElementChat" },
  "permissions": ["activeTab", "scripting", "sidePanel", "storage"],
  "host_permissions": [
    "http://127.0.0.1:8765/*",
    "http://localhost:8765/*",
    "http://*/*",
    "https://*/*"
  ],
  "background": { "service_worker": "background.js" },
  "side_panel": { "default_path": "sidepanel.html" }
}
```

Why broad page host permissions appeared in this prototype: launching the picker from a side panel button is not the same permission path as clicking the extension action on the page. Chrome produced `Cannot access contents of the page. Extension manifest must request permission to access the respective host.` when `background.js` tried to inject `content.js` from the side-panel-triggered `activate-picker` message. Adding explicit page host permissions fixed the injection path. If the target domains are known, prefer a narrower allowlist; otherwise document the broad permission and keep the privacy rule strict: no automatic scraping, inject only after `Select element`, and transmit only the clicked element plus explicit chat messages.

## Side panel message flow

Use the side panel as the persistent UI and the content script as a short-lived page interaction tool:

1. User clicks extension icon; `background.js` opens the side panel.
2. User clicks `Select element` in `sidepanel.js`.
3. Side panel sends `{type: 'activate-picker'}` to `background.js`.
4. Background queries the active tab and injects `content.js` with `chrome.scripting.executeScript`.
5. Content script highlights DOM elements and, on click, builds the element payload.
6. Content script posts the payload to `POST /select` and sends `{type: 'selection-captured', payload}` to the extension runtime.
7. Background stores the payload in `chrome.storage.local` and broadcasts `{type: 'selection-updated', payload}`.
8. Side panel renders URL/title, selector, text preview, and table rows.
9. Side panel sends chat to `POST /chat` with `{message, selected_element}` and renders the response.

This avoids relying on the terminal for the UX while keeping the data path local and explicit.

## Agent command pattern

`WEBELEMENTCHAT_AGENT_COMMAND` is a simple integration seam:

- Compose a prompt from user message + selected element JSON.
- Split the command with `shlex.split`.
- Run it synchronously with prompt on stdin.
- Use stdout as response.
- If shell features/session management are needed, point the env var at a wrapper script.
- Add streaming and durable session continuity later.

Hermes wrapper pattern that worked:

```bash
#!/usr/bin/env bash
set -euo pipefail
prompt=$(cat)
exec /Users/fausto/.local/bin/hermes chat -Q --source webelementchat -q "$prompt"
```

Start the bridge with:

```bash
WEBELEMENTCHAT_AGENT_COMMAND=/path/to/scripts/hermes-agent.sh python3 server.py
```

Verify the integration with `POST /chat` and check the response reports `"mode": "agent"`; if it reports `"mode": "stub"`, the server was started without the env var or needs a restart.

## Data extraction fallback from selected text

Google Admin / Workspace custom table DOMs may produce `table.kind: "none"` even when the selected element's text clearly contains a table. Do not stop at `Visible table rows captured: 0` if `text` or `dataRegion.text` contains headers and repeated row blocks. For one admin subscriptions capture, the text had:

```text
Nome
Stato
Licenze
Piano di pagamento
Pagamento dovuto

Google Workspace for Education Fundamentals
Attivo
2.358 disponibili, 142 assegnate
Prezzi per i rivenditori
tech data italy
Prezzi per i rivenditori
...
```

A practical fallback is to:

1. Split non-empty lines.
2. Drop title/action lines and headers through the last known header.
3. Parse row blocks according to the visible repeated field order.
4. Treat optional detail/subtype lines (for example `Componente aggiuntivo Google Workspace`) as a separate column.
5. Write the CSV and state that it was reconstructed from selected text, not structured DOM rows.

This turns a failed structural extraction into useful output while preserving the follow-up task: improve the extractor for that DOM family later.

## Verification transcript shape

Use stdlib `unittest` so the project has no test dependency by default. Tests can start the server on a temporary port and pass `--state-dir` to avoid polluting real state.

Useful verification commands:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile server.py selection.py
python3 -m json.tool extension/manifest.json >/dev/null
node --check extension/background.js
node --check extension/content.js
node --check extension/sidepanel.js
bash -n open-chrome.sh
curl -sS http://127.0.0.1:8765/health
curl -sS -X POST http://127.0.0.1:8765/select \
  -H 'Content-Type: application/json' \
  --data '{"url":"http://example.test","title":"Test","tagName":"table","selector":"table#demo","text":"A B 1 2","table":{"kind":"html-table","rows":[["Name","Value"],["A","1"]],"rowCountVisible":2,"columnCountMaxVisible":2}}'
curl -sS -X POST http://127.0.0.1:8765/chat \
  -H 'Content-Type: application/json' \
  --data '{"message":"Analyze this table"}'
python3 selection.py
python3 selection.py --csv /tmp/selected-table.csv
```

## Pitfalls

- If a server is already listening on the bridge port from an old project path, new server startup may fail with address-in-use. Kill the stale listener and restart from the moved project directory.
- Background process watch-pattern notifications may arrive after a process has been stopped; verify actual listeners with the OS before acting on delayed notifications.
- When moving the project, update README/instructions that contain absolute paths and verify `POST /select` saves to the new project-local `state/last_selection.json`.
- Do not preserve a lesson as "browser/bookmarklets do not work". The durable pattern is: bookmarklet for quick prototypes, extension content script for strict CSP pages.
- Do not require pytest for this lightweight bridge unless the project already has it; stdlib `unittest` is enough for endpoint smoke tests.
