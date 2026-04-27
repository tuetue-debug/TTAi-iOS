"""
generate_training_data_v2.py
Training data for search decision agent — Round 2.

Sources:
  A) HuggingFace: Trelis/function_calling_extended, glaiveai/glaive-function-calling-v2
  B) Synthetic: OpenAI generates VI + EN search decision pairs

Output: training_data/tuetue_sft_v2_search.jsonl
  Each line: {"messages": [{"role":"system",...}, {"role":"user",...}, {"role":"assistant",...}]}
"""

import json, os, re, sys, time
from pathlib import Path

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
except Exception:
    client = None

OUTPUT_FILE = Path(__file__).parent / "tuetue_sft_v2_search.jsonl"

# ── System prompt (must match chat_routes._DECISION_SYSTEM) ──────────────────
DECISION_SYSTEM = """You are a search decision agent. Analyze the question and return JSON.

Search web when the question asks about:
- Real-time prices: gold, USD, stock market, crypto, gas, oil, electricity
- News, events, latest results (today, this week, recently, latest...)
- Weather, epidemics, continuously updated information
- Sports scores, match results, standings
- Current laws, regulations, policies just announced

Do NOT search when:
- Theory, concept explanation, history, definitions
- Programming, math, writing, creative tasks
- System settings, how-to instructions
- General knowledge questions

Return ONLY JSON (no explanation):
{"search": true, "query": "optimized search query in the question's language"}
or
{"search": false, "query": ""}"""


def make_sample(question: str, search: bool, query: str) -> dict:
    answer = json.dumps({"search": search, "query": query}, ensure_ascii=False)
    return {
        "messages": [
            {"role": "system",    "content": DECISION_SYSTEM},
            {"role": "user",      "content": question},
            {"role": "assistant", "content": answer},
        ]
    }


# ── A: HuggingFace — Trelis/function_calling_extended ────────────────────────
SEARCH_FUNCTIONS = {
    "search_bing", "search_web", "web_search", "search_internet",
    "search_arxiv", "get_current_weather", "get_weather",
    "get_stock_price", "get_news", "get_latest_news",
}

def load_trelis(max_samples: int = 200) -> list[dict]:
    samples = []
    try:
        from datasets import load_dataset
        print("  Loading Trelis/function_calling_extended...")
        ds = load_dataset("Trelis/function_calling_extended", split="train", streaming=True)
        for row in ds:
            if len(samples) >= max_samples:
                break
            try:
                convs = row.get("conversations") or row.get("messages") or []
                # Find user turn
                user_msg = next((c["value"] for c in convs if c.get("from") == "human"), None)
                # Find function call turn
                fn_call = next((c["value"] for c in convs if c.get("from") == "gpt"), None)
                if not user_msg or not fn_call:
                    continue
                # Check if it calls a search function
                needs_search = any(fn in fn_call for fn in SEARCH_FUNCTIONS)
                # Extract query from function call if possible
                query_match = re.search(r'"query"\s*:\s*"([^"]+)"', fn_call)
                query = query_match.group(1) if query_match else (user_msg[:80] if needs_search else "")
                samples.append(make_sample(user_msg.strip(), needs_search, query))
            except Exception:
                continue
        print(f"  → {len(samples)} samples from Trelis")
    except Exception as e:
        print(f"  [Skip] Trelis: {e}")
    return samples


def load_glaive(max_samples: int = 300) -> list[dict]:
    samples = []
    try:
        from datasets import load_dataset
        print("  Loading glaiveai/glaive-function-calling-v2...")
        ds = load_dataset("glaiveai/glaive-function-calling-v2", split="train", streaming=True)
        for row in ds:
            if len(samples) >= max_samples:
                break
            try:
                system = row.get("system", "")
                chat   = row.get("chat", "")
                # Extract user message
                user_match = re.search(r'USER:\s*(.+?)(?=ASSISTANT:|$)', chat, re.DOTALL)
                if not user_match:
                    continue
                user_msg = user_match.group(1).strip()[:300]

                # Check if system defines search-like functions
                needs_search = any(fn in system for fn in SEARCH_FUNCTIONS)
                # Extract function call query
                query_match = re.search(r'"query"\s*:\s*"([^"]+)"', chat)
                query = query_match.group(1) if query_match else (user_msg[:80] if needs_search else "")
                samples.append(make_sample(user_msg, needs_search, query))
            except Exception:
                continue
        print(f"  → {len(samples)} samples from Glaive")
    except Exception as e:
        print(f"  [Skip] Glaive: {e}")
    return samples


