# Qwen3-30B-A3B-Instruct-2507 — Quant / Prune Verification
Retrieved live: 2026-07-24. Sources: Hugging Face model cards/file-trees + arXiv (primary).
Note: HF card "last updated" dates were not reliably rendered by the fetch; where a date
was not shown on the primary page it is marked "date not shown". Sizes are on-disk GB as
listed on each repo's card/file tree.

## Base model (context)
- Qwen/Qwen3-30B-A3B-Instruct-2507 — Apache-2.0, MoE, 30.5B total / 3.3B active,
  128 experts (8 active), 48 layers, 262,144 ctx native. BF16 weights ~61 GB.
  URL: https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507

## Q1 — Notable QUANTIZED variants (primary HF pages)

### GGUF — Unsloth (unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF)
UD-TQ1_0 8.09 | UD-IQ1_S 9.05 | UD-IQ1_M 9.69 | UD-IQ2_XXS 10.3 | UD-IQ2_M 10.8 |
Q2_K 11.3 | Q2_K_L 11.3 | UD-Q2_K_XL 11.8 | UD-IQ3_XXS 12.9 | Q3_K_S 13.3 |
UD-Q3_K_XL 13.8 | Q3_K_M 14.7 | IQ4_XS 16.4 | IQ4_NL 17.3 | Q4_0 17.4 | Q4_K_S 17.5 |
UD-Q4_K_XL 17.7 | Q4_K_M 18.6 | Q4_1 19.2 | Q5_K_S 21.1 | Q5_K_M 21.7 | UD-Q5_K_XL 21.7 |
Q6_K 25.1 | UD-Q6_K_XL 26.3 | Q8_0 32.5 | UD-Q8_K_XL 36 | BF16 61.1  (all GB)
URL: https://huggingface.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF

### GGUF — bartowski (bartowski/Qwen_Qwen3-30B-A3B-Instruct-2507-GGUF)
IQ2_XXS 7.57 | IQ2_S 8.74 | IQ2_M 9.87 | Q2_K 10.91 | Q2_K_L 11.21 | IQ3_XXS 12.22 |
Q3_K_S 13.43 | Q3_K_M 14.08 | Q3_K_XL 14.86 | IQ4_XS 16.46 (recommended) |
IQ4_NL 17.39 | Q4_0 17.63 | Q4_K_S 17.98 (rec) | Q4_K_M 18.63 (rec, "default size") |
Q4_K_L 18.86 (rec) | Q5_K_S 21.10 (rec) | Q5_K_M 21.74 (rec) | Q6_K 25.10 (rec) |
Q8_0 32.48 | bf16 61.10  (all GB). Recommends IQ4_XS / Q4_K_* / Q5_K_* / Q6_K.
URL: https://huggingface.co/bartowski/Qwen_Qwen3-30B-A3B-Instruct-2507-GGUF

### GGUF — mradermacher (static + i1 imatrix)
Q2_K 11.4 | Q3_K_S 13.4 | Q3_K_M 14.8 | Q3_K_L 16.0 | IQ4_XS 16.7 | Q4_K_S 17.6 |
Q4_K_M 18.7 | Q5_K_S 21.2 | Q5_K_M 21.8 | Q6_K 25.2 | Q8_0 32.6 (GB). imatrix at -i1-GGUF.
URL: https://huggingface.co/mradermacher/Qwen3-30B-A3B-Instruct-2507-GGUF

### FP8 — OFFICIAL Qwen (Qwen/Qwen3-30B-A3B-Instruct-2507-FP8)
Fine-grained FP8, block size 128. Apache-2.0. On-disk ~30-32 GB (fp8 ~1 byte/param over
30.5B; exact GB not stated on card). Serve via vLLM>=0.8.5 / SGLang>=0.4.6.post1.
URL: https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507-FP8

### AWQ 4-bit — cpatonn (cpatonn/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit)
W4 AWQ, 4 safetensors shards, total ~18.1 GB on disk. vLLM/SGLang. (group size not shown).
URL: https://huggingface.co/cpatonn/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit/tree/main

### GPTQ / W4A16
A REAP+W4A16 (GPTQ-style 4-bit weight) variant exists: sasa2000/Qwen3-30B-A3B-Instruct-2507-REAP-W4A16 (see Q3).

