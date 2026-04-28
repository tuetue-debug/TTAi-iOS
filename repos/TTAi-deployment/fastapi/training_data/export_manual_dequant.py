"""
export_manual_dequant.py
Bypass save_pretrained hoàn toàn — dequantize BNB thủ công, save safetensors,
rồi chạy llama.cpp converter trực tiếp.

Usage:
  python export_manual_dequant.py
"""
from __future__ import annotations
import os, json, shutil, subprocess, sys
from pathlib import Path

os.environ["UNSLOTH_DISABLE_FUSED_CE"] = "1"
os.environ["UNSLOTH_FUSED_CROSS_ENTROPY"] = "0"

SNAPSHOT   = r"C:\Users\vannt-op\.cache\huggingface\hub\models--unsloth--gemma-4-e4b-it-unsloth-bnb-4bit\snapshots\9746c23553347b443ebdc1caba1d41b52223d0c8"
LORA       = r"D:\Data Share\Train\tuetue-gemma4-e4b-v1\lora"
MERGE_DIR  = r"D:\Data Share\Train\tuetue-gemma4-e4b-v1\merged_fp16"
OUTPUT_DIR = r"D:\Data Share\Train\tuetue-gemma4-e4b-v1\gguf_final"
LLAMA_CONVERT = r"C:\Users\vannt-op\.unsloth\llama.cpp\convert_hf_to_gguf.py"
LLAMA_QUANT   = r"C:\Users\vannt-op\.unsloth\llama.cpp\build\bin\Release\llama-quantize.exe"

from unsloth import FastLanguageModel
from safetensors.torch import load_file, save_file
import torch
import bitsandbytes as bnb

# ── 1. Load model + apply LoRA ────────────────────────────────────────────────
print(f"[1] Free VRAM: {torch.cuda.mem_get_info()[0]/1e9:.1f} GB")
print("[1] Loading model...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=SNAPSHOT, max_seq_length=1024,
    dtype=None, load_in_4bit=True, device_map="cuda",
)
model = FastLanguageModel.get_peft_model(
    model, r=8, lora_alpha=16, lora_dropout=0, bias="none",
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    use_gradient_checkpointing=False, random_state=42,
)

# Zero-init rồi load LoRA
with torch.no_grad():
    for n, p in model.named_parameters():
        if "lora_" in n:
            p.zero_()
weights = load_file(LORA + "/adapter_model.safetensors", device="cuda")
remapped = {
    k.replace(".lora_A.weight", ".lora_A.default.weight")
     .replace(".lora_B.weight", ".lora_B.default.weight"): v
    for k, v in weights.items()
}
missing, unexpected = model.load_state_dict(remapped, strict=False)
print(f"[1] LoRA loaded — Missing: {len(missing)}, Unexpected: {len(unexpected)}")

# ── 2. Dequantize thủ công mỗi BNB layer ─────────────────────────────────────
print("[2] Dequantizing BNB layers manually...")
state_dict_fp16 = {}
n_bnb = 0
n_normal = 0

for name, module in model.named_modules():
    if isinstance(module, bnb.nn.Linear4bit):
        # Dequantize weight từ 4-bit về bf16
        w = module.weight.dequantize().to(torch.bfloat16)
        # Tên key phải khớp với HF format (bỏ "base_model.model." prefix)
        hf_name = name.replace("base_model.model.", "") + ".weight"
        state_dict_fp16[hf_name] = w.cpu()
        if module.bias is not None:
            state_dict_fp16[name.replace("base_model.model.", "") + ".bias"] = module.bias.data.cpu()
        n_bnb += 1
    elif isinstance(module, torch.nn.Linear) and not any(x in name for x in ["lora_A", "lora_B"]):
        hf_name = name.replace("base_model.model.", "") + ".weight"
        if hf_name not in state_dict_fp16:
            state_dict_fp16[hf_name] = module.weight.data.to(torch.bfloat16).cpu()
            if module.bias is not None:
                state_dict_fp16[name.replace("base_model.model.", "") + ".bias"] = module.bias.data.cpu()
            n_normal += 1

# Thêm non-linear params (embeddings, layernorm, etc.)
for name, param in model.named_parameters():
    if "lora_" in name:
        continue
    hf_name = name.replace("base_model.model.", "")
    if hf_name not in state_dict_fp16:
        state_dict_fp16[hf_name] = param.data.to(torch.bfloat16).cpu()

