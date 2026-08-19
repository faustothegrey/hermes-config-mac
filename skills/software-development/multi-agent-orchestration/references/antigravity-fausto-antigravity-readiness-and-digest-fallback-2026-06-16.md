# Fausto Antigravity readiness + digest fallback pattern (2026-06-16)

Context: During an AgentTalk historical-run forensic assessment, Antigravity initially required external Google OAuth. Fausto authenticated it externally, then asked Hermes to check candidate readiness before launching another long delegation.

Reusable pattern:

1. Before long `agy --print` jobs, run a short auth/readiness ping:

```bash
/Users/fausto/.local/bin/agy --print 'Readiness ping: reply with exactly READY and nothing else.' --print-timeout 30s
```

2. Interpret results:

- Exact `READY`: proceed with the delegation.
- OAuth prompt / timeout / non-answer: report that Antigravity is not available; use another delegate if available, otherwise stop and report failure.

3. If a long Antigravity run times out after only progress narration, do not treat the narration as an assessment. Retry with a narrower prompt that forbids additional crawling and asks for final sections immediately from a precomputed digest.

Example digest-only retry shape:

```text
Analyze this existing factual digest only: /tmp/<digest>.md
Do not inspect more files. Do not run commands. Produce final answer immediately.
Output exactly these sections: ...
```

Why this matters:

- Antigravity can be externally authenticated and then become available without Hermes doing auth itself.
- A readiness ping avoids wasting a full delegation timeout on an unavailable candidate.
- Digest-only retry converts a broad exploratory crawl into a bounded synthesis task when the first run times out.
