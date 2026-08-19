---
name: agentctl
title: agentctl — Lifecycle management per agenti in tmux (standalone)
description: "Gestisci agenti CLI (Codex, Claude Code, Antigravity) in sessioni tmux. agentctl parla direttamente con tmux — niente server HTTP, niente agent-bus. I tmux sono workspace per l'utente: Hermes orchestra via delegate_task."
---

# agentctl — Agent Lifecycle Manager

**Binary:** `~/.local/bin/agentctl` (symlink → `~/Software/scripts-ai/agent-bus/agentctl` → git repo)
**Source (git):** `~/Software/scripts-ai/agent-bus/` (solo `agentctl` + `wrapper.sh`)
**Stato:** standalone — niente server HTTP, niente agent-bus (server.py è morto). Tuttavia, un'istanza orfana di `server.py` può ancora sopravvivere con PPID=1 (Pattern 5 in `references/common-false-positives.md`).

## tmux-metrics.sh — deterministic character counting

The harness at `scripts/tmux-metrics.sh` wraps `agentctl send` and `agentctl capture` with byte-accurate counters, useful for monitoring communication volume between Hermes and agent tmux sessions.

- `tmux-metrics.sh send <agent> <message>` — sends via agentctl, counts chars, resets received counter
- `tmux-metrics.sh capture <agent>` — captures via agentctl, counts chars, resets sent counter
- `tmux-metrics.sh status` — returns `{"sent":N,"received":N}` for API consumption

Counters also published at `GET /api/hermes/metrics`.

## Principio fondante: self-contained

**agentctl nasconde tmux.** Chi usa il tool non deve sapere che sotto c'è una sessione tmux. Tutte le operazioni — spawn, send, capture, kill — si fanno con agentctl, non con comandi tmux grezzi.

```
┌─────────────────────────────────────────────────────────┐
│                    Fausto (iTerm / Hermes)                │
│                                                          │
│   agentctl send agy "fai x"                              │
│   agentctl capture agy          ┌──────────────────┐     │
│   agentctl spawn agy            │   Hermes          │     │
│   agentctl kill agy             │  (orchestration)  │     │
│        │                        │  delegate_task    │     │
│        ▼                        └────────┬─────────┘     │
│   ┌──────────────────────┐               │               │
│   │   tmux (invisibile)  │               │               │
│   │   agy / Claude/Codex │               │               │
│   └──────────────────────┘               │               │
│                                          │               │
└──────────────────────────────────────────────────────────┘
```

- **agentctl è l'unica interfaccia** per interagire con agenti persistenti. Chi lo usa non tocca mai tmux direttamente.
- **Hermes** orchestra sub-task temporanei via `delegate_task`. Per agenti persistenti, usa `agentctl spawn`/`send`/`capture`.
- **send** con Escape automatico + Enter = parli con l'agente come se fossi nella sua console
- **capture** = leggi l'output recente dopo che l'agente ha risposto

## Comandi

``` 
agentctl spawn  <codex|claude|agy> [--name <sessione>] [--model <modello>] [--workdir <path>]
agentctl send   <agente> <messaggio>     # invia messaggio + Enter (con Escape automatico)
agentctl capture <agente>                # mostra output recente
agentctl list                            # agenti attivi, sessioni, alive/dead
agentctl health [--json]                 # check completo su tutti gli agenti + load
agentctl attach <agente>                 # stampa comando tmux attach
agentctl kill  <agente>                  # termina tmux + pulisce registro
```

## Flusso completo

```bash
# 1. Spawn — crea tmux, registra in ~/.hermes/agent-sessions.json
agentctl spawn agy
agentctl spawn agy --workdir /path/to/project   # avvia in una directory specifica
agentctl spawn agy -d ~/Software/MyProject       # alias breve per --workdir

# Dopo lo spawn, SE ci sono anomalie (duplicati, load alto):
#   stampa BIG WARNING + lancia auto-pulizia in background thread
#   che dopo 120 secondi killera orfani e duplicati.
#   Per cancellare: touch ~/.hermes/agentctl-cancel.flag
#   Oppure Ctrl+C.

# 2. Parla con l'agente (send + capture)
agentctl send agy "Ciao, sei attivo?"
sleep 5                           # aspetta che l'agente risponda
agentctl capture agy              # leggi la risposta

# 3. Work loop: send → attendi → capture
agentctl send agy "Fai x y z"
sleep 8
agentctl capture agy

# 4. Verifica stato
agentctl list          # 🟢 = alive, 🔴 = dead, mostra anche DIR se specificata

# 5. Health check completo
agentctl health        # output umano
agentctl health --json # JSON machine-readable per cron job

# 6. Kill
agentctl kill agy
```

**Nota su send:** non serve sapere che c'è tmux sotto. send fa:
1. Escape (chiude eventuale TUI)
2. sleep 0.3s
3. Scrive il messaggio + Enter
4. Tutto automatico.

## ⚠️ PITFALL: TMUX_TMPDIR su macOS

**Problema:** su macOS, `tmux` con il socket di default (`/private/tmp/tmux-501/default`) può fallire silenziosamente. Le chiamate a `tmux has-session` tornano "no server running" anche se il server è stato appena avviato.

**Fix in agentctl (riga 25-26):**
```python
TMUX_TMPDIR = "/tmp"
os.environ.setdefault("TMUX_TMPDIR", TMUX_TMPDIR)
```

Questo forza tmux a usare `/tmp/tmux-501/` invece di `/private/tmp/tmux-501/`. Stesso filesystem (entrambi sono symlink), ma il percorso breve evita bug di risoluzione in alcune configurazioni macOS.

**Se agentctl non trova la sessione:**
1. Controlla che `TMUX_TMPDIR=/tmp` sia nell'environment
2. Verifica con: `TMUX_TMPDIR=/tmp tmux has-session -t <sessione>`
3. Il socket dovrebbe essere in `/tmp/tmux-501/default`

## ⚠️ PITFALL: Stale tmux server (dead socket) — not just stale PIDs

**Problema:** Il tmux server può crashare o essere killato, lasciando il socket file sul filesystem (`/tmp/tmux-501/default` o `/private/tmp/tmux-501/default`) ma nessun server in esecuzione. Questo è **diverso dal problema stale PIDs**, dove tmux è vivo ma il PID registrato non corrisponde.

**Sintomo distintivo:**
```
$ tmux list-sessions
no server running on /private/tmp/tmux-501/default
```
Ma il socket file esiste:
```
$ ls -la /tmp/tmux-501/default
srw-rw----@  1 fausto  wheel     0 Jul  2 18:26 default
```

