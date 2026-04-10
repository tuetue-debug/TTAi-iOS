# TTAi Simple Proxy Safe Restore Plan — 2026-04-10

## Mục tiêu
Lập kế hoạch restore `TTAiSimpleProxy` (8015) theo cách an toàn, có giám sát, có rollback, và nằm dưới quyền điều khiển của Control Dashboard.

---

# I. Restore philosophy

## Không restore vì nostalgia
Mục tiêu không phải là “bật lại như cũ”.
Mục tiêu là:
- restore có kiểm soát
- đo được
- tắt được
- đổi mode được
- rollback được
- dashboard control quản được

---

# II. Preconditions before restore

## Must-have
1. WordPress target path must be understood
2. Backend pool redesign must be accepted
3. Home node load stance must be accepted
4. Dashboard control plan for 8015 must be defined

## Strongly recommended
5. local Ollama stance clarified
6. 8005 stance clarified
7. degraded/maintenance behavior defined

---

# III. Safe restore scope

## Initial restore scope
Restore 8015 only as:
- a lightweight routing front door
- with a reduced backend pool
- with hedge conservative or off
- with no blind auto-recovery

## Initial backend pool
- `localhost:8000`
- `100.89.201.7:8000`

## Excluded at first restore
- `localhost:8005`

---

# IV. Suggested restore modes

## Mode A — `stabilize`
### Settings
- backends: local 8000 + remote 8000
- preferred: local 8000 or remote 8000 depending test goal
- hedge: OFF
- auto-recovery: OFF
- verbose logs: ON

### Purpose
- verify 8015 process health
- verify WordPress path compatibility
- verify route telemetry

## Mode B — `balanced-lite`
### Settings
- backends: local 8000 + remote 8000
- preferred: remote 8000
- hedge: optional conservative
- auto-recovery: OFF

### Purpose
- production-like behavior without reviving old heavy local path

---

# V. Restore steps

## Step 1 — Prepare config
- remove or disable `localhost:8005` from active pool
- disable auto-recovery trigger
- set startup mode to `stabilize`
- expose runtime proof endpoints if possible

## Step 2 — Start 8015 manually / controlled
- do not immediately lock into always-on production role
- verify:
  - `/`
  - `/health`
  - runtime state

## Step 3 — Test direct chat through 8015
- send test request to `8015/api/chat`
- observe selected backend
- observe latency
- observe errors

## Step 4 — Dashboard integration validation
- dashboard sees 8015 status
- dashboard sees backend pool
- dashboard can toggle mode or at least read current mode

## Step 5 — WordPress integration test
- temporarily point WordPress to 8015 if needed
- test end-to-end chat
- monitor logs and route decisions

## Step 6 — Decide whether 8015 stays active
If stable and useful, keep.
If not, rollback and use 8000 direct path temporarily.

---

# VI. Rollback plan

## If restore fails
1. stop 8015
2. remove WordPress dependency on 8015
3. point WordPress back to safe path (`8000/api/chat`)
4. preserve logs for analysis

## If 8015 increases load unexpectedly
1. disable hedge
2. keep reduced pool
3. if still bad, stop 8015

---

# VII. Dashboard control requirements after restore

## Minimum required
Dashboard must show:
- 8015 up/down
- backend pool
- healthy/unhealthy backend state
- current mode
- recent route errors

## Target required
Dashboard must control:
- enable/disable 8015
- backend enable/disable
- preferred backend
- hedge on/off
- mode switch
- maintenance mode

---

# VIII. Success criteria

## Safe restore success means:
- 8015 runs without raising home node pressure significantly
- WordPress can use it successfully
- route decisions are observable
- rollback is simple
- dashboard has visibility into it

## Safe restore does NOT mean:
- merely that port 8015 is listening

---

# IX. Strategic recommendation

Do not restore `TTAiSimpleProxy` as a legacy load balancer.
Restore it as a **dashboard-governed routing module**.

That distinction is the difference between:
- bringing back old complexity
and
- building the next correct phase.
