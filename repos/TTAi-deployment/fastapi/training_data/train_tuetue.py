"""
Tuệ Tuệ SFT Training — Unsloth + QLoRA + Gemma4 E4B
Chạy trên vannt-work-op: RTX 5060 Ti 16GB VRAM

Usage:
  python train_tuetue.py --data tuetue_sft_v1.jsonl --output tuetue-gemma4-e4b-v1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# ── Args ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--data",   default="tuetue_sft_v1.jsonl", help="Input JSONL (ShareGPT format)")
parser.add_argument("--output", default="tuetue-gemma4-e4b-v1",  help="Output directory")
parser.add_argument("--epochs", type=int, default=1)
parser.add_argument("--batch",  type=int, default=2)
parser.add_argument("--lr",     type=float, default=2e-4)
args = parser.parse_args()

# ── Load model ────────────────────────────────────────────────────────────────
from unsloth import FastLanguageModel
import torch

MAX_SEQ_LEN = 2048
DTYPE = None         # auto-detect (bfloat16 on Ampere+)
LOAD_IN_4BIT = True  # QLoRA — fits 16GB easily

print("Loading base model...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/gemma-4-E4B-it",
    max_seq_length=MAX_SEQ_LEN,
    dtype=DTYPE,
    load_in_4bit=LOAD_IN_4BIT,
    device_map="cuda",  # load trực tiếp lên GPU, tránh lỗi Windows page file
)

# ── LoRA adapters ─────────────────────────────────────────────────────────────
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_alpha=32,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)
print(f"Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

# ── Dataset ───────────────────────────────────────────────────────────────────
from datasets import Dataset

data_path = Path(args.data)
if not data_path.exists():
    raise FileNotFoundError(f"Data file not found: {data_path}")

raw = [json.loads(l) for l in data_path.read_text(encoding="utf-8").splitlines() if l.strip()]
print(f"Loaded {len(raw)} samples from {data_path}")

CHAT_TEMPLATE = "{% for message in messages %}{{'<start_of_turn>' + message['role'] + '\n' + message['content'] + '<end_of_turn>\n'}}{% endfor %}"

def to_chat(sample: dict) -> dict:
    system = sample.get("system", "")
    convs = sample.get("conversations", [])
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    for turn in convs:
        role = "user" if turn["from"] == "human" else "assistant"
        messages.append({"role": role, "content": turn["value"]})
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return {"text": text}

dataset = Dataset.from_list([to_chat(s) for s in raw])
print(f"Dataset ready: {len(dataset)} samples")

# ── Trainer ───────────────────────────────────────────────────────────────────
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LEN,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        output_dir=args.output,
        save_strategy="epoch",
        report_to="none",
    ),
)

print("Starting training...")
trainer.train()
print("Training complete.")

# ── Save ──────────────────────────────────────────────────────────────────────
out = Path(args.output)
out.mkdir(exist_ok=True)

# Save LoRA adapter
model.save_pretrained(str(out / "lora"))
tokenizer.save_pretrained(str(out / "lora"))
print(f"LoRA saved: {out}/lora")

# Export merged GGUF (Q4_K_M — best balance for Ollama)
print("Exporting GGUF Q4_K_M...")
model.save_pretrained_gguf(
    str(out / "gguf"),
    tokenizer,
    quantization_method="q4_k_m",
)
print(f"GGUF saved: {out}/gguf/")
print("\nNext: ollama create tuetue4:e4b -f Modelfile")
