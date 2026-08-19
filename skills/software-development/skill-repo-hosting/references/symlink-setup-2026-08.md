# Worked example: agenttalk-operator-seat → AgentTalk repo (2026-08-06)

Full session trace of hosting a skill in a git repo via symlink. Use as the
known-good recipe; adapt paths.

## Goal

Make `agenttalk-operator-seat` (canonical home `~/.hermes/skills/software-development/`)
versioned inside the AgentTalk repo so dev agents and worktrees pick it up, while
Hermes keeps loading it.

## Decisions

- Repo home: `/Users/fausto/Software/AgentTalk/design/operator-seat/` —
  sibling of `design/operator/` (per-run artifacts: briefs, bars, gradings)
  and `design/session-primers/` (role docs). The skill is the seat's living
  document, so it sits next to them, not inside the run-artifact dir.
- Direction: symlink in `~/.hermes` → repo. Git stores symlinks as pointer
  blobs (mode 120000); content must live IN the tree to be versioned.
- `.claude/skills` rejected: `.gitignore` has `.claude/*` except `settings.json`.

## Commands actually used

```bash
# 1. Copy (not move) into the repo
mkdir -p /Users/fausto/Software/AgentTalk/design/operator-seat
cp -R SKILL.md references /Users/fausto/Software/AgentTalk/design/operator-seat/

# 2. Integrity
diff -r ~/.hermes/skills/software-development/agenttalk-operator-seat/ \
       /Users/fausto/Software/AgentTalk/design/operator-seat/   # → empty

# 3. Swap: move original OUT of skills tree (never delete), then link
cd ~/.hermes/skills/software-development
mv agenttalk-operator-seat /tmp/agenttalk-operator-seat-backup-20260806
ln -s /Users/fausto/Software/AgentTalk/design/operator-seat agenttalk-operator-seat

# 4. Git sees it as untracked → commit is PO's
cd /Users/fausto/Software/AgentTalk && git status --short design/operator-seat/
# → ?? design/operator-seat/
```

## Verification that caught the real bug

- `skill_view('agenttalk-operator-seat')` ✅ (read path follows symlinks)
- `skill_manage(action='patch', ...)` ❌ `Skill not found in active profile 'default'`

Root cause: read path `iter_skill_index_files` (`agent/skill_utils.py`) uses
`os.walk(followlinks=True)`; write path `_find_skill` (`tools/skill_manager_tool.py`)
used `Path.rglob("SKILL.md")`, which does not descend into symlinked dirs on
Python < 3.13. Confirmed with both `python3` (3.10.8) and venv (3.11):
rglob count 14, agenttalk absent.

Fix (2 sites in `tools/skill_manager_tool.py`):
- `_find_skill` — swap `skills_dir.rglob("SKILL.md")` for
  `iter_skill_index_files(skills_dir, "SKILL.md")` (+ import it)
- `_find_skill_in_other_profiles` — same swap, same function-local import

Tests: `TestSymlinkedSkillDir` in `tests/tools/test_skill_manager_tool.py`
(find-through-symlink + patch-writes-to-real-dir). 88/88 pass.

Fresh-process proof (gateway still cached old module):
```bash
cd ~/.hermes/hermes-agent && venv/bin/python -c "
import sys; sys.path.insert(0, '.')
from tools.skill_manager_tool import _find_skill
print(_find_skill('agenttalk-operator-seat'))"
# → {'path': PosixPath('.../agenttalk-operator-seat')}
```

## Upstream PR artifacts (auth pending)

- Branch `fix/skill-manage-symlinked-skill-dirs` @ `b3f87695f`, pushed to
  local checkout only (SSH key `faustothegrey` has no push rights upstream).
- Prepared for manual submission in `/Users/fausto/agenttalk-hermes-fix/`:
  - `issue-body.md` — matches `.github/ISSUE_TEMPLATE/bug_report.yml` fields
  - `pr-description.md` — matches `.github/PULL_REQUEST_TEMPLATE.md`; `Fixes #<n>`
  - `0001-*.patch` — `git format-patch -1` for portable application

## Relay prompt to the dev agent

The AgentTalk dev agent was told via a pointer-style prompt (artifacts, not
restatements): repo home, pending commit, Hermes fix location. Prompt file:
`/Users/fausto/agenttalk-relay-operator-seat.md`. Style: name the paths and
statuses, don't re-explain the skill.
