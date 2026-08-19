---
name: delegation-readiness-checks
description: Run brief readiness/auth/availability checks before delegating to external agent lanes.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Delegation, Reliability, Agent-Orchestration, Readiness]
    related_skills: [claude-code, antigravity-cli, codex, opencode]
---

# Delegation Readiness Checks

Use this skill whenever Hermes is about to delegate work to an external agent lane such as Claude Code, Antigravity CLI, Codex, OpenCode, or another autonomous CLI/tool-based delegate.

## Step 0: Choose the working directory

Before any readiness checks or delegation, autonomously select the project-appropriate working directory. Set the `workdir` parameter or `cd` into the correct project root before spawning the delegate.

### Project-to-directory mapping (convention)

When the task references a known project by name, use these paths:

| Project | Workdir |
|---------|---------|
| AgentTalk | ~/Software/AgentTalk/ |
| WebElementChat | ~/Software/WebElementChat/ |
| CasaSpese | ~/Software/CasaSpese/ |
| ScienceClick2 | ~/Software/ScienceClick2/ |
| DiagramTalk | ~/Software/DiagramTalk/ |
| mcp-orchestration | ~/Software/mcp-orchestration/ |
| ScrapeCircolari2 | ~/Software/ScrapeCircolari2/ |
| scripts-ai | ~/Software/scripts-ai/ |
| Hermes Agent (config/skills/plugins/cron) | Hermes home (~/.hermes/) |

### When the project is ambiguous or unknown

1. Check `~/Software/` for candidate project directories.
2. Check the Obsidian vault at `~/Documents/Obsidian Vault/Hermes Memory/` for project documentation that might reveal the path.
3. If still uncertain, `read_file` the project's `package.json`, `README.md`, or `CLAUDE.md` from suspected paths to confirm.
4. As a last resort, ask the user which directory.

### Rationale

Different projects have different CLAUDE.md files, dependencies, git branches, and conventions. Spawning a delegate in the wrong directory causes confusion, broken imports, wasted tokens, and out-of-context AI suggestions. Setting the right workdir upfront prevents all of these.

## Core rule

Before any long or meaningful delegation, run a short readiness/auth/availability ping for each candidate delegate.

Do not start a multi-minute delegation until the candidate has proven it is available.

If a candidate is unavailable:

1. Report that the delegate candidate is not available.
2. Continue with another suitable delegate if one is available.
3. If no delegate is available, stop and report delegation failure.
4. Do not wait uselessly on an unauthenticated, stuck, or unavailable delegate.

## What counts as readiness

A readiness check should be short, low-cost, and bounded, typically 15-60 seconds.

Accept readiness only when the candidate returns the expected simple answer or a clear healthy status.

Treat these as unavailable:

- auth/OAuth/login prompts;
- command not found;
- expired credentials;
- timeout;
- tool crashes;
- irrelevant response;
- model/provider quota error;
- candidate starts doing the real task instead of answering readiness.

## Example pings

### agentctl (preferred — all agents: agy, claude, codex)

When agents are managed through agentctl, use `agentctl health --json` as the universal readiness check:

```bash
agentctl health --json
```

Expected response when an agent is already running:

```json
{
  "agents": {
    "agy": {
      "count": 1,
      "orphan_count": 0,
      "anomalies": []
    }
  },
  "anomaly_count": 0
}
```

If the agent is not spawned yet or shows anomalies, spawn first:

```bash
agentctl spawn agy
sleep 5
agentctl health --json
# Verify: anomaly_count == 0, agent count >= 1, orphan_count == 0
```

For a quick interactive ping after spawn:

```bash
agentctl send agy "Readiness ping: reply with exactly READY and nothing else."
sleep 10
agentctl capture agy | grep -q READY && echo "READY"
```

### Antigravity CLI (direct, no agentctl)

```bash
/Users/fausto/.local/bin/agy --print 'Readiness ping: reply with exactly READY and nothing else.' --print-timeout 30s
```

Expected response:

```text
READY
```

### Codex CLI

```bash
codex login status
```

Expected response:

```text
Logged in using ChatGPT
```

Note: `codex auth status` is NOT a valid command — use `codex login status` instead.

### Claude Code

```bash
claude auth status --text
```

Expected response shows login method, organization, and email. For the built-in Hermes `claude_code` tool, use a tiny prompt before a long delegation when availability is uncertain:

```text
Readiness ping: reply with exactly READY and nothing else.
```

For shell CLI checks:

```bash
claude auth status --text
claude -p 'Readiness ping: reply with exactly READY and nothing else.' --max-turns 1
```

## Delegation workflow

0. **Choose the working directory** (see Step 0 above) — infer from project context, set `workdir` on the delegate spawn.
1. Identify candidate delegate lanes.
2. Run readiness ping for each lane before long work.
3. Start only lanes that pass readiness.
4. If a lane fails readiness, mark it unavailable and move to another lane if possible.
5. Keep prompts bounded and self-contained.
6. Save raw output if long.
7. Verify important side effects yourself before reporting success.

## User-specific note

Fausto explicitly requested this as a general workflow rule: readiness checks before delegation are important. Hermes should apply it broadly, not only to Antigravity.

## Delegation boundary

Hermes works directly (no delegation) only for:

- **(a) The Hermes Agent ecosystem** — configuration, tools, skills, plugins, troubleshooting, development, or anything directly or indirectly part of Hermes Agent.
- **(b) System service management.**

For **all other software development**, Hermes acts as a **delegating editor** — delegate substantive work to Claude Code (or another lane) and curate results. This applies beyond exploratory assessment; it covers any development outside the Hermes ecosystem.
