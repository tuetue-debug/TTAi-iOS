"""
train_tuetue_v2.py — Tuệ Tuệ SFT Round 2
Dùng load_in_4bit=False (bf16) để export GGUF được trực tiếp.
Cần ~16GB VRAM — có thể OOM, nếu OOM thì giảm MAX_SEQ_LEN xuống 512.

Usage:
  python train_tuetue_v2.py --data tuetue_sft_combined.jsonl --output tuetue-gemma4-e4b-v2
"""
from __future__ import annotations
import os, argparse, json
from pathlib import Path

os.environ["UNSLOTH_DISABLE_FUSED_CE"] = "1"
os.environ["UNSLOTH_FUSED_CROSS_ENTROPY"] = "0"

parser = argparse.ArgumentParser()
parser.add_argument("--data",   default="tuetue_sft_combined.jsonl")
parser.add_argument("--output", default="tuetue-gemma4-e4b-v2")
parser.add_argument("--epochs", type=int, default=2)
parser.add_argument("--seq",    type=int, default=512, help="Max seq len (giảm nếu OOM)")
args = parser.parse_args()

from unsloth import FastLanguageModel
import torch

MAX_SEQ_LEN = args.seq
print(f"Training config: seq_len={MAX_SEQ_LEN}, epochs={args.epochs}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")

print("Loading model in BF16 (no 4-bit)...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/gemma-4-E4B-it",
    max_seq_length=MAX_SEQ_LEN,
    dtype=torch.bfloat16,
    load_in_4bit=False,   # BF16 — export được GGUF trực tiếp
    device_map="cuda",
)

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
print(f"Trainable: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

from datasets import Dataset

data_path = Path(args.data)
if not data_path.exists():
    raise FileNotFoundError(f"Data not found: {data_path}")

raw = [json.loads(l) for l in data_path.read_text(encoding="utf-8").splitlines() if l.strip()]
print(f"Loaded {len(raw)} samples")

def to_chat(s):
    msgs = []
    if s.get("system"):
        msgs.append({"role":"system","content":s["system"]})
    for t in s.get("conversations",[]):
        role = "user" if t["from"]=="human" else "assistant"
        msgs.append({"role":role,"content":t["value"]})
    # Support messages format too
    if not msgs and s.get("messages"):
        msgs = s["messages"]
    return {"text": tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)}

dataset = Dataset.from_list([to_chat(s) for s in raw])
print(f"Dataset: {len(dataset)} samples")

from trl import SFTTrainer
from transformers import TrainingArguments

torch.cuda.empty_cache()
print(f"Free VRAM before train: {torch.cuda.mem_get_info()[0]/1e9:.1f} GB")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LEN,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        warmup_steps=10,
        num_train_epochs=args.epochs,
        learning_rate=1e-4,
        bf16=True,
        fp16=False,
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        output_dir=args.output,
        save_strategy="epoch",
        report_to="none",
    ),
)

trainer.train()
print("Training complete!")

# Save LoRA
out = Path(args.output)
model.save_pretrained(str(out / "lora"))
tokenizer.save_pretrained(str(out / "lora"))
print(f"LoRA saved: {out}/lora")

# Export GGUF trực tiếp (BF16 model → works với llama.cpp)
print("Exporting GGUF Q4_K_M...")
model.save_pretrained_gguf(
    str(out / "gguf"),
    tokenizer,
    quantization_method="q4_k_m",
)
print(f"GGUF saved: {out}/gguf/")
