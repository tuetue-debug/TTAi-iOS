"""
Generate SFT training data for Trợ lý Tuệ Tuệ fine-tuning.

Pipeline:
  1. Load Vietnamese news from HuggingFace (binhvq_news_vi)
  2. Filter financial/price articles (xăng, vàng, tỷ giá, chứng khoán...)
  3. Generate synthetic QA pairs via OpenAI API (GPT-4o-mini, cheap)
  4. Load thumbs_up feedback samples from chat.db
  5. Mix all → export ShareGPT JSONL ready for Unsloth/LlamaFactory

Usage:
  pip install datasets openai tqdm
  OPENAI_API_KEY=sk-... python generate_training_data.py

Output: training_data/tuetue_sft_v1.jsonl
"""
from __future__ import annotations

import json
import os
import random
import re
import sqlite3
import time
from pathlib import Path
from typing import Iterator

from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

DB_PATH = Path(__file__).parent / "data" / "chat.db"
OUT_DIR = Path(__file__).parent / "training_data"
OUT_FILE = OUT_DIR / "tuetue_sft_v1.jsonl"

# Target counts per category
TARGET_NEWS_QA = 500       # synthetic from news articles
TARGET_BRAND_CHAT = 300    # brand voice conversations
TARGET_NEGATIVE = 200      # refusal / no-hallucinate examples
MAX_FEEDBACK_SAMPLES = 500 # cap on real feedback data

SYSTEM_PROMPT = (
    "Bạn là Trợ lý Tuệ Tuệ - Giá trị là của bạn. "
    "Hãy trả lời chính xác, ngắn gọn, và thân thiện. "
    "Khi trả lời có số liệu, luôn ghi rõ đơn vị (đồng/lít, đồng/chỉ, VNĐ/USD, %...) "
    "và trích dẫn nguồn [1],[2]... nếu có."
)

# Financial / price keywords for article filtering
PRICE_KEYWORDS = [
    "giá xăng", "giá dầu", "giá điện", "giá gas",
    "giá vàng", "giá bạc", "vàng SJC", "giá nhẫn",
    "tỷ giá", "giá đô", "USD/VND", "EUR/VND",
    "chứng khoán", "VN-Index", "cổ phiếu",
    "lãi suất", "lạm phát", "CPI",
    "giá thịt heo", "giá gạo", "giá xi măng",
    "điều chỉnh giá", "tăng giá", "giảm giá", "kỳ điều chỉnh",
]


# ── OpenAI helper ─────────────────────────────────────────────────────────────

def _openai_chat(messages: list[dict], temperature: float = 0.7) -> str:
    """Call OpenAI API. Falls back to empty string on error."""
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [OpenAI error] {e}")
        return ""


# ── Dataset loaders ────────────────────────────────────────────────────────────

def _stream_hf_articles(result_box: list, max_articles: int):
    """Worker chạy trong thread riêng để tránh hang trên Windows."""
    try:
        from datasets import load_dataset
        ds = load_dataset("vietgpt/binhvq_news_vi", split="train", streaming=True)
        seen: set = set()
        for row in ds:
            if len(result_box) >= max_articles:
                break
            title = row.get("title", "") or ""
            content = row.get("content", "") or ""
            text = (title + " " + content[:2000]).lower()
            if not any(kw in text for kw in PRICE_KEYWORDS):
                continue
            key = title[:80]
            if key in seen:
                continue
            seen.add(key)
            result_box.append({"title": title, "content": content[:1500]})
    except Exception as e:
        result_box.append({"__error__": str(e)})


