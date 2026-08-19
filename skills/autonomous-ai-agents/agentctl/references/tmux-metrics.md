# tmux-metrics counter logic

## Reset semantics (PO Fausto, 2026-07-02)

When you start sending input, reset output counter and vice versa.

- `send` → adds message chars to `sent`, resets `received` to 0
- `capture` → adds output chars to `received`, resets `sent` to 0

This means at any snapshot, the counters answer "chars since the last opposite-direction action":

- `sent > 0, received = 0` → last action was sending, no capture since
- `received > 0, sent = 0` → last action was capture, no send since
- Both zero → just initialized, or counters haven't been exercised yet

## Determinism

The harness uses `bash` built-in `${#MESSAGE}` for character counting — no external tools, no locale-dependent byte counting. The same input always produces the same count. Not inferred, measured directly at the shell level before the agentctl subprocess is invoked.

## Files

| File | Content |
|---|---|
| `~/.hermes/heartbeat/tmux-sent` | Cumulative sent chars (reset on capture) |
| `~/.hermes/heartbeat/tmux-recv` | Cumulative received chars (reset on send) |
