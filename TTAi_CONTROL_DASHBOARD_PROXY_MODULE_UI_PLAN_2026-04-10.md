# TTAi Control Dashboard Proxy Module UI Plan — 2026-04-10

## Mục tiêu
Thiết kế UI module trên Control Dashboard để giám sát, benchmark và điều khiển `TTAiSimpleProxy` (8015).

---

# I. UI goals

Module UI phải cho phép operator nhìn là hiểu ngay:
- proxy có đang sống không
- nó đang route theo mode nào
- backend nào đang được ưu tiên
- proxy có đang làm chậm user query không
- có cần chuyển mode hoặc tắt backend nào không

---

# II. UI sections

## 2.1. Proxy status card
Hiển thị:
- service: running/stopped/degraded
- version/build
- current mode
- remote-first: on/off
- hedge: on/off
- current preferred backend

## 2.2. Backend pool table
Columns:
- backend name
- url
- role
- enabled
- healthy
- latency avg
- last error
- weight
- actions

Actions:
- enable/disable
- set preferred
- drain
- maintenance

## 2.3. Benchmark panel
Hiển thị:
- latest benchmark run time
- direct local avg
- direct remote avg
- proxy avg
- proxy overhead
- p50 / p95
- recommended mode

Buttons:
- Run quick benchmark
- Run full benchmark
- Compare direct vs proxy

## 2.4. Route telemetry panel
Hiển thị:
- last selected backends
- failover events
- hedge events
- degraded events
- route counts by backend

## 2.5. Control panel
Controls:
- mode selector
- remote-first toggle
- hedge toggle
- hedge delay input
- backend weight sliders
- proxy enable/disable
- restart proxy

---

# III. Recommended mode presets

## Preset 1 — Stabilize
- remote-first off or optional
- hedge off
- reduced pool
- safest path only

## Preset 2 — Remote-first
- remote preferred
- local fallback only
- hedge off initially

## Preset 3 — Balanced-lite
- remote preferred
- local safe fallback
- conservative hedge optional

## Preset 4 — Diagnostic
- verbose telemetry
- no blind auto-recovery
- detailed benchmark view

---

# IV. Visual priorities

## Highest priority signals
1. user latency impact
2. active backend choice
3. backend health
4. proxy overhead

## Lower priority signals
- build proof
- raw config details
- historic route distribution

---

# V. Key operator question mapping

## Operator asks:
### “Proxy có đang làm chậm chat không?”
UI should answer via:
- proxy overhead card
- direct vs proxy benchmark chart
- latest p95 delta

### “Có nên ưu tiên remote không?”
UI should answer via:
- remote latency card
- home pressure note
- recommended mode

### “Backend nào đang có vấn đề?”
UI should answer via:
- health badges
- last error text
- degraded counters

### “Có thể tắt local-heavy path không?”
UI should answer via:
- backend enable toggle
- active pool view

---

# VI. Next phase implementation hint

Ưu tiên build UI theo thứ tự:
1. proxy status card
2. backend pool table
3. benchmark panel
4. control panel
5. telemetry panel

This ensures immediate operational value before deeper polish.
