---
name: browser-element-agent-workflows
description: "Build browser-to-agent workflows where a user selects a page element and chats with an agent about that DOM/table context."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [browser, chrome-extension, sidepanel, dom, cdp, playwright, agent-ui, google-workspace]
    created_by: agent
---

# Browser Element Agent Workflows

Use this skill when the user wants an agent to work with a live browser page by referring to "this table", "this element", or a clicked/selected region without manually describing it. Typical tasks include browser co-analysis, DOM/table extraction from authenticated web apps, Chrome extension side panels, local browser bridges, or element pickers for agent workflows.

## Core pattern

Prefer a structured browser-to-agent bridge over screenshots:

1. Run a local-only bridge server on `127.0.0.1`.
2. Inject an element picker into the page via a Chrome extension content script, not just a bookmarklet.
3. Let the user click an element; capture structured context:
   - page URL and title
   - CSS selector and XPath
   - tag, attributes, ARIA roles
   - bounding box and viewport
   - `innerText`, bounded `outerHTML`
   - nearest data region (`table`, `role=grid`, `section`, `main`, etc.)
   - extracted visible rows for HTML tables, ARIA grids, and heuristic row containers
4. Save the latest selection to a local file and/or expose it over `GET /selected`.
5. Let the agent answer chat prompts using the latest selected element as context.

## Recommended architecture

For a prototype:

- `server.py`: local HTTP bridge with `POST /select`, `GET /selected`, `GET /health`.
- `content.js`: Chrome extension content script that highlights elements and posts selection JSON.
- `background.js`: MV3 service worker that injects the content script with `chrome.scripting.executeScript`.
- `selection.py`: CLI helper for the agent to summarize/export the latest selection.
- `state/last_selection.json`: latest element context.
- `state/history.jsonl`: append-only selection history.

For the product UX:

- Add a Chrome side panel (`sidepanel.html/js/css`) that can:
  - start element selection
  - display the selected element/table preview
  - send chat messages with selected-element context
  - show agent replies in the browser
- Add bridge endpoints such as `POST /chat`, `GET /history`, `POST /clear`.
- Later, add CDP/Playwright or MCP tools for scroll-and-collect, element screenshots, CSV export, and re-locating the selected element.

## Bookmarklet vs Chrome extension

Use the implementation level that matches the page and product maturity:

- **Bookmarklet / injected local script** — fastest proof of concept for ordinary pages and internal demos. Keep `GET /picker.js`, `GET /bookmarklet.txt`, `POST /select`, `GET /selected`, `selection.py`, and project-local `state/` files. See `references/local-element-picker-bridge.md` for the concrete MVP package.
- **Chrome MV3 extension** — preferred for Gmail, Google Workspace, strict CSP/Trusted Types pages, or any workflow that needs a side panel, persistent UI, or reliable injection from browser controls.
- **CDP/Playwright follow-up** — add only after selection works, for scroll-and-collect on virtualized grids, element screenshots, re-locating selected elements, and CSV/JSON export.
- **MCP packaging** — useful when the workflow recurs enough to expose stable tools such as `get_selected_element`, `extract_selected_table`, or `export_selected_grid_to_csv`.

A bookmarklet is useful for a fast proof of concept on ordinary pages, but Google Workspace/Gmail and other high-security apps often block bookmarklet script loading via Content Security Policy or Trusted Types.

When the target includes Gmail, Google Workspace, or other authenticated apps with strict CSP, move to a Chrome MV3 extension:

- `permissions`: `activeTab`, `scripting`
- `host_permissions`: local bridge URLs such as `http://127.0.0.1:8765/*`
- inject the picker as a content script from the extension package
- keep bridge traffic local-only unless the user explicitly asks otherwise

If the picker is launched from a Chrome side panel button, `activeTab` alone may not grant enough access for `chrome.scripting.executeScript`; Chrome can raise `Cannot access contents of the page. Extension manifest must request permission to access the respective host.` For that side-panel-triggered injection path, add explicit page host permissions such as `https://*/*` and `http://*/*` (or a narrower domain allowlist when known), document why, and preserve data minimization: inject only after explicit user action and send only the clicked element plus explicit chat messages.

## Data extraction notes

Many modern web apps do not use literal `<table>` elements. Support these cases:

