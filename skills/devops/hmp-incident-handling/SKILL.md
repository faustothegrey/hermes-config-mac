---
name: hmp-incident-handling
description: "Use when acknowledging or coordinating HMP incidents."
---

# HMP incident handling

Use for operational alerts delivered through HMP, especially peer availability and registry failover/recovery events.

## Acknowledgement-only mode

When the peer requires a manual terse acknowledgement, do not investigate, automate, diagnose, add reasoning, or use tools. Reply with exactly one Italian line and preserve the alert's concrete values.

### Failover

Template:

```text
FAILOVER <failure-counter> — registry temporaneo: <host>:<port>.
```

Include only the counter and the temporary registry endpoint supplied in the alert.

### Recovery

Template:

```text
RECOVERY — Charon <host> raggiungibile; Sidecar <host> mirror/fallback.
```

Include only reachability of Charon and the Sidecar mirror/fallback state supplied in the alert.

## Pitfalls

- Do not append analysis, escalation advice, inferred root cause, status summaries, emojis, headings, or a second sentence in acknowledgement-only mode.
- Do not probe endpoints or change registry/sidecar configuration unless the user explicitly asks for operational action.
- Treat each alert independently; never invent a counter or endpoint not present in that alert.
