# TTAi Proxy Phase C Build Plan — 2026-04-11

## Mục tiêu
Chạy benchmark thực tế để trả lời câu hỏi:
> **`8015` có làm chậm chat.tuetue.vn không?**

Phase C tập trung vào việc đo latency, throughput, và error rate của:
- direct local 8000
- direct remote 8000
- proxy 8015
- remote-first mode
- stabilize mode

Kết quả sẽ hiển thị trong Control Dashboard dưới dạng bảng và chart, giúp operator đưa ra quyết định restore 8015 hay không.

---

# I. Phase C scope

## In scope
### Benchmark runner
- chạy các test case với payload chat thật
- đo latency (response time)
- đo throughput (requests per second)
- đo error rate
- lưu kết quả vào store

### Benchmark data store
- lưu kết quả benchmark theo timestamp
- hỗ trợ query latest, top N, by mode

### Dashboard benchmark panel
- bảng kết quả benchmark
- chart overhead (proxy vs direct)
- recommendation summary

### Benchmark control
- trigger benchmark từ dashboard
- cancel benchmark đang chạy
- xem log real-time

## Out of scope
- automatic benchmark scheduling
- machine learning recommendation
- multi-node distributed benchmark
- advanced chart drill-down

---

# II. Design principle

## 2.1. Real-world payload
Benchmark phải dùng payload chat thật từ `chat.tuetue.vn` hoặc payload mẫu đại diện.

## 2.2. Isolate benchmark from production traffic
Benchmark runner phải chạy trong sandbox riêng, không ảnh hưởng đến traffic thật.

## 2.3. Dashboard is the control center
Operator trigger benchmark, xem kết quả, và đưa ra quyết định từ dashboard.

## 2.4. Remote-first vs stabilize comparison
Benchmark phải so sánh được remote-first mode vs stabilize mode.

---

# III. Files to create / update

## Create
### 1. `repos/TTAi-deployment/fastapi/proxy_benchmark_runner.py`
Purpose:
- chạy benchmark suite
- đo latency, throughput, error rate
- lưu kết quả vào store

### 2. `repos/TTAi-deployment/fastapi/proxy_benchmark_store.py`
Purpose:
- lưu kết quả benchmark
- query latest, top N, by mode

### 3. `repos/TTAi-deployment/fastapi/proxy_benchmark_models.py`
Purpose:
- Pydantic models cho benchmark request/response
- benchmark result model

## Update
### 4. `repos/TTAi-deployment/fastapi/proxy_benchmark.py`
Purpose:
- mở rộng để gọi runner
- expose latest benchmark results

### 5. `repos/TTAi-deployment/fastapi/main.py`
Add endpoints:
- `/control-api/proxy/benchmark/run`
- `/control-api/proxy/benchmark/status`
- `/control-api/proxy/benchmark/results`
- `/control-api/proxy/benchmark/cancel`

### 6. `repos/TTAi-deployment/control-frontend/app.js`
Add benchmark panel và controls.

---

# IV. Benchmark test cases

## 4.1. Test case definitions
Mỗi test case gồm:
- target (local, remote, proxy)
- mode (stabilize, remote-first)
- payload (chat message)
- concurrency (1, 2, 5)
- duration (10 seconds)

## 4.2. Suggested test matrix
| ID | Target | Mode | Concurrency | Description |
|----|--------|------|-------------|-------------|
| T1 | local 8000 | N/A | 1 | baseline direct local |
| T2 | remote 8000 | N/A | 1 | baseline direct remote |
| T3 | proxy 8015 | stabilize | 1 | proxy stabilize mode |
| T4 | proxy 8015 | remote-first | 1 | proxy remote-first mode |
| T5 | proxy 8015 | stabilize | 2 | concurrency 2 |
| T6 | proxy 8015 | remote-first | 2 | concurrency 2 |

## 4.3. Payload
Sử dụng payload chat thật:
```json
{
  "messages": [
    {"role": "user", "content": "Xin chào, bạn có thể giới thiệu về TTAi không?"}
  ],
  "model": "gemma3:4b-remote",
  "stream": false
}
```

---

# V. Benchmark runner design

## 5.1. Runner interface
```python
async def run_benchmark_suite(
    test_cases: List[BenchmarkTestCase],
    progress_callback: Optional[Callable] = None
) -> List[BenchmarkResult]:
```

## 5.2. Measurement
- latency: time từ request đến response
- throughput: requests per second
- error rate: số request fail / tổng request
- overhead: proxy latency - min(direct local, direct remote)

