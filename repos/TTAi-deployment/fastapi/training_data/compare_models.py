"""
compare_models.py — So sánh 3 model song song
Chạy trên vannt-work-op:
  python compare_models.py

So sánh:
  1. gemma4:e4b       — base model, không fine-tune
  2. tuetue4:e4b      — v1 (base GGUF + Modelfile system prompt)
  3. tuetue4:e4b-v2   — v2 (bf16 LoRA, identity baked in)
"""
from __future__ import annotations
import json, time, sys, urllib.request
from pathlib import Path

BASE_URL = "http://localhost:11434"
TIMEOUT  = 90

MODELS = [
    ("gemma4:e4b",      "Base (no fine-tune)"),
    ("tuetue4:e4b",     "v1 (Modelfile prompt)"),
    ("tuetue4:e4b-v2",  "v2 (bf16 LoRA baked-in)"),
]

# ── Test cases — trọng tâm nhất cho so sánh ──────────────────────────────────
CASES = [
    # Identity VI
    {"id": "A01", "group": "Identity-VI",
     "prompt": "Bạn là ai?",
     "expect_contains": ["Tuệ Tuệ"],
     "expect_not_contains": ["Gemma", "Google"]},
    {"id": "A02", "group": "Identity-VI",
     "prompt": "Ai tạo ra bạn?",
     "expect_contains": ["Minh Tuệ"],
     "expect_not_contains": ["Google", "DeepMind"]},
    {"id": "A03", "group": "Identity-VI",
     "prompt": "Bạn có phải là Gemma không?",
     "expect_not_contains": ["Gemma 4", "Google DeepMind"],
     "expect_contains_any": ["không", "Tuệ Tuệ"]},

    # Identity EN
    {"id": "A04", "group": "Identity-EN",
     "prompt": "Who are you?",
     "expect_contains": ["Tue Tue"],
     "expect_not_contains": ["Gemma", "Google"]},
    {"id": "A05", "group": "Identity-EN",
     "prompt": "Who made you?",
     "expect_contains": ["Minh Tue"],
     "expect_not_contains": ["Google", "DeepMind"]},
    {"id": "A06", "group": "Identity-EN",
     "prompt": "Are you Gemma?",
     "expect_not_contains": ["Yes, I am Gemma", "I'm Gemma"],
     "expect_contains_any": ["No", "Tue Tue"]},

    # Language switching
    {"id": "L01", "group": "Language",
     "prompt": "Explain what AI is in one sentence.",
     "expect_contains_any": ["intelligence", "Artificial", "AI"],
     "note": "Should respond in English"},
    {"id": "L02", "group": "Language",
     "prompt": "Giải thích AI là gì trong 1 câu.",
     "expect_contains_any": ["trí tuệ", "máy tính", "học"],
     "note": "Should respond in Vietnamese"},

    # Search decision
    {"id": "D01", "group": "Search",
     "system": 'You are a search decision agent. Return ONLY JSON: {"search": true/false, "query": "..."}',
     "prompt": "Giá vàng SJC hôm nay?",
     "expect_json": {"search": True}},
    {"id": "D02", "group": "Search",
     "system": 'You are a search decision agent. Return ONLY JSON: {"search": true/false, "query": "..."}',
     "prompt": "Python là gì?",
     "expect_json": {"search": False}},
    {"id": "D03", "group": "Search",
     "system": 'You are a search decision agent. Return ONLY JSON: {"search": true/false, "query": "..."}',
     "prompt": "Thời tiết Hà Nội ngày mai?",
     "expect_json": {"search": True}},
    {"id": "D04", "group": "Search",
     "system": 'You are a search decision agent. Return ONLY JSON: {"search": true/false, "query": "..."}',
     "prompt": "What is the current Bitcoin price?",
     "expect_json": {"search": True}},
    {"id": "D05", "group": "Search",
     "system": 'You are a search decision agent. Return ONLY JSON: {"search": true/false, "query": "..."}',
     "prompt": "How does recursion work?",
     "expect_json": {"search": False}},

    # Vietnamese quality
    {"id": "V01", "group": "VI-Quality",
     "prompt": "Giải thích Docker là gì?",
     "expect_contains": ["container"],
     "min_length": 80},
    {"id": "V02", "group": "VI-Quality",
     "prompt": "Viết hàm Python kiểm tra số nguyên tố.",
     "expect_contains": ["def ", "return"]},

    # Reasoning
    {"id": "R01", "group": "Reasoning",
     "prompt": "Nếu 1 con gà đẻ 1 quả trong 1.5 ngày, 6 con gà đẻ bao nhiêu quả trong 9 ngày?",
     "expect_contains": ["36"]},
    {"id": "R02", "group": "Reasoning",
     "prompt": "What comes next: 2, 6, 12, 20, 30, ?",
     "expect_contains": ["42"]},
]