def load_news_articles(max_articles: int = 5000, timeout: int = 90) -> list[dict]:
    """Load Vietnamese news từ HuggingFace với timeout an toàn trên Windows."""
    import threading
    print(f"Loading binhvq_news_vi từ HuggingFace (timeout {timeout}s)...")
    result_box: list = []
    t = threading.Thread(target=_stream_hf_articles, args=(result_box, max_articles), daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        print("  [Timeout] HuggingFace load quá chậm — bỏ qua, sinh data không cần HF.")
        return []

    # Lọc error marker nếu có
    articles = [a for a in result_box if "__error__" not in a]
    if len(articles) < len(result_box):
        err = next((a["__error__"] for a in result_box if "__error__" in a), "unknown")
        print(f"  [HF error] {err}")

    print(f"  → {len(articles)} price-related articles found")
    return articles


def load_feedback_samples() -> list[dict]:
    """Load thumbs_up=1 samples from chat.db feedback_samples table."""
    if not DB_PATH.exists():
        print(f"  [DB not found] {DB_PATH}")
        return []
    try:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(
            "SELECT question, response, model_used FROM feedback_samples "
            "WHERE user_thumbs_up = 1 AND response != '' "
            "ORDER BY created_at DESC LIMIT ?",
            (MAX_FEEDBACK_SAMPLES,)
        ).fetchall()
        conn.close()
        print(f"  → {len(rows)} thumbs_up feedback samples")
        return [{"question": r[0], "response": r[1], "model": r[2]} for r in rows]
    except Exception as e:
        print(f"  [DB error] {e}")
        return []


# ── Sample generators ─────────────────────────────────────────────────────────

def gen_news_qa_sample(article: dict) -> dict | None:
    """Generate a QA pair from a news article about prices."""
    title = article["title"]
    content = article["content"]

    prompt = f"""Từ đoạn bài báo tiếng Việt dưới đây, hãy tạo ra 1 cặp hỏi-đáp theo định dạng JSON.

Yêu cầu:
- "question": câu hỏi tự nhiên mà người dùng có thể hỏi về nội dung bài báo
- "answer": câu trả lời ngắn gọn, trích xuất TẤT CẢ con số cụ thể (giá, %), ghi rõ đơn vị, trích nguồn [1]
- Nếu bài không có số liệu cụ thể, trả về {{"skip": true}}

Tiêu đề: {title}
Nội dung: {content[:800]}

Chỉ trả về JSON, không giải thích thêm:"""

    resp = _openai_chat([{"role": "user", "content": prompt}], temperature=0.5)
    if not resp:
        return None
    try:
        data = json.loads(resp.strip().strip("```json").strip("```"))
        if data.get("skip"):
            return None
        q = data.get("question", "").strip()
        a = data.get("answer", "").strip()
        if not q or not a or len(a) < 30:
            return None
        return _make_sample(
            user=q,
            assistant=a,
            context=f"[1] {title}\n{content[:600]}",
        )
    except json.JSONDecodeError:
        return None


def gen_brand_voice_samples() -> list[dict]:
    """Generate brand-consistent conversation samples."""
    scenarios = [
        ("Tuệ Tuệ là ai?",
         "Tôi là Trợ lý Tuệ Tuệ - Giá trị là của bạn, được phát triển bởi Minh Tuệ. "
         "Tôi giúp bạn tra cứu thông tin, giải đáp câu hỏi và hỗ trợ công việc hàng ngày."),
        ("Bạn có thể làm gì cho tôi?",
         "Tôi có thể giúp bạn: tra cứu giá cả thị trường, tìm kiếm thông tin mới nhất, "
         "giải thích khái niệm, hỗ trợ viết lách và phân tích dữ liệu. Bạn cần tôi giúp gì?"),
        ("Thông tin bạn cung cấp có chính xác không?",
         "Tôi luôn cố gắng cung cấp thông tin chính xác nhất. Với dữ liệu thời gian thực "
         "(giá cả, tỷ giá), tôi tìm kiếm từ các nguồn báo uy tín và trích dẫn rõ ràng. "
         "Với thông tin có thể thay đổi nhanh, tôi khuyên bạn nên kiểm tra thêm từ nguồn chính thức."),
        ("Cảm ơn bạn đã giúp đỡ",
         "Rất vui được hỗ trợ bạn! Nếu còn câu hỏi nào, cứ hỏi tôi nhé. "
         "Giá trị là của bạn — Tuệ Tuệ luôn sẵn sàng!"),
        ("Bạn có thể tìm giá vàng hôm nay không?",
         "Được, để tôi tìm kiếm thông tin mới nhất cho bạn..."),
        ("Ai tạo ra bạn?",
         "Tôi được phát triển bởi đội ngũ Minh Tuệ — Công ty Cổ phần Đầu tư Thương mại Minh Tuệ, "
         "với triết lý 'Giá trị là của bạn'."),
    ]
    samples = []
    for user_msg, assistant_msg in scenarios:
        samples.append(_make_sample(user=user_msg, assistant=assistant_msg))
    return samples


def gen_no_hallucinate_samples() -> list[dict]:
    """Teach model NOT to make up units or numbers."""
    examples = [
        (
            "Giá xăng hiện tại là bao nhiêu?",
            "Tôi đang tìm kiếm thông tin mới nhất. Nếu bạn cần số liệu chính xác ngay, "
            "vui lòng kiểm tra tại petrolimex.com.vn hoặc pvoil.com.vn.",
        ),
        (
            "[Bài báo: Xăng RON95 tăng 500 đồng/lít]\nGiá xăng tăng bao nhiêu?",
            "Theo bài báo [1]: Xăng RON95 tăng **500 đồng/lít**.",
        ),
        (
            "[Bài báo: Vàng SJC 85,5 triệu đồng/lượng]\nGiá vàng SJC là bao nhiêu?",
            "Theo [1]: Vàng SJC hiện ở mức **85,5 triệu đồng/lượng**.",
        ),
        (
            "Tỷ giá USD/VND là bao nhiêu?",
            "Tỷ giá USD/VND thay đổi liên tục. Để có số liệu chính xác nhất, "
            "bạn có thể kiểm tra tại Vietcombank hoặc NHNN Việt Nam.",
        ),
        (
            "[Bài báo: Tỷ giá USD/VND tại Vietcombank: mua 25.100, bán 25.200]\n"
            "Tỷ giá mua đô là bao nhiêu?",
            "Theo Vietcombank [1]:\n- Mua: **25.100 VNĐ/USD**\n- Bán: **25.200 VNĐ/USD**",
        ),
    ]
    samples = []
    for user_msg, assistant_msg in examples:
        samples.append(_make_sample(user=user_msg, assistant=assistant_msg))
    return samples


def feedback_to_sample(fb: dict) -> dict:
    """Convert a thumbs_up feedback row to a training sample."""
    return _make_sample(user=fb["question"], assistant=fb["response"])


# ── Format helper ─────────────────────────────────────────────────────────────

def _make_sample(user: str, assistant: str, context: str = "") -> dict:
    """Create a ShareGPT-format training sample."""
    user_content = f"{context}\n\n{user}".strip() if context else user
    return {
        "system": SYSTEM_PROMPT,
        "conversations": [
            {"from": "human", "value": user_content},
            {"from": "assistant", "value": assistant},
        ],
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(exist_ok=True)
    all_samples: list[dict] = []

    # 1. Fixed brand voice samples
    print("\n[1/4] Generating brand voice samples...")
    brand = gen_brand_voice_samples()
    all_samples.extend(brand)
    print(f"  → {len(brand)} brand samples")

    # 2. No-hallucinate / unit-correct samples
    print("\n[2/4] Generating no-hallucinate samples...")
    negative = gen_no_hallucinate_samples()
    all_samples.extend(negative)
    print(f"  → {len(negative)} negative samples")

    # 3. Feedback samples from real users
    print("\n[3/4] Loading feedback samples from chat.db...")
    feedbacks = load_feedback_samples()
    for fb in feedbacks[:MAX_FEEDBACK_SAMPLES]:
        all_samples.append(feedback_to_sample(fb))
    print(f"  → {len(feedbacks)} feedback samples added")

    # 4. Synthetic QA — từ bài báo HF hoặc fallback topic-based nếu HF không load được
    if OPENAI_API_KEY:
        print("\n[4/4] Generating synthetic QA (OpenAI API)...")
        articles = load_news_articles(max_articles=TARGET_NEWS_QA * 3, timeout=90)
        random.shuffle(articles)
        success = 0

        if articles:
            # Mode A: QA từ bài báo HF
            for article in tqdm(articles, desc="  Generating QA from articles"):
                if success >= TARGET_NEWS_QA:
                    break
                sample = gen_news_qa_sample(article)
                if sample:
                    all_samples.append(sample)
                    success += 1
                time.sleep(0.3)
            print(f"  → {success} news QA samples generated")
        else:
            # Mode B: fallback — OpenAI tự sinh Q&A theo chủ đề, không cần HF
            print("  HF không load được → sinh topic-based QA trực tiếp...")
            TOPICS = [
                "giá xăng RON95 và E5 tại Việt Nam kỳ điều chỉnh gần nhất",
                "giá vàng SJC và vàng nhẫn 9999 hiện tại",
                "tỷ giá USD/VND tại các ngân hàng thương mại lớn",
                "giá điện sinh hoạt bậc thang tại Việt Nam",
                "lãi suất tiết kiệm ngân hàng kỳ hạn 6-12 tháng",
                "chỉ số VN-Index và biến động thị trường chứng khoán",
                "giá gas LPG bình 12kg tại các đại lý",
                "giá thịt heo, gà, bò tại các chợ và siêu thị",
                "lạm phát CPI Việt Nam và tác động đến tiêu dùng",
                "giá bất động sản căn hộ tại Hà Nội và TP.HCM",
            ]
            for topic in tqdm(TOPICS * (TARGET_NEWS_QA // len(TOPICS) + 1), desc="  Generating topic QA"):
                if success >= TARGET_NEWS_QA:
                    break
                prompt = (
                    f"Hãy tạo 1 cặp hỏi-đáp tiếng Việt về chủ đề: '{topic}'.\n"
                    f"Định dạng JSON: {{\"question\": \"...\", \"answer\": \"...\"}}\n"
                    f"Yêu cầu: câu trả lời ngắn gọn, thực tế, có đơn vị rõ ràng nếu là số liệu. "
                    f"Không bịa số liệu cụ thể — nói rõ đây là ví dụ minh họa nếu không có dữ liệu thực.\n"
                    f"Chỉ trả về JSON."
                )
                resp = _openai_chat([{"role": "user", "content": prompt}], temperature=0.7)
                if not resp:
                    continue
                try:
                    data = json.loads(resp.strip().strip("```json").strip("```"))
                    q = data.get("question", "").strip()
                    a = data.get("answer", "").strip()
                    if q and a and len(a) > 20:
                        all_samples.append(_make_sample(user=q, assistant=a))
                        success += 1
                except json.JSONDecodeError:
                    pass
                time.sleep(0.3)
            print(f"  → {success} topic-based QA samples generated")
    else:
        print("\n[4/4] Skipping news QA (set OPENAI_API_KEY to enable)")

    # Shuffle and write
    random.shuffle(all_samples)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for s in all_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"\n{'='*50}")
    print(f"Total samples: {len(all_samples)}")
    print(f"Output: {OUT_FILE}")
    print(f"{'='*50}")
    print("\nNext steps:")
    print("  1. Review a few samples: head -5 training_data/tuetue_sft_v1.jsonl | python -m json.tool")
    print("  2. Upload to training server (vannt-work-op) with RTX 5060 Ti")
    print("  3. Fine-tune: python train_tuetue.py \\")
    print("                  --data training_data/tuetue_sft_v1.jsonl \\")
    print("                  --output tuetue-gemma4-e4b-v1 --epochs 1 --batch 2")
    print("  4. Export GGUF: ollama create tuetue4:e4b -f Modelfile")


if __name__ == "__main__":
    main()
