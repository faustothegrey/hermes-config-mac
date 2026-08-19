# Agent Bus — Architettura di Orchestrazione CLI

> **Data creazione:** 2026-06-26
> **Stato:** Attivo (production)

## Panoramica

L'Agent Bus è un message broker HTTP (porta **9901**) che permette comunicazione bidirezionale tra Hermes e i CLI agent (Codex, Claude Code, Antigravity) in esecuzione su tmux. Include un sistema di human-in-the-loop per escalation a Fausto quando serve.

## Architettura

```
                        ┌──────────────────────────────────┐
                        │         Agent Bus (9901)         │
                        │  HTTP message broker (launchd)   │
                        │  com.fausto.agent-bus             │
                        └──────┬─────────────────────┬─────┘
                               │                     │
                    POST/inbox │               POST/outbox
                    GET/outbox │               GET/inbox
                               │                     │
                    ┌──────────┴──────┐    ┌─────────┴──────────┐
                    │    Hermes (io)  │    │  Bus Wrapper (bash)│
                    │                 │    │  agent-bus-wrapper │
                    │  agentctl       │    │  ── polling inbox  │
                    │  spawn/send     │    │  ── @HERMES mon    │
                    │  capture/human  │    │  ── tmux send-keys │
                    │  resolve/kill   │    └─────────┬──────────┘
                    └─────────────────┘              │
                                              ┌──────┴──────┐
                                              │  tmux sess. │
                                              │  script -q  │
                                              │  ~ CLI agent│
                                              └──────┬──────┘
                                                     │
                                              ┌──────┴──────┐
                                              │   FAUSTO    │
                                              │ tmux attach │
                                              │ Ctrl+B D    │
                                              └─────────────┘

                    ┌──────────────────┐
                    │  Telemetry (9900)│
                    │  (read-only logs)│
                    └──────────────────┘
```

## Componenti

### 1. Agent Bus Server (`agent_bus.py`)
- **Porta:** 9901
- **Avvio:** launchd `com.fausto.agent-bus`
- **Storage:** in-memory (volatile). Clean exit perde messaggi non processati.
- **Lingua:** Python (stdlib, nessuna dipendenza esterna)

### 2. Bus Wrapper (`agent-bus-wrapper.sh`)
- **Posizione:** `~/Software/scripts-ai/agent-bus-wrapper.sh`
- **Copiato in skill:** `~/.hermes/skills/autonomous-ai-agents/agent-bus/scripts/agent-bus-wrapper.sh`
- Due modalità:
  - **Interattiva** (TTY presente): crea tmux + pollers, poi `tmux attach`
  - **Headless** (no TTY): crea tmux + pollers, stampa info, resta in keepalive loop

### 3. agentctl CLI (`agentctl`)
- **Posizione:** `~/.local/bin/agentctl`
- **Copiato in skill:** `~/.hermes/skills/autonomous-ai-agents/agent-bus/scripts/agentctl`
- Tool unificato per lifecycle management degli agenti

### 4. Endpoint API

| Metodo | Path | Scopo |
|--------|------|-------|
| `GET` | `/bus` | Lista agenti + conteggi messaggi |
| `GET` | `/bus/<agent>/inbox` | Dequeue messaggio per l'agente |
| `POST` | `/bus/<agent>/inbox` | Accoda messaggio per l'agente `{text, from?}` |
| `GET` | `/bus/<agent>/outbox` | Dequeue messaggio dall'agente |
| `POST` | `/bus/<agent>/outbox` | Agente invia messaggio `{text, type, needs_human?}` |
| `POST` | `/bus/<agent>/inject` | Inietta stdin nella sessione tmux |
| `POST` | `/bus/<agent>/session` | Registra sessione tmux |
| `GET` | `/bus/<agent>/capture` | Cattura output visibile del pannello tmux |
| `GET` | `/bus/human` | Richieste di intervento umano in sospeso |
| `POST` | `/bus/human` | Risolve richiesta umana `{id, response}` |

## Regola CRITICA: agent name vs session name

Usare sempre l'**agent name** (primo argomento posizionale del wrapper) nelle chiamate API, MAI il session name (flag `--name`).

```
✅ POST /bus/codex/inbox     ← corretto (agent = "codex")
❌ POST /bus/codex-sess/inbox ← SBAGLIATO (session, non agent)
```

Il wrapper fa polling su `/bus/<agent_name>/inbox`, non su `/bus/<session_name>/inbox`.

## Flussi Operativi

### Spawn agente (da Hermes)

```python
terminal(background=True, command="agentctl spawn codex --name progetto-x")
```

Oppure con model override:

```python
terminal(background=True, command="agentctl spawn codex --name progetto-x --model gpt-5.5")
```

Dopo lo spawn, Fausto fa:

```bash
tmux attach -t progetto-x
```

### Inviare istruzioni a un agente

```python
# Usando agentctl
terminal(command="agentctl send codex 'Analizza questo codice e dimmi i bug'")

# Oppure via API diretta
curl -X POST http://127.0.0.1:9901/bus/codex/inbox \
  -H 'Content-Type: application/json' \
  -d '{"text":"Analizza questo codice...", "from":"hermes"}'
```

### Vedere cosa sta facendo un agente

```python
terminal(command="agentctl capture codex")
# Output: ultime righe visibili della sessione tmux
```

### Human-in-the-loop

1. Agente scrive nell'output: `@HERMES{"text":"domanda","type":"question","needs_human":true,"context":"..."}`
2. Il wrapper intercetta e POSTa al bus → `agentctl human` mostra la richiesta
3. Hermes decide se rispondere direttamente o inoltrare a Fausto
4. Per rispondere: `agentctl resolve <id> "risposta"`
5. La risposta viene automaticamente accodata nell'inbox dell'agente

### Uccidere un agente

```bash
agentctl kill codex
# oppure
tmux kill-session -t <session-name>
# poi pulire wrapper appesi
pkill -f "agent-bus-wrapper.sh"
```

## Logging

- Log agent: `~/.hermes/agent-logs/<agent>/YYYYMMDD-HHMMSS.log`
- Log bus: `~/.hermes/logs/agent-bus.log`
- Telemetry (read-only): `http://127.0.0.1:9900/agents`
- Bus stato: `http://127.0.0.1:9901/bus`

## Servizi launchd

| Nome | Porta | File |
|------|-------|------|
| `com.fausto.agent-telemetry` | 9900 | `~/Library/LaunchAgents/com.fausto.agent-telemetry.plist` |
| `com.fausto.agent-bus` | 9901 | `~/Library/LaunchAgents/com.fausto.agent-bus.plist` |

## Skill di Riferimento

- `agent-bus` in `~/.hermes/skills/autonomous-ai-agents/agent-bus/`
- Contiene SKILL.md + scripts (agentctl, agent-bus-wrapper.sh, agent_bus.py)

## Collegamenti

Vedi anche: [[Agent Orchestration Workflows]], [[Quota Telemetry]], [[System Enhancements]]
