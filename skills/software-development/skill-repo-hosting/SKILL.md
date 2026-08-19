---
name: skill-repo-hosting
title: Host a Hermes skill in a git repo and load it via symlink
description: "Version a skill in a git repo (shared with dev agents, diffable, reviewable) while Hermes keeps loading it — symlink direction, verification, and the skill_manage symlink-scan pitfall."
version: 1.0.0
created: 2026-08-06
author: Hermes
source: agenttalk-operator-seat relocation session (2026-08-06)
---

# Hosting a skill in a git repo (symlink pattern)

## When to use

- The user wants a skill **versioned in a repo** so dev agents working in that repo (and every worktree/clone) can pick it up, while Hermes still loads it from `~/.hermes/skills/`
- A skill's canonical home should move out of the Hermes-proprietary tree into a project the user owns
- Agent-to-agent handoff: the user documents projects so other agents can consume them — a repo-hosted skill is the same pattern

## The direction rule (load-bearing)

**Symlink in `~/.hermes` → INTO the repo. NEVER the reverse.**

- ❌ `repo/skill → ~/.hermes/skills/...`: git stores a symlink as a *pointer blob* (mode 120000), never the dereferenced content. Clones and other machines get a broken link. The content is NOT versioned — only the pointer is.
- ✅ `~/.hermes/skills/<cat>/<name> → /path/to/repo/<dir>/`: content is a real tracked file → versioned, diffable, reviewable. Worktrees share it automatically. Hermes loads it through the link.

Precedent already exists in the AgentTalk repo: `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` are all tracked symlinks → `AGENT.md`. The only difference: those point *within* the tree — the skill must too.

## Procedure

1. **Pick the repo home.** Match existing conventions (`design/<seat>/`, `docs/`, etc.). For a role/seat skill, sibling of `design/operator/` and `design/session-primers/` style dirs is natural. Keep the skill dir name equal to the skill name if possible.
2. **Copy, don't move**: `mkdir -p <repo>/<dir> && cp -R SKILL.md references <repo>/<dir>/`
3. **Verify integrity**: `diff -r ~/.hermes/skills/<cat>/<name>/ <repo>/<dir>/` → must print nothing.
4. **Swap**: `mv` the original skill dir OUTSIDE the skills tree (e.g. `/tmp/<name>-backup-<date>` — do NOT delete; user hates data loss) then `ln -s <repo>/<dir> ~/.hermes/skills/<cat>/<name>`
5. **Verify read path**: `skill_view(name)` and `skills_list` must resolve through the link.
6. **Verify write path**: `skill_manage(action='patch', name=...)` must land in the repo file — confirm with `ls -li <repo>/.../SKILL.md ~/.hermes/.../SKILL.md` → **same inode**.
7. **Leave the commit to the user/PO** (operator seat never commits; governed repo changes flow as a diff). Tell the user the repo dir is untracked (`?? <dir>/`) and ready for their commit.

## Pitfalls

1. **`skill_manage` cannot see symlinked skills (Hermes bug, Python < 3.13).** The read path (`iter_skill_index_files` in `agent/skill_utils.py`) uses `os.walk(followlinks=True)` → follows symlinks. The write path (`_find_skill` / `_find_skill_in_other_profiles` in `tools/skill_manager_tool.py`) used `Path.rglob("SKILL.md")` → does NOT follow symlinked dirs before Python 3.13. Symptom: skill visible in `skills_list`/`skill_view`, but `skill_manage` fails with `Skill '<name>' not found in active profile 'default'`.

   Symptom table (read/write asymmetry):

   | Path | Result before fix |
   |------|-------------------|
   | `skills_list` / `skill_view` (read) | ✅ found the skill through the symlink |
   | `skill_manage` patch/edit/delete (write) | ❌ "Skill 'X' not found in active profile" |

   Root cause: `Path.rglob("SKILL.md")` does not descend into symlinked directories on Python ≤ 3.12 (the `follow_symlinks` glob parameter only arrived in 3.13). Verified: `list(Path(...).rglob('SKILL.md'))` returns 14 hits with the symlinked skill absent.
   - Fix: make `_find_skill` use the same `iter_skill_index_files` helper as the read path (keeps the exclusion set identical). Fix is on branch `fix/skill-manage-symlinked-skill-dirs` in hermes-agent; regression tests in `TestSymlinkedSkillDir`.
   - Verify in a fresh process before trusting in-session behavior: `venv/bin/python -c "from tools.skill_manager_tool import _find_skill; print(_find_skill('<name>'))"`.