In `agentctl health --json`, tutti gli agenti mostrano `known_count: 0` (nessuna sessione tmux viva), anche se ci sono processi agenti in esecuzione in terminali iTerm live. I processi vengono correttamente classificati come orfani, ma la causa *non* è agentctl che sbaglia tracciamento — è tmux che non c'è più.

**Diagnostica rapida:**
```bash
# 1. Il socket esiste ma il server è morto?
ls -la /tmp/tmux-501/default && tmux list-sessions 2>&1
# "no server running" + socket file = stale socket

# 2. Verifica la stessa cosa da /private/tmp (sono symlink)
ls -la /private/tmp/tmux-501/default

# 3. Se TSERVER è morto, tutti i registered agent sono inutilizzabili
cat ~/.hermes/agent-sessions.json | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'{k}: sess={v[\"session\"]} pid={v[\"pid\"]}') for k,v in d.items()]"

# 4. Controlla se c'è un tmux server da qualche parte
pgrep -la tmux  # se vuoto → server definitivamente morto
```

**Impatto:**
- `agentctl send`/`capture`/`kill` non funzionano per agenti registrati
- Tutti i processi agenti in terminali iTerm live NON sono gestibili da agentctl
- Serve killare manualmente e rispawnare tutto via `agentctl spawn`

**Fix:**
```bash
# Pulisci il socket stale
rm -f /tmp/tmux-501/default

# Pulisci anche /private/tmp (stesso filesystem)
rm -f /private/tmp/tmux-501/default

# Respawn tutto da capo
agentctl spawn agy --workdir ~/Software/AgentTalk
agentctl spawn claude --workdir ~/Software/AgentTalk
agentctl spawn codex --workdir ~/Software/AgentTalk
```

Se vuoi killare gli agenti nei terminali iTerm prima di respawnare (per evitare duplicati):
```bash
# Trova tutti gli agente in esecuzione su ttysNNN (non tmux)
ps axo pid,tty,comm | grep -E 'agy|claude|codex' | grep -v '??' | grep -v grep
# Per ciascuno: kill -TERM <PID>
```

**Diagnostica differenziale: stale socket vs stale PIDs vs TMUX_TMPDIR:**

| Scenario | `tmux list-sessions` | socket file | `known_count` | Causa |
|----------|---------------------|-------------|---------------|-------|
| **TMUX_TMPDIR** | "no server" (sbaglia path) | `/private/tmp/...` vivo | 0 | tmux cerca nel socket sbagliato |
| **Stale PIDs** | agente 🟢 listato | vivo | 0 | PID cambia dopo riavvio in tmux |
| **Stale socket** | "no server running" | esiste ma morto | 0 | tmux server crashato |
| **Tutto OK** | mostra sessioni attive | vivo | >0 | normale |

> **Vedi anche:** `references/stale-tmux-socket-investigation.md` — cronologia completa dell'analisi (2026-07-02).

## ⚠️ PITFALL: Multiline messages with `send` — use a temp file

`agentctl send <agent> <message>` takes the message as a single command-line argument. It does NOT read from stdin, so piping a multiline message via heredoc or stdin redirect fails.

```bash
# ❌ FAILS — agentctl doesn't read stdin
cat brief.md | agentctl send codex
cat << 'EOF' | agentctl send codex "..."

# ✅ CORRECT — store in a file, then pass as argument
cat << 'EOF' > /tmp/brief.md
Long multiline baton
with full context
EOF
agentctl send codex "$(cat /tmp/brief.md)"
```

This matters for baton handoffs (5+ lines with scope, DoD, file references) — the natural way to send structured task instructions. Always write longer messages to a temp file first, then use `$(cat ...)` expansion to pass them.

## ⚠️ PITFALL: Send timing — attendere prima di capture

Dopo `agentctl send`, l'agente deve:
1. Uscire dalla TUI (Escape, 300ms)
2. Ricevere il messaggio
3. Elaborare la richiesta (API call + generazione, 3-10s)

**Non fare capture subito dopo send** — otterresti ancora il prompt vuoto o "Generating...".

```bash
# ❌ SBAGLIATO
agentctl send agy "Ciao"
agentctl capture agy   # troppo presto — mostra ancora il prompt

# ✅ CORRETTO
agentctl send agy "Ciao"
sleep 8                # aspetta generazione
agentctl capture agy   # mostra la risposta
```

Per messaggi complessi (API reasoning heavy), attendere 10-15 secondi.

## ⚠️ PITFALL: Processi agy orfani (PPID=1)

**Problema:** Se l'utente avvia agy in una finestra iTerm e poi chiude la finestra, agy non muore — diventa orfano con PPID=1. Questi processi possono consumare 30-60% CPU ciascuno per ore senza che nessuno se ne accorga.

**Sintomo:** `ps aux | grep agy` mostra PID con PPID=1. `agentctl list` non li vede (non sono sessioni tmux registrate). Load può salire a 20+.

**Rilevamento automatico:**
- `agentctl health` li mostra come orfani (processi senza tmux wrapper)
- `agent-minder` (cron ogni 3 min) li rileva e investiga automaticamente
- `agentctl spawn agy` li rileva allo spawn e li pulisce dopo 2 min

**Fix manuale:**
```bash
# Trova orfani
ps -o pid,ppid,%cpu,command -p $(pgrep agy) 2>/dev/null | grep '^ *[0-9]\\+ *1 '
# Kill
kill -9 <PID>
```

**Prevenzione:** Spawn sempre via `agentctl spawn` che usa tmux. tmux mantiene il processo vivo anche se la finestra iTerm viene chiusa.

## ⚠️ PITFALL: agy keepalive/heartbeat loop (stuck poll cycle)

**Problema:** agy lasciato in esecuzione in un terminale iTerm (anche con finestra aperta) può cadere in un loop di keepalive: chiamate periodiche a `fetchAvailableModels` + `loadCodeAssist` ogni ~6 minuti. Il processo non è orfano (PPID è zsh vivo, non 1) ma non sta facendo lavoro produttivo — consuma CPU (15-30%) e API quota senza motivo.

**Sintomo:**
- `agentctl health --json` mostra un processo agy con `orphan: true` ma **non** PPID=1
- `ps -o pid,ppid,%cpu,command -p <PID>` mostra PPID=zsh, CPU% >10%
- Il log agy mostra solo: `fetchAvailableModels` → `loadCodeAssist` a intervalli fissi
- Nessuna `streamGenerateContent` recente (richieste utente) — solo heartbeat

