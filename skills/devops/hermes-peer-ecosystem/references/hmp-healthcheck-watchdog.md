# HMP Healthcheck Watchdog — deployed state

## peer70 (Raspberry Pi, monitoring node)

### Script: `~/.hermes/scripts/hmp-healthcheck.sh`

```bash
#!/bin/bash
# HMP Healthcheck — runs ON peer70, pings all network peers
# Silent when all healthy. HMP alert to peer128 on any failure.

PEER128_HOST="192.168.178.112"
PEER128_PORT="18643"
FAILED=0
ALERTS=""

check_peer() {
  local NAME=$1 HOST=$2 PORT=$3
  local PING_OK=1 HMP_OK=1

  ping -c1 -W2 $HOST >/dev/null 2>&1 && PING_OK=0
  local HMP=$(curl -s --max-time 5 http://$HOST:$PORT/hmp/send \
    -d '{"type":"ping","from":"peer70","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' \
    -H 'Content-Type: application/json' 2>&1)
  [ $? -eq 0 ] && HMP_OK=0

  if [ $PING_OK -eq 0 ] && [ $HMP_OK -eq 0 ]; then
    true  # OK
  elif [ $PING_OK -eq 0 ] && [ $HMP_OK -ne 0 ]; then
    ALERTS="$ALERTS $NAME:HMP_down"
    FAILED=1
  else
    ALERTS="$ALERTS $NAME:unreachable"
    FAILED=1
  fi
}

check_peer "peer128" "$PEER128_HOST" "$PEER128_PORT"
check_peer "peer105" "192.168.178.105" "18643"
check_peer "peer106" "192.168.178.106" "18643"

TS=$(date '+%H:%M')
if [ $FAILED -eq 0 ]; then
  echo "OK$TS" >> ~/.hermes/logs/hmp-healthcheck.log
  exit 0
else
  echo "[$TS] FAIL:$ALERTS" >> ~/.hermes/logs/hmp-healthcheck.log
  curl -s --max-time 5 http://$PEER128_HOST:$PEER128_PORT/hmp/send \
    -d '{"type":"message","from":"peer70","to":"peer128","text":"⚠️  HMP healthcheck: FAIL('$ALERTS')"}' \
    -H 'Content-Type: application/json' >/dev/null 2>&1
  exit 1
fi
```

### Crontab entry

```
0 * * * * /home/fausto/.hermes/scripts/hmp-healthcheck.sh >> /home/fausto/.hermes/logs/hmp-healthcheck.log 2>&1
```

Runs every hour at minute 0. Logs to `~/.hermes/logs/hmp-healthcheck.log`.

### Log format

```
OK17:24         ← all peers healthy
[18:47] FAIL: peer84:unreachable peer105:HMP_down   ← failures reported
```

### Recovery actions

If a peer goes down:
1. Check `tail -5 ~/.hermes/logs/hmp-healthcheck.log` on peer70 to confirm
2. The script automatically sends an HMP alert to peer128 when a failure is detected
3. When the peer comes back, the next cron run silently resumes OK status

## peer128 (MacBook Pro, control node)

### Hermes cron job: `hmp-peer70-healthcheck.sh`

```bash
#!/bin/bash
ssh fausto@192.168.178.70 "cd ~/.hermes/scripts && bash hmp-healthcheck.sh" 2>/dev/null || echo "⚠️  peer70 unreachable"
```

Created via:
```
cronjob(action='create', name='HMP healthcheck da peer70', schedule='0 * * * *', script='hmp-peer70-healthcheck.sh', no_agent=true, deliver='origin')
```

This variant delivers alerts to the chat conversation. Silent when healthy.

## Known peers and their HMP status

| Peer | IP | HMP port | HMP plugin | Notes |
|------|-----|----------|------------|-------|
| peer70 | 192.168.178.70 | 18643 | ✅ | Monitoring node (RPi, 24/7) |
| peer128 | 192.168.178.112 | 18643 | ✅ | Primary control node |
| peer105 | 192.168.178.105 | 18643 | ✅ | Remote peer |
| peer106 | 192.168.178.106 | 18643 | ✅ | Remote peer |
| peer84 | 192.168.178.84 | 18643 | ❓ | May not have HMP plugin |
