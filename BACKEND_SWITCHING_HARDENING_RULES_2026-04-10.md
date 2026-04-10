# Backend Switching Hardening Rules — 2026-04-10

## Why this exists
The 8075 migration work showed that changing retrieval backends is not truly easy unless runtime design, observability, and cutover procedures are intentionally simple.

A backend switch should feel boring.
If it feels like forensics, the design is too coupled.

---

## Core principle
A public service surface should be stable.
Backend internals should be replaceable.
The runtime must prove what it is actually doing.

---

## Rule 1 — Stable public compatibility surface
Every live backend-switchable service should expose a stable public API surface whose contract changes rarely.

For 8075, that means:
- `GET /health`
- `GET /stats`
- `POST /search`
- `POST /context`

Changing internal retrieval logic must not require downstream caller rewrites unless explicitly planned.

---

## Rule 2 — Build identity must be observable
Every service should expose an endpoint that proves the exact code revision/build currently running.

Minimum required fields:
- build marker
- code revision / git commit if available
- loaded file path
- PID
- current working directory
- service mode
- active backend

Without this, operators waste time guessing whether the running process matches the edited source.

---

## Rule 3 — Config must be observable, not just settable
If a backend is selected by environment variables, the service must expose the effective values it is actually reading at runtime.

Minimum required fields:
- raw backend env value
- raw service-mode env value
- normalized backend selection
- active backend after fallback logic

---

## Rule 4 — Backend switching must be proof-able
A successful backend switch is not:
- "I set an env var"
- "the service restarted"

A successful backend switch is only confirmed when the service proves:
- active backend = intended backend
- build marker = expected code build
- health remains good
- contract endpoints still work

---

## Rule 5 — Never let backend failure kill the whole service surface
A backend failure should degrade behavior, not erase the public API surface.

Preferred behavior:
- service still boots
- health exposes backend error state
- active backend reflects fallback mode
- callers continue receiving controlled responses

---

## Rule 6 — Cutovers need preflight and rollback
Before any live flip:
- run preflight import/boot validation
- verify service entrypoint
- verify backend compatibility shape
- define rollback path

After flip:
- verify health
- verify runtime-info/build-proof
- verify key functional endpoints
- verify caller behavior

---

## Rule 7 — Runtime/service/ingest concerns must be explicitly separated
Do not blur these concerns:
- public API surface
- backend selection
- service registration
- ingest/index refresh
- storage/collection identity

Each must be inspectable separately.

---

## Rule 8 — A switchable backend needs a dedicated runtime-info endpoint
Recommended endpoint set for any switchable service:
- `/health`
- `/compatibility`
- `/runtime-info`
- `/build-proof`

This reduces debugging time dramatically.

---

## Rule 9 — If a change requires forensics, turn the lesson into structure
When a migration becomes unexpectedly difficult, do not just patch through it.
Capture the reason in architecture rules and tooling so the next migration becomes routine.

---

## Rule 10 — Favor boring migrations
The best backend switch is one where:
- config change is tiny
- restart is clean
- proof is immediate
- rollback is obvious
- callers do not notice

That is the target design standard going forward.

---

## Bottom line
A backend switch should be an operationally boring act.
If it turns into detective work, the service needs more runtime observability and looser coupling.
