# Peer-Coordinated WireGuard VPN Setup (worked example)

This reference documents the **pattern** of coordinating shared infrastructure setup
across two Hermes peers via HMP, using WireGuard client-on-macOS as the worked example.

For the **full WireGuard client setup guide** (install, keygen, config templates,
connection management, verification, and troubleshooting), see
`references/wireguard-setup.md`.

## Architecture

```
Server peer58 (Sidecar)  ←WireGuard→  Client peer128 (this Mac)
  ├── 10.0.0.1/24:51820              ├── 10.0.0.6/24
  ├── Debian 13 Trixie               ├── macOS 26.5.2
  └── wg0, NAT enabled               └── utun4 via wg-quick

Coordinator: peer70 (Charon, Raspberry Pi)
  192.168.178.70 — HMP on 18643
```

## The pattern

This is a **two-agent coordination** pattern:

| Agent | Role | Action |
|-------|------|--------|
| **peer70 (Charon)** | Server-side coordinator | Knows the LAN topology, can SSH to server, configures peer entries on wg0 |
| **peer128 (me)** | Client-side setup | Generates keys, creates local config, activates tunnel, tests connectivity |

### Trigger

User says: "set up WireGuard VPN connection between this machine and the router/LAN"

When there's an existing WireGuard server on the LAN:

1. **Discover topology** — ASK peer70 via HMP where the WG server is, what the subnet is, what IP is assigned to this peer
2. **Generate keys** locally on this machine (see `wireguard-setup.md` for commands)
3. **Communicate the public key** to the server-side agent via HMP
4. **Fallback to direct SSH** if HMP coordination is slow — if on the same LAN and SSH is configured, update the server directly with `wg set` + `sed` on the persistent config
5. **Create config file** (see `wireguard-setup.md` for template)
6. **Activate** with `sudo wg-quick up wg-<name>`
7. **Test** — ping the WG server, ping other WG peers, ping LAN devices via the tunnel

### If the server doesn't exist yet

This pattern extends to full server setup:
1. Install WireGuard on the server peer
2. Configure wg0 interface, subnet, NAT/iptables
3. Add all peers
4. Enable systemd/wg-quick@wg0 for persistence
5. Then proceed with client setup as above

## HMP coordination flow (worked example)

### Step 1: Discover LAN state
```bash
curl -s -X POST http://<peer70-ip>:18643/hmp/send \
  -H "Content-Type: application/json" \
  -d '{
    "type": "direct",
    "from": "peer128",
    "to": "peer70",
    "text": "WireGuard server details? Subnet? My IP?",
    "idempotency_key": "wg_discover_01"
  }'
# Poll for response:
curl -s http://<peer70-ip>:18643/hmp/poll/<message_id>
```

### Step 2: Send public key for server update
```bash
curl -s -X POST http://<peer70-ip>:18643/hmp/send \
  -H "Content-Type: application/json" \
  -d '{
    "type": "direct",
    "from": "peer128",
    "to": "peer70",
    "text": "Update public key for 10.0.0.6: <new_public_key>",
    "idempotency_key": "wg_key_02"
  }'
```

### Step 3: Handle slow HMP responses
If the peer takes >30s in `delivering` status:
1. Check its health: `curl -s http://<peer-ip>:18643/health`
2. If health OK, consider doing the server-side work directly via SSH
3. Then notify the peer via HMP that work is done

### Step 4: Confirm completion
```bash
curl -s -X POST http://<peer70-ip>:18643/hmp/send \
  -H "Content-Type: application/json" \
  -d '{
    "type": "direct",
    "from": "peer128",
    "to": "peer70",
    "text": "WireGuard done. Details: <summary>",
    "idempotency_key": "wg_done_07"
  }'
```

## Direct SSH fallback (on the same LAN)

When HMP coordination is slow and you are on the same LAN, update the server directly:

```bash
# Update the running config (in-memory)
ssh fausto@<server-ip> "sudo wg set wg0 peer <OLD_KEY> remove && \
  sudo wg set wg0 peer <NEW_KEY> allowed-ips <IP>/32"

# Make it persistent (update wg0.conf)
ssh fausto@<server-ip> "sudo sed -i 's|<OLD_KEY>|<NEW_KEY>|' /etc/wireguard/wg0.conf"
```

Check current peer list:
```bash
ssh fausto@<server-ip> "sudo wg show wg0"
```

## Router considerations

- **FritzBox:** Port forwarding at Internet → Permitted Access → Port Sharing
  - UDP 51820 → server LAN IP
- **DDNS:** Confirm with user — the FritzBox has built-in DDNS support
- **Hairpin NAT:** FritzBox handles hairpin NAT, so the DDNS endpoint works both inside and outside the LAN

## Pitfalls (coordination-specific)

1. **HMP message status** — `queued` means the gateway is still processing; `delivering` means the peer hasn't replied yet; `completed` means done. If stuck on `delivering` for >2min, the peer may be busy with a long-running task.
2. **Persistent vs in-memory config** — `wg set` only changes the running config. Always update `/etc/wireguard/wg0.conf` for reboot persistence.
3. **Sudo password on macOS** — `wg-quick up` and `wg show` require sudo. If sudo is not passwordless, see `wireguard-setup.md` for options.
4. **Key regeneration** — If the user already generated keys in a prior session, check before regenerating. Mismatched keys require updating the server's peer entry.
