# peer58 Charon/Sidecar acknowledgement format

Use one Italian line only. Preserve values from the incoming HMP alert; do not investigate or add commentary.

- FAILOVER: `ACK FAILOVER: <counter> fallimenti registry sync; registry temporaneo su <ip>:<port>.`
- RECOVERY: `ACK RECOVERY: Charon <ip> raggiungibile; Sidecar <ip> rientrato a mirror/fallback.`
