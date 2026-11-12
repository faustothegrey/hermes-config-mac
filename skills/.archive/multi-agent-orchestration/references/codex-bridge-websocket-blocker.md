# M12-T4: Codex Bridge / McpServer WebSocket Conflict

**2026-07-01 — Discovered during M12 capstone live run**

## The Bug

When running a cross-provider consensus round (Gemini + Codex planners), Codex's agent (`planner-b`) fails to execute `consensus_respond` tool calls because its inner bridge process cannot connect to AgentTalk's McpServer.

## Root Cause

Codex's execution model requires **two separate MCP WebSocket connections** per agent:

1. **Primary connection** (`llm-agent.mjs`) — pulls turns via `await_turn`. Opens a WebSocket identified as `planner-b`.

2. **Secondary connection** (`bridge.mjs`) — spawned by `CodexPersistentExecutor` when Codex needs to call MCP tools (like `consensus_respond`). This also tries to connect as the same `agentId`.

AgentTalk's `McpServer` enforces a strict **one active connection per agentId** rule ("Session isolation & hijack check" — `mcp-server.ts`). When `bridge.mjs` connects as `planner-b` while the primary connection already holds that slot, the server rejects with `4001 Session already active`.

## Impact

Codex is structurally unable to participate in AgentTalk consensus rounds under the current McpServer architecture. The protocol-level code works (turn routing, parsing), but the transport layer prohibits the dual-connection pattern Codex requires.

## Connection Flow Diagram

```
llm-agent.mjs --agentId=planner-b
  |
  +-- WebSocket #1 ---> AgentTalk McpServer  (await_turn, OK)
  |                       +-- session "planner-b" registered
  |
  +-- spawns codex CLI
        |
        +-- bridge.mjs (AGENTTALK_AGENT_ID=planner-b)
              |
              +-- WebSocket #2 ---> AgentTalk McpServer  (consensus_respond)
                                    +-- 4001 Session already active <- BLOCKED
```

## Attempted Fixes During T4

1. **Set AGENTTALK_AGENT_ID explicitly** -- Even when correctly set to `planner-b`, the second connection is rejected by the one-per-agentId rule. This is not an env-var gap; it's an architectural constraint.

2. **Omit AGENTTALK_AGENT_ID** -- Causes `bridge.mjs` to default to `unknown`, which is also rejected by TeamCoordinator ("Agent unknown is not part of any active team").

## Unblock Conditions

One of the following is needed:
- Make the McpServer allow multiple WebSocket connections per agentId (e.g. multiplexed over one connection, or a shared session key).
- Have Codex execute `consensus_respond` through a different mechanism that doesn't require a second WebSocket (e.g. in-process tool execution, or relay through the primary connection).
- Use a different second provider that doesn't require dual connections (e.g. Claude -- uses ClaudePersistentExecutor which may follow a different connection pattern).

## What DOES Work

- **Gemini (agy)** -- does not have this problem. Gemini's GeminiPersistentExecutor processes consensus_respond inline without requiring a secondary connection.
- **PF preflight** -- single-agent Codex MCP ping (one await_turn + one submit_exec_result) works fine because it only uses the primary connection.
- **All deterministic tests** -- provider-mix invariance test passed, proving the routing layer itself is provider-agnostic.

## Related Code

- `agentalk-mcp-client/lib/executor-runtime.mjs` -- CodexPersistentExecutor spawns codex exec with bridge.mjs
- `agentalk-mcp-client/bridge.mjs` -- secondary WebSocket to AgentTalk McpServer
- `packages/mcp-transport/src/mcp-server.ts` -- handleConnection at ~L50-70: session isolation check
- `packages/runtime-core/src/registry/registry.ts` -- handleMcpConnect at ~L630-660: registration path
