# Hermes Gateway API server on macOS launchd

This reference captures a verified pattern for configuring Hermes Gateway as a macOS headless/background service with the OpenAI-compatible API server bound to all interfaces.

## Configuration

File: `~/.hermes/.env`

Required API server variables:

```sh
API_SERVER_ENABLED=true
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8642
API_SERVER_KEY=<strong secret>
```

If `API_SERVER_KEY` is absent, generate one before exposing the server, for example:

```sh
python3 - <<'PY'
import secrets
print('hermes_' + secrets.token_urlsafe(32))
PY
```

Do not print the key in final user-facing output unless the user explicitly asks for it. Give a retrieval command instead.

## Install and start

Use Hermes' built-in launchd installer:

```sh
hermes gateway install --force
```

On macOS default profile this installs:

```text
~/Library/LaunchAgents/ai.hermes.gateway.plist
```

The generated plist runs:

```text
<venv>/bin/python -m hermes_cli.main gateway run --replace
```

and includes `RunAtLoad` plus `KeepAlive` so the gateway is relaunched by launchd for the user session.

## Verification checklist

```sh
hermes gateway status
launchctl list ai.hermes.gateway
plutil -lint ~/Library/LaunchAgents/ai.hermes.gateway.plist
lsof -nP -iTCP:8642 -sTCP:LISTEN
netstat -anv -p tcp | grep '\.8642 .*LISTEN'
curl -fsS http://127.0.0.1:8642/health
```

Expected socket when bound to all IPv4 interfaces:

```text
tcp4 ... *.8642 ... LISTEN ... python3.11:<pid>
```

Expected health response:

```json
{"status": "ok", "platform": "hermes-agent"}
```

Authenticated model-list probe:

```sh
set -a; . ~/.hermes/.env; set +a
curl -fsS -H "Authorization: Bearer $API_SERVER_KEY" \
  http://127.0.0.1:8642/v1/models | python3 -m json.tool
```

If sourcing `.env` fails because unrelated values contain spaces or shell-special characters, use Python to read only `API_SERVER_KEY` instead of sourcing the whole file.

## Logs and delayed readiness

Primary logs:

```text
~/.hermes/logs/gateway.log
~/.hermes/logs/gateway.error.log
```

The launchd service can be loaded and show a PID before the API server has bound the port. If an immediate health check fails, inspect the logs and retry after a short delay. Capture the final listener/health evidence, not just `launchctl` status.

## Scope note

`hermes gateway install` on macOS creates a user LaunchAgent. It autostarts headlessly for the user's launchd GUI session. It is not a system LaunchDaemon that starts pre-login; installing that would require admin privileges and a different plist location/ownership model.
