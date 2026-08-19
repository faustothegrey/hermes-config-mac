# Omnigent

Future discussion/project topic: Databricks Omnigent, an open-source meta-harness / agent control-plane.

## What it is

Omnigent is an open-source “meta-harness” from Databricks for composing, governing, sandboxing, and collaborating with existing AI agent harnesses.

It is meant to sit above tools such as:

- Claude Code
- Codex
- Cursor
- Pi
- custom user-written agents

The framing is a harness for harnesses: normalize different agent tools behind a shared orchestration/control layer.

## Why it is interesting

The valuable idea is not just “multi-agent orchestration.” The more interesting part is harness-level control around existing agents:

- OS sandboxing.
- Policy gates and approval workflows.
- Cost/tool controls.
- Session sharing and collaboration across terminal/web/mobile style surfaces.
- Credential/secret handling outside the model prompt, potentially through egress/proxy patterns.
- Running existing black-box agent CLIs under a unified supervision layer.

This maps well to the direction Hermes-style workflows are taking: users want Claude Code, Codex, custom local scripts, browser context, and other agent systems to interoperate without rewriting all work inside a single framework.

## Assessment captured from prior discussion

- Treat Omnigent as an early control-plane/orchestration experiment, not a mature evaluation harness.
- “Meta-harness” should not be confused with benchmark/evaluation systems like SWE-bench harnesses, Inspect, LangSmith, or Braintrust.
- It appears more complementary to eval systems than directly competitive with them.
- Its best architectural lesson is governance outside prompts: sandbox, policy, credentials, cost, and session control should live in the harness/control-plane layer.
- The approach is compelling because it wraps existing useful agents rather than forcing everything into a new Python framework abstraction.

## Potential future project angles

- Try Omnigent on a low-risk sandbox repo with Claude Code + Codex in parallel.
- Use it to compare agent diffs and have one agent review another agent’s output.
- Study whether the sandbox/policy model can inspire Hermes-native or WebElementChat-adjacent agent governance.
- Explore whether Hermes could provide a lighter-weight local meta-harness pattern without adopting all of Omnigent.
- Combine Omnigent-style orchestration with real eval harnesses for measurable comparisons.

## Caveats

- Public information was sparse/new when first discussed.
- Treat it as alpha; do not assume stability or production readiness.
- Wrapping opaque CLIs can be brittle because those tools may change output formats, permission flows, TUI behavior, or session semantics.
- Independently audit sandboxing and secret handling before using it with sensitive repositories.

## Related notes

- [[Projects]]
- [[Workflows]]
- [[User Preferences]]
