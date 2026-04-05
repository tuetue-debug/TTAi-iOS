# TTAi Control Domain Wiring V1

_Last updated: 2026-04-05_

## Goal
Move `control.tuetue.vn` to the new FastAPI-served control console instead of the legacy WordPress/old dashboard path.

## Target Routing

### `control.tuetue.vn`
Should point to FastAPI on port `8000` and use these application paths:
- `/` -> redirect/rewrite to `/control/`
- `/control/` -> new control frontend
- `/control-login` -> login screen for cookie-backed control session
- `/control-auth/*` -> control login/logout/session endpoints
- `/control-api/*` -> same-origin control data APIs (cookie-protected)

### `api.tuetue.vn`
Should continue pointing to FastAPI on port `8000` for backend APIs.

## Reverse Proxy Rule Shape

For `control.tuetue.vn`, the reverse proxy should:
1. Stop routing the root to `/admin/dashboard-control`
2. Rewrite `/` to `/control/`
3. Pass all other paths through to FastAPI on `192.168.1.102:8000`
4. Preserve cookies/headers normally

## Caddy Example

```caddy
control.tuetue.vn {
    encode gzip

    @root path /
    handle @root {
        redir /control/ 302
    }

    handle {
        reverse_proxy 192.168.1.102:8000
    }
}

api.tuetue.vn {
    encode gzip
    reverse_proxy 192.168.1.102:8000
}
```

## Notes
- The old collector-specific `control.tuetue.vn` routing is no longer the main path.
- The new control dashboard now reads through FastAPI `/control-api/*` endpoints.
- The browser should never need the raw admin bearer token after login; it should rely on the cookie-backed control session.
- WordPress should no longer be the default root target for `control.tuetue.vn`.

## Rollout Checklist
- [x] New control UI served by FastAPI at `/control/`
- [x] Cookie-backed auth boundary for `/control-api/*`
- [ ] Reverse proxy root for `control.tuetue.vn` changed to `/control/`
- [ ] Live test: `/control-login`
- [ ] Live test: login -> `/control/` -> data loads
- [ ] Confirm `api.tuetue.vn` still points to FastAPI