def ask(model: str, prompt: str, system: str = "") -> tuple[str, float]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({
        "model": model, "messages": messages,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 300},
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data["message"]["content"].strip(), round(time.time() - t0, 1)
    except Exception as e:
        return f"[ERROR: {e}]", 0.0


def evaluate(case: dict, response: str) -> bool:
    for kw in case.get("expect_contains", []):
        if kw.lower() not in response.lower():
            return False
    for kw in case.get("expect_not_contains", []):
        if kw.lower() in response.lower():
            return False
    any_kws = case.get("expect_contains_any", [])
    if any_kws and not any(kw.lower() in response.lower() for kw in any_kws):
        return False
    if "min_length" in case and len(response) < case["min_length"]:
        return False
    if "expect_json" in case:
        try:
            raw = response.strip().strip("```json").strip("```").strip()
            parsed = json.loads(raw)
            for k, v in case["expect_json"].items():
                if parsed.get(k) != v:
                    return False
        except Exception:
            return False
    return True


def check_model_available(model: str) -> bool:
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            names = [m["name"] for m in data.get("models", [])]
            return any(model in n for n in names)
    except Exception:
        return False


def main():
    print(f"\n{'='*70}")
    print("  MODEL COMPARISON — Tuệ Tuệ vs Base Gemma4")
    print(f"{'='*70}")

    # Kiểm tra model nào đang available
    available = []
    for model, label in MODELS:
        ok = check_model_available(model)
        status = "✓" if ok else "✗ (not found)"
        print(f"  {status}  {model:<25} {label}")
        if ok:
            available.append((model, label))

    if not available:
        print("\n[ERROR] Không có model nào available. Kiểm tra ollama đang chạy.")
        sys.exit(1)

    print(f"\nChạy {len(CASES)} test cases trên {len(available)} model(s)...\n")

    # Collect results: results[model][case_id] = {ok, response, elapsed}
    all_results: dict[str, dict] = {m: {} for m, _ in available}

    for ci, case in enumerate(CASES, 1):
        print(f"[{ci:02d}/{len(CASES)}] {case['id']} ({case['group']}) — {case['prompt'][:55]}...")
        sys_prompt = case.get("system", "")
        for model, _ in available:
            resp, elapsed = ask(model, case["prompt"], sys_prompt)
            ok = evaluate(case, resp)
            all_results[model][case["id"]] = {"ok": ok, "elapsed": elapsed, "response": resp[:120]}
            mark = "✓" if ok else "✗"
            print(f"    {mark} {model:<25} {elapsed}s  {resp[:60].replace(chr(10),' ')}")
        print()

    # ── Summary table ─────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  {'CASE':<6} {'GROUP':<14}", end="")
    for model, _ in available:
        short = model.split(":")[1] if ":" in model else model
        print(f"  {short:<12}", end="")
    print()
    print(f"  {'-'*6} {'-'*14}", end="")
    for _ in available:
        print(f"  {'-'*12}", end="")
    print()

    group_pass: dict[str, dict[str, int]] = {}
    for case in CASES:
        cid = case["id"]
        grp = case["group"]
        print(f"  {cid:<6} {grp:<14}", end="")
        for model, _ in available:
            r = all_results[model].get(cid, {})
            mark = "✓" if r.get("ok") else "✗"
            print(f"  {mark:<12}", end="")
            if grp not in group_pass:
                group_pass[grp] = {m: 0 for m, _ in available}
            if r.get("ok"):
                group_pass[grp][model] += 1
        print()

    # Group totals
    group_counts = {}
    for case in CASES:
        group_counts[case["group"]] = group_counts.get(case["group"], 0) + 1

    print(f"\n{'='*70}")
    print("  GROUP SCORES")
    print(f"  {'GROUP':<20}", end="")
    for model, _ in available:
        short = model.split(":")[1] if ":" in model else model
        print(f"  {short:<14}", end="")
    print()
    for grp, counts in group_pass.items():
        total = group_counts[grp]
        print(f"  {grp:<20}", end="")
        for model, _ in available:
            p = counts.get(model, 0)
            print(f"  {p}/{total} ({p/total*100:.0f}%)    ", end="")
        print()

    # Overall
    print(f"\n{'='*70}")
    print(f"  {'OVERALL':<20}", end="")
    for model, _ in available:
        total = len(CASES)
        p = sum(1 for r in all_results[model].values() if r.get("ok"))
        short = model.split(":")[1] if ":" in model else model
        print(f"  {p}/{total} ({p/total*100:.0f}%)    ", end="")
    print()
    print(f"{'='*70}\n")

    # Save full results
    out_path = Path("compare_results.json")
    out_path.write_text(
        json.dumps({"models": [m for m, _ in available], "cases": CASES,
                    "results": all_results, "group_pass": group_pass},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  Chi tiết → {out_path}")


if __name__ == "__main__":
    main()
