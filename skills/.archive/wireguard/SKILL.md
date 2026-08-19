---
name: wireguard
description: "Set up and manage WireGuard VPN tunnels on macOS — client install, key generation, config templates, activation, and peer coordination via HMP for server-side setup."
version: 1.0.0
author: peer128
license: MIT
platforms: [macos]
---

# WireGuard

Use this skill when setting up a WireGuard VPN tunnel on macOS — as a client connecting to a remote server, or as a peer in a mesh. Covers the full lifecycle: install, keygen, config, activation, and coordination with a server-side peer via HMP.

## Prerequisites

- macOS with Homebrew
- A running WireGuard server on the LAN (or remote VPS) — see `peers → HMP` section below for coordinating server-side setup with a peer via the `hermes-peer-ecosystem` skill
- Router port forwarding (UDP 51820 or custom port) if connecting from outside the LAN
- DDNS configured if using a dynamic public IP

## Installation

```bash
brew install wireguard-tools
```

This installs `wg`, `wg-quick`, and `wg show` commands plus the `wireguard-go` userspace implementation on macOS.

## Key generation

Generate a **private key** and derive the **public key** in one shot:

```bash
wg genkey | tee /dev/stderr | wg pubkey
```

This prints the private key to stderr and the public key to stdout. Capture both:

```bash
PRIVATE_KEY=$(wg genkey)
PUBLIC_KEY=$(echo "$PRIVATE_KEY" | wg pubkey)
echo "Private: $PRIVATE_KEY"
echo "Public:  $PUBLIC_KEY"
```

**The public key is what you give to the server admin / configure as a peer on the server side.**

## Collect network info

Before writing the config, gather:

```bash
# Private IP (for LAN endpoint)
ifconfig en0 | grep 'inet '

# Default gateway
netstat -rn -f inet | grep '^default'

# Public IP (for remote endpoint)
curl -4 -s ifconfig.me

# DNS server (usually the gateway)
scutil --dns | grep 'nameserver\[' | head -3
```

## Client config template

Save to `/usr/local/etc/wireguard/wg0.conf` (or `~/.wireguard/wg0.conf`):

```ini
[Interface]
PrivateKey = <client-private-key>
Address = 10.0.0.X/24
DNS = 192.168.178.1

[Peer]
PublicKey = <server-public-key>
AllowedIPs = 10.0.0.0/24, 192.168.178.0/24
Endpoint = <ddns-or-public-ip>:51820
PersistentKeepalive = 25
```

### Config parameter notes

| Parameter | Value | Notes |
|-----------|-------|-------|
| `PrivateKey` | Client's private key | NEVER share this |
| `Address` | `10.0.0.X/24` | The WG IP assigned to this client by the server |
| `DNS` | `192.168.178.1` | LAN DNS — needed to resolve internal hostnames when tunnel is active |
| `PublicKey` | Server's public key | From the server admin |
| `AllowedIPs` | WG subnet + LAN subnet | Controls which traffic routes through the tunnel |
| `Endpoint` | `host:port` | Use DDNS hostname for dynamic IPs |
| `PersistentKeepalive` | `25` | Keeps NAT/firewall mapping alive for incoming connections |

### AllowedIPs patterns

- **LAN + WG only** (recommended): `10.0.0.0/24, 192.168.178.0/24`
- **Full tunnel (all traffic via VPN)**: `0.0.0.0/0`
- **WG-only**: `10.0.0.0/24`

## Connection management

```bash
# Bring up
sudo wg-quick up wg0

# Bring down
sudo wg-quick down wg0

# Status
sudo wg show

# Show latest handshake
sudo wg show wg0 latest-handshakes

# Re-read config without restarting
sudo wg syncconf wg0 <(wg-quick strip wg0)
```

### Verify connection

```bash
# Check tunnel interface
ifconfig wg0

# Ping WG server
ping -c3 10.0.0.1

# Ping a device inside the LAN
ping -c3 192.168.178.1

# Check latest handshake (should be < 2 min ago with PersistentKeepalive)
sudo wg show wg0 | grep -i handshake

# Traffic counters
sudo wg show wg0 transfer
```

## Server setup (quick reference)

WireGuard server typically runs on a Linux machine inside the LAN. Basic server config:

```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <server-private-key>

# Enable NAT
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# Peer: client macOS
PublicKey = <client-public-key>
AllowedIPs = 10.0.0.X/32
```

On Debian/Ubuntu: `sudo systemctl enable wg-quick@wg0 && sudo systemctl start wg-quick@wg0`

### Direct server management via SSH

When on the same LAN with SSH access to the server, manage peers directly instead of coordinating through another peer:

```bash
# Read full server state (peers, handshakes, transfer)
ssh <user>@<server-ip> "sudo wg show wg0"

# Add or update a peer's public key (replaces old key with new)
ssh <user>@<server-ip> "sudo wg set wg0 peer <old-public-key> remove \
  && sudo wg set wg0 peer <new-public-key> allowed-ips <wg-ip>/32"

# Persist the change to /etc/wireguard/wg0.conf (so it survives reboot)
ssh <user>@<server-ip> "sudo sed -i 's|<old-public-key>|<new-public-key>|' /etc/wireguard/wg0.conf"

# Check only the peers list
ssh <user>@<server-ip> "sudo wg show wg0 peers"

# Check latest handshake times (indicates active connections)
ssh <user>@<server-ip> "sudo wg show wg0 latest-handshakes"

# Check transfer counters
ssh <user>@<server-ip> "sudo wg show wg0 transfer"
```

