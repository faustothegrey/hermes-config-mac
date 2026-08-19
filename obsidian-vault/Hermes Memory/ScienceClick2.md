# ScienceClick2

Source: [[Software Projects Review 2026-06-16]]
Project path: `/Users/fausto/Software/ScienceClick2`

## One-line purpose

ScienceClick2 is a Next.js / React educational app where teachers place labels on an image and students drag terms to correct spots.

## Review classification

The 2026-06-16 software projects review calls ScienceClick2 the best-engineered project in `/Users/fausto/Software`.

## Technology

- Next.js 16.
- React 19.

## Educational concept

- Teachers define visual scenes by placing target labels on an image.
- Students complete the activity by dragging terms to the correct positions.
- The interaction is suited for vocabulary, science diagrams, everyday objects, jobs, universe/space, and other visual-labeling lessons.

## Features mentioned in the portfolio review

- Spectator mode.
- Results store.
- i18n.
- Four populated scene categories:
  - biology
  - everyday
  - jobs
  - universe

## Engineering quality notes

The review describes this as the most disciplined repository among Fausto's projects.

Important structural assets:

- Real `PROJECT.md`.
- Unified multi-agent skills system.
- `skills/` is the source for skills/instructions.
- Skills sync out to `.claude`, `.codex`, and `.agents`.
- Worktree conventions exist.

Review-highlighted commit/work themes:

- Touch interaction.
- “Nails/hanging paintings” drop-target metaphor.
- Dead-code removal.

## Current caution from review

At review time, uncommitted `future-scenes/` was sitting untracked.

## Reusable pattern

The skill-versioning / sync approach in ScienceClick2 is valuable beyond this project.

Potential reuse:

- Standardize AI agent instructions across Claude Code, Codex, and other agent tooling.
- Avoid instruction drift between `.claude`, `.codex`, `.agents`, and any future agent directories.
- Use a single source-of-truth `skills/` directory in other AI-assisted projects.

Potential recipient projects:

- [[WebElementChat]]
- [[CasaSpese]]
- scripts-ai / AI quota tooling
- Any future personal AI infrastructure project

## Deep portfolio assessment notes

Source: [[Deep Portfolio Assessment 2026-06-16]]

Claude's deeper project review keeps ScienceClick2 as medium-priority: already healthy, with strongest value in exporting its engineering patterns.

Key development directions from that assessment:

- Commit or intentionally ignore `future-scenes/`.
- Extract/document `sync-skills.py` as a reusable portfolio-level pattern.
- Add automated tests for match/result logic.
- Harden result/match stores for concurrent classroom use if classroom deployment becomes real.
- Add Google Sheets export for results if useful.
- Add teacher analytics such as per-term error rates.
- Longer-term: shareable scene packs, hosted multi-classroom mode, and prompt-assisted scene generation with a human review loop.

Cross-project leverage:

- ScienceClick2 should be treated as the source of the multi-agent skills-sync pattern for CasaSpese, WebElementChat, scripts-ai, and future projects.

## Related notes

- [[Projects]]
- [[Software Projects Review 2026-06-16]]
- [[Cross-Project Patterns 2026-06-16]]
- [[Deep Portfolio Assessment 2026-06-16]]
- [[WebElementChat]]
- [[CasaSpese]]
