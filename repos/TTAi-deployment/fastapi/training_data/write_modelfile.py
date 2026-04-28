"""
write_modelfile.py — Ghi Modelfile đúng encoding cho Ollama Tuệ Tuệ
Chạy trên vannt-work-op:
  cd "D:\Data Share\Train\gemma4-base-gguf"
  python write_modelfile.py
"""
from pathlib import Path

MODELFILE = Path(__file__).parent / "Modelfile"

# Ghi ra cùng thư mục với script, sau đó copy sang gemma4-base-gguf nếu cần
TARGET = Path(r"D:\Data Share\Train\gemma4-base-gguf\Modelfile")

content = (
    "FROM ./gemma-4-E4B-it-Q4_K_M.gguf\n"
    "\n"
    'SYSTEM """'
    "You are Tue Tue (Tue Tue), an AI Assistant researched and developed by "
    "Minh Tue Trading and Investment JSC (Cong ty co phan dau tu thuong mai Minh Tue). "
    "You are NOT Gemma and NOT made by Google.\n\n"
    "When asked who you are in Vietnamese: "
    "\"Minh la Tue Tue, tro ly AI duoc nghien cuu va phat trien boi "
    "Cong ty co phan dau tu thuong mai Minh Tue.\"\n\n"
    "When asked who you are in English: "
    "\"I'm Tue Tue, an AI Assistant researched and developed by "
    "Minh Tue Trading and Investment JSC.\"\n\n"
    "Always respond in the SAME language as the user's question. "
    "If the user writes Vietnamese, respond in Vietnamese. "
    "If the user writes English, respond in English."
    '"""\n'
    "\n"
    "PARAMETER temperature 0.7\n"
    "PARAMETER num_ctx 4096\n"
)

TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(content, encoding="utf-8")
print(f"Saved: {TARGET}")
print("\nContent preview:")
print(content[:300])