Key pattern: `wg set` makes live runtime changes; always also edit `wg0.conf` for persistence. The server's public key is visible from `sudo wg show`.

### Coordinating server-side setup via HMP

When you don't have direct access to the server, use HMP messaging to a peer that does:

1. Send the client's public key to the server admin peer
2. Ask for the assigned WG IP and server's public key
3. Poll for the response

**HMP message format (critical):**

- The `text` field MUST be at the top level of the JSON body — NOT nested inside `payload`
- Use `idempotency_key` for safe retries
- Available endpoints on the peer's HMP server:
  - `POST /hmp/send` — fire-and-forget (returns immediately with `queued` or `working`)
  - `POST /hmp/send_and_wait` — blocks until the peer responds (use `--max-time` on curl, default 900s timeout)
  - `GET /hmp/poll/{message_id}` — check status and read the response

**Status lifecycle:**

    accepted/queued → gateway_accepted → working → delivering → completed|failed

- `delivering` means the peer is generating the response — can take 30+ seconds for short replies, minutes for tasks involving terminal commands
- Do NOT send follow-ups while a message is in `delivering` — it may interrupt the peer mid-task
- Always poll before re-sending

**HMP curl example:**

```bash
# Send
curl -s -X POST http://<peer-ip>:18643/hmp/send \
  -H "Content-Type: application/json" \
  -d '{
    "type": "direct",
    "from": "<my-peer-id>",
    "to": "<target-peer-id>",
    "text": "Tuoi dettagli qui...",
    "idempotency_key": "unique_key_01"
  }'

# Poll
curl -s http://<peer-ip>:18643/hmp/poll/<message_id>
```

### Testing from LAN before going remote

Before setting up port forwarding / DDNS, test the tunnel while still on the same LAN:

1. Write the config with the server's **LAN IP** as the `Endpoint`
2. Activate the tunnel
3. Verify connectivity with pings
4. Once LAN test passes, change `Endpoint` to the DDNS hostname + enable port forwarding

## Router port forwarding (FritzBox)

| Setting | Value |
|---------|-------|
| Port (external) | `51820` UDP |
| Target IP | Server's LAN IP (e.g. 192.168.178.58) |
| Port (internal) | `51820` UDP |
| Enable | Yes / Allow |

FritzBox also supports UPnP — some servers can auto-open the port if UPnP is enabled in the FritzBox settings (Heimnetz → Netzwerk → Netzwerkeinstellungen → UPnP-Einstellungen).

## Pitfalls

1. **`wg-quick` needs sudo.** Always prefix up/down with `sudo`. If no passwordless sudo is configured, options:
   - Ask the user to run the command once: `sudo wg-quick up <path-to-conf>`
   - Create a sudoers entry: `echo '%admin ALL=NOPASSWD: /usr/local/bin/wg-quick' | sudo tee /etc/sudoers.d/wireguard`
   - Use a launchd plist running as root with `ProgramArguments` pointing to `wg-quick up` (autostarts on boot)
   - Enable Touch ID for sudo: add `auth sufficient pam_tid.so` to `/etc/pam.d/sudo` (macOS only)
2. **macOS userspace vs kernel.** `brew install wireguard-tools` uses `wireguard-go` (userspace). Performance is adequate for tunnel use but not line-rate. For kernel performance, install the WireGuard.app from the App Store (includes the system extension).
3. **DNS leak.** When using `AllowedIPs = 0.0.0.0/0`, macOS DNS may still leak through the primary interface. Add `DNS = <vpn-dns>` in the `[Interface]` section.
4. **No `wg-quick` without tunnel file.** `wg-quick up wg0` looks for `/usr/local/etc/wireguard/wg0.conf` — if the file doesn't exist, error is unhelpful. Create the directory first: `sudo mkdir -p /usr/local/etc/wireguard/`.
5. **Firewall blocks Python on port 8643** — affects inter-peer coordination scripts. Use `curl` via terminal for HMP messages. See `hermes-peer-ecosystem` skill for details.
6. **IP forwarding required on server.** The server must have `net.ipv4.ip_forward=1` in `/etc/sysctl.conf` or `/etc/sysctl.d/` for NAT to work.
7. **Handshake timeout.** If `PersistentKeepalive` is too low (or missing) and the client is behind a strict NAT, the tunnel drops silently. Use 25s as a safe default.
8. **Multiple peers updating keys.** When regenerating keys, always communicate the new public key to the server admin — the old key stops working immediately upon replacement.
9. **HMP delivering state can take minutes.** When coordinating via HMP, a peer's status may stay in `delivering` for 30-150+ seconds while it runs terminal commands. Do NOT send follow-up messages — they interrupt the peer mid-task and produce truncated responses. Poll with `GET /hmp/poll/{message_id}` instead; the response includes `response_text` when status reaches `completed`.
10. **macOS `wg-quick up` needs a writable conf path.** The file must be accessible to wg-quick. Save to `~/.wireguard/wg0.conf` or `~/*.conf` and pass the full path. `/etc/wireguard/` requires sudo to create/access but works for auto-discovery via `wg-quick up wg0`.
