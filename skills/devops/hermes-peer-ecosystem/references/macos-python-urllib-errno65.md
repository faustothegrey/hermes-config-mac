# macOS Python urllib errno 65 — "No route to host" on HMP ports 18643/8643

## Discovery (2026-09-26)

During HMP failover diagnostics, 793 consecutive registry sync failures were
traced to Python's `urllib.request.urlopen()` failing with `[Errno 65] No route
to host` when POSTing to `192.168.178.70:18643/hmp/send`, while `curl` worked
perfectly against the same endpoint.

## Root cause

macOS (14+) applies socket-level restrictions to Python's network stack —
likely via per-application firewall (Little Snitch, socketfilterfw) or TCC
sandbox rules. This affects **both** port 18643 (HMP staging) and port 8643
(HMP production). The existing belief that "18643 is NOT blocked for Python"
is incorrect — it **is** blocked (intermittently or consistently depending on
the firewall configuration).

## Verification pattern

```bash
# ✅ Works (curl via terminal)
curl -s -m5 http://192.168.178.70:18643/health
# → {"status":"ok","node_id":"peer70",...}

# ❌ FAILS (Python urllib on same host:port)
python3 -c "
from urllib.request import urlopen
print(urlopen('http://192.168.178.70:18643/health', timeout=5).read())
"
# → URLError: [Errno 65] No route to host
```

## Affected scripts

- `~/.hermes/registry/registry-publish.py` — uses `urllib.request.urlopen()`
  to POST REGISTRY_PUBLISH to Charon (peer70:18643)

## Workaround

Always use **curl via terminal** for HMP communication from macOS. In Python
scripts, call curl via `subprocess.run()` instead of urllib:

```python
import subprocess, json
r = subprocess.run(['curl', '-s', '-m', '10', '-X', 'POST',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(payload),
    'http://192.168.178.70:18643/hmp/send'],
    capture_output=True, text=True, timeout=15)
result = json.loads(r.stdout)
```

## Why not pip install requests

The firewall restriction is on Python's socket layer, not urllib specifically.
`requests` (which wraps urllib3) fails with the same errno 65.