# TTAi Serving Route Map / Serving Flow Map

_Last updated: 2026-04-14_

## Purpose
This document is the practical serving map for the current TTAi stack.

It has two jobs:
1. **Serving Route Map** — which HTTP routes exist, who uses them, and which ones are canonical vs compatibility.
2. **Serving Flow Map** — how a real request moves through FastAPI 8000, routing logic, provider groups, control UI state, and telemetry.

This file should describe the **actual current serving behavior**, not just the desired future architecture.

---

# Part A — Serving Route Map

## 1. Canonical serving surfaces

### Product / Runtime surface
- **Domain:** `api.tuetue.vn`
- **Primary runtime today:** FastAPI on port `8000`
- **Responsibility:** chat serving, classification, routing, telemetry, quota/billing hooks, provider dispatch

### Operator / Control surface
- **Domain:** `control.tuetue.vn`
- **Primary runtime today:** same FastAPI backend exposes control routes under `/control-api/*`
- **Responsibility:** operator visibility, routing controls, serving map controls, traffic split controls, remote ollama slot controls

### Developer / Portal surface
- **Domain:** `console.tuetue.vn`
- **Responsibility:** developer portal / signup / login / dashboard / future API key and billing self-service

### End-user chat surface
- **Domain:** `chat.tuetue.vn`
- **Responsibility:** end-user product chat UI (present/future product surface)

---

## 2. Public runtime API routes
Used by product clients and machine-facing callers.

### Chat
- Legacy: `POST /api/chat`
- Canonical: `POST /api/v1/chat`

### Classification
- Legacy: `POST /api/classify`
- Canonical: `POST /api/v1/classify`

- Legacy: `POST /api/classify/batch`
- Canonical: `POST /api/v1/classify/batch`

### Hybrid compatibility
- Legacy: `POST /api/hybrid/chat`
- Canonical: `POST /api/v1/hybrid/chat`

### Health
- Legacy: `GET /health`
- Canonical: `GET /api/v1/system/health`

- Legacy: `GET /health/detailed`
- Canonical: `GET /api/v1/system/health/detailed`

---

## 3. System / routing API routes
Used for runtime visibility and serving control.

### Load balancer visibility
- Legacy: `GET /api/loadbalancer/metrics`
- Canonical: `GET /api/v1/system/loadbalancer/metrics`

- Legacy: `GET /api/loadbalancer/providers`
- Canonical: `GET /api/v1/system/loadbalancer/providers`

### Provider enable / disable
- Legacy: `POST /api/loadbalancer/providers/{provider_name}/disable`
- Canonical: `POST /api/v1/system/loadbalancer/providers/{provider_name}/disable`

- Legacy: `POST /api/loadbalancer/providers/{provider_name}/enable`
- Canonical: `POST /api/v1/system/loadbalancer/providers/{provider_name}/enable`

### Models / runtime visibility
- Legacy: `GET /api/models/status`
- Canonical: `GET /api/v1/models/status`

- Legacy: `GET /api/models/status/{model_name}`
- Canonical: `GET /api/v1/models/status/{model_name}`

- Legacy: `POST /api/models/warmup/{model_name}`
- Canonical: `POST /api/v1/models/warmup/{model_name}`

- Legacy: `POST /api/models/warmup/all`
- Canonical: `POST /api/v1/models/warmup/all`

### Ollama runtime visibility
- Legacy: `GET /api/ollama/models`
- Canonical: `GET /api/v1/ollama/models`

- Legacy: `GET /api/ollama/health`
- Canonical: `GET /api/v1/ollama/health`

- Legacy: `POST /api/ollama/generate`
- Canonical: `POST /api/v1/ollama/generate`

- Legacy: `POST /api/ollama/chat`
- Canonical: `POST /api/v1/ollama/chat`

---

## 4. Control UI routes (`/control-api/*`)
Used by `control.tuetue.vn` operator UI.

### Core control pages / summaries
- `GET /control-api/models`
- `GET /control-api/system`
- `GET /control-api/topology`
- `GET /control-api/usage`
- `GET /control-api/errors`
- `GET /control-api/session`

### Serving control routes already wired into the map UI
- `GET /control-api/traffic-split`
- `PUT /control-api/traffic-split`

- `GET /control-api/remote-ollama`
- `PUT /control-api/remote-ollama/slots/{port}`

### Notes
- `traffic-split` is now a **real control path**, not visual-only.
- `remote-ollama` is now a **real state/control path by port** (`11434`, `11435`) at the FastAPI control-plane layer.
- These routes require a valid control session.

---

## 5. Usage / telemetry routes relevant to serving map

### Operator usage feed
- `GET /control-api/usage`

Important payload note:
- recent traffic events are returned in **`recent_events`**
- not in `events`

This matters because the Models page “Recent Model Traffic” panel binds to these normalized recent events.

---

# Part B — Serving Flow Map

## 6. Real serving flow (high-level)

```text
Client
  -> api.tuetue.vn
  -> FastAPI 8000
  -> classify request / determine routing path
  -> load balancer chooses provider group + provider
  -> provider executes
  -> usage event written
  -> control UI can observe result via /control-api/usage and load balancer metrics
```

---

## 7. Runtime decision layers

A live request through FastAPI 8000 currently passes these layers:

### Layer 1 — Request ingress
Main entry is the chat/runtime API:
- `POST /api/chat`
- canonical alias: `POST /api/v1/chat`

### Layer 2 — Query classification
FastAPI classifies the request for routing hints:
- complexity
- confidence
- language
- needs_context

This classification influences routing posture but does **not replace** operator-set serving controls.

