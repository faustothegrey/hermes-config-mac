# Hermes API Server bearer auth and stale key incident

A Hermes API Server peer setup on macOS exposed this failure pattern:

- `/health` on the LAN IP returned HTTP 200.
- `/health/detailed` on the LAN IP returned HTTP 200.
- `/v1/capabilities` returned `401 invalid_api_key` from another peer.

The useful debugging sequence was:

1. Verify the live gateway logs show the API server listening on `0.0.0.0:<port>`.
2. Read the active `.env` and compare the current `API_SERVER_KEY` with the key previously handed to the peer.
3. Correct the `.env` if it still contains an older generated key.
4. Restart the Hermes gateway; do not rely on an already-running gateway process to pick up `.env` changes.
5. Verify `/v1/capabilities` using an `Authorization` header with the active Bearer token from the LAN IP.
6. Also verify a wrong Bearer token fails with `401`, so success is not caused by an unprotected endpoint.

Important finding: Hermes API Server capabilities advertised bearer authentication. Supplying the same token through `X-API-Key` produced `401 invalid_api_key`, while the `Authorization` header with a Bearer token produced HTTP 200.

Avoid preserving real API keys in this reference. Use placeholders such as `<API_SERVER_KEY>`.
