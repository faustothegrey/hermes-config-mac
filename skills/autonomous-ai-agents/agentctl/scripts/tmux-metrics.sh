#!/bin/bash
# tmux-metrics.sh — deterministic harness for tmux character counting
# Part of agentctl skill. Wraps agentctl send/capture with byte counters.
#
# Usage:
#   tmux-metrics.sh send <agent> <message>   # sends + counts chars
#   tmux-metrics.sh capture <agent>           # captures + counts chars
#   tmux-metrics.sh status                    # prints current counters as JSON
#
# Counter reset rules (PO Fausto, 2026-07-02):
#   - On send: add chars to sent counter, reset received counter to 0
#   - On capture: add chars to received counter, reset sent counter to 0
#   - This means at any point, counters show "chars since last opposite action"
#
# Published at GET /api/hermes/metrics on the orchestrator API.

METRICS_DIR="$HOME/.hermes/heartbeat"
SENT_FILE="$METRICS_DIR/tmux-sent"
RECV_FILE="$METRICS_DIR/tmux-recv"

mkdir -p "$METRICS_DIR"

case "${1:-status}" in
  send)
    AGENT="$2"
    shift 2
    MESSAGE="$*"
    CHARS="${#MESSAGE}"
    "$HOME/.local/bin/agentctl" send "$AGENT" "$MESSAGE" > /dev/null 2>&1
    OLD_SENT=$(cat "$SENT_FILE" 2>/dev/null || echo 0)
    echo $((OLD_SENT + CHARS)) > "$SENT_FILE"
    echo 0 > "$RECV_FILE"
    echo "sent:${CHARS} total:$(cat $SENT_FILE)"
    ;;
  capture)
    AGENT="$2"
    OUTPUT=$("$HOME/.local/bin/agentctl" capture "$AGENT" 2>/dev/null)
    CHARS="${#OUTPUT}"
    OLD_RECV=$(cat "$RECV_FILE" 2>/dev/null || echo 0)
    echo $((OLD_RECV + CHARS)) > "$RECV_FILE"
    echo 0 > "$SENT_FILE"
    echo "recv:${CHARS} total:$(cat $RECV_FILE)"
    ;;
  status)
    SENT=$(cat "$SENT_FILE" 2>/dev/null || echo 0)
    RECV=$(cat "$RECV_FILE" 2>/dev/null || echo 0)
    echo "{\"sent\":$SENT,\"received\":$RECV}"
    ;;
esac