### Layer 3 — Provider group routing
Serving is organized into 3 operator-facing groups in the map:

- **Core A** → Ollama group
- **Core B** → CLI Proxy group
- **Core C** → GPT fallback group

### Layer 4 — Provider selection inside each group
Once a group is selected, the load balancer chooses an enabled provider inside that group.

### Layer 5 — Telemetry / usage truth
The chosen provider, final route, model, status, processing time, fallback flags, and token estimates are written into usage events.

---

## 8. Current group mapping

### Core A — Ollama Group
Core A represents self-hosted Ollama capacity.

It includes:
- `OLLAMA_LOCAL`
- `OLLAMA_REMOTE`

Current logical providers under these groups include:
- local:
  - `gemma3:4b-local`
  - `qwen3:4b-local`
  - `deepseek-r1:8b-local`
- remote:
  - `gemma4:e4b-remote`
  - `gemma3:4b-remote`
  - `deepseek-r1:8b-remote`

### Core B — CLI Proxy
Core B represents cloud/CLI mediated serving.

Current providers:
- `cliproxy-deepseek`
- `cliproxy-gpt`
- `cliproxy-gemini`

### Core C — GPT Fallback
Core C represents direct fallback path.

Current provider:
- `gpt-5.2-direct`

---

## 9. Traffic Split control flow
The operator map now controls traffic split in a real way.

### UI behavior
In the Models map:
- Core A is editable
- Core B is editable
- Core C is auto-calculated as `100 - A - B`

### API path
- `GET /control-api/traffic-split`
- `PUT /control-api/traffic-split`

### Persistence
Saved in:
- `fastapi/data/traffic_split_state.json`

### Backend effect
The saved split is applied to provider groups:
- Core A percentage distributed across enabled Ollama providers
- Core B percentage distributed across enabled CLI Proxy providers
- Core C percentage assigned to GPT fallback provider(s)

### Important behavioral note
This is **group-weight control**, not a full rewrite of the internal routing engine.
That is intentional.

The control map changes the effective serving posture while preserving existing internal routing logic where possible.

---

## 10. Remote Ollama port control flow
This is the most important recent upgrade in the serving map.

### Why this exists
The map UI showed Remote Ollama as two ports:
- `11434`
- `11435`

Previously that was mostly visual.
Now it has real control-plane state.

### Control routes
- `GET /control-api/remote-ollama`
- `PUT /control-api/remote-ollama/slots/{port}`

### Persistence
Saved in:
- `fastapi/data/remote_ollama_state.json`

### State shape
Each remote slot tracks:
- `port`
- `model`
- `enabled`

Derived UI state also exposes:
- `healthy`
- `warm`
- `provider_name`
- `available_models`

### Current meaning
This currently controls the **FastAPI serving control-plane mapping**:
- slot `11434` selects which logical remote provider on port `11434` should be active
- slot `11435` selects which logical remote provider on port `11435` should be active
- selecting `off` disables that slot

### Important boundary
This is currently **true control of FastAPI routing state**, but not yet guaranteed full orchestration of the remote Ollama daemon itself.

In plain terms:
- FastAPI/load balancer state is real
- provider enable/disable is real
- operator UI mapping is real
- remote host model-serving orchestration is still a separate future layer

---

## 11. Current map state model
The operator map on the Models page now has real control value in these areas:

### Real control
- Traffic Split (A/B editable, C derived)
- Core status lights (group health view)
- Remote Ollama per-port model selection
- Remote Ollama per-port enable/off state
- Recent Model Traffic panel fed from real usage events

### Still partly visual / partially future-facing
- some local warm controls
- some warm-state indicators that currently reflect available health/control state more than deep runtime orchestration state

This distinction matters: the map is no longer mock UI, but not every pixel is yet backed by a fully remote-executed runtime action.

---

## 12. Recent Model Traffic data flow
The Models page includes a “Recent Model Traffic” panel.

### Actual data source
- `GET /control-api/usage`
- field: `recent_events`

### Source of truth behind it
Usage events are persisted in:
- `fastapi/data/usage_events.jsonl`

Typical event fields include:
- `timestamp`
- `provider`
- `model`
- `provider_type`
- `initial_provider`
- `final_provider`
- `final_model`
- `final_endpoint`
- `final_route_class`
- `fallback_used`
- `status`
- `http_status`
- `processing_time`

### Operator meaning
This panel is the easiest live proof that the serving map is actually being used.
It shows where recent requests really went.

---

## 13. Status light meaning in the map
Current Core A / B / C lights are intended to reflect operator-serving readiness at group level.

### Current rule
- green: at least one known provider in that group is healthy
- yellow: providers are known but none currently healthy
- gray: no health data / no recognized provider state

This is intentionally simpler than percentage-based health coloring.

---

## 14. Canonical interpretation of the serving map today

### The map is now an operator control surface
Not just a diagram.

### The map currently controls
- serving split between Core A / B / C
- remote ollama lane selection by port
- visible health posture at group level
- recent observed traffic path

### The map currently does not fully guarantee
- remote daemon-level model loading on the remote host for every slot change
- deep runtime orchestration parity for every warm indicator

That future layer should be added without changing the control-plane meaning already established here.

---

## 15. Migration / documentation rule going forward
When this map changes, update this file based on **actual runtime behavior**, not aspirational design.

That means:
- if a control is visual only, say so clearly
- if a control writes real state, name the route and state file
- if a control changes provider routing, state exactly how
- if a control does not yet reach the final remote runtime, say that explicitly

This file should stay trustworthy for operator work.
