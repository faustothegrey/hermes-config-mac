# skill_manage vs symlinked skill dirs — full debug session (2026-08-06)

## Scenario

User asked to relocate the `agenttalk-operator-seat` Hermes skill into the AgentTalk repo
(`/Users/fausto/Software/AgentTalk/design/operator-seat/`) so it is versioned and repo agents
can pick it up. Direction chosen: **canonical content in the repo, symlink in
`~/.hermes/skills/software-development/agenttalk-operator-seat` → repo path** (the user
explicitly approved this direction after the operator explained git tracks pointers, not content).

## Symptom

After the symlink was created:
- `skills_list` and `skill_view` found the skill fine (read path OK).
- `skill_manage(action='patch', ...)` failed with `Skill 'agenttalk-operator-seat' not found in active profile 'default'.`
- The failure persisted across two identical retries (loop warning fired) — not transient.

## Root cause

Two different scan implementations:

| Code path | Function | Mechanism | Follows symlinked dirs? |
|-----------|----------|-----------|--------------------------|
| Read (skills_list / skill_view) | `iter_skill_index_files` in `agent/skill_utils.py` | `os.walk(..., followlinks=True)` | ✅ yes |
| Write (skill_manage) | `_find_skill` in `tools/skill_manager_tool.py` | `Path.rglob("SKILL.md")` | ❌ no (Python < 3.13) |

Verified directly:
```bash
cd ~/.hermes/hermes-agent
venv/bin/python -c "
from pathlib import Path
p = Path('/Users/fausto/.hermes/skills/software-development')
hits = list(p.rglob('SKILL.md'))
print(len(hits), any('agenttalk' in str(h) for h in hits))  # 14, False — symlink skipped
"
```

`rglob` does not descend into symlinked directories on Python ≤ 3.12 (the `follow_symlinks`
glob parameter only arrived in 3.13).

## Fix (tools/skill_manager_tool.py)

Both lookup sites switched to the shared helper:

```python
from agent.skill_utils import (
    get_all_skills_dirs,
    is_excluded_skill_path,
    iter_skill_index_files,
)
for skills_dir in get_all_skills_dirs():
    if not skills_dir.exists():
        continue
    for skill_md in iter_skill_index_files(skills_dir, "SKILL.md"):
        ...
```

Same replacement in `_find_skill_in_other_profiles` (second rglob site, line ~357) —
same bug class, cross-profile lookup. Added `iter_skill_index_files` to that function's
local import too.

## Tests

Added `tests/tools/test_skill_manager_tool.py::TestSymlinkedSkillDir`:

1. `test_find_skill_through_symlink` — real skill dir outside the tree, symlinked in under
   a category subdir; asserts `_find_skill("my-skill")` resolves it.
2. `test_patch_skill_through_symlink_writes_to_real_dir` — patches through the symlink and
   asserts the write lands in the real directory behind the link (not a copy).

Result: 88 passed (86 pre-existing + 2 new).

## Gateway restart requirement

The running gateway (launchd `ai.hermes.gateway`) cached the old module. Even after the
source fix + tests passed, in-session `skill_manage` kept failing until the user ran
`hermes gateway restart`. After restart, the patch succeeded and the change appeared in the
repo file (same inode via `ls -li`). Fresh-process proof without restart:

```bash
cd ~/.hermes/hermes-agent && venv/bin/python -c "
import sys; sys.path.insert(0, '.')
from tools.skill_manager_tool import _find_skill
print(_find_skill('agenttalk-operator-seat'))  # {'path': PosixPath('/Users/fausto/.hermes/skills/software-development/agenttalk-operator-seat')}
"
```

## PR state (as of session end)

- Branch `fix/skill-manage-symlinked-skill-dirs`, commit `b3f87695f`, committed ONLY the two
  fix files (the checkout had unrelated uncommitted work: tools_config.py, toolsets.py,
  antigravity_tool.py, claude_code_tool.py — deliberately left out of the commit).
- Push blocked: SSH key (`faustothegrey`) has no write access to `NousResearch/hermes-agent`.
- No `gh` CLI, `GITHUB_TOKEN` commented out in `~/.hermes/.env`, browser not logged into
  GitHub. So fork+PR requires user to supply a token, log in via browser, or fork manually.
- Session ended asking the user which path they prefer.

## Operational notes for the repo-side skill

- The relocated skill's SKILL.md carries a "This skill: `design/operator-seat/` in the
  AgentTalk repo (canonical, versioned — Hermes loads it via symlink)" line under
  Sources of truth, so future sessions know where writes land.
- Original skill dir moved aside (not deleted) to `/tmp/agenttalk-operator-seat-backup-20260806`.