# ── B: Synthetic via OpenAI ───────────────────────────────────────────────────
SYNTHETIC_TOPICS = {
    "vi_search": [
        # Thời tiết
        "Thời tiết Hà Nội ngày mai thế nào?",
        "Hôm nay ở TP.HCM có mưa không?",
        "Dự báo thời tiết tuần này ở Đà Nẵng",
        "Nhiệt độ hiện tại ở Hà Nội là bao nhiêu?",
        "Thời tiết cuối tuần này ở Huế ra sao?",
        # Giá cả
        "Giá vàng SJC hôm nay bao nhiêu?",
        "Tỷ giá USD/VND hiện tại là bao nhiêu?",
        "Giá xăng RON 95 hôm nay là bao nhiêu?",
        "Giá Bitcoin hôm nay bằng bao nhiêu đô?",
        "Giá điện sinh hoạt mới nhất 2026?",
        "VNIndex hôm nay đóng cửa ở mức nào?",
        "Giá dầu thô thế giới hôm nay?",
        # Tin tức
        "Tin tức mới nhất về bầu cử Mỹ 2026?",
        "Có sự kiện gì lớn ở Việt Nam hôm nay không?",
        "Kết quả bóng đá V-League vòng mới nhất?",
        "Dịch bệnh COVID-19 hiện nay ra sao?",
        "Luật thuế mới nhất ở Việt Nam 2026?",
        "Thị trường chứng khoán tuần này diễn biến thế nào?",
        # Không cần search
        "Python là gì?",
        "Giải thích thuật toán quick sort",
        "Viết cho tôi một bài thơ về mùa xuân",
        "Làm thế nào để học tiếng Anh hiệu quả?",
        "Lịch sử thành lập nước Việt Nam",
        "Giải phương trình bậc 2: x² - 5x + 6 = 0",
        "Viết hàm Python đọc file CSV",
        "Tôi cần giải thích về machine learning",
    ],
    "en_search": [
        # Weather
        "What's the weather like in New York tomorrow?",
        "Will it rain in London this weekend?",
        "Current temperature in Tokyo?",
        "Weather forecast for Paris next week?",
        # Finance
        "What is the current price of gold?",
        "How much is Bitcoin worth today?",
        "What is the EUR/USD exchange rate right now?",
        "NASDAQ closing price today?",
        "Apple stock price right now?",
        "Latest inflation rate in the US 2026?",
        # News & events
        "What happened in the news today?",
        "Latest sports scores from last night?",
        "Who won the Champions League match yesterday?",
        "Current status of the US-China trade talks?",
        "Latest COVID variant spreading in 2026?",
        "What are the top trending news today?",
        # No search needed
        "What is machine learning?",
        "Write a Python function to reverse a string",
        "Explain the concept of recursion",
        "What is the capital of France?",
        "How do I install Docker on Ubuntu?",
        "Write me a haiku about autumn",
        "What is the Pythagorean theorem?",
        "How do binary trees work?",
    ],
}

BATCH_PROMPT = """Given these questions, for each one return a JSON search decision.
Format: one JSON per line, in order.
{"search": true/false, "query": "optimized search query or empty string"}

Questions:
{questions}

Rules:
- search=true for: weather, real-time prices, breaking news, sports scores, current events
- search=false for: theory, programming help, math, writing, history, definitions
- query should be an optimized search engine query in the same language as the question
- Return exactly {n} lines of JSON, one per question."""


def generate_synthetic(topics: dict, samples_per_batch: int = 20) -> list[dict]:
    if not client or not client.api_key:
        print("  [Skip] No OPENAI_API_KEY")
        return []

    all_questions = []
    for category, questions in topics.items():
        all_questions.extend([(q, category) for q in questions])

    # Add more via GPT generation
    print("  Generating additional questions via OpenAI...")
    extra = _generate_extra_questions()
    all_questions.extend(extra)

    samples = []
    # Process in batches
    batch_size = 10
    for i in range(0, len(all_questions), batch_size):
        batch = all_questions[i:i+batch_size]
        questions_text = "\n".join(f"{j+1}. {q}" for j, (q, _) in enumerate(batch))
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": BATCH_PROMPT.format(
                    questions=questions_text, n=len(batch)
                )}],
                temperature=0,
                max_tokens=800,
            )
            raw = resp.choices[0].message.content.strip()
            lines = [l.strip() for l in raw.split("\n") if l.strip().startswith("{")]
            for (question, _), line in zip(batch, lines):
                try:
                    parsed = json.loads(line)
                    samples.append(make_sample(
                        question,
                        bool(parsed.get("search", False)),
                        str(parsed.get("query", "")).strip(),
                    ))
                except Exception:
                    continue
            time.sleep(0.3)
        except Exception as e:
            print(f"  [Batch error] {e}")
            continue

    print(f"  → {len(samples)} synthetic samples")
    return samples


def _generate_extra_questions() -> list[tuple[str, str]]:
    """Ask GPT to generate more diverse questions in VI + EN."""
    if not client:
        return []
    prompt = """Generate 60 diverse questions for a search-decision training dataset.
Mix of:
- 20 Vietnamese real-time questions (weather, prices, news, sports) needing web search
- 10 Vietnamese questions NOT needing search (theory, coding, math, writing)
- 20 English real-time questions needing web search
- 10 English questions NOT needing search

Format: one question per line, no numbering, no labels."""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1200,
        )
        lines = resp.choices[0].message.content.strip().split("\n")
        return [(l.strip(), "generated") for l in lines if l.strip() and len(l.strip()) > 5]
    except Exception as e:
        print(f"  [Extra questions error] {e}")
        return []


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("generate_training_data_v2.py — Search Decision Training")
    print("=" * 60)

    all_samples = []

    print("\n[A] Loading from HuggingFace...")
    all_samples += load_trelis(max_samples=200)
    all_samples += load_glaive(max_samples=300)

    print("\n[B] Generating synthetic (OpenAI)...")
    all_samples += generate_synthetic(SYNTHETIC_TOPICS)

    # Deduplicate by user message
    seen = set()
    unique = []
    for s in all_samples:
        key = s["messages"][1]["content"][:100]
        if key not in seen:
            seen.add(key)
            unique.append(s)

    print(f"\n{'='*60}")
    print(f"Total unique samples: {len(unique)}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for s in unique:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"Output: {OUTPUT_FILE}")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("  1. Review: python -c \"import json; [print(json.dumps(json.loads(l)['messages'][1]['content'][:80])) for l in open('training_data/tuetue_sft_v2_search.jsonl')][:10]\"")
    print("  2. Merge with v1 (optional): cat tuetue_sft_v1.jsonl tuetue_sft_v2_search.jsonl > tuetue_sft_combined.jsonl")
    print("  3. Train: python train_tuetue.py --data training_data/tuetue_sft_v2_search.jsonl --output tuetue-gemma4-e4b-v2 --epochs 2 --batch 2")


if __name__ == "__main__":
    main()
