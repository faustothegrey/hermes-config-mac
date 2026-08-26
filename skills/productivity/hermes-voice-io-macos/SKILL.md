---
name: hermes-voice-io-macos
description: "Configure Hermes TTS/STT (voice in/out) on macOS."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [TTS, STT, voice, edge-tts, whisper, macos, config]
    related_skills: [claude-code]
---

# Hermes Voice I/O on macOS

Configure and verify text-to-speech (TTS) and speech-to-text (STT) for Hermes on macOS.
This is the how-to for "set up voice", "make it talk", "let me talk to you with my voice",
and diagnosing "I heard nothing".

## Inspect current state FIRST

```
hermes config get tts            # provider + per-provider voice settings
hermes config get stt            # provider + language + local whisper model
hermes status | grep -i "tts\|speech"
```

`hermes status` shows what is *active* vs *not currently selected*. Note: the config may
report a provider/model as present while status still says "not currently selected" — trust
the config values for what will actually be used.

## TTS setup (making Hermes speak)

Default provider is often `openai` with voice `alloy` (English). For an Italian user this is
wrong — switch to `edge` (Microsoft Edge neural voices, free, no API key, already installed at
`/usr/local/bin/edge-tts` on this Mac):

```
hermes config set tts.provider edge
hermes config get tts.provider          # verify
```

Italian edge voices (all natively Italian, NO English accent — the kind Fausto accepts):
- `it-IT-ElsaNeural`     — female (default already configured)
- `it-IT-IsabellaNeural` — female
- `it-IT-DiegoNeural`    — male

Change voice anytime: `hermes config set tts.edge.voice it-IT-IsabellaNeural`

Verify by actually generating audio with the `text_to_speech` tool (provider="edge"), then
play it — do NOT assume success from config alone.

## Playing audio on the CLI (critical)

On the terminal there is no audio attachment channel. `MEDIA:` tags are NOT rendered here.
To let the user actually HEAR a generated clip, play it with macOS `afplay`:

```
afplay /path/to/clip.mp3
```

PITFALL — short clips at normal volume are easily missed. A ~1.7s "ciao" at system volume 41
was inaudible on first play. Fix: boost afplay volume for short clips:

```
afplay -v 2 /path/to/clip.mp3     # -v 2 = double volume
```

### "I heard nothing" diagnostic ladder
1. `osascript -e 'output volume of (get volume settings)'` and `... output muted ...` — check level/mute.
2. `afinfo <file>` — confirm the mp3 is valid (duration > 0, has audio bytes).
3. `system_profiler SPAudioDataType | grep -A2 -i output` — confirm the default output device.
4. Play a known system sound to isolate file-vs-audio-path: `afplay /System/Library/Sounds/Glass.aiff`
5. Replay the clip at boosted volume: `afplay -v 2 <file>`
6. Ask the user which of {system ding, the clip} they heard — that pinpoints file vs volume vs device.

## STT setup (letting the user talk)

Whisper runs locally/offline via faster-whisper (model `base` cached at `~/.cache/whisper/`).
Set the language to Italian so transcription is accurate (default may be `en`):

```
hermes config set stt.language it
hermes config set stt.local.language it
```

### CLI has no push-to-talk
In the terminal chat there is no native mic button that sends voice straight to the agent
(unlike Telegram, where voice memos auto-transcribe). The practical flow on CLI: record a
memo -> transcribe with local Whisper -> user pastes the text into the prompt.

The `parla` helper automates record+transcribe. Install it with the packaged script:
`scripts/parla.sh` -> copy to `~/.local/bin/parla`, `chmod +x`. Usage: run `parla`, speak,
press Enter to stop; add `-c` to also copy the transcript to the clipboard (pbcopy).
Requires: `rec`/`sox` (installed), `faster_whisper` (installed), python3.

## Pitfalls
- Config saying a provider is set != it being audible. Always verify TTS end-to-end with a real generate+play.
- `MEDIA:/path` tags do nothing on CLI — state the plain path and/or `afplay` it.
- Short TTS clips at moderate system volume are easy to miss; use `afplay -v 2`.
- Wrong STT language (default `en`) garbles Italian; set both `stt.language` and `stt.local.language`.
- Fausto rejects English-accented voices — always pick a native `it-IT-*Neural` edge voice.
