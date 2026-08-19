# Import Chain Debug — 2026-06-28

## Scenario

Quota API at `127.0.0.1:9899` returned NameError for all three interactive fetchers:

```json
{"claude": {"ok": false, "error": "name 'claude_interactive_usage' is not defined"},
 "codex": {"ok": false, "error": "name 'codex_interactive_status' is not defined"},
 "antigravity": {"ok": false, "error": "name 'antigravity_interactive_usage' is not defined"}}
```

OpenRouter worked fine. Time between fetches was ~2-3s (impossible — real scrapes take 10-35s each).

## Debugging trail

### Step 1 — Check the process

```bash
lsof -i :9899     # → PID 822 (old), 26248 (after kill+restart)
ps -p 822 -o command=
# → /usr/bin/python3 ...quota-monitoring/api.py
```

### Step 2 — Test the import from the same Python

```bash
# Shell python3 (homebrew) — works
python3 -c "from lib import claude_interactive_usage; print('OK')"
# → OK

# /usr/bin/python3 (launchd's Python) — fails
/usr/bin/python3 -c "from lib import claude_interactive_usage; print('OK')"
# → ModuleNotFoundError: No module named 'lib'
# (because cwd is /, not the quota-monitoring dir)
```

But api.py inserts the absolute path: `sys.path.insert(0, "/Users/fausto/Software/scripts-ai/quota-monitoring")`:

```bash
/usr/bin/python3 -c "
import sys
sys.path.insert(0, '/Users/fausto/Software/scripts-ai/quota-monitoring')
from lib import claude_interactive_usage
print('OK')
"
# → OK — lib.py resolves from the absolute path
```

### Step 3 — Follow the chain into lib.py

`lib.py` is just: `from ai_quota_lib import *`

```bash
/usr/bin/python3 -c "import ai_quota_lib; print(ai_quota_lib.__file__)"
# → ModuleNotFoundError: No module named 'ai_quota_lib'

python3 -c "import ai_quota_lib; print(ai_quota_lib.__file__)"
# → /Users/fausto/Software/scripts-ai/ai-quota-lib/ai_quota_lib/__init__.py
```

Shell `python3` finds it (PYTHONPATH or homebrew site-packages), but `/usr/bin/python3` doesn't. `ai_quota_lib` is NOT a pip package — just a directory on the filesystem.

### Step 4 — Root cause

The import chain in api.py:

```python
sys.path.insert(0, "/Users/fausto/Software/scripts-ai/quota-monitoring")   # ← added quota-monitoring
try:
    from lib import (                           # ← loads lib.py OK (absolute path)
        claude_usage_from_transcripts,
        codex_interactive_status,
        claude_interactive_usage,
        antigravity_interactive_usage,
    )
except ImportError:
    pass                                        # ← ai_quota_lib import fails silently inside lib.py!
```

`lib.py`'s `from ai_quota_lib import *` raises `ImportError`, which propagates out of `lib.py`'s import and is caught by the `except ImportError: pass` in `api.py`. All 4 names stay undefined.

### Step 5 — Fix

```python
sys.path.insert(0, "/Users/fausto/Software/scripts-ai/quota-monitoring")
sys.path.insert(0, "/Users/fausto/Software/scripts-ai/ai-quota-lib")   # ← add this
try:
    from lib import (...)
except ImportError:
    pass
```

### Step 6 — Restart

Kill the PID; launchd KeepAlive restarts it with the fixed import.

## Key lesson

`try/except ImportError: pass` at the top of any module is dangerous — it swallows ALL import chain failures silently. The server keeps running, logs say everything is fine ("done in 3s"), but the cache never populates.

**Always test the complete import chain with the EXACT Python the service uses**, not your shell's python3.
