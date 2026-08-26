#!/usr/bin/env bash
# parla — record from mic and transcribe to Italian with local Whisper (offline).
# Install: cp this to ~/.local/bin/parla && chmod +x ~/.local/bin/parla
# Usage: parla       -> record until you press Enter, then print the transcript
#        parla -c    -> same, but also copy the text to the clipboard (pbcopy)
# Requires: rec/sox, python3 with faster_whisper, whisper 'base' model cached.
set -euo pipefail

TMPDIR_REC="$(mktemp -d)"
WAV="$TMPDIR_REC/parla_$(date +%Y%m%d_%H%M%S).wav"
trap 'rm -rf "$TMPDIR_REC"' EXIT

COPY=0
[[ "${1:-}" == "-c" ]] && COPY=1

echo "🎤  Registrazione... parla pure. Premi INVIO per fermare."
# 16kHz mono is optimal for Whisper
rec -q -c 1 -r 16000 -b 16 "$WAV" >/dev/null 2>&1 &
REC_PID=$!

read -r _ </dev/tty
kill "$REC_PID" 2>/dev/null || true
wait "$REC_PID" 2>/dev/null || true

if [[ ! -s "$WAV" ]]; then
  echo "⚠️  Nessun audio registrato." >&2
  exit 1
fi

echo "📝  Trascrivo (Whisper base, italiano)..." >&2

TEXT="$(python3 - "$WAV" <<'PY'
import sys
from faster_whisper import WhisperModel
wav = sys.argv[1]
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, _ = model.transcribe(wav, language="it", vad_filter=True)
print(" ".join(s.text.strip() for s in segments).strip())
PY
)"

if [[ -z "$TEXT" ]]; then
  echo "⚠️  Non ho capito nulla (silenzio o audio troppo basso)." >&2
  exit 1
fi

echo
echo "🗣️  $TEXT"

if [[ "$COPY" == "1" ]]; then
  printf '%s' "$TEXT" | pbcopy
  echo "📋  (copiato negli appunti)" >&2
fi
