# Projects

Recurring project context that may matter across sessions.

## Portfolio review

See [[Software Projects Review 2026-06-16]] for a detailed review of the `/Users/fausto/Software` project portfolio.
See [[Cross-Project Patterns 2026-06-16]] for the Claude-delegated follow-up assessment of cross-project similarities, reusable patterns, and convergence opportunities.
See [[Deep Portfolio Assessment 2026-06-16]] for Claude's deeper per-project development ideas, roadmap, strengthening opportunities, and avoid-overbuilding notes.
See [[Antigravity Portfolio Assessment 2026-06-16]] for Antigravity CLI's independent delegated assessment of the same portfolio and its comparison against Claude's conclusions.
See [[AgentTalk]], [[Claude AgentTalk Assessment 2026-06-16]], [[Antigravity AgentTalk Assessment 2026-06-16]], and [[AgentTalk Comparative Synthesis 2026-06-16]] for the newly added AgentTalk project's multi-agent consensus/control-plane assessment.
See [[AgentTalk Historical Runs Failure Synthesis 2026-06-16]] plus [[Claude AgentTalk Historical Runs Failure Analysis 2026-06-16]] and [[Antigravity AgentTalk Historical Runs Failure Analysis 2026-06-16]] for delegated analysis of historical `transcripts/` and `planning_runs/` failures.
See [[AgentTalk Protocol-Adherence Thesis Discussion 2026-06-16]] for Fausto's central diagnosis and Claude's follow-up: agents should not directly operate a rigid consensus protocol; the runtime/control plane should own canonical protocol events, phase fencing, proposal identity, and loop/progress guards.

Key takeaways from that review and follow-up assessment:

- `/Users/fausto/Software` contains Fausto's main software projects.
- Most promising to push on: [[WebElementChat]] and [[CasaSpese]].
- Best-engineered repository: [[ScienceClick2]].
- Emerging cross-project theme: local-first, privacy-aware personal AI infrastructure plus practical Italian school/admin tooling.
- Cross-cutting hygiene issue: secrets and `.DS_Store` files should be handled before projects become public/repos.
- Cross-cutting consolidation opportunity: CasaSpese's Google Sheets sync could potentially reuse SpreadGit's minimal-diff patching primitive.
- Strongest cross-project AI pattern: subscription-CLI-as-AI-backend across CasaSpese, WebElementChat, and scripts-ai.
- CasaSpese and ScienceClick2 share a near-identical Next.js stack, suggesting a possible personal Next.js starter/template.
- Deep roadmap priorities before AgentTalk: hygiene sweep; make WebElementChat work with a default real agent; extract shared scripts/skills utilities; integrate SpreadGit into CasaSpese; add tests to pure cores; consolidate scripts-ai into `ai-quota`.
- AgentTalk changes the portfolio thesis: it is likely the strategic local-first multi-agent control-plane core; WebElementChat becomes its strongest likely input/context surface, scripts-ai its metering layer, and CasaSpese remains the mature real-world value anchor.
- AgentTalk historical run artifacts currently look like a reliability stress/failure corpus: 49/49 planning-run JSON files were `interrupted`; delegated analysis points to Gemini quota exhaustion, Codex proposal/acceptance payload mismatches, stale phase fallback/desynchronization, and strict failure propagation as the main suspected causes.

## WebElementChat

See [[WebElementChat]] for detailed project memory.

- Project path: `/Users/fausto/Software/WebElementChat`.
- Purpose: local-first Chrome MV3 side-panel extension + localhost bridge for selecting a DOM element in the browser and chatting with Hermes about that exact selected element.
- Server URL: `http://127.0.0.1:8765`.
- Main start command with real Hermes responses:

```bash
cd /Users/fausto/Software/WebElementChat
WEBELEMENTCHAT_AGENT_COMMAND=/Users/fausto/Software/WebElementChat/scripts/hermes-agent.sh python3 server.py
```

- Chrome extension folder: `/Users/fausto/Software/WebElementChat/extension`.
- Current status: side panel, element picker, `/select`, `/selected`, `/chat`, chat history, and Hermes wrapper are implemented and verified.

## CasaSpese

See [[CasaSpese]] for detailed project memory.

- Project path: `/Users/fausto/Software/CasaSpese`.
- Purpose: local-first Next.js home expense visualizer and rules-based categorizer integrated with Google Sheets.
- Current status: basic authentication, deterministic rules engine, monthly/weekly recurrence simulation, and pro dashboard page with charts are active.

## ScienceClick2

See [[ScienceClick2]] for detailed project memory.

- Project path: `/Users/fausto/Software/ScienceClick2`.
- Purpose: Next.js / React drag-and-drop educational scene app where teachers place labels on an image and students drag terms to correct positions.
- Review status: best-engineered repo in the 2026-06-16 portfolio review; has `PROJECT.md`, worktree conventions, and a unified skills source synced to `.claude`, `.codex`, and `.agents`.
- Reusable pattern: ScienceClick2's skill-versioning/sync approach may be useful across other AI-assisted projects.

## Omnigent

See [[Omnigent]] for detailed project/discussion memory.

- Topic: Databricks Omnigent, an open-source meta-harness / control-plane for composing, governing, sandboxing, and collaborating with existing AI agent harnesses.
- Relevant harnesses/tools: Claude Code, Codex, Cursor, Pi, and custom agents.
- Interest: future discussion/project topic around agent control planes, cross-agent orchestration, sandboxing, policy gates, and governance outside prompts.