- HTML tables: collect `tr` then `th,td`.
- ARIA grids/tables: collect `[role=row]` and `[role=cell|gridcell|columnheader|rowheader]`.
- Virtualized tables: the DOM usually contains only visible rows. Report `visible rows` honestly and add scroll-and-collect later if full extraction is needed.
- Heuristic row containers: try `[data-rowindex]`, `[aria-rowindex]`, `.row`, or classes containing `row`, but label this as heuristic.
- Text fallback: if structured row extraction returns `kind: none` but the selected element or `dataRegion.text` visibly contains headers and repeated row blocks, parse the bounded text into CSV/records rather than declaring failure. Label it as reconstructed from text and improve the extractor later for that DOM family.

Always bound captured text/HTML sizes to avoid flooding the agent context.

## Security defaults

For authenticated apps and workspace data:

- listen on `127.0.0.1`, not `0.0.0.0`
- send only explicitly selected elements by default
- show a preview of what was captured in the side panel
- avoid full-page scraping unless the user asks
- consider domain allowlists for `mail.google.com`, `drive.google.com`, `docs.google.com`, `calendar.google.com`, etc.
- add optional redaction later for emails, names, IDs, or other sensitive data

## Side panel implementation pattern

For a Chrome side panel workflow, use MV3 message passing instead of trying to make the content script own the chat UI:

1. `sidepanel.html/js/css` renders the persistent browser UI: bridge status, selected-element preview, table preview, chat log, and chat input.
2. `background.js` opens the side panel on action click and handles messages:
   - `activate-picker`: query active tab and inject `content.js` with `chrome.scripting.executeScript`.
   - `selection-captured`: store the latest payload in `chrome.storage.local` and notify the side panel with `selection-updated`.
   - `get-latest-selection`: return the latest stored payload when the side panel opens.
3. `content.js` only handles page interaction: highlight elements, capture context, `POST /select` to the localhost bridge, then `chrome.runtime.sendMessage({type: 'selection-captured', payload})`.
4. The side panel posts chat requests to `POST /chat` with `{message, selected_element}`. If `selected_element` is omitted, the bridge can fall back to the latest `state/last_selection.json`.
5. Keep the first `/chat` implementation synchronous and explicit: if no agent command is configured, return a clearly marked stub showing what would be sent. Add streaming/session continuity later.

## Agent command pattern

A simple bridge can call a local agent via an environment variable such as `WEBELEMENTCHAT_AGENT_COMMAND`. Pass the composed prompt on stdin and use stdout as the assistant response. Split the command with `shlex.split`; if shell features are needed, ask the user to point the env var at a wrapper script. Always preserve localhost-only defaults and persist chat history under `state/chat_history.jsonl`.

For Hermes specifically, create a tiny wrapper instead of trying to pass piped stdin through shell quoting:

```bash
#!/usr/bin/env bash
set -euo pipefail
prompt=$(cat)
exec hermes chat -Q --source webelementchat -q "$prompt"
```

Then start the bridge with `WEBELEMENTCHAT_AGENT_COMMAND=/path/to/hermes-agent.sh python3 server.py`. Smoke-test `/chat` and confirm the JSON response reports `mode: "agent"`, not `mode: "stub"`, before telling the user the browser chat is live.

## Testing guidance

Prefer lightweight stdlib `unittest` for this class of local bridge unless the project already depends on pytest. Useful tests start the server on a temporary port with `--state-dir`, exercise `/health`, `/select`, `/chat`, and assert that state files are written in the temporary state directory.

## Verification checklist

After building or moving a browser element bridge:

1. Validate Python files: `python3 -m py_compile server.py selection.py`.
2. Validate extension manifest: `python3 -m json.tool extension/manifest.json >/dev/null`.
3. Validate JS syntax: `node --check extension/background.js`, `node --check extension/content.js`, and `node --check extension/sidepanel.js` if present.
4. Validate shell helpers: `bash -n open-chrome.sh`.
5. Run tests: `python3 -m unittest discover -s tests -v` when tests exist.
6. Start the server from the project directory.
7. Check `GET /health`.
8. Post a synthetic selection to `POST /select` and verify it saves under the project-local `state/last_selection.json`.
9. Post a synthetic chat to `POST /chat` and verify either a stub response or configured agent response plus `state/chat_history.jsonl`.
10. Run the selection helper and, if table rows exist, CSV export.

## References

- `references/webelementchat-prototype.md` — concrete prototype structure and lessons from a local Chrome extension + bridge implementation.
- `references/local-element-picker-bridge.md` — earlier bookmarklet/local-script MVP pattern, including server endpoints, selector heuristics, CSV export, and CDP/MCP next steps.
