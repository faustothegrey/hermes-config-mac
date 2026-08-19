# Local element picker bridge prototype

This reference captures a proven MVP pattern for letting a user click a web page element and pass it to an agent as structured DOM/table context.

## Use case

The user must explore an authenticated web UI manually (for example Google Workspace pages) and wants to say “analyze this table” after clicking it, without taking screenshots or verbally describing which table they mean.

## Directory layout used in the prototype

```text
hermes-browser-bridge/
├── server.py          # local HTTP bridge on 127.0.0.1:8765
├── picker.js          # injected element picker/highlighter
├── bookmarklet.txt    # tiny bookmarklet loading picker.js
├── selection.py       # agent CLI: summary, full JSON, CSV export
├── open-chrome.sh     # optional isolated Chrome + CDP launcher
├── README.md
└── state/
    ├── last_selection.json
    └── history.jsonl
```

## Server behavior

Recommended endpoints:

- `GET /` renders instructions and a draggable bookmarklet.
- `GET /health` returns `{ok: true}`.
- `GET /picker.js` serves the injected script.
- `GET /bookmarklet.txt` returns the bookmarklet text.
- `POST /select` accepts the selected element payload and writes:
  - `state/last_selection.json`
  - append-only `state/history.jsonl`
- `GET /selected` returns the latest selection JSON.

Important implementation details:

- Bind to `127.0.0.1`.
- Set CORS headers for local page-to-bridge posts:
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Methods: GET, POST, OPTIONS`
  - `Access-Control-Allow-Headers: Content-Type`
- Add `received_at` and `bridge_version` on the server side.
- Keep JSON UTF-8 and `ensure_ascii=False` for international data.

## Picker script behavior

The injected script should:

1. Add overlay CSS for a fixed-position highlight rectangle and label.
2. Track hovered elements with capture-phase `mousemove`.
3. On click:
   - `preventDefault()`
   - `stopPropagation()`
   - `stopImmediatePropagation()`
   - build the payload
   - `POST` it to the local bridge
4. Support `Escape` cleanup.
5. Truncate large `text` and `outerHTML` fields.
6. Toggle off/cleanup if run twice.

Useful payload fields:

```json
{
  "captured_at": "...",
  "url": "...",
  "title": "...",
  "tagName": "table",
  "selector": "...",
  "xpath": "...",
  "text": "...",
  "outerHTML": "...",
  "attributes": {},
  "rect": {"x": 0, "y": 0, "width": 0, "height": 0},
  "viewport": {"width": 0, "height": 0, "scrollX": 0, "scrollY": 0, "devicePixelRatio": 2},
  "dataRegion": {
    "tagName": "...",
    "selector": "...",
    "xpath": "...",
    "role": "grid",
    "text": "...",
    "rect": {}
  },
  "table": {
    "kind": "html-table | aria-grid | heuristic-rows | none",
    "selector": "...",
    "rowCountVisible": 0,
    "columnCountMaxVisible": 0,
    "rows": []
  }
}
```

## CSS selector generation

Good selector generation should prefer stable attributes before falling back to positional selectors:

1. `id`
2. `data-testid`, `data-test`
3. `aria-label`
4. `name`
5. `role`
6. `:nth-of-type(n)` fallback

Always include XPath too as a fallback.

## Table extraction heuristics

Try in this order:

1. `table tr` with `th,td`
2. ARIA grid/table/treegrid:
   - rows: `[role=row]`
   - cells: `[role=cell],[role=gridcell],[role=columnheader],[role=rowheader]`
3. Heuristic rows:
   - `[data-rowindex]`
   - `[aria-rowindex]`
   - `.row`
   - classes containing `row`

Capture only visible rows at MVP stage. If the UI is virtualized, full extraction requires CDP/Playwright scrolling.

## CLI reader

A useful `selection.py` should support:

```bash
python3 selection.py          # compact summary
python3 selection.py --json   # full payload
python3 selection.py --csv /tmp/selected-table.csv
```

The summary should print URL, title, timestamps, element selector, data region selector, text preview, table kind, row/column counts, and the first visible rows.

## Isolated Chrome helper

For future CDP/Playwright integration, launch Chrome with a separate profile:

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-hermes-google" \
  --no-first-run \
  --no-default-browser-check \
  "http://127.0.0.1:8765/"
```

This avoids attaching to the user’s main browsing profile while still letting the user log into the target app inside the isolated profile.

## Verification transcript shape

A working bridge should produce evidence like:

```text
GET /health -> {"ok": true, "time": "..."}
POST /select -> {"ok": true, "saved_to": ".../state/last_selection.json", "table_rows": 3}
selection.py -> Table kind: html-table rows=3 cols=2
selection.py --csv /tmp/file.csv -> writes rows
```

Do not report success until these checks have actually run.

## Known limitations and next steps

- Bookmarklets can be blocked by strict CSP. Convert the same picker logic to a local Chrome extension when this happens.
- Google and other SaaS UIs often use virtualized tables; only visible rows are in the DOM.
- For full-table analysis, add a CDP/Playwright tool that finds the selected region, scrolls its nearest scroll container, accumulates rows, and deduplicates them.
- For recurring use, package the bridge as an MCP server with tools such as `get_selected_element`, `extract_selected_table`, and `export_selected_grid_to_csv`.
