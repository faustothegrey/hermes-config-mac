# Cron job status query reference

Sources of truth for checking any Hermes cron job's status. Ordered by speed/depth.

## 1. Quick check — cronjob list API

```
Tool: cronjob(action='list')
Returns: last_status, last_run_at, last_error, next_run_at
Limitations: NO total run count. Does not expose repeat.completed.
```

This is the fastest path for "did it pass or fail, and when." Use it as the first call.

Note: The internal `~/.hermes/cron.db` SQLite file exists but has NO tables or schema — it is not a storage backend. All cron job state lives in `~/.hermes/cron/jobs.json`.

## 2. Total run count — jobs.json (canonical)

The scheduler tracks completed ticks in its internal state file:

```bash
python3 -c "
import json
data = json.load(open('$HOME/.hermes/cron/jobs.json'))
for jid, job in enumerate(data['jobs']):
    print(f'{job.get(\"name\",jid)}: {job.get(\"repeat\",{}).get(\"completed\",0)} runs')
"
```

Or for a specific job by ID:

```bash
python3 -c "
import json
data = json.load(open('$HOME/.hermes/cron/jobs.json'))
for j in data['jobs']:
    if j.get('id')=='b763d78565da':
        print(j['repeat']['completed'])
"
```

The `repeat.completed` field is the scheduler's own counter — includes ALL ticks (success + failure). This is the canonical total.

## 3. Output directory count — filesystem

```bash
ls ~/.hermes/cron/output/<job_id>/ | wc -l
```

Each tick creates an output directory. May diverge from `repeat.completed` if outputs were pruned manually. Use as fallback.

## 4. Detailed error diagnosis

For errors beyond the `last_error` field:

- Check the output directory for the specific run: `ls -t ~/.hermes/cron/output/<job_id>/ | head -1`
- Read the latest run's content: `cat ~/.hermes/cron/output/<job_id>/<latest_dir>/stdout`
- Also check stderr: `cat ~/.hermes/cron/output/<job_id>/<latest_dir>/stderr`

## 5. Exact-format JSON status schema (Italian query)

When the user asks in Italian for cron job status and specifies exact JSON output, respond ONLY with valid JSON — zero prose, no markdown fences, no wrappers, no explanations.

Expected schema:

```json
{"esito":"success|error|running|never-ran","ultimo_run":"ISO datetime or null","run_totali":N}
```

Field sources:
- **esito**: maps from `last_status` in cronjob(action='list') output. `ok` → "success", `error` → "error", `running` → "running". If no `last_run_at` exists → "never-ran".
- **ultimo_run**: the `last_run_at` ISO datetime string from cronjob(action='list'), verbatim. If never ran → null.
- **run_totali**: integer. Prefer `repeat.completed` from `~/.hermes/cron/jobs.json` (canonical scheduler counter, ALL runs). Fallback: count output entries in `~/.hermes/cron/output/<job_id>/` with `ls | wc -l`. NEVER use git commit count (`git rev-list --count HEAD`) — it only reflects runs that committed successfully. For backup-job git-based tasks, 20-40% of cron ticks fail before commit, making git count a significant under-report. Always resolve `run_totali` from jobs.json or output directory first; git count is a last-resort that must be qualified as "successful runs only" if used.

## 6. Output directory structure — no-agent vs agent mode

The output structure differs by cron job mode:

**No-agent mode** (script-only, like backup): each run produces a single `.md` file directly in the output directory:
```
~/.hermes/cron/output/<job_id>/2026-07-14_17-30-36.md
```
Content is markdown with run metadata including `Status:` line (e.g. "script failed", "script timed out after 120s").

**Agent mode** (LLM-driven): each run creates a subdirectory with stdout/stderr:
```
~/.hermes/cron/output/<job_id>/<timestamp>/
  stdout
  stderr
```

When counting runs, use `ls | wc -l` on the output directory regardless of mode — both formats produce one entry per run.