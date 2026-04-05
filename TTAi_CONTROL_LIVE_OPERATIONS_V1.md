# TTAi Control Live Operations V1

_Last updated: 2026-04-05_

## Live Surfaces

### `control.tuetue.vn`
- Purpose: internal operator/admin dashboard
- Live entrypoint: `https://control.tuetue.vn`
- Expected root behavior: redirect to `/control-login`
- Login target: `/control-login`
- Auth/session endpoints:
  - `/control-auth/login`
  - `/control-auth/logout`
  - `/control-auth/session`
- Main app path: `/control/`
- Data APIs: `/control-api/*`

### `api.tuetue.vn`
- Purpose: FastAPI backend/core API
- Reverse proxy target: local FastAPI on `127.0.0.1:8000`

## Control Login Flow
1. Open `https://control.tuetue.vn`
2. Browser is redirected to `/control-login`
3. Enter admin token
4. Server sets `ttai_control_session` cookie
5. Browser opens `/control/`
6. Frontend fetches `/control-api/*` using same-origin cookie session

## Logout Flow
- Use the top-right `Logout` button in the control UI
- This calls `POST /control-auth/logout`
- Browser returns to `/control-login`

## Reverse Proxy Notes
Current Caddy intent:
- `control.tuetue.vn` -> `127.0.0.1:8000`
- `api.tuetue.vn` -> `127.0.0.1:8000`
- `chat.tuetue.vn` remains separate

## Fallback / Troubleshooting
If `control.tuetue.vn` looks blank or wrong:
1. Check `https://control.tuetue.vn/control-login`
2. Confirm it returns the new TTAi Control login HTML (not the old portal app)
3. Verify Caddy target is `127.0.0.1:8000`, not `192.168.1.102:8000`
4. Reload Caddy:
   - `C:\caddy\caddy.exe reload --config C:\caddy\Caddyfile`
5. Verify local FastAPI:
   - `http://127.0.0.1:8000/control-login`

## Legacy Status
- Legacy WordPress/old dashboard path should no longer be considered the primary control surface.
- `control.tuetue.vn` now belongs to the FastAPI-served control dashboard.
- Old control/dashboard references should be treated as deprecated operator paths.
