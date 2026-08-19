# WireGuard VPN Setup on macOS (full reference)

> Previously a standalone skill (`wireguard`), absorbed into `hermes-peer-ecosystem`.
> Covers the full client lifecycle on macOS: install, keygen, config templates, activation,
> verification, troubleshooting. The peer-coordination pattern is at
> `peer-coordinated-wireguard-setup.md`.

## Prerequisites

- macOS with Homebrew
- A running WireGuard server on the LAN (or remote VPS)
- Router port forwarding (UDP 51820 or custom port) if connecting from outside the LAN
- DDNS configured if using a dynamic public IP

## Installation

```bash
brew install wireguard-tools
```

Installs `wg`, `wg-quick`, `wg show`, plus `wireguard-go` userspace implementation.

## Key generation

```bash
wg genkey | tee /dev/stderr | wg pubkey
```

Capture both keys:
```bash
PRIVATE_KEY=$(wg genkey)
PUBLIC_KEY=$(echo "$PRIVATE_KEY" | wg pubkey)
echo "Private: $PRIVATE_KEY"
echo "Public:  $PUBLIC_KEY"
```

**The public key is what you give to the server admin / configure as a peer on the server side.**

## Collect network info

```bash
# Private IP (for LAN endpoint)
ifconfig en0 | grep 'inet '

# Default gateway
netstat -rn -f inet | grep '^default'

# Public IP (for remote endpoint)
curl -4 -s ifconfig.me

# DNS server (usually the gateway)
scutil --dns | grep 'nameserver\\[' | head -3
```

## Client config template

Save to `/usr/local/etc/wireguard/wg0.conf` or `~/.wireguard/wg0.conf`:

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
| `DNS` | LAN gateway | Needed to resolve internal hostnames when tunnel is active |
| `PublicKey` | Server's public key | From the server admin |
| `AllowedIPs` | WG subnet + LAN subnet | Controls which traffic routes through the tunnel |
| `Endpoint` | `host:port` | Use DDNS hostname for dynamic IPs |
| `PersistentKeepalive` | `25` | Keeps NAT/firewall mapping alive |

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

WireGuard server typically runs on a Linux machine inside the LAN:

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

```bash
# Read full server state
ssh <user>@<server-ip> "sudo wg show wg0"

# Add or update a peer's public key
ssh <user>@<server-ip> "sudo wg set wg0 peer <old-public-key> remove \
  && sudo wg set wg0 peer <new-public-key> allowed-ips <wg-ip>/32"

# Persist to config file
ssh <user>@<server-ip> "sudo sed -i 's|<old-public-key>|<new-public-key>|' /etc/wireguard/wg0.conf"

# Check peers list
ssh <user>@<server-ip> "sudo wg show wg0 peers"

# Check latest handshakes
ssh <user>@<server-ip> "sudo wg show wg0 latest-handshakes"

# Check transfer counters
ssh <user>@<server-ip> "sudo wg show wg0 transfer"
```

Key pattern: `wg set` makes live runtime changes; always also edit `wg0.conf` for reboot persistence.

## HMP coordination for server-side setup

See `peer-coordinated-wireguard-setup.md` for the pattern of coordinating server-side setup
via HMP with a peer that has SSH access to the WireGuard server.

## Testing from LAN before going remote

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

## Pitfalls

1. **`wg-quick` needs sudo.** If no passwordless sudo, options: user runs it manually, create sudoers entry, use launchd plist, or enable Touch ID for sudo.
2. **macOS userspace vs kernel.** `brew install wireguard-tools` uses `wireguard-go` (userspace). For kernel performance, install WireGuard.app from the App Store.
3. **DNS leak.** With `AllowedIPs = 0.0.0.0/0`, add `DNS = <vpn-dns>` in `[Interface]`.
4. **No `wg-quick` without tunnel file.** Create directory first: `sudo mkdir -p /usr/local/etc/wireguard/`.
5. **macOS firewall blocks Python TCP on port 8643** — affects inter-peer coordination scripts. Use `curl` via terminal for HMP.
6. **IP forwarding required on server.** `net.ipv4.ip_forward=1` in `/etc/sysctl.conf` or `/etc/sysctl.d/`.
7. **Handshake timeout.** Use `PersistentKeepalive = 25` as safe default behind strict NAT.
8. **Multiple peers updating keys.** Communicate new public key to server admin — old key stops working immediately.
9. **HMP delivering state can take minutes.** Poll with `GET /hmp/poll/{message_id}` instead of re-sending.
10. **macOS `wg-quick up` needs a writable conf path.** Save to writable location and pass full path, or use `/etc/wireguard/`.
