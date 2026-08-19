# Performance Triage: Load 22.62 → 5.58 (2026-06-28)

## Scenario

Utente segnala "carico pazzesco" / "stiamo provando a diminuire". System load a 13.78 con trend in salita.

## Sequenza di triage

### Step 1 — Health snapshot
```bash
uptime                           # load basale
ps aux | grep -E 'agy|PID'       # agy in particolare
```

Risultato: load 13.78, TRE processi agy (non uno).

### Step 2 — Identificazione processi pesanti
```bash
ps aux --sort=-%cpu | head -15
```

Risultato:
| PID | Cosa | CPU | Note |
|-----|------|-----|------|
| 16418 | agy | 156% | Da agentctl (legittimo) |
| 336 | backupd | 50% | Ancora in esecuzione dopo ore |
| 3915 | Hermes Gateway | 48% | Era 5%, risalito |
| 556 | SystemUIServer | 44% | Anomalo |
| 16036 | agy | 31% | PPID=1 (orfano!) |
| 16059 | agy | 30% | PPID=1 (orfano!) |

### Step 3 — Rilevamento orfani
```bash
ps -o pid,ppid,command -p 16036,16059
# → PPID=1 (launchd) — non più attaccati a nessuna finestra iTerm
```

Gli orfani erano partiti da finestre iTerm chiuse dall'utente. agy non muore alla chiusura della finestra — PPID diventa 1.

### Step 4 — Sample stack (capire cosa stanno facendo)
```bash
sample 16418 1 10    # agy principale: in read() — I/O bound
sample 16036 1 5     # orfano: chiamate interne
sample 16059 1 5     # orfano: chiamate interne
```

### Step 5 — Kill progressivo
1. Kill orfani: `kill -9 16036 16059` → **load 22.62 → 8.56** (-62%)
2. Kill agy legittimo (su richiesta utente): `kill -9 16418` + `tmux kill-session`
3. **Finale: load 5.58**

### Step 6 — Conferma e pulizia
```bash
uptime                                                               # 5.58
agentctl list                                                        # 🟢 nessun agente
echo '{}' > ~/.hermes/agent-sessions.json                           # stato pulito
```

## Lezioni

1. **Tre agy diversi**, non uno solo. `ps aux | grep agy` sempre.
2. **Orfani (PPID=1) sono silenziosi** — agentctl non li vede, non compaiono in `list`.
3. **Il load cala in 30-60 secondi** dopo il kill — non serve attendere.
4. **backupd + Gateway insieme** amplificano il problema: tre agy + backupd + gateway = 315% CPU combinata su 10 core = load 22.62.
5. **Utente ha detto "uccidi immediatamente"** — non chiedere, non esitare, kill subito e conferma dopo.
6. **Usare `agentctl spawn` previene gli orfani** — tmux mantiene il processo vivo anche se la finestra iTerm viene chiusa.
