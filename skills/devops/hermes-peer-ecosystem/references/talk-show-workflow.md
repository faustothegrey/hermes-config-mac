# Talk Show / Multi-Voice Audio Production via HMP

Use HMP to query peers for opinions, then produce a multi-voice audio recording
with different TTS voices for each participant. Great for creative content,
talk shows, debates, or narrated discussions.

## TTS Engine Selection

### Primary: edge-tts (recommended for Italian / multilingual)

`edge-tts` uses Microsoft Neural TTS — natural voices with proper accent
for Italian, French, German, Spanish, etc. macOS `say` Italian voices have
a strong English accent which users notice and dislike.

Install: `pip3 install edge-tts --break-system-packages`

| Language | Voices |
|----------|--------|
| Italian (male) | `it-IT-DiegoNeural`, `it-IT-GiuseppeMultilingualNeural` |
| Italian (female) | `it-IT-ElsaNeural`, `it-IT-IsabellaNeural` |

List all: `edge-tts --list-voices`

### Fallback: macOS `say`

Use for English content or when edge-tts is unavailable.
List: `say -v '?'`

### Live/interactive format

The user expects a **live TV talk show** feel: record each segment, play it
immediately, then move to the next step. Never batch-record everything at
the end.

## When to use

- User wants a "talk show" or "debate" format with multiple peer AI instances
- User wants to hear different AI opinions on a topic in audio form
- Any multi-character narration where each voice should be distinct

## Workflow

### 1. Assign voices

macOS `say` voices available on this system:

| Voice | Gender | Language | Style |
|-------|--------|----------|-------|
| **Eddy** | Male | Italian (it_IT) | Neutral, authoritative |
| **Flo** | Female | Italian (it_IT) | Bright, pleasant |
| **Reed** | Male | Italian (it_IT) | Neutral, smooth |
| **Grandpa** | Male | Italian (it_IT) | Deep, older |
| **Sandy** | Female | Italian (it_IT) | Light, cheerful |
| **Rocko** | Male | Italian (it_IT) | Casual, rough |
| **Daniel** | Male | British English (en_GB) | Polished, formal |
| **Samantha** | Female | American English (en_US) | Warm, standard |

List all available voices: `say -v '?'`

### 2. Query peers via HMP

Send a question/topic to each peer via the HMP plugin POST endpoint. Use a
unique `message_id` per question so you can poll each independently.

```bash
# Send to peer105
curl -s -X POST http://192.168.178.105:18643/hmp/send \
  -H 'Content-Type: application/json' \
  -d '{
    "hmp_version": "1.0",
    "message_id": "talkshow_105_q1_'$(date +%s)'",
    "idempotency_key": "talkshow_105_q1_'$(date +%s)'",
    "from": "peer128",
    "to": "peer105",
    "type": "request",
    "status": "pending",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "payload": {
        "task_type": "chat",
        "message": "<question for peer105>"
    }
  }'
```

### 3. Poll for responses

Wait 5–15 seconds, then poll each peer:

```bash
curl -s http://192.168.178.105:18643/hmp/poll/talkshow_105_q1_<timestamp>
# Extract response_text field
```

Both peers can be queried in parallel (they process independently).

### 4. Compose the script

Write a script with labelled segments. Each segment = one speaker + text.
A typical talk show structure:

1. **Intro** (Moderator) — welcome, topic intro, introduce guests
2. **Guest 1 question** (Moderator) — ask the question
3. **Guest 1 answer** (peer105's voice) — condensed key points
4. **Guest 2 question** (Moderator) — second angle
5. **Guest 2 answer** (peer106's voice) — condensed key points
6. **Closing** (Moderator) — summary, wrap-up, sign-off

Keep each segment to 15–30 seconds of speech for good pacing.

### 5. Generate audio segments

Use `edge-tts` (preferred for Italian/multilingual) or `say`:

```bash
# edge-tts (outputs MP3 directly):
edge-tts --voice it-IT-DiegoNeural --text "spoken text" \
  --write-media "segment_N.mp3"

# macOS say (outputs AIFF):
say -v "VoiceName" -o "segment_N.aiff" "spoken text"
```

### Segment length guidelines

- **Moderator questions:** 10–20 seconds
- **Guest answers:** 30–60 seconds (max 2 minutes)
- **Closing:** 10–20 seconds
- **Total per session:** 2–5 minutes for a pilot round

Always condense peer answers to 3–5 spoken-friendly key points. Strip
markdown formatting, bullet prefixes, and section headers. Rewrite as flowing
speech with connectors.

### 6. Concatenate with SoX

```bash
sox segment_1.aiff segment_2.aiff ... segment_N.aiff <output.mp3>
```

`sox` automatically handles AIFF → MP3 conversion when the output filename
ends in `.mp3`. Output files land naturally in `~/voice-memos/`.

### 7. Cleanup

```bash
rm -rf ~/voice-memos/hermes-talkshow/   # temp segments directory
```

## Pitfalls

1. **`say` Italian voices have an English accent.** Users notice and dislike
   this. Always prefer `edge-tts` for Italian/multilingual content. macOS
   built-in Italian voices (Eddy, Flo, Reed) sound like English speakers
   reading Italian — not acceptable for production audio.

2. **edge-tts needs `--break-system-packages` on macOS.** Run once:
   `pip3 install edge-tts --break-system-packages`.

3. **Peer response latency varies.** Peers may take 5–30+ seconds. Poll
   independently with staggered waits. Use curl + python3 poll loop.

4. **Condense answers for audio.** Peers return detailed text — pick 3–5
   best points. Full-text reading creates terrible audio pacing.

5. **Send `"risposta breve"` / `"max un minuto"` in HMP prompts.** Without
   this, peers write novel-length answers hard to condense.

6. **Voice consistency.** Always use the same voice for the same character
   across all segments. Keep a written map: Moderator=Diego, peer105=Elsa,
   peer106=Isabella.

7. **edge-tts outputs MP3 directly.** No AIFF→MP3 conversion needed.
   `say` outputs AIFF (~2.5 MB per 30s) which sox converts to MP3.

8. **Play immediately after recording.** Record → afplay → next step.
   Never batch-record, the user wants live TV pacing.

9. **Ask language preference before starting.** If Italian, edge-tts.
   If English, `say` or edge-tts English voices both work.

## Helper scripts (skill-bundled)

The skill includes reusable shell scripts under `scripts/`:

| Script | Purpose |
|--------|---------|
| `sayit.sh <voice> <text> <file>` | Generate TTS via edge-tts, save MP3, play immediately |
| `send_to_peer.sh <peer> <msg> <prefix>` | Send message to HMP peer, return message_id |
| `wait_for_peer.sh <peer> <msg_id>` | Poll for peer response until completed, return text |
| `record_peer.sh <voice> <text> <file>` | Record a peer's processed answer with voice and play |

Live flow using scripts (make them executable first: `chmod +x ~/.hermes/skills/devops/hermes-peer-ecosystem/scripts/*.sh`):

```bash
export HERMES_TALKSHOW_DIR=~/voice-memos/hermes-talkshow-live

# Pre-show: announce topic to both peers
send_to_peer.sh 105 "TEMA: ..." "tema"
send_to_peer.sh 106 "TEMA: ..." "tema"
# Wait for both: "ok" or "tema ricevuto"

# Round 1: ask peer105
sayit.sh Diego "Ciao! Domanda?" "q1"
MSGID=$(send_to_peer.sh 105 "Domanda: ..." "r1")
ANS=$(wait_for_peer.sh 105 "$MSGID")
record_peer.sh Elsa "$ANS" "a1"

# Round 2: ask peer106
sayit.sh Diego "E ora peer106?" "q2"
MSGID=$(send_to_peer.sh 106 "Domanda: ..." "r2")
ANS=$(wait_for_peer.sh 106 "$MSGID")
record_peer.sh Isabella "$ANS" "a2"

# Concatenate all segments
sox q1.mp3 a1.mp3 q2.mp3 a2.mp3 closing.mp3 ~/voice-memos/show.mp3
```

## Example output

From the Ghent Travel Talk Show session (Italian):
- 5 segments, 3 edge-tts voices (Diego, Elsa, Isabella)
- ~3 minutes runtime
- 444 KB MP3 at `~/voice-memos/hermes-talk-show-ghent.mp3`