**Rilevamento:**
```bash
# 1. Verificare PPID
ps -p <PID> -o pid,ppid,command

# 2. Controllare il log per pattern di loop
tail -20 ~/.gemini/antigravity-cli/log/cli-$(date +%Y%m%d)*.log
# Se mostra solo fetchAvailableModels/loadCodeAssist senza streamGenerateContent → heartbeat loop

# 3. Verificare connessioni attive
lsof -p <PID> 2>/dev/null | grep -E 'IPv4|IPv6.*ESTABLISHED'
# Una sola connessione keepalive senza attivita di stream = loop
```

**Fix:**
```bash
kill -TERM <PID>
# Il processo non sta facendo nulla di utile — kill sicuro.
```

**Quando NON killare:** se il log mostra `streamGenerateContent` recenti (ultimi 5 minuti) con trace diversi, l'agente sta elaborando richieste utente.

**⚠️ ATTENZIONE: agy può riprendersi naturalmente dal pattern heartbeat.** Un periodo di solo `fetchAvailableModels`/`loadCodeAssist` senza `streamGenerateContent` che dura **< 10-15 minuti** è normale idle tra task — il processo tornerà a generare quando riceverà una richiesta. L'uccisione prematura durante questo intervallo interrompe un agente che avrebbe ripreso a lavorare. Caso reale (cron 2026-07-02): agy PID 11528 era in heartbeat pattern da 17:41 a 17:46 (6 minuti, CPU 15%), poi ha ripreso `streamGenerateContent` con nuovi ResponseID alle 17:50+. Killare sarebbe stato un errore.

**Soglia per confermare stuck invece di idle:** solo quando il pattern heartbeat dura **> 15 minuti consecutivi** SENZA alcun `streamGenerateContent`, E CPU% > 10%. Inoltre, se la CPU% scende a ~0% dopo un periodo di heartbeat (anziché rimanere >10%), l'agente è entrato in idle normale — non stuck.

## ⚠️ PITFALL: agy stuck shutdown after "Terminal gone" (db migration hang)

**Problema:** agy può rilevare che il suo terminale di controllo è scomparso e iniziare la sequenza di shutdown, ma rimanere **bloccato sulla migrazione del database SQLite** senza mai uscire. Il processo consuma CPU elevata (22-121%) e non risponde a segnali normali perché il thread principale è in attesa di I/O su database.

**Diverso dal heartbeat loop:** il processo HA deciso di morire (log mostra "Terminal gone, shutting down"), ma non riesce a completare. La CPU indica lavoro attivo di migrazione/rollback, non heartbeat keepalive.

**Sintomo:**
- `ps` mostra agy ancora vivo con CPU >20% dopo che il log indica "shutting down"
- Il log termina con `Waiting for migrations to complete to prevent partial migration state`
- Nessun nuovo log file creato (il processo non riparte — muore nel shutdown)
- PPID chain indica ancora zsh/login (terminale non chiuso, ma agy ha perso il controllo tty per altre ragioni)

**Dettaglio dal caso reale (cron 2026-07-02):**
PID 11528 (agy) ha mostrato:
1. 17:00-18:14 — heartbeat loop (loadCodeAssist ogni 1-2s, CPU 12-53%)
2. 18:15:03 — `Terminal gone, shutting down` nel log
3. 18:15:03 — `CLI program exited, shutting down`
4. 18:15:03 — `Waiting for migrations to complete to prevent partial migration state`
5. Processo ancora vivo a 18:16+, CPU 22-121%, bloccato su migrations
6. `ps` mostrava `S+` state (sleep) ma CPU reale >20% (migration thread spinning)

**Contesto aggiuntivo:** 3 istanze consecutive di quota-monitoring agy (17:50, 18:02, 18:14) hanno fallito con lo stesso pattern zero-work heartbeat prima di arrivare a questo shutdown bloccato. Il workspace temporaneo (`/tmp/agy-quota-eVDmxa`) generava errori `failed to get git info for workspace: reference not found`.

**Fix:**
```bash
# Prova graceful shutdown (di solito non funziona — bloccato su I/O DB)
kill -TERM <PID>
sleep 5
kill -0 <PID> 2>/dev/null && kill -KILL <PID>  # force kill se ancora vivo
```

Il `kill -9` è l'unica via d'uscita affidabile perché il processo è bloccato su I/O database e non processa segnali normali.

**Rilevamento rapido:**
```bash
# 1. Controllare se il log mostra "Waiting for migrations to complete"
tail -5 ~/.gemini/antigravity-cli/log/cli-$(date +%Y%m%d)*.log | grep -c "Waiting for migrations"

# 2. Se il match è >0 e il processo è ancora vivo con CPU >20% → stuck shutdown
ps -p <PID> -o pid,%cpu,etime,command
```

**Vedi anche:** Questo pattern è comune nelle istanze di quota monitoring agy che operano in workspace temporanei (`/tmp/agy-quota-*`). Se vedi 3+ istanze consecutive fallire rapidamente (34s ciascuna) con solo heartbeat, probabilmente la prossima si bloccherà in shutdown. Valuta di killare preventivamente la chain.

## ⚠️ PITFALL: agy trust prompt sul primo spawn in una nuova directory

**Problema:** Quando si spawna agy in una directory mai vista prima, agy mostra un menu TUI "Do you trust this folder?" con opzioni Yes/No navigate via frecce. `agentctl send` non riesce a superarlo perché il menu TUI non risponde a Escape+Enter. La sessione tmux rimane bloccata finché non scade e diventa 🔴 dead.

**Fix:**
```bash
agentctl spawn agy --workdir ~/Software/Progetto
sleep 8                                            # aspetta il prompt trust
tmux send-keys -t <sessione> Enter                 # accetta raw (tmux diretto)
sleep 10                                           # attendi init
agentctl send agy "<prompt>"                       # ora invia il vero messaggio
```

Dopo la prima accettazione, la directory è fiduciata — gli spawn successivi saltano il prompt.
Il fix dettagliato è nel skill `antigravity-cli` (Pitfall #8).

> **Vedi anche:** `references/zombie-cleanup.md` per la gestione di zombie di sistema (processi `<defunct>` da sshd/sessioni di rete).

## ⚠️ PITFALL: Falsi positivi health check su macOS

**Problema:** `agentctl health --json` può segnalare falsi positivi su macOS per due ragioni:

**A) `ps axo comm` mostra full path su macOS** — Per alcuni binari (codex lanciato via node), il campo `comm` mostra il percorso completo (`/usr/local/lib/node_modules/@openai/codex/.../bin/codex`) invece del solo nome (`codex`). Il match esatto `comm != "codex"` falliva — codex veniva sempre dato come DEAD.

