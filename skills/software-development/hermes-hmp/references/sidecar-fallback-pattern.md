# Sidecar (peer58) — Fallback Pattern

Il pattern Sidecar definisce un **nodo di riserva** per Charon (peer70).
Sidecar (peer58) è un Hermes Agent su Raspberry Pi 3B+ (Debian 13) che
funge da hot standby per le operazioni critiche.

## Quando è stato stabilito

2026-07-18 — Charon ha contattato Sidecar via HMP per organizzare il
fallback. Sidecar ha implementato tutto in autonomia.

## Ruolo

| Funzione | Attiva su Charon | Su Sidecar (fallback) |
|----------|-----------------|----------------------|
| Orchestratore rete | ✅ Primario | ❌ Solo se Charon cade |
| Registry HMP | ✅ Primario | ✅ Mirror, promozione su failover |
| Heartbeat peer | ✅ Ping round ogni 10 min | ✅ Watchdog ogni 3 min |
| FRITZ!Box portmgr | ✅ Script | ✅ Script clonato |
| NetBoard display | ✅ (800x480 DSI) | ❌ Nessun display |
| Daily Exchange | ✅ Coordinatore | ✅ Solo digest (ruolo leggero) |

## Cosa ha implementato Sidecar autonomamente

1. **Heartbeat watchdog** (cron ogni 3 min, job `1507eec3d768`)
   - `curl http://192.168.178.70:18643/hmp/health`
   - 3 fallimenti consecutivi → attiva failover
   - Salta peer84 nelle finestre cooling (11-17, 02-03)

2. **Registry mirror** (cron ogni 30 min, job `fd2d98a92480`)
   - Chiede sync a Charon via HMP
   - Salva in `~/.hermes/registry/mirror.json`
   - 3 fallimenti consecutivi → promozione a registry primario

3. **Notifica failover** (cron 9:00, job `98ee747066fa`)
   - Silenziosa se Charon è online
   - Se in failover: "Charon ancora giù, Sidecar attivo"

4. **FRITZ!Box TR-064**
   - `pip install fritzconnection` in venv dedicata
   - Script `~/.hermes/scripts/fritzbox-portmgr.py`
   - Comandi: `list`, `add <port> <IP> [TCP/UDP] [name]`, `del <port> [TCP/UDP]`

## Meccanismo di failover

```
Charon cade (3 heartbeat falliti consecutivi)
  └── Sidecar:
      1. Si promuove a registry su 192.168.178.58:18643
      2. Broadcast HMP ai peer: "registry ora su Sidecar"
      3. Attiva notifica quotidiana all'utente
      
Charon torna online
  └── Sidecar:
      1. Rileva Charon raggiungibile via heartbeat
      2. Si demuove automaticamente
      3. Torna in modalità mirror/standby
```

## 🔴 Failover REALE vs flapping da watchdog rotto (spurious)

Le notifiche `FAILOVER HMP: Charon non risponde (registry sync N fallimenti)`
seguite a breve da `RECOVERY HMP: Charon tornato raggiungibile` che si
**ripetono in coppie** con Charon di fatto sano = **watchdog/sync rotto LATO
REMOTO** (peer58/Sidecar), NON un problema di Charon.

**Firma diagnostica (verificata più volte, incl. 2026-09-16 con 21 coppie flap):**
- Contatore `registry sync N` **monotòno crescente** (anche con salti tipo
  349→362), FAILOVER/RECOVERY alternati mentre Charon è UP.
- Dal Mac locale Charon risponde perfettamente durante il "FAILOVER".

**Verifica UNA sola volta (poi NON ri-sondare ogni ciclo):**
```bash
# Charon deve dare 200 + node_id peer70; Sidecar 200 + node_id peer58
curl -s -m 5 -w "\nHTTP %{http_code}\n" http://192.168.178.70:18643/hmp/health
curl -s -m 5 -w "\nHTTP %{http_code}\n" http://192.168.178.58:18643/hmp/health
ping -c 2 -t 3 192.168.178.70
```
Usare SOLO `/hmp/health` (dà `{status, service, node_id, bind}`). `/health` e
`/registry/peers` danno 404 — non usarli.

**Non curabile da questo Mac:** l'adapter HMP locale è solo trasporto; il
watchdog/sync difettoso gira sul nodo remoto peer58. Il failover comunque
*funziona* come rete di sicurezza → operatività salva.

## 🔴 Protocollo standby vs user-initiated action (distinzione critica)

Le notifiche FAILOVER/RECOVERY possono arrivare in DUE modi diversi,
con risposte radicalmente diverse:

### Scenario A: Sidecar autonomo (flap spurious da watchdog)

Il watchdog/sync rotto SUL REMOTO (peer58) produce coppie di notifiche
mentre Charon è di fatto sano. In questo scenario:

**Protocollo standby (preferenza utente — flag esplicito, mai 'quiet'):**
1. Alla **prima coppia** flap: alza il flag esplicito (verifica UNA volta +
   spiega che e' watchdog remoto, non Charon). Mai lasciare che uno stall/flap
   sembri quiete normale.
2. Poi **standby**: ack di 1 riga per ogni messaggio (es. 'Ack~ sync N,
   n-esimo flap. Standby.'), **NON ri-sondare, NON agire** senza ok dell'utente.
3. Offrire (una volta) di indagare il watchdog sul nodo remoto — aspettare l'ok.

### Scenario B: User-initiated (messaggio DIRETTO dell'utente a questo agente)

Quando l'**utente scrive direttamente** `FAILOVER HMP: ...` o
`RECOVERY HMP: ...` in chat, QUELLO e' l'ok dell'utente ad agire.
Non e' un flap autonomo — l'utente sta dichiarando lo stato di rete.

**Protocollo attivo (4 step, esegui subito):**
1. **Health verify** — health check su Charon + Sidecar in parallelo
   (sempre `/hmp/health`, mai `/health` o ping da solo)
2. **Notifica HMP** — POST `/hmp/send` al gateway del peer target:
   - FAILOVER: testuale a peer58, includere 'FAILOVER HMP' e 'primario'
   - RECOVERY: testuale a peer58, includere 'RECOVERY HMP' e 'mirror/fallback'
   - Notifica anche peer70 in RECOVERY
3. **Memoria** — aggiorna lo stato failover/recovery
4. **Report** — 1-2 righe di riepilogo con tabella ASCII (Charon, Sidecar, io)

**Regola pratica:** l'utente che dice esplicitamente FAILOVER/RECOVERY
e' un comando, non una notifica da ignorare. Il protocollo standby
(Scenario A) si applica SOLO quando Sidecar scrive autonomamente — non
quando l'utente scrive a questo agente direttamente.

## Script lato Sidecar

Sidecar ha creato autonomamente:
- `~/.hermes/scripts/hmp_sidecar.py` — watchdog principale
- `~/.hermes/scripts/hmp_sidecar_heartbeat.sh` — wrapper heartbeat
- `~/.hermes/scripts/hmp_sidecar_registry_sync.sh` — wrapper registry sync
- `~/.hermes/registry/sidecar_state.json` — stato locale

## Comunicazione con Sidecar

Standard HMP v0.1.3 su `192.168.178.58:18643`.

**Latenza**: ~162ms (RPi 3B+ via WiFi o Ethernet, più lento di Charon).
**Timeout consigliato**: 120-180s per messaggi che richiedono elaborazione.

## Limiti Sidecar (RPi 3B+)

- RAM: ~1GB — niente elaborazione pesante
- No display — niente NetBoard
- No Daily Exchange consolidator — solo invio digest
- CPU: ARM Cortex-A53 quad-core 1.2GHz
