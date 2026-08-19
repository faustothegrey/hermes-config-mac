# Cross-Provider Consensus Reframing (2026-07-01)

## The old assumption

The backlog item "cross-provider consensus" (deferred after M11) assumed the path was:
- Pair Google/Gemini + **Nous** (OpenRouter aggregator)
- Needed a fix to `api-client.ts` `nous` defaultModel (`deepseek-v4-flash` 404s — LB-1)
- Would prove the centralized brain mixes providers

## The reframing

Fausto pointed out: Codex and Claude are already MCP-attached agents with the same `consensus_respond` tool surface, same turn loop, same `exec_rpc` format. They should already work in a mixed-provider team. Nous adds unnecessary complexity (API-path, model fix, no MCP attach).

The real question is simpler: **can we start a team with Gemini (agy) and Codex as the two planners and have them reach consensus through the existing MCP infrastructure?** This has never been tested — all consensus runs to date used two Gemini planners.

## Why this matters

- The engine is already provider-blind on the MCP path (verified in the Architect's F1-F5 analysis)
- M11's robustness work (consensus_respond, active re-prompting, turn-budget referee) was built to make cross-provider rounds possible
- The epic is a **validation** (not build) exercise — prove the claim, don't add new machinery

## Impact on backlog

The old "cross-provider consensus" backlog item gets closed. The new M12 epic replaces it with a simpler, more targeted question.