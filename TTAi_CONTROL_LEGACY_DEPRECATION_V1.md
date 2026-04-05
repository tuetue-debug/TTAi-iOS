# TTAi Control Legacy Deprecation V1

_Last updated: 2026-04-05_

## Decision
The legacy control/dashboard experience is now deprecated as the primary operator path.

## Primary Control Surface (Now)
- `https://control.tuetue.vn`
- Backed by FastAPI control frontend at `/control/`
- Protected by `/control-login` + cookie-backed control session

## Deprecated As Primary
The following should no longer be treated as the main admin/operator destination:
- WordPress-centric control entrypoints
- Legacy `/admin/dashboard-control` assumptions
- Any reverse-proxy rule that sends `control.tuetue.vn` to the older portal/dashboard app

## Rationale
- Clear separation between public site, control plane, and backend core
- Admin/operator work now lives in the dedicated FastAPI control surface
- Avoid confusion from two dashboards showing different states

## Operator Guidance
- If someone asks for the control dashboard, send them to `control.tuetue.vn`
- If old admin/dashboard pages are still reachable, treat them as legacy references only
- Do not use old dashboard output as the canonical source when the new control dashboard is available
