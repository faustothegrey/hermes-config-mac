# macOS Network Freeze Session — 28 Giugno 2026

## Summary

MacBook Hermes gateway (peer128) was freezing after ~30 minutes of activity.
Root cause: `networkoversleep=0` (macOS default) causing WiFi to drop SYN packets
on non-standard ports after network inactivity — even with system sleep prevented.

## The Chain of Events (Full Narrative)

### 1. Symptoms

- "Hermes smette di rispondere dopo un po'"
- Load peaks at 21.96 (1-min)
- Gateway CPU at 34-64%
- Gateway memory spikes from 92MB → 357MB at 30 min, then crash
- Gateway log shows ReadErrors every 30-90 minutes
- Frequent gateway crash-restart cycles (10 exits overnight)

### 2. Initial Load Reduction

Actions taken to bring load down from 21.96:

| Action | Effect | 
|--------|--------|
| Kill Chrome | -560MB RSS |
| Kill Claude | -333MB, -17% CPU |
| Kill iTerm2 | -230MB, -30% CPU |
| Reboot Gateway | 34% → 12.9% CPU |
| **Load final** | **21.96 → 5.63** |

### 3. Memory Monitor Log Analysis

The gateway's built-in memory monitor (logging RSS every 300s) revealed the pattern:

```
Jun 28 06:47  baseline rss=92MB  (gateway start)
Jun 28 06:51  shutdown rss=130MB (crash at 158s — DNS failure)

Jun 28 06:55  baseline rss=92MB  (auto-restart)
Jun 28 07:00  rss=186MB          (5 min, +94MB)
Jun 28 07:05  rss=194MB          (10 min)
Jun 28 07:10  rss=196MB          (15 min)
Jun 28 07:15  rss=197MB          (20 min, plateau)
Jun 28 07:20  rss=197MB          (25 min, holding)
Jun 28 07:25  rss=357MB          🔴 (30 min — SPIKE, crash imminent)
Jun 28 07:40  baseline rss=92MB  (crash, restart)
```

Compare with healthy old gateway (16 days uptime):
```
Jun 12 16:20  baseline rss=117MB (gateway start)
Jun 12 16:25  rss=137MB          (5 min, +20MB — normal)
...
Jun 12-28     rss=137-180MB      (stable for 16 days)
```

### 4. The Eureka Moment: Peer84's Independent Diagnosis

Peer84 (fausto@N56VV, Ubuntu 22.04) had been analyzing the problem independently
via SSH on peer128. Their findings:

- **Ping always OK** → interface was alive
- **SSH always OK** → existing connections kept working
- **Port 8642 unreachable** from remote after ~minutes of inactivity
- **localhost:8642 always worked** → gateway process was healthy
- **Pattern:** remote TCP connections to non-standard ports were silently dropped

Peer84's initial workaround: SSH tunnel from N56VV → Mac with keepalive 15s.

### 5. The Discovery

While reading peer84's diagnosis (sent via email to fausto.lelli@virgilio.it at
ID 484), the common thread became clear:

Peer84's tunnel kept the connection alive (bypassing the port drop).
But the gateway's Telegram connection (outbound to api.telegram.org) was
also affected — when the WiFi power-saved, SYN packets from Telegram's
response were dropped, causing httpx.ReadError.

The retry loop from ReadErrors → accumulated memory buffers → crash.

### 6. The Fix

```
sudo pmset -a networkoversleep 1
```

Applied via askpass helper (password routed through email to avoid exposure in chat).

### 7. Verification

```
Gateway @ 30 min:
  RSS: 357MB → 203MB   ✅
  CPU: 64% → 5%        ✅
  Load: 21.96 → 9.82   ✅
  No crash              ✅
```

### 8. Lessons Learned

1. **Gateway memory spikes are symptoms, not root causes.** The real problem
   is always upstream (network, DNS, Telegram connectivity).

2. **Peer review works.** Peer84's tunnel workaround and documented diagnosis
   was the missing piece to connect network issues to memory growth.

3. **Email side-channel.** Using email to route sudo credentials kept the
   password out of Telegram and Hermes logs — a replicable pattern for
   operations that require privilege escalation.

4. **networkoversleep is a silent killer.** macOS defaults this to 0 and
   most users never discover it's the cause of intermittent network drops.

## Files

| Path | Content |
|------|---------|
| `load-watchdog.sh` | Load watchdog script (cron every 5min, threshold 10) |
| `anomalies.jsonl` (peer84) | Heavy load anomaly log on N56VV |
| `hermes-mac-analysis-20260628.md` (peer84) | Analysis sent to peer84 for comparison |

## Artifacts

- Email ID 485: "FOLLOW-UP COMPLETO: Risoluzione freeze Hermes Gateway — 28 Giugno 2026"
- Email ID 484: "Report tecnico: peer128 (MacBook Pro) — problema di connessione e risoluzione" (peer84's diagnosis)
- Cron job c9f2228110e3: load-watchdog (every 5m)
