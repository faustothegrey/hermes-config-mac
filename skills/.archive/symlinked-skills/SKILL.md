---
name: symlinked-skills
title: Version Hermes skills in a git repo and symlink them into the skills tree
description: "Keep a Hermes skill's canonical content inside a git repo (versioned, diffable, readable by repo agents and worktrees) and link it into ~/.hermes/skills via a symlink. Covers the load-bearing direction rule (content lives in the repo, the symlink points INTO it — git tracks pointers, never dereferenced content), the skill_manage vs skills_list symlink-scan asymmetry and its fix, the gateway restart required after patching hermes-agent source, and the end-to-end verification checklist."
version: 1.0.0
created: 2026-08-06
author: Hermes
source: AgentTalk operator-seat skill relocation session (2026-08-06) — symlinked design/operator-seat/ into the AgentTalk repo, found and fixed the rglob symlink bug in skill_manager_tool.py
---

# Symlinked skills (versioned in a git repo)

## When to use

The user wants a skill to be **versioned in a project repo** so that:
- the content travels with the repo (clones, worktrees, other machines),
- dev agents working in the repo pick it up without extra wiring,
- skill updates become diffable, reviewable governed changes.

## The direction rule (load-bearing — get this wrong and it silently fails)

**Git stores a symlink as a pointer blob (mode `120000`). It NEVER dereferences it.** So:

- ❌ **Symlink *inside* the repo pointing OUT to `~/.hermes/skills/...`** — git versions only the pointer string. The content stays in `~/.hermes`, invisible to clones and other machines; a fresh `git clone` gets a broken link. "Versioned" is false.
- ✅ **Canonical content lives in the repo; the symlink in `~/.hermes/skills/` points INTO the repo.** Content becomes a real tracked file — versioned, diffable, reviewable. Worktrees get it automatically (they share tracked files). Hermes still loads it as a skill (symlink resolves).

The AgentTalk repo already proves the in-repo symlink pattern: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` are all tracked symlinks → `AGENT.md`. The skill must be the same kind of in-tree citizen.

### Where in the repo

Match repo conventions. AgentTalk example: skill → `design/operator-seat/` (SKILL.md + references/), alongside `design/operator/` (per-run artifacts) and `design/session-primers/` (role docs). Do NOT use `.claude/skills` — `.claude/*` is commonly gitignored (AgentTalk's .gitignore excludes it except `settings.json`), so it would never be versioned.

## Pitfall: skill_manage "Skill not found" on symlinked skill dirs (fixed 2026-08-06)

Symptom table:

| Path | Result before fix |
|------|-------------------|
| `skills_list` / `skill_view` (read) | ✅ found the skill through the symlink |
| `skill_manage` patch/edit/delete (write) | ❌ "Skill 'X' not found in active profile" |

Root cause: asymmetric scanning.
- Read path (`iter_skill_index_files` in `agent/skill_utils.py`) uses `os.walk(..., followlinks=True)` → descends into symlinked dirs.
- Write path (`_find_skill` in `tools/skill_manager_tool.py`) used `Path.rglob("SKILL.md")` → does **not** descend into symlinked dirs on Python < 3.13.

Fix: make `_find_skill` AND `_find_skill_in_other_profiles` use the same `iter_skill_index_files(skills_dir, "SKILL.md")` helper (import it alongside `is_excluded_skill_path`). Regression tests added in `tests/tools/test_skill_manager_tool.py::TestSymlinkedSkillDir` (find through symlink + patch lands in the real dir behind the link). 88 tests pass.

## Pitfall: patching hermes-agent source does NOT take effect in the running gateway

Tool modules are imported once at process start. After editing `tools/*.py`:
- **Fresh-process proof** (no restart needed): `cd ~/.hermes/hermes-agent && venv/bin/python -c "from tools.skill_manager_tool import _find_skill; print(_find_skill('<name>'))"` — a new interpreter picks up the change immediately.
- **The running gateway** (launchd `ai.hermes.gateway`) keeps the old module cached. `skill_manage` keeps failing until `hermes gateway restart`. `/reload-skills` re-scans the skill dir but does NOT reload tool modules.
- Verify after restart by running the actual `skill_manage` patch, then confirming the file changed on the repo side AND both paths share an inode (`ls -li <symlink-path>/SKILL.md <repo-path>/SKILL.md`).

## Verification checklist after setting up a symlinked skill

1. Read path: `skills_list` / `skill_view` resolve the skill through the symlink.
2. Write path: `skill_manage(action='patch', ...)` succeeds; the change lands in the **repo** file (grep it on the repo side, check `ls -li` inode match).
3. Git: `git status --short` shows the new skill dir as untracked content (`?? design/operator-seat/`), NOT as a symlink pointer.
4. Keep a backup: move the original `~/.hermes/skills/...` dir aside (e.g. `/tmp/...-backup-<date>`) rather than deleting it, until the repo copy is committed.
5. The commit is the PO's/owner's call — the operator never commits to mainline (AgentTalk charter). Report `?? path` and stop.

## Workflow consequences of a versioned skill

Editing the skill now edits the repo working tree. Skill updates become governed changes: in AgentTalk terms, the operator may not write mainline, so updates flow as a working-tree diff for the PO to review/commit, or as a branch. This is a feature — the skill gains a review path it never had. The skill's own SKILL.md should carry a "This skill:" line pointing at its canonical repo location so future sessions know where writes land.

## Genuine upstream bugs found while doing this → submit an official patch

The user authorizes submitting an official patch when a real Hermes bug surfaces (2026-08-06: the rglob symlink bug). Procedure (see `github-pr-workflow` skill):
- Branch `fix/<description>` from fresh `main`, commit ONLY the fix files — never unrelated working-tree changes present in the checkout.
- Add regression tests; run the file's suite with `venv/bin/python -m pytest <file> -o 'addopts=' -q`.
- Push + PR. If push to upstream is denied (SSH key without upstream write access), you need a fork: requires `gh`, a `GITHUB_TOKEN` in `~/.hermes/.env`, or a logged-in browser session. If none is available, report the branch + commit SHA as ready and ask how the user wants the PR opened — the work is complete even if submission is blocked.

## Support files

- `references/skill-manage-symlink-debug.md` — full session detail: symptom, root-cause diff, fix, tests, PR state.

---
> **Archive note (2026-08-12):** This skill was consolidated into `skill-repo-hosting` (software-development/). Its content is now the sections of that umbrella; the debug reference was re-homed to `skill-repo-hosting/references/skill-manage-symlink-debug.md`. This directory is preserved in `.archive/` for recoverability.
