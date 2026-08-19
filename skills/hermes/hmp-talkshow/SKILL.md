---
name: hmp-talkshow
description: "Host an interactive live talk show with remote Hermes peers via HMP. Moderator asks questions aloud (edge-tts voices), peers respond via HMP, responses are read aloud with distinct voices. Pre-show topic announcement + N rounds of live back-and-forth."
version: 1.0.0
author: Hermes Agent
platforms: [macos]
---

# HMP Talk Show — Live Audio Show

Run an interactive live audio talk show where **peer128** (you, the moderator) questions remote Hermes peers (opinionists) and every exchange is spoken aloud with distinct Italian TTS voices.

## Prerequisites

- **HMP plugin** installed and enabled on all peers (`hermes plugins list` → `hmp` should be `enabled`)
- **edge-tts** installed: `pip3 install edge-tts --break-system-packages`
- **sox** installed: `brew install sox`
- Helper scripts at `~/.hermes/scripts/hermes-talkshow/`

## Scripts setup

Run once after installing edge-tts:

```bash
export HERMES_TALKSHOW_DIR=~/voice-memos/hermes-talkshow-live
```

The four helpers:

| Script | Usage |
|--------|-------|
| `sayit.sh <voce> "<testo>" <nome_file>` | Generate + play TTS audio |
| `send_to_peer.sh <peer_n> "<testo>" <prefisso>` | Send HMP message, print message_id |
| `wait_for_peer.sh <peer_n> <message_id>` | Poll until completed, print response |
| `record_peer.sh <voce> "<testo>" <nome_file>` | Generate + play TTS (for answers) |

## Voice assignments

| Role | edge-tts voice | ID |
|------|---------------|-----|
| **Moderator** (peer128) | Diego | `it-IT-DiegoNeural` |
| **peer105** | Elsa | `it-IT-ElsaNeural` |
| **peer106** | Isabella | `it-IT-IsabellaNeural` |

Alternative: GiuseppeMultilingualNeural for a third male voice.

## Standard talk show workflow

### 0. Setup
```bash
export HERMES_TALKSHOW_DIR=~/voice-memos/hermes-talkshow-live
rm -rf "$HERMES_TALKSHOW_DIR" && mkdir -p "$HERMES_TALKSHOW_DIR"
SEQ=0
```

### 1. Pre-show — announce topic (silent)
Send the topic to ALL peers. They confirm with "ok" — this pre-heats their context.

```bash
bash ~/.hermes/scripts/hermes-talkshow/send_to_peer.sh 105 "TEMA: ..." "tema_105"
bash ~/.hermes/scripts/hermes-talkshow/send_to_peer.sh 106 "TEMA: ..." "tema_106"
bash ~/.hermes/scripts/hermes-talkshow/wait_for_peer.sh 105 "<msgid>"
bash ~/.hermes/scripts/hermes-talkshow/wait_for_peer.sh 106 "<msgid>"
```

### 2. Live rounds — N rounds, alternating (or same-guest follow-ups)

Each round = 4 sub-steps:

```bash
# a) Moderator asks question (audio)
SEQ=$((SEQ+1))
bash ~/.hermes/scripts/hermes-talkshow/sayit.sh Diego "Domanda..." "r${SEQ}_domanda_105"

# b) Send question silently to peer
MSGID=$(bash ~/.hermes/scripts/hermes-talkshow/send_to_peer.sh 105 "Domanda..." "r${SEQ}_105")

# c) Wait for response
R=$(bash ~/.hermes/scripts/hermes-talkshow/wait_for_peer.sh 105 "$MSGID")

# d) Record response and play
bash ~/.hermes/scripts/hermes-talkshow/record_peer.sh Elsa "Risposta..." "r${SEQ}_risposta_105"
```

### 3. Closing
```bash
SEQ=$((SEQ+1))
bash ~/.hermes/scripts/hermes-talkshow/sayit.sh Diego "Chiudiamo..." "r${SEQ}_chiusura"
```

### 4. Concatenate final audio
```bash
cd "$HERMES_TALKSHOW_DIR"
# List files in order
files=$(ls -1 *.mp3 | sort)
sox $files ~/voice-memos/hermes-talk-show-final.mp3
echo "Saved: ~/voice-memos/hermes-talk-show-final.mp3"
```

## Timing guidelines

- **Pre-show topic message:** send to both peers before any audio — cuts response time by 50-70%
- **Moderator question:** 10-20 sec of audio (2-3 sentences)
- **Guest response:** 30-60 sec of audio (4-8 sentences)
- **Poll interval:** 4 seconds in wait_for_peer.sh
- **Total show time:** 7-10 min for 4 rounds

## Pitfalls

1. **`sayit.sh` timeout on long audio.** `afplay` blocks until the audio finishes — a 60-second response means the shell command runs for ~60s. Set terminal timeout to 90s minimum per call.

2. **Message IDs must be unique.** The `send_to_peer.sh` script appends a timestamp to the prefix, but if you call it twice in the same second, IDs can collide. Add a counter or use `$RANDOM`.

3. **Peer might be busy.** If a peer is already processing another request, the new one gets queued. Check the status — if "working" takes longer than 60s, the peer's session might be in a long conversation.

4. **edge-tts first call latency.** The first edge-tts call loads the model — subsequent calls are faster. Consider a silent warm-up call before the show.

5. **HERMES_TALKSHOW_DIR** must be set in the same shell session or the scripts fall back to their default. Export it explicitly.

6. **sox doesn't handle spaces in filenames** well without quoting. Keep filenames simple: `r1_domanda_105.mp3`.

## Verification

After a complete show, verify:
- Final MP3 exists and has content: `ls -lh ~/voice-memos/hermes-talk-show-*.mp3`
- All segments are concatenated (duration check): `ffprobe ~/voice-memos/hermes-talk-show-*.mp3 2>&1 | grep Duration`
- Audio plays correctly: `afplay ~/voice-memos/hermes-talk-show-*.mp3`
