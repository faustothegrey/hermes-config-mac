# Zombie / Orphan Process Cleanup

## Overview

System zombies and orphan agent processes can accumulate on macOS. Two distinct classes:

| Class | Sintomo | Impatto | Rilevamento |
|---|---|---|---|
| **Agent orphans** | `ps aux \| grep agy` mostra PID con PPID=1, 30-60% CPU | Load 20+, CPU sprecata | `agentctl health --json` → orphan_count > 0 |
| **System zombies** | `ps axo state,pid,comm \| grep ' Z'` mostra `<defunct>`, PPID di un processo ancora vivo | 0% CPU, occupano entry nel proc table | `ps axo state \| grep Z` |

## Agent orphans (PPID=1)

**Causa:** agy (o Claude/Codex) avviato in una finestra iTerm che viene chiusa. Il processo sopravvive orfano di launchd (PPID=1).

**Rilevamento automatico:**
- `agentctl health --json` → `agents.<name>.orphan_count > 0`
- `agent-minder` cron (ogni 3 min) → report su Telegram

**Pulizia automatica (allo spawn):**
```bash
agentctl spawn agy
# Se trova duplicati/orfani: stampa warning e dopo 120s auto-pulisce
```

**Pulizia manuale:**
```bash
# Trova orfani
ps -o pid,ppid,%cpu,command -p $(pgrep agy) | grep '^ *[0-9]\{1,\} *1 '
# Kill
kill -9 <PID_orfano>
```

## System zombies

**Causa:** un processo figlio termina ma il genitore non fa `wait()`/`waitpid()` per reaparlo. Su macOS, il genitore è spesso una sessione SSH (`sshd-session`) o un processo di rete terminato male.

**Sintomo:**
```
Z    12694 <defunct>         # PID 12694 è zombie
```
Il genitore (es. `sshd-session`) è ancora vivo con PPID=1 (launchd).

**Pulizia:** l'unico modo per far sparire uno zombie è killare il genitore, così init (launchd) lo riapre.

```bash
# 1. Trova il genitore
ps -p <zombie_pid> -o ppid=
# Esempio: ps -p 12694 -o ppid= → 12689

# 2. Verifica chi è il genitore
ps -p <ppid> -o pid,ppid,comm,lstart

# 3. Kill genitore (spesso serve sudo su macOS per processi di sistema)
# Ottieni password da email Virgilio (fausto.lelli@virgilio.it)
himalaya envelope list --page 1 | head -10
# Leggi l'email con la password (subject "Saluti" da gmail)
himalaya message read <id>
# Kill con sudo
echo "<password>" | sudo -S kill <genitore_pid>
# Cancella email password
himalaya message delete <id>

# 4. Verifica
ps -p <zombie_pid> 2>/dev/null || echo "Zombie ripulito"
ps axo state,pid,comm | grep ' Z' | grep -v grep || echo "Nessuno zombie"
```

**Nota:** killare il genitore può terminare anche processi attivi (es. sessioni SSH aperte). Verificare prima di killare.

## Workflow completo (dalla scoperta alla pulizia)

1. **Scoperta:** `ps axo state,pid,comm | grep ' Z'` o `agentctl health --json` con anomalie
2. **Diagnosi:** determinare classe (zombie di sistema vs orfano agente)
3. **Agente orfano:** `kill -9 <PID>` direttamente (nessun sudo necessario)
4. **Zombie di sistema:** 
   a. Trovare genitore (`ps -p <zombie> -o ppid=`)
   b. Verificare che sia sicuro killarlo
   c. Ottenere password sudo da email Virgilio
   d. `sudo kill <genitore>`
   e. Cancellare email password
5. **Verifica:** `ps axo state | grep Z` — zero risultati = pulito
