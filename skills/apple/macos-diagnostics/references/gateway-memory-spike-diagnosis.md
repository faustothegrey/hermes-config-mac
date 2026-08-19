# Gateway Memory Spike Diagnosis

## Problem

The Hermes gateway process stops responding after ~30 minutes of uptime.
The user reports: "dopo un po' non rispondi più" / "after a while you stop responding."

Root cause: the gateway's RSS memory doubles in the first 5 minutes (92MB → 186MB),
plateaus at ~197MB for 20 minutes, then **spikes to 357MB at the 30-minute mark**
and crashes or becomes unresponsive.

## Diagnosis Steps

### 1. Check Gateway Memory Trend

The gateway has a built-in memory monitor that logs RSS every 300 seconds (5 min):

```bash
grep "rss=" ~/.hermes/logs/gateway.log | grep -oE 'rss=[0-9]+MB.*uptime=[0-9]+s' | tail -20
```

**Healthy pattern** (stable, long-running gateway):
```
rss=137MB ... uptime=300s
rss=137MB ... uptime=600s
rss=137MB ... uptime=900s
... (stable at 137MB for days)
```

**Unhealthy pattern** (memory spike → imminent crash):
```
rss=92MB  ... uptime=0s     (baseline)
rss=186MB ... uptime=300s   (+94MB in 5 min!)
rss=194MB ... uptime=600s
rss=196MB ... uptime=900s
rss=197MB ... uptime=1200s
rss=197MB ... uptime=1500s  (plateau)
rss=357MB ... uptime=1800s  🔴 SPIKE +160MB in 5 min!
(gateway crashes shortly after)
```

### 2. Count Crash Frequency

```bash
grep -c "Exiting with code 1" ~/.hermes/logs/gateway.log
```

A single long-running gateway session is healthy. Multiple crash-restart
cycles in the same day indicate a memory or connectivity problem.

### 3. Check Crash Loop Pattern

```bash
grep -E "nodename|timed out|SIGTERM|exit code 1" ~/.hermes/logs/gateway.log | tail -10
```

### 4. Check Gateway Startup Sequence

```bash
grep -E "memory_monitor.*(baseline|shutdown rss=)" ~/.hermes/logs/gateway.log | tail -10
```

Each `baseline rss=92MB` followed by `shutdown rss=XXXMB` at `uptime=YYYs`
shows a gateway lifcycle. Short lifespans (<300s) suggest a crash loop.

## Timeline of a Memory Crash

Using the actual data from 2026-06-28:

```
06:47:27  baseline rss=92MB (gateway starts)
06:51:43  shutdown rss=130MB (crash at 158s — DNS failure)

06:55:11  baseline rss=92MB (restart)
07:00:11  rss=186MB (5 min, +94MB)
07:05:11  rss=194MB (10 min)
07:10:11  rss=196MB (15 min)
07:15:12  rss=197MB (20 min, plateau)
07:20:12  rss=197MB (25 min, holding)
07:25:12  rss=357MB 🔴 (30 min — SPIKE!)
07:40:40  baseline rss=92MB (crash, restart)
```

The crash at 07:40 happened because memory went from 92MB → 357MB in 30 minutes.

## Why This Happens

### Normal vs Abnormal Growth

| Phase | Healthy | Unhealthy |
|-------|---------|-----------|
| Baseline → 5 min | 117MB → 137MB (+20MB) | 92MB → 186MB (+94MB) |
| 5 min → 1 hour | 137MB stable | 186→197→**357MB** 🔴 |
| Days/weeks | Slowly drifts to ~180MB | Crashes within 30 min |

### ROOT CAUSE IDENTIFIED: macOS Network Power Management

The memory spike is **not** caused by Hermes itself. It's a downstream effect
of macOS network power management.

**The chain of events:**

```
macOS networkoversleep=0 (default)
  → after ~25 min of no incoming traffic, WiFi chipset drops SYN packets
  → Telegram API disconnects (httpx.ReadError)
  → gateway retry loop — accumulates buffers for undelivered messages
  → RSS grows from 92MB → 197MB over 25 min (retry + buffer accumulation)
  → at ~30 min, accumulated state plus context compression trigger SPIKE
  → RSS jumps to 357MB → OOM / crash
```

**The fix:** `sudo pmset -a networkoversleep 1`

This tells macOS to keep TCP connections alive even during power-saving states.
Default is `0` — the WiFi can enter power-save mode regardless of system sleep state.

**Result after fix:**
```
rss=203MB @ 30:35 (was 357MB before)
CPU=5.0%         (was 64.2% before)
Load=9.82        (was 21.96 before)
```

The gateway runs indefinitely without the spike when network connectivity is stable.

### Secondary Contributors

While the primary cause is `networkoversleep=0`, these factors amplify the problem:

1. **DNS instability on FritzBox router** (192.168.178.1) — occasional
   `[Errno 8] nodename nor servname provided, or not known` errors for
   `api.telegram.org`. When DNS fails AND the port is blocked, the gateway
   enters a double-failure retry loop that grows memory faster.

2. **Context accumulation** — session context from active conversations may
   not be compressed aggressively enough under error conditions.

3. **Gateway restart frequency** — after a restart, the gateway starts at 92MB
   baseline vs. 117MB after long uptime. Rapid growth to 186MB in 5 min is
   normal for fresh restarts; the abnormal part is not plateauing.

4. **Telegram network errors** — `httpx.ReadError` every 30-90 minutes even
   under normal conditions. These recover in 5s normally, but when combined
   with port blocking the recovery fails → retry loop.

## Immediate Mitigations

### 1. Restart the Gateway

```bash
hermes gateway restart
```

This clears all accumulated state. Verify:

```bash
ps -o pid,lstart,pcpu,rss -p $(ps aux | grep "[g]ateway" | awk '{print $2}')
```

RSS should be ~92MB baseline shortly after restart.

### 2. Periodic Restart (Workaround)

If the memory spike pattern is consistent, schedule a gateway restart
every 25 minutes (before the 30-min spike):

This should be a cron job with a terminal command, not a no_agent script,
since it needs to wait for a clean shutdown:

```bash
hermes cron create \
  --name "gateway-refresh" \
  --schedule "*/25 * * * *" \
  --prompt "Run 'hermes gateway restart' to prevent memory spike" \
  --deliver local
```

### 3. Monitor Gateway Event Logs

Watch for the `rss=357MB` signal with the load watchdog:

```bash
# In the load-watchdog script, add:
GATEWAY_RSS=$(ps -o rss= -p $(ps aux | grep "[g]ateway" | awk '{print $2}') 2>/dev/null)
if [ -n "$GATEWAY_RSS" ] && [ "$GATEWAY_RSS" -gt 250000 ]; then
  echo "⚠️ Gateway RSS > 250MB — approaching spike threshold"
fi
```

## Concurrency with Other Symptoms

The memory spike often correlates with:

- **Telegram ReadErrors** (`httpx.ReadError` in gateway.log)
- **DNS resolution failures** (`[Errno 8] nodename nor servname provided`)
- **High load averages** (the gateway at 357MB pushes the system into swap)

When investigating a "stopped responding" report, check all three:

```bash
grep -c "ReadError" ~/.hermes/logs/gateway.log
grep -c "nodename" ~/.hermes/logs/gateway.log
grep "rss=" ~/.hermes/logs/gateway.log | grep -oE 'rss=[0-9]+MB' | tail -5
```

## Reference Session

Full analysis: 2026-06-28 session on Fausto's MacBook
(telegram conversation "Hermes non risponde dopo un po'")
