# agentctl health --json Output Schema

Esegui: `agentctl health --json` dal repo `~/Software/scripts-ai/agent-bus/`

## Top-level

| Campo | Tipo | Descrizione |
|---|---|---|
| `load` | `{1m, 5m, 15m}` | Load averages da `sysctl vm.loadavg` |
| `load_warn_threshold` | int | Soglia WARN (default 10) |
| `load_crit_threshold` | int | Soglia CRIT (default 18) |
| `agents` | `{name: AgentInfo}` | Mappa nome agente → processo |
| `anomaly_count` | int | 0 = tutto ok |
| `anomalies` | string[] | Descrizioni testuali anomalie |
| `timestamp` | ISO-8601 | UTC |

## AgentInfo

| Campo | Tipo | Descrizione |
|---|---|---|
| `count` | int | Numero processi trovati |
| `processes` | ProcessInfo[] | Dettaglio per ogni PID |
| `orphan_count` | int | PID non in sessioni tmux note |
| `known_count` | int | PID in sessioni tmux vive |
| `anomalies` | string[] | Anomalie specifiche di questo agente |

## ProcessInfo

| Campo | Tipo | Descrizione |
|---|---|---|
| `pid` | int | Process ID |
| `ppid` | int | Parent PID |
| `state` | string | Stato (`Ss+`, `R+`, etc.) |
| `in_tmux` | bool | Se il processo è sotto `script -q` wrapper tmux |
| `orphan` | bool | PID non in known_pids (tmux registrato) |

## Parsing pattern (Python)

```python
import json, subprocess

r = subprocess.run(
    ["agentctl", "health", "--json"],
    capture_output=True, text=True, timeout=10,
)
data = json.loads(r.stdout)

if data["anomaly_count"] > 0:
    for anomaly in data["anomalies"]:
        print(f"⚠️ {anomaly}")
    for name, info in data["agents"].items():
        if info["anomalies"]:
            print(f"  {name}: {info['count']} proc, "
                  f"{info['orphan_count']} orfani, "
                  f"{info['known_count']} registrati")
            for p in info["processes"]:
                tag = "tmux" if p["in_tmux"] else "orphan"
                print(f"    PID {p['pid']:<6} {tag}  PPID={p['ppid']}")
```