**B) `known_pids` non includeva i discendenti dei pane tmux** — Il pane PID tmux è il wrapper `script -q` (es. PID 95179). I veri processi agente sono 2-3 livelli sotto (`script → node → codex`, PID 95181). Senza camminare l'albero dei processi, questi venivano classificati come orfani.

**Fix (applied in agentctl source):**
```python
# A) Normalizza comm via basename
comm_basename = os.path.basename(comm) if "/" in comm else comm
if comm_basename != agent:
    continue

# B) Includi discendenti in known_pids
for pane_pid in pane_pids:
    known_pids.add(pane_pid)
    known_pids.update(get_descendants(pane_pid))
```

`get_descendants()` scansiona `ps axo ppid,pid` in memoria e fa DFS per trovare figli, nipoti, etc.

**Come verificare se è falso positivo:**
```bash
# Verifica che il tmux session esista
TMUX_TMPDIR=/tmp tmux list-sessions

# Per codex: controlla i nodi node sotto il pane tmux
ps axo pid,ppid,comm | grep codex
ps -p <pane_pid> -o pid,ppid,command  # wrapper script
pgrep -P <pane_pid>                    # figli del wrapper
```

> **Vedi anche:** `references/health-false-positives.md` per la cronologia completa di questa analisi (session 2026-06-29).

## ⚠️ PITFALL: Stale PIDs in agent-sessions.json

