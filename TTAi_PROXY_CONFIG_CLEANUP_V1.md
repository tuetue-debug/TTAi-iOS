# TTAi Proxy Config Cleanup V1

_Last updated: 2026-04-06_

## Summary
Completed a cleanup pass on live reverse-proxy configuration so the new TTAi control surface is easier to reason about and less likely to drift back toward legacy routing.

## Current Intent

### `control.tuetue.vn`
- Canonical entrypoint: `/control-login`
- Reverse proxy target: `http://127.0.0.1:8000`
- FastAPI is responsible for:
  - control login
  - control session auth
  - `/control/` frontend
  - `/control-api/*`

### `api.tuetue.vn`
- Canonical backend surface
- Reverse proxy target: `http://127.0.0.1:8000`

### `chat.tuetue.vn`
- Separate product surface
- Currently remains routed to `http://192.168.1.102:8080`

## Cleanup Actions Completed
- Simplified `control.tuetue.vn` block so it clearly points at local FastAPI
- Kept root redirect explicit: `/` -> `/control-login`
- Removed stale collector/legacy dashboard assumptions from the live control-domain proxy block
- Added comments so future edits are less likely to reintroduce the old pathing
- Ran `caddy fmt --overwrite` and reloaded Caddy successfully

## Operational Note
If `control.tuetue.vn` ever looks wrong again, first verify the proxy target has not drifted back to `192.168.1.102:8000` or another non-canonical app target.