2. **Running gateway caches modules.** A source fix in `~/.hermes/hermes-agent` does NOT take effect in the running gateway until `hermes gateway restart`. In-session tool calls keep failing after the patch; fresh-process tests pass. Don't loop on the tool — restart (ask user first: service change) or prove via fresh process.
3. **`.claude/skills` is not an option** if the repo gitignores `.claude/` — check the repo's `.gitignore` before proposing it.
4. **Relative vs absolute symlink.** `~/.hermes` → `~/Software/<repo>` can't be a short relative path (different roots). `../../../../Software/<repo>/...` survives user-dir moves but not repo relocation. Absolute is fine for single-machine setups; note the trade-off.
5. **Backup first, delete never.** Keep the pre-symlink copy in `/tmp` until the repo commit lands.

## Workflow consequences of a versioned skill

Editing the skill now edits the repo working tree. Skill updates become governed changes: in AgentTalk terms, the operator may not write mainline, so updates flow as a working-tree diff for the PO to review/commit, or as a branch. This is a feature — the skill gains a review path it never had. The skill's own SKILL.md should carry a "This skill:" line pointing at its canonical repo location (e.g. `design/operator-seat/` in the AgentTalk repo) so future sessions know where writes land.

## Genuine upstream bugs found while doing this → submit an official patch

The user authorizes submitting an official patch when a real Hermes bug surfaces (2026-08-06: the rglob symlink bug). Procedure (see `github-pr-workflow` skill):
- Branch `fix/<description>` from fresh `main`, commit ONLY the fix files — never unrelated working-tree changes present in the checkout.
- Add regression tests; run the file's suite with `venv/bin/python -m pytest <file> -o 'addopts=' -q`.
- Push + PR. If push to upstream is denied (SSH key without upstream write access), you need a fork: requires `gh`, a `GITHUB_TOKEN` in `~/.hermes/.env`, or a logged-in browser session. If none is available, report the branch + commit SHA as ready and ask how the user wants the PR opened — the work is complete even if submission is blocked.

## Supporting files

- `references/symlink-setup-2026-08.md` — full worked example: agenttalk-operator-seat → AgentTalk repo, exact commands, bug diagnosis, upstream PR artifacts.
- `references/skill-manage-symlink-debug.md` — deep debug session: read/write scan asymmetry root cause, code-path table, regression tests (`TestSymlinkedSkillDir`), gateway restart proof, PR state. (Absorbed from the former `symlinked-skills` skill.)

## Verification checklist

- [ ] `diff -r` clean after copy
- [ ] `skill_view` resolves through the link
- [ ] `skill_manage` patch writes to the repo (same inode via `ls -li`)
- [ ] Original dir backed up in `/tmp`, not deleted
- [ ] Repo status shows the new dir untracked → commit left to user/PO
- [ ] If `skill_manage` says "not found": fresh-process `_find_skill` probe → gateway restart needed

> **Package integrity note:** The `symlinked-skills` skill (hermes/) was absorbed into this umbrella on 2026-08-12. Its unique content — the read/write scan asymmetry symptom table, the workflow-consequences section, and the upstream-fix submission procedure — is now in the sections above. Its debug reference was re-homed to `references/skill-manage-symlink-debug.md`. The original skill directory has been moved to `.archive/`.