## 5.3. Concurrency handling
Sử dụng `asyncio` và `httpx` để chạy concurrent requests.

## 5.4. Progress reporting
Runner phải report progress real-time để dashboard hiển thị.

---

# VI. Benchmark store design

## 6.1. Storage
Sử dụng JSON file hoặc SQLite đơn giản.

### Suggested schema
```json
{
  "run_id": "uuid",
  "started_at": "timestamp",
  "completed_at": "timestamp",
  "status": "running|completed|failed|cancelled",
  "test_cases": [
    {
      "id": "T1",
      "target": "local-8000",
      "mode": null,
      "concurrency": 1,
      "requests": 50,
      "errors": 0,
      "latency_avg_ms": 120,
      "latency_p95_ms": 180,
      "throughput_rps": 8.3,
      "error_rate": 0.0
    }
  ],
  "summary": {
    "direct_local_latency": 120,
    "direct_remote_latency": 350,
    "proxy_stabilize_latency": 450,
    "proxy_remote_first_latency": 380,
    "overhead_stabilize": 330,
    "overhead_remote_first": 260,
    "recommendation": "proxy adds ~260ms overhead in remote-first mode"
  }
}
```

## 6.2. Query functions
- `get_latest_benchmark()`
- `get_benchmark_by_id(run_id)`
- `list_benchmarks(limit=10)`

---

# VII. New backend endpoints

## 7.1. Run benchmark
### Endpoint
`POST /control-api/proxy/benchmark/run`

### Request
```json
{
  "test_cases": ["T1", "T2", "T3", "T4"],
  "concurrency": 1,
  "duration_seconds": 10
}
```

### Response
```json
{
  "ok": true,
  "run_id": "uuid",
  "message": "Benchmark started"
}
```

## 7.2. Get benchmark status
### Endpoint
`GET /control-api/proxy/benchmark/status/{run_id}`

## 7.3. Get benchmark results
### Endpoint
`GET /control-api/proxy/benchmark/results/{run_id}`

## 7.4. Cancel benchmark
### Endpoint
`POST /control-api/proxy/benchmark/cancel/{run_id}`

## 7.5. List benchmarks
### Endpoint
`GET /control-api/proxy/benchmark/list?limit=10`

---

# VIII. Frontend implementation tasks

## 8.1. Benchmark panel
Thêm panel mới trong Overview hoặc tab riêng.

### Panel content
- Run benchmark button
- Progress bar
- Results table
- Overhead chart
- Recommendation summary

## 8.2. Chart library
Sử dụng Chart.js hoặc simple SVG chart.

## 8.3. Real-time updates
Sử dụng polling hoặc WebSocket để cập nhật progress.

---

# IX. Validation rules

## Test case IDs
Allowed values: `T1`, `T2`, `T3`, `T4`, `T5`, `T6`

## Concurrency
- integer
- between `1` and `10`

## Duration
- integer
- between `5` and `60` seconds

---

# X. Acceptance criteria

## Backend accepted when
- benchmark runner có thể chạy test suite
- kết quả được lưu vào store
- endpoint run/status/results/cancel hoạt động
- progress reporting real-time

## Frontend accepted when
- operator có thể trigger benchmark từ dashboard
- thấy progress real-time
- thấy bảng kết quả sau khi hoàn thành
- thấy chart overhead
- thấy recommendation summary

## Product accepted when
Operator có thể trả lời được câu hỏi:
> "8015 có làm chậm chat.tuetue.vn không?"

với số liệu thật:
- overhead bao nhiêu ms
- error rate tăng bao nhiêu
- nên restore 8015 không

---

# XI. Risks and mitigation

## Risk 1 — benchmark ảnh hưởng đến production traffic
Mitigation:
- giới hạn concurrency thấp
- duration ngắn
- payload nhẹ

## Risk 2 — benchmark runner bị treo
Mitigation:
- timeout mỗi test case
- cancel endpoint
- background task với state tracking

## Risk 3 — chart quá phức tạp
Mitigation:
- bắt đầu với simple table
- thêm chart đơn giản sau

---

# XII. Recommended next step after Phase C

Sau Phase C, dựa vào kết quả benchmark:
- quyết định restore 8015 hay không
- nếu restore, chọn mode nào (remote-first vs stabilize)
- điều chỉnh weight dựa trên benchmark

---

# XIII. Final statement

Phase C mang lại **data-driven decision** cho việc restore proxy.
Không còn phải đoán mò về performance overhead.
Dashboard sẽ có đủ thông tin để operator đưa ra quyết định đúng.
