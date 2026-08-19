# HMP Talk Show — Interactive Live Audio Show Architecture

**Data:** 2026-07-16  
**Peer:** peer128 (macOS, moderatore)  
**Ospiti:** peer105, peer106  
**Voci:** edge-tts (Microsoft Neural TTS, multilingua, qualità alta)

---

## Concept

Talk show interattivo dove il moderatore (peer128) fa domande dal vivo a opinionisti remoti (peer105, peer106) via **HMP plugin** (porta 18643), e ogni intervento viene **letto ad alta voce** con voci TTS neurali italiane distinte. L'effetto è di una trasmissione live in TV con tre "persone" che conversano.

## Flusso esecutivo

### Pre-show (silenzioso)
1. Il moderatore invia il **tema** della puntata a tutti gli ospiti via HMP
2. Ogni ospite conferma con "ok" o "tema ricevuto"
3. **Vantaggio:** quando parte la domanda audio, l'ospite ha già il contesto — risposta molto più veloce

### Live show (audio)
Per ogni round:
1. **Moderatore** → registra domanda con edge-tts (voce Diego), riproduce
2. **Invio** domanda via HMP all'ospite
3. **Attesa** risposta (polling /hmp/poll)
4. **Ospite** → registra risposta con edge-tts (Elsa/Isabella), riproduce
5. Si ripete per il round successivo

### Post-produzione
- Tutti i segmenti MP3 vengono concatenati con `sox` in un unico file
- Salvato in `~/voice-memos/hermes-talk-show-<tema>.mp3`

## Voci assegnate

| Ruolo | Voce edge-tts | ID voce | Carattere |
|-------|--------------|---------|-----------|
| **Moderatore** (peer128) | Diego | `it-IT-DiegoNeural` | Maschile, autorevole, amichevole |
| **peer105** | Elsa | `it-IT-ElsaNeural` | Femminile, chiara, calorosa |
| **peer106** | Isabella | `it-IT-IsabellaNeural` | Femminile, pacata, riflessiva |

Tutte le voci edge-tts sono **Microsoft Neural TTS** — italiano naturale, senza accento inglese.

## Script di accelerazione

Path: `~/.hermes/scripts/hermes-talkshow/`

### `sayit.sh <voce> <testo> <nome_file>`
Genera audio con edge-tts e lo riproduce.
- Voce: Diego, Elsa, Isabella, Giuseppe (senza suffisso Neural)
- Output: `$HERMES_TALKSHOW_DIR/<nome_file>.mp3`
- Variabile ambiente: `HERMES_TALKSHOW_DIR` (default: `~/voice-memos/hermes-talkshow-live`)

### `send_to_peer.sh <peer> <testo> <prefisso>`
Invia messaggio HMP a un peer, stampa il message_id.
- Peer: numero (es. 105 → 192.168.178.105:18643)
- Testo: il contenuto del messaggio
- Prefisso: identificativo usato nel message_id

### `wait_for_peer.sh <peer> <message_id>`
Polling ogni 4 secondi finché lo stato è "completed", poi stampa la response_text.

### `record_peer.sh <voce> <testo> <nome_file>`
Come sayit.sh ma non include il nome del ruolo nel commento. Usato per registrare le risposte degli ospiti.

## Endpoint HMP

Ogni peer espone il plugin HMP su `0.0.0.0:18643`:
- `POST /hmp/send` — invia un messaggio
- `GET /hmp/poll/{message_id}` — verifica stato e risposta
- `GET /hmp/health` — health check
- `GET /hmp/agent-card` — info peer

Messaggi in formato JSON standard HMP con campi: `from`, `to`, `type`, `status`, `payload.message`, `hmp_version`, `message_id`, `idempotency_key`, `timestamp`.

## Lunghezze consigliate

- **Domanda moderatore:** 10-20 secondi di audio (2-3 frasi)
- **Risposta ospite:** 30-60 secondi di audio (4-8 frasi)
- **Round completo:** 1-2 minuti
- **Show totale:** 3-10 minuti

## Config peer128 (questo Mac)

```yaml
# In ~/.hermes/config.yaml
platforms:
  hmp:
    enabled: true
    extra:
      host: 0.0.0.0
      port: 18643
      node_id: peer128
      allow_all_peers: true
      database_path: /Users/fausto/.hermes/data/hmp_gateway_plugin/messages.db
      request_timeout_seconds: 900
```

## Edge-TTS installazione

```bash
pip3 install edge-tts --break-system-packages
```

Voci italiane disponibili: Diego (M), Elsa (F), GiuseppeMultilingualNeural (M), Isabella (F).

## Esempio di puntata — "Gand per 6 giorni"

### Pre-show
```
send_to_peer 105 "TEMA: Fausto va a Gand..."    → tema_105_105_<ts>   → "ok"
send_to_peer 106 "TEMA: Fausto va a Gand..."    → tema_106_106_<ts>   → "ok"
```

### Round 1 — peer105: cosa vedere?
```
sayit Diego "Peer105, cosa deve vedere?"           → r1_domanda_105.mp3
send_to_peer 105 "Domanda: cosa vedere?"            → r1_105_<ts>
wait_for_peer 105 <msgid>                           → testo risposta
record_peer Elsa "Il castello, la cattedrale..."   → r1_risposta_105.mp3
```

### Round 2 — peer105: cosa mangiare?
```
sayit Diego "Peer105, cosa mangiare?"               → r2_fup_105.mp3
send_to_peer 105 "Domanda: cibo e birre?"           → r2_105_<ts>
wait_for_peer 105 <msgid>
record_peer Elsa "Waterzooi, stoverij, Gruut..."    → r2_risposta_105.mp3
```

### Round 3 — peer106: angoli nascosti?
```
sayit Diego "Peer106, angoli segreti?"              → r3_domanda_106.mp3
send_to_peer 106 "Domanda: angoli nascosti?"        → r3_106_<ts>
wait_for_peer 106 <msgid>
record_peer Isabella "Dr.Guislain, Begijnhof..."    → r3_risposta_106.mp3
```

### Round 4 — peer106: gite fuori?
```
sayit Diego "Peer106, gite fuori porta?"            → r4_fup_106.mp3
send_to_peer 106 "Follow-up: Bruges o Anversa?"     → r4_106_<ts>
wait_for_peer 106 <msgid>
record_peer Isabella "3gg Gand, 1 Bruges..."        → r4_risposta_106.mp3
```

### Chiusura
```
sayit Diego "Buon viaggio Fausto!"                  → r5_chiusura.mp3
```

### Concatenazione
```bash
sox r1_domanda_105.mp3 r1_risposta_105.mp3 ... r5_chiusura.mp3 ~/voice-memos/hermes-talk-show-ghent.mp3
```

## Note tecniche

- **Mac firewall:** Python non può fare TCP outbound su porte specifiche? No — il nuovo HMP va in POST diretto ai peer, usa curl via terminal (funziona sempre)
- **edge-tts:** ogni chiamata genera un file MP3. La concatenazione con sox funziona su MP3 direttamente
- **Peer offline:** se un peer non risponde, il polling va in timeout dopo ~90 secondi. Gestire con `failed` status
- **Tema pre-annunciato:** riduce i tempi di attesa del 50-70% perché l'ospite ha già processato il contesto
- **Durata totale:** puntata da 4 round + pre-show si completa in 7-10 minuti

## Possibili evoluzioni

- Round di dibattito (peer105 vs peer106 sullo stesso tema)
- Punteggio / reaction con jingle
- Aggiungere effetti sonori tra i segmenti (applausi, musichetta)
- Puntate programmate con cron job