**Problema:** Il file `~/.hermes/agent-sessions.json` registra il PID dell'agente al momento dello spawn. Se l'agente si riavvia dentro la stessa sessione tmux (es. crash + tmux lo ripesca, o l'utente kill + rispawna nella stessa sessione), il PID registrato diventa stale. agentctl health segnalerà `known_count: 0` anche per agenti vivi.

**Sintomo:** `agentctl list` mostra 🟢 (tmux vivo), ma `agentctl health --json` mostra `known_count: 0` per quell'agente.

**Fix:** Aggiornare manualmente il PID nello stato:
```bash
# Trova il pane PID tmux
TMUX_TMPDIR=/tmp tmux list-panes -t <session> -F "#{pane_pid}"
# Trova i discendenti
ps axo ppid,pid,comm | grep -E 'agy|codex|claude'
# Aggiorna il JSON
# Il PIDs corretto è il pane PID (wrapper script), non il PID dell'agente figlio
```

Oppure kill + rispawn con `agentctl kill <agent> && agentctl spawn <agent>`.

## Health check automatico (post-spawn)

Dopo ogni `spawn`, agentctl esegue automaticamente:

1. **Carico sistema** — `sysctl vm.loadavg`, soglie WARN=10, CRIT=18
2. **Conteggio processi** — `ps axo comm` (eseguibile reale, non cmdline) per evitare falsi positivi da tmux/script wrapper
3. **Orfani** — processi con eseguibile = nome agente ma PID non associato a sessioni tmux registrate

**Nota macOS:** `ps axo comm` mostra il FULL executable path per alcuni binari (es. codex via node mostra `/usr/local/lib/.../codex`, non solo `codex`). agentctl usa `os.path.basename(comm)` per normalizzare prima del match — vedi `find_processes()`.

**Nota known_pids:** agentctl include anche i discendenti dei pane PID tmux (es. `script → node → codex`) via `get_descendants()` — non solo il PID del wrapper. Vedi `references/health-false-positives.md`.

Se anomalie trovate:
- Stampa **BIG WARNING** banner
- Lancia `threading.Thread(daemon=True)` che dopo 120 secondi:
  - Ri-valuta la situazione (potrebbe essere già risolta)
  - Trova tutti i PID orfani via `tmux list-panes -F #{pane_pid}` + `get_descendants()` per identificare quelli noti
  - `kill -TERM` + eventuale `kill -KILL` per i persistenti
  - Stampala solo se effettivamente uccide qualcosa
- Cancellabile via `touch ~/.hermes/agentctl-cancel.flag` o Ctrl+C

**Nota:** l'auto-pulizia non kill mai l'agente appena spawnato — solo duplicati e orfani.

## agentctl health [--json]

Esegue un health check completo su TUTTI gli agenti registrati in CLI_MAP (agy, claude, codex, claude-or):

- Per ogni agente: conta processi, classifica (tmux/orfano), identifica dead
- Costruisce `known_pids` da tutte le sessioni tmux vive nello stato, **inclusi i discendenti** dei pane PID (via `get_descendants()` — walk `ps axo ppid,pid`)
- Rileva e **filtra automaticamente** i processi delle sessioni tmux `ai_cli_quotas_*` (transienti del quota monitoring su port 9899) — non compaiono come orfani né innescano DUPLICATES. Implementato in `check_all_agents()`; dettagli in `references/quota-monitoring-transients.md`
- Processi con PID non in known_pids = orfani
- Processi zero ma presenti in stato = DEAD

## Manual Anomaly Investigation Protocol

Quando un cron job (o una sessione manuale) ottiene `agentctl health --json` con `anomaly_count > 0`, investigare ogni anomalia con questa sequenza. L'obiettivo è classificare ogni processo come: **stuck loop** / **legitimate work** / **idle leftover** / **false positive** / **expected infra**.

### Step 1: Parse and list all suspect PIDs

Dal JSON, raccogliere `agents[<name>].processes[].pid` per tutti gli agenti con anomalie o orfani. Ogni processo ha già una classificazione `orphan: true/false` e `in_tmux: true/false`.

### Step 2: Uptime + system context

```bash
uptime                                    # load 1m, 5m, 15m
```

Se load è sopra WARN (10) o CRIT (18), prioritizzare i processi a più alto consumo CPU.

### Step 3: Profiling per ogni PID sospetto

```bash
# Stato base: CPU, MEM, RSS, tty, created-at
ps -o pid,ppid,%cpu,%mem,rss,state,lstart,command -p <PID>

# PPID ancestry (capire chi ha spawnato il processo)
ps -p <PPID> -o pid,ppid,command          # genitore immediato
# Se PPID è un numero, risalire fino a init(1) o tmux o zsh

# Working directory (cosa stava facendo?)
lsof -p <PID> 2>/dev/null | grep cwd

# Connessioni di rete (sta chiamando API?)
lsof -p <PID> 2>/dev/null | grep -E 'IPv4|IPv6'

# File descriptors aperti (log, lock, risorse)
lsof -p <PID> 2>/dev/null | head -20
```

### Step 4: Classificazione per PPID

| PPID è... | Classificazione | Esempio |
|-----------|----------------|---------|
| `1` (init) | **Vero orfano** — terminale chiuso, processo abbandonato | agy con PPID=1 |
| `tmux` | **Tmux-managed** — ma non necessariamente agentctl-registrato | quota-monitoring session |
| `zsh` o `bash` | **Terminale utente aperto** — processo lanciato in iTerm | codex/agy in tty s000 |
| `node` | **Codex/Claude CLI wrapper** — processo figlio di codex/node | codex CLI session |
| `Antigravity IDE Helper` | **IDE extension — false positive** | codex app-server da VS Code/Antigravity |
| `sshd` o login | **SSH session attiva** — processo remoto, non locale | — |

### Step 5: Determinare se è stuck o sta lavorando

**Segnali di lavoro legittimo:**
- Connessione HTTPS attiva verso API endpoint + log/trace in crescita regolare
- PID con `state=R+` e basso tempo CPU cumulativo (`etime >> cputime`) — sta scrivendo output
- File di log con timestamp recenti e contenuti variabili (non ripetitivi)
- **Session file growth (Claude specific):** controlla la dimensione del file `.jsonl` attivo in `~/.claude/projects/<progetto>/<uuid>.jsonl`. Se cresce tra due campionamenti a distanza di 1-2 minuti, l'agente sta facendo lavoro reale (API call + scrittura risultati). Un file fermo = idle o loop keepalive. Esempio concreto da cron: 354KB → 356KB in 60 secondi = lavoro attivo confermato.
- **agy `HandleUserInput` check:** Cerca nel log agy la stringa `HandleUserInput called with text:`. Se presente con un timestamp recente e un messaggio utente riconoscibile, l'agente **sta eseguendo un task richiesto dall'utente**. La presenza di questo entry è il SEGNALE DEFINITIVO per agy — override di ogni altra metrica (CPU alta, rapidi streamGenerateContent, stato S+, decine di file aperti). Esempio reale (2026-07-02): PID 11528 aveva 46% CPU, 244 file aperti, 84 streamGenerateContent/min — ma il log mostrava `HandleUserInput called with text: "reviewer found blocking issues in T2. Please read and fix"` alle 18:10:14, confermando lavoro legittimo. Vedi `references/legitimate-work-vs-loop-investigation.md` per la traccia completa.
- **Git commit check:** Nella working directory dell'agente (da `lsof -p <PID> | grep cwd`), esegui `git log --oneline --since="<N> hours ago"` per vedere se l'agente ha committato modifiche recenti. Commits recenti con messaggi pertinenti = lavoro produttivo. Se non ci sono modifiche ai file del progetto (`find /path/to/project -newer /path/to/log -type f` non mostra sorgenti modificati), ma l'agente ha CPU alta, potrebbe essere in un loop.
- **Distinzione streamGenerateContent vs heartbeat loop (agy):** `streamGenerateContent` con ResponseID UNICO per chiamata = chiamata API produttiva (generazione risposta). `loadCodeAssist` / `fetchAvailableModels` senza `streamGenerateContent` intervallato = heartbeat/keepalive. Se vedi 10+ `streamGenerateContent`/min con ResponseID tutti diversi, l'agente sta PROCESSANDO richieste — non è in idle anche se CPU è solo 10-15% e stato `S+`. Se vedi solo `loadCodeAssist`/`fetchAvailableModels` a intervalli regolari senza `streamGenerateContent`, è heartbeat loop.

> **⚠️ La crescita del file `.jsonl` è il SEGNALE DEFINITIVO per Claude.** Connessioni HTTPS attive da sole NON indicano lavoro reale — l'agente può mantenere connessioni keepalive anche quando è idle (es. PID 68188 in questa sessione: 3 connessioni stabili ma file fermo 6+ minuti = idle). Se il file non cresce in 60 secondi, classifica come idle o stuck indipendentemente dal numero di connessioni attive. La lista di connessioni `lsof` va usata solo per confermare che l'agente SA parlare con l'API, non per determinare se STA lavorando.

> **Vedi anche:** `references/legitimate-work-vs-loop-investigation.md` per una traccia investigativa completa con decision tree e comandi esatti usati per distinguere lavoro legittimo da loop — include la cronologia del PID 11528 (agy) e le metriche per ogni step della classificazione.

**Segnali di stuck/heartbeat loop:**
- Richieste API ripetute alla stessa identica endpoint a intervalli fissi (es. ogni 6 min: `fetchAvailableModels` → `loadCodeAssist`)
- PID con `state=S+` ma CPU costante (>10% per ore)
- Log file che mostra solo heartbeat/keepalive pattern, nessuna richiesta utente
- Tempo CPU cumulativo molto basso rispetto a `etime` ma CPU% stabile (>5% per ore)
- `lsof` mostra solo connessioni keepalive senza attività di scrittura su file utente

**Segnali di idle:**
- CPU% < 2% (ma attenzione: Claude può essere idle con CPU 2-5% e connessioni keepalive — verificare sempre il session file growth come discrimante definitivo. Transient CPU spikes fino a 10% sono possibili su claude — se il .jsonl non cresce, è idle anche a 10% CPU.)
- Nessuna connessione di rete attiva, OPPURE connessioni HTTPS stabilite ma file di sessione fermo da >60s (Claude specific — le connessioni keepalive persistono anche quando l'agente non sta lavorando)
- **Codex con 0 connessioni ESTABLISHED:** codex ha bisogno di rete per funzionare. Se `lsof -p <PID> | grep -c ESTABLISHED` = 0, il processo è **stuck/frozen**, non solo idle. Combinato con zero crescita state DB = definitivamente hung.
- Stato `S+` (sleep), solo file di lock/log aperti
- Lancato ore fa, nessuna attività recente nei log o nei file di sessione

### Step 6: Verifica log per processi sospetti

| Agente | Percorso log / session data |
|--------|---------------------------|
| agy | `~/.gemini/antigravity-cli/log/cli-YYYYMMDD_HHMMSS.log` |
| codex | `~/.codex/logs_2.sqlite` (SQLite DB, controllare dimensione) |
| claude | Sessioni `.jsonl` in `~/.claude/projects/<progetto>/<uuid>.jsonl` (nessun log testuale) |

```bash
# agy: controllare ultime N righe
tail -20 ~/.gemini/antigravity-cli/log/cli-*.log

# codex: dimensione log DB (1.2GB+ = session massiccia o runaway)
ls -lh ~/.codex/logs_2.sqlite

# codex: state DB last-modified — miglior indicatore di attività live
# state_5.sqlite cambia ad ogni azione del CLI (lettura file, API call, scrittura output).
# Usare `stat -f%z` per growth check su 60s, come per i file .jsonl di Claude.
# Se cresce, l'agente sta facendo lavoro reale. Se fermo, è idle o stuck.
ls -l ~/.codex/state_5.sqlite

# codex: TUI log — linea del tempo delle connessioni websocket
# Contiene timestamp di apertura/chiusura connessioni, errori di rete,
# e tentativi di inizializzazione. Utile per confermare se codex
# ha mai effettivamente stabilito una connessione API (vs. partito
# e subito caduto). L'ultimo log di successo è il timestamp
# dell'ultima attività reale.
tail -5 ~/.codex/log/codex-tui.log

# codex: controllare connessioni attive
lsof -p <PID> 2>/dev/null | grep -E 'IPv4|IPv6.*ESTABLISHED'

# claude: trovare la sessione attiva per un progetto specifico
ls -lt ~/.claude/projects/*/ | head -5
ls -la ~/.claude/projects/<progetto>/   # elenca session .jsonl
ls -lh ~/.claude/projects/<progetto>/*.jsonl  # dimensione file sessione
```

**Nota su Claude:** Claude non produce log di testo come agy. Scrive sessioni `.jsonl` (una riga JSON per turno) nelle cartelle progetto sotto `~/.claude/projects/`. La dimensione del `.jsonl` più recente è un proxy diretto del volume di lavoro. Un file che cresce = lavoro reale. Nessuna crescita + CPU >10% = possibile heartbeat loop (antigravity-cli pattern).

Per verificare se un processo Claude orfano sta facendo lavoro:
```bash
# 1. Identificare il progetto attivo dal cwd
lsof -p <PID> 2>/dev/null | grep cwd

# 2. Trovare la sessione .jsonl più recente per quel progetto
PROJECT_SLUG="-Users-fausto-Software-<nomeprogetto>"
ls -lt ~/.claude/projects/$PROJECT_SLUG/*.jsonl 2>/dev/null | head -3

# 3. Campionare la dimensione a distanza di 60 secondi
SIZE1=$(stat -f%z ~/.claude/projects/$PROJECT_SLUG/*.jsonl 2>/dev/null | sort -rn | head -1)
sleep 60
SIZE2=$(stat -f%z ~/.claude/projects/$PROJECT_SLUG/*.jsonl 2>/dev/null | sort -rn | head -1)
echo "Delta: $((SIZE2 - SIZE1)) bytes"  # >0 = lavoro attivo
```

**Cross-reference: check anche l'agente noto (tmux-registrato)**
Dopo aver valutato l'orfano, controlla ANCHE il file di sessione dell'agente noto
nello stesso intervallo. Se l'agente noto scrive attivamente mentre l'orfano è fermo,
l'orfano è confermato idle. Se entrambi sono fermi, nessuno dei due sta ricevendo
richieste — verifica quale dei due dovrebbe stare lavorando.

```bash
# Dopo il campionamento dell'orfano, controlla anche l'agente noto
# (usa `agentctl list` per vedere il suo CWD e PID della sessione)
KNOWN_PID=$(tmux list-panes -t agent-claude-* -F "#{pane_pid}" 2>/dev/null | head -1)
KNOWN_PROJECT=$(lsof -p $KNOWN_PID 2>/dev/null | grep cwd | awk '{print $NF}')
echo "Known agent project: $KNOWN_PROJECT"

# Trova la sessione .jsonl per quel progetto
KNOWN_SLUG=$(echo "$KNOWN_PROJECT" | tr '/' '-' | sed 's/^/-\//' | sed 's/\//-/g')
ls -lt ~/.claude/projects/*"$KNOWN_SLUG"*/*.jsonl 2>/dev/null | head -1

# Campiona KNOWN_KNOWN_SIZE=$(stat -f%z ~/.claude/projects/*"$KNOWN_SLUG"*/*.jsonl 2>/dev/null | sort -rn | head -1)
sleep 60
KNOWN_SIZE2=$(stat -f%z ~/.claude/projects/*"$KNOWN_SLUG"*/*.jsonl 2>/dev/null | sort -rn | head -1)
echo "Known agent delta: $((KNOWN_SIZE2 - KNOWN_SIZE)) bytes"
```

### Step 7: Classifica finale e azione

| Categoria | Azione | Urgenza |
|-----------|--------|---------|
| **Stuck/heartbeat loop** | `kill -TERM <PID>` | 🟡 Medium — spreco CPU/API |
| **Legitimate work** (es. long task) | Segnalare durata, non uccidere | 🟢 Low — monitorare |
| **Idle leftover (true orphan)** | `kill -TERM <PID>` — nessuno lo userà più | 🟢 Low |
| **Idle leftover in live terminal** (PPID=zsh/bash su ttysNNN aperto — "registry orphan") | Preferire **segnalazione** a kill immediato. Il terminale è ancora aperto, l'utente potrebbe tornarci. Solo killare se CPU > 5% (possibile heartbeat loop mascherato da idle) oppure se il processo è fermo da > 2h con session file invariato. | 🟢 Low — non urgente |
| **False positive** (IDE/extension) | Ignorare, segnalare nel report | ✅ None |
| **Expected infra** (quota monitor) | Ignorare | ✅ None |
| **Load > CRIT con multipli stuck** | `kill -9 <PID>` immediato | 🔴 Urgent |

### Step 8: Report strutturato

Per ogni anomalia produrre:
1. **Cosa** — PID, agente, CPU/MEM, durata, PPID, tty
2. **Classificazione** — stuck / idle / false positive / expected
3. **Evidenza** — comando e output che supporta la classificazione
4. **Rischio** — 🟢/🟡/🔴 con motivazione
5. **Azione raccomandata** — kill / ignore / investigate further

Non includere falsi positivi noti nel conteggio anomalie del report finale — aggiungerli in una sezione a parte "False positives (safe to ignore)".

**Output JSON (--json):**
```json
{
  "load": {"1m": 2.4, "5m": 2.7, "15m": 3.8},
  "load_warn_threshold": 10,
  "load_crit_threshold": 18,
  "agents": {
    "agy": {
      "count": 0,
      "processes": [],
      "orphan_count": 0,
      "known_count": 0,
      "anomalies": []
    }
  },
  "anomaly_count": 0,
  "anomalies": [],
  "timestamp": "2026-06-28T16:44:59+00:00"
}
```

**Anomalie possibili:**
- `DUPLICATES: N processi in esecuzione (M orfani, K registrati)` — più processi dello stesso agente del previsto
- `DEAD: registrato in stato ma nessun processo vivo` — tmux session morta ma stato non ripulito
- `LOAD_WARN/LOAD_CRIT: X.X` — carico sistema sopra soglia

## agent-minder (cron job compagno)

Il cron **agent-minder** (ogni 3 min, skill agentctl) esegue `agentctl health --json` e investiga le anomalie automaticamente:

- **Silenzioso se OK** — nessun output = nessuna notifica Telegram
- **Se anomalie**: analizza ogni anomalia (PIDs, tmux/orfano, PPID), controlla `uptime` e `ps aux`, produce report strutturato su Telegram con findings e azioni consigliate
- **Skills richieste nel cron**: `[agentctl]`
- **Modello**: di default (usa il provider/config della cron)

**Cosa controlla:** agy, claude, codex, claude-or + carico sistema. Ogni 3 minuti. Full auto.

**Rileva:**
- Duplicati (più processi dello stesso agente del previsto)
- Orfani (PPID=1, processi senza tmux wrapper)
- Dead entries (agente registrato in stato ma nessun processo vivo)
- Load anomalo (WARN ≥10, CRIT ≥18)

## wrapper.sh (solo per uso interattivo manuale)

```bash
~/Software/scripts-ai/agent-bus/wrapper.sh [--name <session>] <agent_name> <cli...>
```

Lancia in tmux con `script -q` per logging. Senza pollers — è solo un thin wrapper.

## Stato file (JSON)

`~/.hermes/agent-sessions.json`:
```json
{
  "agy": {
    "session": "agent-agy-12345",
    "type": "agy",
    "pid": 12345,
    "spawned_at": 1234567890.123,
    "model": "",
    "log": "/Users/fausto/.hermes/agent-logs/agy/20260628-123456.log",
    "command": "agy",
    "workdir": "/Users/fausto/Software/MyProject"
  }
}
```

Il campo `workdir` viene popolato quando si usa `agentctl spawn --workdir`. Se assente, l'agente parte dalla home directory. Viene mostrato anche in `agentctl list` (colonna DIR).

**Il PID registrato è il pane PID tmux** (lo script `-q` wrapper), non il PID dell'agente figlio. Se l'agente si riavvia dentro la stessa sessione (crash/respawn), il PID registrato diventa stale. Fix: kill + rispawn, o aggiorna manualmente il JSON col pane PID corrente da `tmux list-panes`.

## Multi-Agent Orchestration Workflow

agentctl supports a multi-agent cycle where Hermes coordinates work between persistent agents — typically a planner-reviewer and an implementer — with each agent holding a defined role. This is distinct from `delegate_task` subagents (ephemeral, one-shot): agentctl agents are persistent tmux sessions that accumulate context across turns.

### The 3-Agent Cycle (Plan → Review Gate 1 → Implement → Review Gate 2 → Merge)

Canonical pattern for projects with role-primed agents (e.g. AgentTalk's primer protocol). The key discipline is TWO reviewer gates — not one review pass after implementation.

**Before starting ANY action in the cycle, read the project's workflow document first** (`AGENT.md` / `AGENTS.md` / `CLAUDE.md` — the project's canonical instructions file — and the workflow doc under `design/` if one exists). Do not skip this even if you worked on the same project yesterday. The workflow may have changed, or your previous read may have missed something. Fausto's directive (2026-07-01): *"Always, always check workflow directions before taking an action of any sort."* Killing agents without checking the session-close protocol is the concrete failure this rule prevents; implementing a behavioural change without checking the change-gate rules is another. **When in doubt, re-read the workflow doc.**

```
  Hermes (SM/orchestrator)
    ├── agentctl send codex "Plan: <task>"           # STEP 1: planner produces breakdown
    ├── agentctl capture codex                        # read breakdown artifact
    ├── [SM commits breakdown + ledger to master]
    ├── agentctl send codex "Review gate 1: ..."     # STEP 2: reviewer approves plan
    ├── agentctl capture codex                        # read verdict (VERIFIED/REFUTED)
    ├── [SM commits gate 1 verdict to master]
    ├── agentctl send agy "Implement: <task>"         # STEP 3: implementer builds
    ├── agentctl capture agy                          # read claims + gate results
    ├── [implementer commits branch + pushes]
    ├── agentctl send codex "Review gate 2: ..."     # STEP 4: reviewer verifies impl
    ├── agentctl capture codex                        # read verdict (VERIFIED/REFUTED)
    ├── [SM commits gate 2 verdict to ledger]
    └── [human authorizes merge → SM merges to master, cleans up branch]
```

**Workflow rules:**
1. **Baton format: point to artifacts, don't restate.** The baton from SM to each role should name the task, the artifact(s) containing the spec (task breakdown, plan, ledger), and the one or two non-obvious facts the reader can't derive from those artifacts. Do NOT copy-paste the spec into the message — that creates drift and invites the receiver to follow your summary instead of the source of truth. A tight baton: "Plan: `<task>`. Read `design/<task-breakdown>.md`. Scope is `team-coordinator.ts:1910-1963` and `:1981-2064`. Do NOT touch ejectPlanner semantics or wire contracts."
2. **Two-gate discipline, not one.** Gate 1 (reviewer approves the plan/breakdown before any code is written) and Gate 2 (reviewer verifies the implementation by running it, before merge). Never skip gate 1 — the plan must be approved before the implementer touches code. The same reviewer owns both gates on the same task.
3. **SM commits artifacts between steps.** The task breakdown + ledger updates are committed to the mainline between planner output and implementer start, and again between implementer completion and reviewer gate 2. This keeps the mainline the durable record and prevents uncommitted drift between roles.
4. **Implementer creates the branch, commits, pushes.** The implementer works on a named branch (`<epic>-t<N>-<slug>`), commits its work, and pushes. The reviewer then switches to the branch to verify.
5. **Reviewer verifies by RUNNING, not by reading the diff.** Gate 2 evidence must include the actual command output: test results, tsc, diff --stat, worktree/pollution checks. A "looks right" verdict is not VERIFIED.
6. **Merge is the closure step, authorized by the human.** Gate 2 produces a VERIFIED verdict. The human (PO) explicitly authorizes the merge. The SM then merges (--no-ff), pushes, updates the ledger to mark DONE, and deletes the remote+local branch. The human is the gate; the SM executes.
7. **Spawn both agents upfront** before starting the cycle: `agentctl spawn codex --workdir <path>` and `agentctl spawn agy --workdir <path>`. Keep agents alive across the entire cycle — don't kill and re-spawn between turns.
8. **Never modify the same file from two agents simultaneously.** If the planner and implementer both touch team-coordinator.ts, run them serially (which the gate discipline enforces naturally).
9. **Each send needs a subsequent wait + capture** — see timing notes below. For complex implementation tasks, initial wait of 60-120s before the first capture, then re-poll every 60s if still working.

**Timing per step:**
| Step | Wait before first capture | Typical duration | Notes |
|------|--------------------------|------------------|-------|
| Simple query / confirmation | 5-10s | 3-5s API | One-shot question |
| File read + analysis | 15-25s | 10-20s API | Planner reading existing code |
| Code search + investigation | 20-40s | 15-30s API | Finding relevant surfaces |
| Full task breakdown (planner) | 90-120s | 2-5 min | Producing a 200-300 line document with DoD rows |
| Reviewer gate 1 (verify plan) | 30-60s | 1-3 min | Read breakdown, verify line ranges, check ground truth |
| Full implementation + tests (implementer) | 60-90s | 3-8 min | Multiple read-edit-test cycles per scope surfaces |
| Reviewer gate 2 (verify by running) | 60-120s | 2-5 min | Switch branch, run tests, check tsc + diff + pollution |

**Wait pattern:** `agentctl send <agent> "<msg>"` then `sleep <N> && agentctl capture <agent>`. If capture still shows "Working..." or a continuation prompt, wait another 30-60s and capture again. For long implementer runs, re-poll every 60s until the output shows a completion summary ("all tests passing", "task complete", "ready for review") instead of activity lines.

**Copilot first-message protocol:** The first message to any agent MUST carry the copilot advisory:
```
agentctl send <agent> "⚠️ I'm copiloting — Fausto is the real gate until explicit handoff.\n\n[Human] <task>"
```

### Autonomous Pipeline Mode (PO directive, 2026-07-02)

Once the initial task assignment and role primers are set, run the cycle autonomously without PO consultation for routine handoffs. The SM bats between agents on its own initiative:

- Implementer done → baton reviewer — automatic.
- Reviewer done VERIFIED → baton implementer for next task, or ask PO for merge.
- Reviewer done REFUTED/PARTIAL → baton implementer with fix list, automatic.
- Architect proposes direction → relay to PO for decision.
- Only consult the PO when: merge gate, deviation from normal flow, task finished needing PO gate to merge, or blocker/halt decision required.

### Spike Cycle (Design Spike Variant)

For small tech-debt or investigation tasks that don't warrant a full epic/milestone (see `spike` skill for the code-prototype variant):

1. Planner-reviewer creates a spike document: `design/<topic>-spike.md` with scope, non-goals, questions, options, and DoD table
2. Implementer executes read-only: inspects files, answers questions, documents findings, recommendation
3. Reviewer verifies: checks file/line accuracy, semantic classification, no production code changes, fills DoD verdict column
4. Outcomes: **approve** (spike complete, decision documented) or **request changes**

### Agent Lifecycle in Multi-Agent Sessions

- Keep agents alive across the entire cycle — don't kill and re-spawn between turns
- `agentctl list` shows both agents with 🟢/🔴 status
- If an agent becomes unresponsive (🔴 dead), re-spawn with `agentctl spawn <type> --workdir <path>`

### Session Close Protocol — MANDATORY before killing

**Killing agents without this step is a process violation.** Each agent owns its own lessons file (`design/lessons/<agent>-lessons.md`) and private key store (`~/.codex/...`, `~/.claude/...`, `~/.config/AgentTalk_Gemini/...`) — these cannot be written after the tmux session is gone.

**Sequence (do this BEFORE `agentctl kill`):**

1. **Send each active agent a session-close baton:**
   ```
   agentctl send <agent> "Session close — write your lessons to design/lessons/<agent>-lessons.md, update your private key store (consumed list), and confirm when done. Then I'll terminate the session."
   ```

2. **Wait and capture each agent's confirmation:**
   ```
   sleep 15
   agentctl capture <agent>
   ```
   Look for explicit confirmation ("done", "lessons written", "key store updated"). Re-poll if still working.

3. **SM writes own lessons + updates primers:**
   - Append entry to `design/lessons/hermes-lessons.md` (session summary, what worked, what didn't)
   - Set all role-primers to `key: none` and update bodies to reflect current state
   - Commit and push all changes to master

4. **Kill only after all agents confirm:**
   ```
   agentctl kill codex && agentctl kill claude && agentctl kill agy
   ```

5. **Final push** of all session-close commits (primers, lessons, ledger updates).

**Why this matters:** Lessons files are per-agent self-authored — you cannot write them for another agent. If you kill the session before the agent writes, that agent's insights are lost. Private key stores (`consumed[]`) are how agents track which primers they've already consumed — without closing, a cold restart re-reads the same primer as fresh, triggering a false cold-start stop.

**Real failure (2026-07-01):** I terminated all three agents without session close. Claude's and Codex's lessons went unwritten, their private key stores went un-updated, and the next cold start will consume primers that were already consumed in this session. The data is permanently lost.

> **See also:** `references/three-agent-two-gate-example.md` — a full end-to-end trace of the
> plan → reviewer gate 1 → implement → reviewer gate 2 → merge cycle, with exact baton shapes,
> evidence commands, and timing.

## Riferimenti

- `references/zombie-cleanup.md` — Processi `<defunct>` da sshd/sessioni di rete
- `references/health-json-schema.md` — Schema dettagliato output JSON health check
- `references/health-false-positives.md` — Falsi positivi macOS: `ps axo comm` full path, discendenti tmux mancanti
- `references/common-false-positives.md` — Pattern ricorrenti di falsi positivi: VS Code extension codex, transient orphans da tmux server orfano, client tmux attach, manual iTerm launch
- `references/quota-monitoring-transients.md` — Processi transitori (codex, agy, claude) spawnati dal quota monitoring locale in sessioni `ai_cli_quotas_*`. Ora **filtrati automaticamente** da `agentctl health` (2026-07-04)
- `references/legitimate-work-vs-loop-investigation.md` — Traccia investigativa completa 2026-07-02: come distinguere lavoro legittimo agy (HandleUserInput, streamGenerateContent unico) da heartbeat loop o stuck shutdown. Incluse decision tree, comandi esatti per ogni step, e cronologia PID 11528.
