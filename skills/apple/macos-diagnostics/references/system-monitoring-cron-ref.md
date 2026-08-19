# Cron jobs attivi (monitoring)

| Nome | ID | Frequenza | Script | Deliver | 
|------|-----|-----------|--------|---------|
| load-sampler | bdd8a7b271c1 | every 2m | load-sampler.sh | origin |
| load-analyzer | 78f09e4a6c3a | every 10m | load-analyzer.sh | origin |
| service-watchdog | 7a8c50bfdacc | every 5m | service-watchdog | all |
| tm-backup-progress | 4feee8bd6041 | every 15m | tm-backup-watchdog.sh | origin |
| agy-kill-switch | 2f7048c6f97a | every 1m | agy-kill-switch.sh | local |

# Soglie load

| Soglia | Valore | Azione |
|--------|--------|--------|
| WARN | ≥ 10 | Alert Telegram (analyzer) |
| CRIT | ≥ 18 | Alert Telegram + Email (sampler + analyzer) |
| TREND | ≥ 7.0 e in salita | Alert Telegram (analyzer) |
| TREND margine | 0.5 | Differenza minima 1m > 30m per trend valido |

# Cooldown

| Tipo | Cooldown |
|------|----------|
| WARN | 10 min |
| CRIT | 5 min |
| TREND | 10 min |

# History file

`~/.hermes/cron/output/.load_history` — formato CSV:
```
<epoch>,<load_1m>,<load_5m>,<load_15m>
```
Max 90 entry (3 ore di dati a 2 min di sampling).
