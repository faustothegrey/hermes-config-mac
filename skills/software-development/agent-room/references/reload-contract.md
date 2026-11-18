# Hot-reload contract and module recipe

agent-room reloads code and rulebooks live (`/reload`; dev mode `--dev` watches `src/*.mjs` and the
rulebooks). The mechanism, in `src/cli.mjs`:

- startup: `let ui = await import(\`./ui.mjs?v=${Date.now()}\`)`.
- `reloadAll`: `next = await import(\`./ui.mjs?v=${Date.now()}\`)`, then `next.load(ctx, \`?v=${Date.now()}\`)`.
- `ui.mjs` `load(ctx, v)` re-imports every local module with `${v}`:
  `import(\`./agents.mjs${v}\`)`, `import(\`./room.mjs${v}\`)`, `import(\`./docs.mjs${v}\`)`, etc.

Consequence: a bare static `import './x.mjs'` inside any of these modules resolves to the un-versioned
(cached) URL and is never re-evaluated on reload — edits to that module silently stop hot-reloading (only a
Restart picks them up). The rulebooks themselves reload because they are read as FILES at load time, not
imported as code.

## Adding a shared module without breaking reload (default-parameter pattern)

`src/instructions.mjs` is the worked example. In the consumer module (e.g. `room.mjs`):

```js
import * as defaultInstructions from './instructions.mjs'; // static: cached fallback (tests, non-reload callers)

export function createRoom(agents, state, instr = defaultInstructions) {
  const { intro, summaryFormat, draftTask, reviewTask } = instr;
  // ...
}
```

In `ui.mjs` `load()`:

```js
const instr = await import(`./instructions.mjs${v}`); // fresh, version-tagged
// ...
return { room: createRoom(agents, ctx.state, instr), /* ... */ instructions: instr };
```

The static import is only the fallback; the runtime always passes the fresh version-tagged copy (stored on
`ctx.instructions`), so edits to the shared module still hot-reload. Tests that call `createRoom(agents)`
with no third argument keep working via the default.

## Replacing a large block full of literal `\n` escapes

The worker-dispatch prompt strings in `ui.mjs` are inline template literals containing literal `\n`
(backslash-n) sequences. The `patch` tool's `old_string` treats `\n` as a newline, so matching those
requires writing `\\n` — error-prone over a 30-line block. Prefer a Python anchor-slice: find two unique
markers (the first line of the block and the first line after it), and replace only the span between them,
transcribing just the NEW code (a raw string, so `\n` stays literal):

```python
from pathlib import Path
text = Path('src/ui.mjs').read_text()
start = text.index('      const d = task.discussion;\n')
end = text.index('      // Its briefing is now known', start)
new = r'''      const instr = ctx.instructions ?? defaultInstructions;
      ... new block, with \n literal inside template literals ...'''
text = text[:start] + new + text[end:]
Path('src/ui.mjs').write_text(text)
```

Verify afterwards that the removed inline assignments are gone and the new calls are present, then run
`npm test`.