print(f"[2] Dequantized {n_bnb} BNB layers + {n_normal} normal layers")
print(f"[2] Total keys in state dict: {len(state_dict_fp16)}")
total_gb = sum(v.numel() * 2 for v in state_dict_fp16.values()) / 1e9
print(f"[2] Estimated size: {total_gb:.1f} GB bf16")

# ── 3. Save state dict → safetensors ─────────────────────────────────────────
print(f"[3] Saving merged fp16 to {MERGE_DIR} ...")
Path(MERGE_DIR).mkdir(parents=True, exist_ok=True)

# Split thành chunks ~5GB để tránh file quá lớn
from safetensors.torch import save_file as _save_file
chunk_size = 5_000_000_000  # 5GB
chunks, current, current_size = [{}], {}, 0
for k, v in state_dict_fp16.items():
    sz = v.numel() * 2
    if current_size + sz > chunk_size and current:
        chunks.append({})
        current = chunks[-1]
        current_size = 0
    chunks[-1][k] = v
    current_size += sz

if len(chunks) == 1:
    _save_file(chunks[0], str(Path(MERGE_DIR) / "model.safetensors"))
    print(f"[3] Saved single shard: model.safetensors")
else:
    index = {"metadata": {"total_size": int(total_gb * 1e9)}, "weight_map": {}}
    for i, chunk in enumerate(chunks):
        fname = f"model-{i+1:05d}-of-{len(chunks):05d}.safetensors"
        _save_file(chunk, str(Path(MERGE_DIR) / fname))
        for k in chunk:
            index["weight_map"][k] = fname
        print(f"[3] Saved shard {i+1}/{len(chunks)}: {fname}")
    with open(Path(MERGE_DIR) / "model.safetensors.index.json", "w") as f:
        json.dump(index, f, indent=2)

# Copy config files (không copy quantization_config)
for fname in ["config.json", "tokenizer.json", "tokenizer_config.json",
              "generation_config.json", "chat_template.jinja", "processor_config.json"]:
    src = Path(SNAPSHOT) / fname
    if src.exists():
        shutil.copy2(src, Path(MERGE_DIR) / fname)

# Xóa quantization_config khỏi config.json để converter không cố dequantize BNB nữa
cfg_path = Path(MERGE_DIR) / "config.json"
if cfg_path.exists():
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg.pop("quantization_config", None)
    cfg.pop("_pre_quantization_dtype", None)
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[3] Removed quantization_config from config.json")

print(f"[3] Merged fp16 model saved to: {MERGE_DIR}")

# ── 4. Convert HF → GGUF bf16 ─────────────────────────────────────────────────
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
bf16_path = str(Path(OUTPUT_DIR) / "tuetue4-e4b-v1.BF16.gguf")

print(f"[4] Converting to GGUF bf16: {bf16_path}")
result = subprocess.run(
    [sys.executable, LLAMA_CONVERT, MERGE_DIR,
     "--outfile", bf16_path, "--outtype", "bf16"],
    capture_output=True, text=True
)
print(result.stdout[-2000:] if result.stdout else "")
if result.returncode != 0:
    print(f"[4] CONVERT ERROR: {result.stderr[-1000:]}")
    sys.exit(1)

size_bf16 = Path(bf16_path).stat().st_size / 1e9
print(f"[4] BF16 GGUF size: {size_bf16:.2f} GB")

# ── 5. Quantize → Q4_K_M ───────────────────────────────────────────────────────
q4_path = str(Path(OUTPUT_DIR) / "tuetue4-e4b-v1.Q4_K_M.gguf")
print(f"[5] Quantizing to Q4_K_M: {q4_path}")
result2 = subprocess.run(
    [LLAMA_QUANT, bf16_path, q4_path, "Q4_K_M"],
    capture_output=True, text=True
)
print(result2.stdout[-1000:] if result2.stdout else "")
if result2.returncode != 0:
    print(f"[5] QUANTIZE ERROR: {result2.stderr[-500:]}")
    sys.exit(1)

size_q4 = Path(q4_path).stat().st_size / 1e9
print(f"\n{'='*60}")
print(f"DONE! Q4_K_M GGUF: {q4_path}")
print(f"Size: {size_q4:.2f} GB")
print(f"\nNext: ollama create tuetue4:e4b -f Modelfile")