## Q2 — Single-GPU fit
- 24 GB GPU: All GGUF up through ~Q5_K_M (21.7 GB) fit weights + modest KV cache.
  AWQ 4-bit (~18.1 GB) fits with ~5 GB left for KV cache. IQ4_XS (~16.5 GB) most headroom.
  Q6_K (~25 GB) exceeds 24 GB weights-only (needs partial CPU offload). FP8 (~31 GB) does
  NOT fit 24 GB (card itself says reduce ctx to 32k on OOM — still >24 GB).
- ~48 GB GPU: FP8 (~31 GB), Q8_0 (~32.5 GB), and the bf16 REAP-23B (44 GB) all fit.
  Full bf16 (61 GB) does NOT fit 48 GB.
- Smallest usable quant that keeps GOOD quality: Q4_K_M (~18.6 GB) or IQ4_XS (~16.5 GB)
  GGUF, or AWQ 4-bit (~18 GB). bartowski labels Q4_K_M "good quality, default" and IQ4_XS
  "recommended." On 24 GB you can go up to Q5_K_M for extra margin.

## Q3 — REAP
- REAP = Router-weighted Expert Activation Pruning. Cerebras. Paper: "REAP the Experts:
  Why Pruning Prevails for One-Shot MoE compression," arXiv:2510.13999, submitted 2025-10-15.
  Prunes whole experts (not merge) using router gate-values x expert activation norms to
  minimize reconstruction error. Claims near-lossless at ~50% expert pruning on Qwen3-Coder-480B/Kimi-K2.
  URL: https://arxiv.org/abs/2510.13999
- Cerebras did NOT ship a REAP of Instruct-2507. Closest official: cerebras/Qwen3-Coder-REAP-25B-A3B
  (base Qwen3-Coder-30B-A3B-Instruct; 128->103 experts, 20% pruned; 25B/3B; ~49.8 GB bf16;
  "almost identical performance"; Apache-2.0). URL: https://huggingface.co/cerebras/Qwen3-Coder-REAP-25B-A3B
- COMMUNITY REAP of the EXACT shortlisted brain DOES exist:
  * SamsungSAILMontreal/Qwen3-30B-A3B-Instruct-2507-REAP — 128->96 experts, ~23B params,
    44 GB bf16, retains >=90% (avg benchmark 69.7 -> 65.0, ~93%). Apache-2.0.
    URL: https://huggingface.co/SamsungSAILMontreal/Qwen3-30B-A3B-Instruct-2507-REAP
  * sasa2000/Qwen3-30B-A3B-Instruct-2507-REAP-W4A16 (REAP + 4-bit -> fits 24 GB)
  * sasa2000/Qwen3-30B-A3B-Instruct-2507-REAP-Q8_0-GGUF
  * ryfernandes/Qwen3-30B-A3B-Instruct-2507-REAP-25pct-and-FP8-DYNAMIC
  * moe-pruning-analysis-project/...-medinst-reap-0/1/2

## Q4 — Real-time fitness (tokens/sec, latency)
UNVERIFIABLE from primary sources found now. None of the fetched model cards (Unsloth,
bartowski, mradermacher, Qwen FP8, cpatonn AWQ, Cerebras/Samsung REAP) state tokens/sec or
per-turn latency on a single GPU. The Unsloth Qwen3 run/fine-tune docs page 404'd on fetch.
Architecturally the model activates only 3.3B params/token (fast decode expected), but that
is an inference from the config, NOT a cited benchmark. A live benchmark on the target GPU
is required to confirm sub-second voice turns.

## Q5 — Bottom line
YES — a fitting quant exists. AWQ 4-bit (~18 GB) or GGUF Q4_K_M (~18.6 GB) / IQ4_XS (~16.5 GB)
fit one 24 GB GPU with KV-cache headroom at "good" quality; a REAP+4-bit (sasa2000 W4A16) also
fits 24 GB. FP8 (~31 GB) needs ~48 GB. Real-time voice fitness is NOT proven by any primary
benchmark and must be validated with a live tok/s + latency test on the actual GPU.
