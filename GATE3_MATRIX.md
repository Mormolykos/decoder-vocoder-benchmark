# GATE 3 — FROZEN GPU TIMING BENCHMARK

**Machine-generated on 2026-09-11T20:35:15+00:00 from `results/gate3_raw_*.jsonl`. Every statistic is recomputed from raw; nothing is transcribed by hand.**

**Device:** NVIDIA GeForce RTX 5080 · torch 2.10.0+cu128 · CUDA 12.8 · seed 20260911 · N=30 warm + 3 cold, 5 warm-ups discarded · block-randomised · §7.4 one GPU process at a time.

> ### What `MEASURED - CELLS COMPLETED AND ADMISSIBLE` means — and what it does not
>
> 'MEASURED - CELLS COMPLETED AND ADMISSIBLE' means EVERY cell for that arm completed and every timed row passed the structural synchronize assertion. IT IS NOT A PERFORMANCE VERDICT. It does not mean the arm holds real time, does not mean its streamed output is valid, and implies no recommendation. Real-time capability is the underrun / real-time-margin columns; streamed validity is the §8 column; neither is folded into this word.

- ⛔ Measured: REPRESENTATION -> WAVEFORM only. Generator/AR timing is outside this study; a decode-only number read as end-to-end TTS performance is a failed report.
- ⛔ Wall clock is PRIMARY; CUDA events are DIAGNOSTIC. They measure different scopes and are not expected to agree, and disagreement never voids a run.
- ⛔ EAGER MODE for every arm - no torch.compile, no CUDA graphs. MelFlow ships a compiled path and its upstream recommends CUDA graphs, so its latency here is an UPPER BOUND, not its best achievable latency (amendment 9.10).
- ⛔ Seam metrics compare a decoder against ITSELF. They are not a quality ranking between decoders. QUALITY COMPARISON NOT ESTABLISHED.
- ⛔ Route A and Route B are never merged into one ranking.
- ⛔ Jitter statistics (p50/p95/p99/IQR/max) are over the STEADY-STATE population, excluding the first chunk of every repetition, because TTFA reports the first chunk separately. The all-chunks population is reported beside them and the two are never mixed in one row.
- ⛔ Device-side timing cannot by itself separate genuine model work from GPU preemption by another process. §7.4 declares one GPU process at a time but is not instrumented per cell.

## E6 — the §7.2 environment control, and what it decides

`encodec24_q8`, byte-identical tokens, same GPU, run as a **single arm** in every environment that produced arm rows. Single-arm on every side on purpose: the decbench arm rows were block-randomised among 14 other arms, so comparing an interleaved run against a solo run would confound the environment effect with run context.

| environment | transformers | median ratio vs decbench | effect | consequence |
|---|---|---|---|---|
| `decbench` | 4.57.3 | 1.000 | **0.0%** | reference |
| `decbench_melflow` | 5.17.0 | 1.005 | **0.5%** | ✅ COMPARABLE |
| `fish` | 4.35.2 | 0.498 | **50.2%** | ⛔ **NOT COMPARABLE** |

| condition | decbench ms | fish ms | melflow-env ms |
|---|---|---|---|
| offline 1.0 | 8.171 | 4.372 | 7.530 |
| offline 2.0 | 10.367 | 6.353 | 9.953 |
| offline 5.0 | 15.373 | 12.175 | 15.819 |
| offline 10.0 | 26.964 | 23.486 | 27.968 |
| offline 30.0 | 74.726 | 71.875 | 76.372 |
| stream 26.7 | 5.570 | 1.978 | 5.523 |
| stream 53.3 | 5.457 | 2.018 | 5.781 |
| stream 93.3 | 5.976 | 2.067 | 5.540 |
| stream 173.3 | 5.705 | 2.272 | 5.869 |
| stream 333.3 | 6.587 | 2.596 | 6.108 |
| stream 653.3 | 7.089 | 3.262 | 6.722 |
| stream 1013.3 | 7.326 | 4.247 | 7.466 |

**The effect is a near-constant ~3.0–4.0 ms offset and it is DEVICE-SIDE, not host-side.** At the 2 s offline condition host overhead is 0.022 ms in decbench and 0.024 ms in fish, while CUDA time is **10.344 ms vs 6.328 ms** — the two `transformers` versions launch different GPU work for the same decode. torch is identical everywhere (2.10.0+cu128).

⛔ **`fish_modified_dac` — the incumbent — may not be compared numerically against any decbench arm.** Its own numbers stand within its own environment. The direction matters: `fish` is FASTER, so the incumbent's environment flatters it by ~3.5 ms per call relative to the environment 17 other arms were measured in. **Nothing here says Fish ModifiedDAC is fast or slow; it says its number and theirs cannot be put in one ranking.**

## Headline — one row per arm, at the ~80 ms chunk anchor

**All jitter statistics are STEADY-STATE**, excluding the first chunk of every repetition; the first chunk is reported separately as TTFA. **§8** is the frozen streamed-output validity gate. **env?** is cross-environment comparability.

| arm | route | env? | §8 streamed | cold s | RTF@10s | TTFA ms | p50 | p95 | p99 | IQR | max | underrun | RT margin | anchor VRAM MiB | drift % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `focalcodec_50hz_4k_causal` | A | ✅ | PASS | 1.27 | 0.00059 | 3.11 | 3.07 | 3.25 | 3.40 | 0.10 | 3.50 | 0.0000 | 26.1× | 1321.0 | -0.697 |
| `focalcodec_50hz_2k_causal` | A | ✅ | PASS | 1.25 | 0.00061 | 3.10 | 3.04 | 3.23 | 3.32 | 0.10 | 3.50 | 0.0000 | 26.2× | 1317.9 | 0.632 |
| `focalcodec_50hz_65k_causal` | A | ✅ | PASS | 1.24 | 0.00059 | 3.11 | 3.06 | 3.24 | 3.31 | 0.10 | 3.66 | 0.0000 | 26.1× | 1324.9 | 0.122 |
| `focalcodec_50hz` | A | ✅ | PASS | 0.98 | 0.00039 | 2.92 | 2.84 | 3.02 | 3.11 | 0.10 | 3.55 | 0.0000 | 28.1× | 880.0 | -2.013 |
| `focalcodec_25hz` | A | ✅ | PASS | 0.90 | 0.00038 | 2.91 | 2.86 | 2.99 | 3.06 | 0.09 | 3.29 | 0.0000 | 28.0× | 876.3 | -0.722 |
| `focalcodec_12_5hz` | A | ✅ | ⛔ **FAIL** | 0.94 | 0.00039 | 2.99 | 2.93 | 3.10 | 3.22 | 0.09 | 3.51 | 0.0000 | 27.3× | 892.3 | -0.673 |
| `mimi_q8` | A | ✅ | PASS | 0.57 | 0.00124 | 9.85 | 9.84 | 10.24 | 11.27 | 0.22 | 11.96 | 0.0000 | 8.1× | 466.3 | 0.109 |
| `mimi_q32` | A | ✅ | PASS | 0.60 | 0.00130 | 10.33 | 10.33 | 10.68 | 10.88 | 0.24 | 11.35 | 0.0000 | 7.7× | 518.4 | 0.121 |
| `encodec24_q8` | A | ✅ | PASS | 0.46 | 0.00264 | 5.94 | 5.91 | 6.92 | 7.50 | 0.44 | 7.78 | 0.0000 | 15.8× | 188.1 | 0.310 |
| `encodec_vocos` | A | ✅ | PASS | 0.52 | 0.00024 | 1.94 | 1.90 | 2.19 | 2.66 | 0.12 | 2.92 | 0.0000 | 49.0× | 145.7 | -0.280 |
| `dac44` | A | ✅ | PASS | 0.49 | 0.00922 | 3.13 | 3.09 | 3.25 | 3.52 | 0.10 | 3.96 | 0.0000 | 26.3× | 403.8 | -0.708 |
| `dualcodec_12hz_v1` | A | ✅ | PASS | 2.55 | 0.00098 | 3.88 | 3.82 | 3.96 | 4.05 | 0.10 | 4.34 | 0.0000 | 20.9× | 2791.4 | -0.990 |
| `dualcodec_25hz_v1` | A | ✅ | PASS | 2.56 | 0.00311 | 3.56 | 3.48 | 3.70 | 4.02 | 0.12 | 4.45 | 0.0000 | 23.0× | 2956.9 | -0.616 |
| `qwen3_tts_tokenizer_12hz` | A | ✅ | PASS | 0.90 | 0.00558 | 16.00 | 15.90 | 16.52 | 17.39 | 0.34 | 208.10 | 0.0013 | 5.0× | 754.6 | -0.385 |
| `fish_modified_dac` | A | ⛔ **NOT COMP** | PASS | 2.62 | 0.00796 | 11.22 | 11.63 | 14.43 | 16.18 | 1.53 | 25.95 | 0.0000 | 8.0× | 1886.7 | -0.302 |
| `melflow` | B | ✅ | n/a | 0.39 | 0.06961 | **NOT ESTABLISHED** | 375.91 | 416.04 | 454.96 | 18.51 | 519.28 | 1.0000 | 0.2× | 586.7 | -1.054 |
| `vocos_mel24` | B | ✅ | ⛔ **FAIL** | 0.45 | 0.00023 | 1.37 | 1.33 | 1.62 | 1.74 | 0.06 | 1.88 | 0.0000 | 64.0× | 120.7 | -1.795 |
| `bigvgan22` | B | ✅ | PASS | 1.61 | 0.02109 | 27.64 | 27.44 | 31.76 | 41.68 | 1.16 | 48.27 | 0.0000 | 3.0× | 472.6 | -0.468 |
| `griffinlim` | B | ✅ | ⛔ **FAIL** | 0.00 | 0.00122 | 11.27 | 11.12 | 11.42 | 11.59 | 0.23 | 11.75 | 0.0000 | 7.7× | 65.8 | -0.268 |
| `nanocodec` | A | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

`nanocodec` — **BLOCKED — PLATFORM.** No timing number is manufactured; its absence is reported as BLOCKED, never as zero and never omitted.

⛔ **These arms produce streamed output that is INADMISSIBLE under the study's own frozen §8 gate at EVERY chunk size tested.** Their timing numbers are real; what they timed is not a valid streaming configuration.

- **`vocos_mel24`** — §8 0/7 conditions pass; failing predicate `duration_ok`. **E3 minimum viable streaming configuration = NOT ACHIEVABLE.**
- **`griffinlim`** — §8 0/6 conditions pass; failing predicate `duration_ok`. **E3 minimum viable streaming configuration = NOT ACHIEVABLE.**

⚠️ **`melflow` — §8 was NEVER EVALUATED on a chunked decode.** no condition was decoded at a chunk size: this arm's decode granularity is one frame and every chunk condition is COMPOSED from the per-frame stream (amendment 9.6). §8 was therefore never evaluated on a chunked decode for it - that is untested, NOT failed. **E3 = NOT ESTABLISHED. This is untested, NOT failed, and the two must not be read as the same thing.**

⚠️ **`focalcodec_12_5hz` fails §8 at the anchor** (2/5 conditions pass, failing `energy_ok`). Its minimum viable streaming configuration is **640.8 ms**, not the anchor.

## E3 — minimum viable streaming configuration (§5)

Two different questions, kept apart. **min chunk that ran** is execution feasibility only. **E3** is the frozen estimand and requires the streamed output to PASS §8.

| arm | min chunk that ran | §8 pass/total | **E3 minimum viable** | failing predicate |
|---|---|---|---|---|
| `focalcodec_50hz_4k_causal` | 80.0 ms | 5/5 | **80.0 ms** | — |
| `focalcodec_50hz_2k_causal` | 80.0 ms | 5/5 | **80.0 ms** | — |
| `focalcodec_50hz_65k_causal` | 80.0 ms | 5/5 | **80.0 ms** | — |
| `focalcodec_50hz` | 80.1 ms | 5/5 | **80.1 ms** | — |
| `focalcodec_25hz` | 80.1 ms | 4/5 | **80.1 ms** | energy_ok |
| `focalcodec_12_5hz` | 80.1 ms | 2/5 | **640.8 ms** | energy_ok |
| `mimi_q8` | 79.7 ms | 6/6 | **79.7 ms** | — |
| `mimi_q32` | 79.7 ms | 6/6 | **79.7 ms** | — |
| `encodec24_q8` | 26.7 ms | 7/7 | **26.7 ms** | — |
| `encodec_vocos` | 26.7 ms | 7/7 | **26.7 ms** | — |
| `dac44` | 23.2 ms | 7/7 | **23.2 ms** | — |
| `dualcodec_12hz_v1` | 80.1 ms | 5/5 | **80.1 ms** | — |
| `dualcodec_25hz_v1` | 40.1 ms | 6/6 | **40.1 ms** | — |
| `qwen3_tts_tokenizer_12hz` | 80.0 ms | 5/5 | **80.0 ms** | — |
| `fish_modified_dac` | 46.4 ms | 6/6 | **46.4 ms** | — |
| `melflow` | — ms | 0/0 | ⚠️ **NOT ESTABLISHED** | — |
| `vocos_mel24` | 21.3 ms | 0/7 | ⛔ **NOT ACHIEVABLE** | duration_ok |
| `bigvgan22` | 23.2 ms | 7/7 | **23.2 ms** | — |
| `griffinlim` | 42.7 ms | 0/6 | ⛔ **NOT ACHIEVABLE** | duration_ok |

## E1 — the controlled pair (§5)

**byte-identical EnCodec 24 kHz Q=8 token tensor; codebooks verified bitwise identical (AUDIT.md §3.1). The DECODER is the only variable that moves.**

*paired on the INPUT, not on the measurement occasion - the two arms ran in separate batches, so the interval is a bootstrap percentile interval (4000 resamples, seed 20260911), not a within-occasion paired t.* both in `decbench`; E1 is WITHIN-environment, so E6 does not bear on it.

| condition | `encodec24_q8` | `encodec_vocos` | difference (95% CI) | ratio (95% CI) |
|---|---|---|---|---|
| offline 1 s | 7.378 ms | 2.421 ms | 4.957 [4.832, 5.107] | **3.048×** [2.971, 3.117] |
| offline 2 s | 9.526 ms | 2.464 ms | 7.062 [6.953, 7.225] | **3.866×** [3.816, 3.939] |
| offline 5 s | 15.423 ms | 2.481 ms | 12.942 [12.857, 13.134] | **6.217×** [6.114, 6.297] |
| offline 10 s | 26.388 ms | 2.387 ms | 24.001 [23.842, 24.192] | **11.056×** [10.940, 11.237] |
| offline 30 s | 74.241 ms | 2.995 ms | 71.247 [70.754, 71.445] | **24.793×** [24.475, 24.913] |
| stream (steady-state) 26.7 ms | 5.364 ms | 1.907 ms | 3.457 [3.447, 3.467] | **2.813×** [2.804, 2.822] |
| stream (steady-state) 53.3 ms | 5.448 ms | 1.917 ms | 3.531 [3.516, 3.547] | **2.842×** [2.826, 2.853] |
| stream (steady-state) 93.3 ms | 5.908 ms | 1.902 ms | 4.006 [3.979, 4.043] | **3.106×** [3.086, 3.131] |
| stream (steady-state) 173.3 ms | 5.626 ms | 1.914 ms | 3.712 [3.682, 3.739] | **2.940×** [2.913, 2.969] |
| stream (steady-state) 333.3 ms | 5.961 ms | 2.122 ms | 3.839 [3.800, 3.873] | **2.809×** [2.777, 2.847] |
| stream (steady-state) 653.3 ms | 6.642 ms | 2.194 ms | 4.447 [4.263, 4.518] | **3.027×** [2.797, 3.105] |
| stream (steady-state) 1013.3 ms | 7.394 ms | 2.045 ms | 5.348 [5.254, 5.420] | **3.615×** [3.502, 3.679] |

⭐ **The ratio is NOT constant across duration: 3.05x at 1 s rising to 24.79x at 30 s. `encodec_vocos` is nearly duration-INDEPENDENT (2.42 -> 3.00 ms from 1 s to 30 s, every condition §8 PASS, allocated memory scaling normally so the full input is processed), while `encodec24_q8` scales strongly (7.38 -> 74.24 ms). On byte-identical tokens, with the decoder as the only moving variable, the two decoders have different COMPLEXITY CLASSES in this range, not just different constants.**

**Memory, by scope — never quoted across scopes:**

| scope | `encodec24_q8` | `encodec_vocos` | ratio |
|---|---|---|---|
| anchor peak allocated MiB | 188.1 | 145.7 | **1.292×** |
| offline sweep peak allocated MiB | 511.2 | 236.2 | **2.165×** |
| session peak allocated MiB | 511.2 | 236.2 | **2.165×** |
| anchor peak reserved MiB | 824.0 | 158.0 | **5.215×** |
| offline sweep peak reserved MiB | 826.0 | 646.0 | **1.279×** |
| session peak reserved MiB | 828.0 | 646.0 | **1.282×** |

⚠️ `reserved` is an ALLOCATOR CACHING quantity and is NOT monotonic in workload - encodec_vocos reserves 162, 646, 164, 182, 270 MiB across 1/2/5/10/30 s. A ratio built on it is a ratio of caching behaviour, not of memory demand, which is why the anchor-reserved ratio (5.2x) and the session-reserved ratio (1.3x) disagree so violently. `allocated` is the interpretable denominator; reserved is reported beside it (R18) and must never be quoted alone.

## E4 — offline versus streaming ordering (§5)

Computed over **17 qualifying arms**, named below. Spearman ρ between the RTF ranking and the TTFA ranking = **0.8627**. **Orderings differ: True.**

**Subset:** `focalcodec_50hz_4k_causal`, `focalcodec_50hz_2k_causal`, `focalcodec_50hz_65k_causal`, `focalcodec_50hz`, `focalcodec_25hz`, `focalcodec_12_5hz`, `mimi_q8`, `mimi_q32`, `encodec24_q8`, `encodec_vocos`, `dac44`, `dualcodec_12hz_v1`, `dualcodec_25hz_v1`, `qwen3_tts_tokenizer_12hz`, `vocos_mel24`, `bigvgan22`, `griffinlim`

**Excluded, with reasons:** no TTFA (NOT ESTABLISHED) → `melflow` · NOT COMPARABLE environment (§7.2) → `fish_modified_dac` · blocked → `nanocodec`

Arms whose position moves three or more ranks between the two orderings:

| arm | rank by RTF | rank by TTFA | shift |
|---|---|---|---|
| `dac44` | 16 | 9 | -7 |
| `dualcodec_25hz_v1` | 14 | 10 | -4 |
| `griffinlim` | 10 | 15 | +5 |

*A decoder that is cheap per second of audio is not necessarily the one that returns the first block soonest. This says which ordering you get, not which arm to pick.*

## §17 latency budget — decoder-only

**75 ms competitive · 50 ms stretch · 200 ms red zone.** ⚠️ **VENDOR-REPORTED**, from vendors' own systems and own measurement conditions. **MARKET ANCHORS, NOT measurements comparable to anything produced here.**

**This table admits an arm only if its streamed output PASSES §8 at the anchor AND its environment is comparable to the reference.** Arms excluded on either ground are listed underneath rather than shown with a clean percentage.

| arm | TTFA @ anchor | % of the 75 ms budget | ms left for everything else |
|---|---|---|---|
| `focalcodec_50hz_4k_causal` | 3.11 ms | 4.1% | 71.89 ms |
| `focalcodec_50hz_2k_causal` | 3.10 ms | 4.1% | 71.90 ms |
| `focalcodec_50hz_65k_causal` | 3.11 ms | 4.2% | 71.89 ms |
| `focalcodec_50hz` | 2.92 ms | 3.9% | 72.08 ms |
| `focalcodec_25hz` | 2.91 ms | 3.9% | 72.09 ms |
| `mimi_q8` | 9.85 ms | 13.1% | 65.15 ms |
| `mimi_q32` | 10.33 ms | 13.8% | 64.67 ms |
| `encodec24_q8` | 5.94 ms | 7.9% | 69.06 ms |
| `encodec_vocos` | 1.94 ms | 2.6% | 73.06 ms |
| `dac44` | 3.13 ms | 4.2% | 71.87 ms |
| `dualcodec_12hz_v1` | 3.88 ms | 5.2% | 71.12 ms |
| `dualcodec_25hz_v1` | 3.56 ms | 4.7% | 71.44 ms |
| `qwen3_tts_tokenizer_12hz` | 16.00 ms | 21.3% | 59.00 ms |
| `bigvgan22` | 27.64 ms | 36.9% | 47.36 ms |

**Excluded from the budget table:**

- `focalcodec_12_5hz` — streamed §8 **FAIL** at the anchor
- `fish_modified_dac` — **NOT COMPARABLE** environment (§7.2)
- `melflow` — TTFA **NOT ESTABLISHED**
- `vocos_mel24` — streamed §8 **FAIL** at the anchor
- `griffinlim` — streamed §8 **FAIL** at the anchor

⛔ **Decoder-only.** Text frontend, acoustic generation and serving all come out of the same budget and none of them is measured here.

## Offline duration sweep — fixed cost versus marginal cost (E2)

**Per arm, never averaged across arms.**

| arm | fixed cost ms | ms per audio second | fit residual ms | fit valid? | RTF @1 s | @5 s | @30 s |
|---|---|---|---|---|---|---|---|
| `focalcodec_50hz_4k_causal` | 2.79 | 0.38 | 0.77 | yes | 0.00347 | 0.00097 | 0.00048 |
| `focalcodec_50hz_2k_causal` | 2.68 | 0.39 | 0.55 | yes | 0.00351 | 0.00090 | 0.00049 |
| `focalcodec_50hz_65k_causal` | 2.65 | 0.39 | 0.64 | yes | 0.00339 | 0.00091 | 0.00049 |
| `focalcodec_50hz` | 2.79 | 0.12 | 0.27 | yes | 0.00329 | 0.00063 | 0.00022 |
| `focalcodec_25hz` | 3.13 | 0.07 | 0.27 | yes | 0.00361 | 0.00066 | 0.00017 |
| `focalcodec_12_5hz` | 2.94 | 0.08 | 0.17 | yes | 0.00318 | 0.00065 | 0.00017 |
| `mimi_q8` | 9.14 | 0.43 | 1.02 | yes | 0.00985 | 0.00220 | 0.00074 |
| `mimi_q32` | 9.66 | 0.41 | 0.70 | yes | 0.01034 | 0.00222 | 0.00074 |
| `encodec24_q8` | 4.36 | 2.32 | 1.13 | yes | 0.00738 | 0.00308 | 0.00247 |
| `encodec_vocos` | 2.36 | 0.02 | 0.17 | yes | 0.00242 | 0.00050 | 0.00010 |
| `dac44` | ⛔ **-1.33** | ⛔ **9.44** | 4.06 | ⛔ **NOT INTERPRETABLE** | 0.00643 | 0.00880 | 0.00941 |
| `dualcodec_12hz_v1` | ⛔ **2.15** | ⛔ **0.87** | 1.13 | ⛔ **NOT INTERPRETABLE** | 0.00417 | 0.00117 | 0.00096 |
| `dualcodec_25hz_v1` | ⛔ **3.76** | ⛔ **2.11** | 6.21 | ⛔ **NOT INTERPRETABLE** | 0.00523 | 0.00231 | 0.00219 |
| `qwen3_tts_tokenizer_12hz` | 7.36 | 5.19 | 3.75 | yes | 0.01676 | 0.00609 | 0.00549 |
| `fish_modified_dac` | ⛔ **8.55** | ⛔ **7.31** | 4.81 | ⛔ **NOT INTERPRETABLE** | 0.01402 | 0.00866 | 0.00762 |
| `melflow` | ⛔ **-39.46** | ⛔ **76.03** | 36.38 | ⛔ **NOT INTERPRETABLE** | 0.07292 | 0.06225 | 0.07509 |
| `vocos_mel24` | 1.50 | 0.10 | 0.33 | yes | 0.00192 | 0.00038 | 0.00015 |
| `bigvgan22` | ⛔ **-44.10** | ⛔ **29.42** | 42.78 | ⛔ **NOT INTERPRETABLE** | 0.02810 | 0.01304 | 0.02851 |
| `griffinlim` | 11.40 | -0.01 | 0.88 | yes | 0.01111 | 0.00228 | 0.00037 |

⛔ **The fixed/marginal decomposition DOES NOT HOLD for these arms and is NOT INTERPRETABLE for them.** The measurements stand; the linear reading of them is withdrawn.

- `dac44` — negative fixed cost (-1.33 ms) and max residual 4.06 ms against a 6.42 ms shortest measurement.
- `dualcodec_12hz_v1` — max residual 1.13 ms against a 4.00 ms shortest measurement.
- `dualcodec_25hz_v1` — max residual 6.21 ms against a 5.23 ms shortest measurement.
- `fish_modified_dac` — max residual 4.81 ms against a 14.33 ms shortest measurement.
- `melflow` — negative fixed cost (-39.46 ms) and max residual 36.38 ms against a 72.34 ms shortest measurement.
- `bigvgan22` — negative fixed cost (-44.10 ms) and max residual 42.78 ms against a 28.06 ms shortest measurement.

## Per-arm streaming detail

### `focalcodec_50hz_4k_causal`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.0 | 4 | PASS | 3.11 | 3.068 | 3.251 | 3.396 | 0.104 | 3.501 | 0.0000 | 26.1× | 0.0 | 720 | no |
| 160.0 | 8 | PASS | 3.04 | 3.023 | 3.194 | 3.272 | 0.085 | 3.314 | 0.0000 | 52.9× | 0.0 | 330 | no |
| 320.0 | 16 | PASS | 3.01 | 2.963 | 3.138 | 3.269 | 0.113 | 3.303 | 0.0000 | 107.7× | 0.0 | 150 | no |
| 640.0 | 32 | PASS | 3.23 | 3.191 | 3.388 | 3.438 | 0.123 | 3.443 | 0.0000 | 200.1× | 0.0 | 90 | no |
| 1040.0 | 52 | PASS | 3.43 | 3.418 | 5.734 | 6.294 | 0.713 | 6.944 | 0.0000 | 303.8× | 0.0 | 90 | no |

⚠️ **Delay calibration is NOISE for this arm** — normalised peak correlation 0.106. The -19.33 ms estimate is recorded but **is not used as a fact anywhere in this study**.

### `focalcodec_50hz_2k_causal`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.0 | 4 | PASS | 3.10 | 3.043 | 3.230 | 3.317 | 0.097 | 3.502 | 0.0000 | 26.2× | 0.0 | 720 | no |
| 160.0 | 8 | PASS | 3.02 | 3.020 | 3.180 | 3.292 | 0.082 | 3.415 | 0.0000 | 53.0× | 0.0 | 330 | no |
| 320.0 | 16 | PASS | 3.03 | 2.997 | 3.329 | 4.019 | 0.143 | 4.137 | 0.0000 | 106.6× | 0.0 | 150 | no |
| 640.0 | 32 | PASS | 3.22 | 3.219 | 3.424 | 3.578 | 0.124 | 3.929 | 0.0000 | 198.8× | 0.0 | 90 | no |
| 1040.0 | 52 | PASS | 3.52 | 3.455 | 4.567 | 5.270 | 0.248 | 5.316 | 0.0000 | 300.6× | 0.0 | 90 | no |

⚠️ **Delay calibration is NOISE for this arm** — normalised peak correlation 0.118. The +14.96 ms estimate is recorded but **is not used as a fact anywhere in this study**.

### `focalcodec_50hz_65k_causal`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.0 | 4 | PASS | 3.11 | 3.064 | 3.236 | 3.310 | 0.105 | 3.665 | 0.0000 | 26.1× | 0.0 | 720 | no |
| 160.0 | 8 | PASS | 3.02 | 3.016 | 3.182 | 3.359 | 0.084 | 3.851 | 0.0000 | 53.0× | 0.0 | 330 | no |
| 320.0 | 16 | PASS | 2.99 | 2.964 | 3.125 | 3.377 | 0.078 | 4.145 | 0.0000 | 107.8× | 0.0 | 150 | no |
| 640.0 | 32 | PASS | 3.24 | 3.177 | 3.324 | 3.421 | 0.084 | 3.436 | 0.0000 | 200.3× | 0.0 | 90 | no |
| 1040.0 | 52 | PASS | 3.23 | 3.252 | 3.448 | 3.624 | 0.178 | 3.697 | 0.0000 | 320.4× | 0.0 | 90 | no |

⚠️ **Delay calibration is NOISE for this arm** — normalised peak correlation 0.151. The +27.79 ms estimate is recorded but **is not used as a fact anywhere in this study**.

### `focalcodec_50hz`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.1 | 4 | PASS | 2.92 | 2.837 | 3.015 | 3.111 | 0.099 | 3.547 | 0.0000 | 28.1× | 0.0 | 720 | no |
| 160.2 | 8 | PASS | 2.89 | 2.844 | 3.009 | 3.091 | 0.097 | 3.103 | 0.0000 | 56.1× | 0.0 | 330 | no |
| 320.4 | 16 | PASS | 2.87 | 2.819 | 3.004 | 3.092 | 0.082 | 3.120 | 0.0000 | 113.1× | 0.0 | 150 | no |
| 640.8 | 32 | PASS | 3.29 | 3.235 | 4.087 | 4.796 | 0.476 | 4.907 | 0.0000 | 196.1× | 0.0 | 90 | no |
| 1041.3 | 52 | PASS | 3.09 | 3.039 | 3.382 | 3.426 | 0.170 | 3.597 | 0.0000 | 341.3× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 4 | 80.1 | 2.814 | 28.4× | PASS |
| 8 | 160.2 | 2.830 | 28.3× | PASS |
| 16 | 320.4 | 3.195 | 25.1× | PASS |

⚠️ **Delay calibration is NOISE for this arm** — normalised peak correlation 0.083. The +29.12 ms estimate is recorded but **is not used as a fact anywhere in this study**.

### `focalcodec_25hz`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.1 | 2 | PASS | 2.91 | 2.857 | 2.989 | 3.062 | 0.093 | 3.288 | 0.0000 | 28.0× | 0.0 | 720 | no |
| 160.2 | 4 | PASS | 2.94 | 2.842 | 2.999 | 3.128 | 0.083 | 3.239 | 0.0000 | 56.2× | 0.0 | 330 | no |
| 320.4 | 8 | ⛔ FAIL | 2.87 | 2.838 | 3.077 | 4.068 | 0.077 | 4.223 | 0.0000 | 112.6× | 0.0 | 150 | no |
| 640.8 | 16 | PASS | 3.17 | 3.081 | 3.306 | 3.855 | 0.130 | 4.120 | 0.0000 | 205.5× | 0.0 | 90 | no |
| 1041.3 | 26 | PASS | 3.07 | 3.048 | 3.231 | 3.275 | 0.064 | 3.295 | 0.0000 | 340.5× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 2 | 80.1 | 2.853 | 28.0× | PASS |
| 4 | 160.2 | 2.850 | 28.0× | PASS |
| 8 | 320.4 | 3.063 | 26.1× | FAIL |

⚠️ **Delay calibration is NOISE for this arm** — normalised peak correlation 0.099. The +36.44 ms estimate is recorded but **is not used as a fact anywhere in this study**.

### `focalcodec_12_5hz`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.1 | 1 | ⛔ FAIL | 2.99 | 2.925 | 3.101 | 3.225 | 0.085 | 3.514 | 0.0000 | 27.3× | 0.0 | 720 | no |
| 160.2 | 2 | ⛔ FAIL | 2.93 | 2.860 | 3.030 | 3.100 | 0.081 | 3.810 | 0.0000 | 55.9× | 0.0 | 330 | no |
| 320.4 | 4 | ⛔ FAIL | 2.93 | 2.865 | 3.076 | 3.206 | 0.084 | 3.914 | 0.0000 | 111.1× | 0.0 | 150 | no |
| 640.8 | 8 | PASS | 3.18 | 3.090 | 3.714 | 3.738 | 0.111 | 3.763 | 0.0000 | 205.7× | 0.0 | 90 | no |
| 1041.3 | 13 | PASS | 3.05 | 3.004 | 3.181 | 3.310 | 0.129 | 3.706 | 0.0000 | 345.1× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 80.1 | 2.996 | 26.6× | FAIL |
| 2 | 160.2 | 2.869 | 27.9× | FAIL |
| 4 | 320.4 | 3.080 | 26.0× | FAIL |

⚠️ **Delay calibration is NOISE for this arm** — normalised peak correlation 0.197. The +28.62 ms estimate is recorded but **is not used as a fact anywhere in this study**.

### `mimi_q8`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 79.7 | 1 | PASS | 9.85 | 9.839 | 10.243 | 11.270 | 0.217 | 11.964 | 0.0000 | 8.1× | 0.0 | 720 | no |
| 159.4 | 2 | PASS | 10.13 | 9.972 | 10.336 | 10.489 | 0.207 | 10.682 | 0.0000 | 16.0× | 0.0 | 330 | no |
| 239.1 | 3 | PASS | 9.99 | 9.996 | 10.355 | 10.400 | 0.241 | 10.960 | 0.0000 | 24.0× | 0.0 | 210 | no |
| 398.5 | 5 | PASS | 10.01 | 9.965 | 10.235 | 10.495 | 0.179 | 11.301 | 0.0000 | 40.1× | 0.0 | 120 | no |
| 717.3 | 9 | PASS | 10.40 | 10.392 | 10.730 | 10.924 | 0.196 | 11.036 | 0.0000 | 69.3× | 0.0 | 90 | no |
| 1036.1 | 13 | PASS | 10.43 | 10.402 | 10.807 | 10.984 | 0.231 | 11.065 | 0.0000 | 99.9× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 79.7 | 9.999 | 8.0× | PASS |
| 2 | 159.4 | 9.914 | 8.1× | PASS |
| 4 | 318.8 | 9.987 | 8.0× | PASS |

### `mimi_q32`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 79.7 | 1 | PASS | 10.33 | 10.331 | 10.678 | 10.881 | 0.236 | 11.351 | 0.0000 | 7.7× | 0.0 | 720 | no |
| 159.4 | 2 | PASS | 10.55 | 10.487 | 10.812 | 10.995 | 0.246 | 11.504 | 0.0000 | 15.2× | 0.0 | 330 | no |
| 239.1 | 3 | PASS | 10.54 | 10.453 | 10.844 | 11.035 | 0.215 | 11.796 | 0.0000 | 22.9× | 0.0 | 210 | no |
| 398.5 | 5 | PASS | 10.44 | 10.393 | 12.349 | 12.527 | 0.281 | 12.612 | 0.0000 | 38.4× | 0.0 | 120 | no |
| 717.3 | 9 | PASS | 11.58 | 11.590 | 12.877 | 13.511 | 0.468 | 13.787 | 0.0000 | 62.1× | 0.0 | 90 | no |
| 1036.1 | 13 | PASS | 10.90 | 10.844 | 11.216 | 11.446 | 0.211 | 11.570 | 0.0000 | 95.8× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 79.7 | 10.483 | 7.6× | PASS |
| 2 | 159.4 | 10.439 | 7.7× | PASS |
| 4 | 318.8 | 10.415 | 7.7× | PASS |

### `encodec24_q8`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 26.7 | 2 | PASS | 5.44 | 5.364 | 5.777 | 6.130 | 0.212 | 9.526 | 0.0000 | 5.0× | 0.0 | 2220 | no |
| 53.3 | 4 | PASS | 5.49 | 5.448 | 5.802 | 6.016 | 0.231 | 6.481 | 0.0000 | 9.8× | 0.0 | 1080 | no |
| 93.3 | 7 | PASS | 5.94 | 5.908 | 6.920 | 7.496 | 0.441 | 7.783 | 0.0000 | 15.8× | 0.0 | 600 | no |
| 173.3 | 13 | PASS | 5.73 | 5.626 | 5.982 | 6.298 | 0.212 | 6.407 | 0.0000 | 30.8× | 0.0 | 300 | no |
| 333.3 | 25 | PASS | 5.96 | 5.961 | 7.336 | 8.925 | 0.211 | 9.394 | 0.0000 | 55.9× | 0.0 | 150 | no |
| 653.3 | 49 | PASS | 6.65 | 6.642 | 7.141 | 7.267 | 0.269 | 7.332 | 0.0000 | 98.4× | 0.0 | 90 | no |
| 1013.3 | 76 | PASS | 7.34 | 7.394 | 10.740 | 13.753 | 0.371 | 14.320 | 0.0000 | 137.2× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 13.3 | 5.447 | 17.1× | PASS |
| 2 | 26.7 | 5.489 | 17.0× | PASS |
| 4 | 53.3 | 5.557 | 16.8× | PASS |

### `encodec_vocos`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 26.7 | 2 | PASS | 1.97 | 1.907 | 2.368 | 2.733 | 0.145 | 3.199 | 0.0000 | 14.0× | 0.0 | 2220 | no |
| 53.3 | 4 | PASS | 1.98 | 1.917 | 2.405 | 2.805 | 0.165 | 3.422 | 0.0000 | 27.8× | 0.0 | 1080 | no |
| 93.3 | 7 | PASS | 1.94 | 1.902 | 2.189 | 2.662 | 0.117 | 2.923 | 0.0000 | 49.0× | 0.0 | 600 | no |
| 173.3 | 13 | PASS | 1.95 | 1.914 | 2.301 | 2.707 | 0.180 | 2.881 | 0.0000 | 90.2× | 0.0 | 300 | no |
| 333.3 | 25 | PASS | 2.21 | 2.122 | 2.572 | 2.741 | 0.147 | 2.786 | 0.0000 | 155.8× | 0.0 | 150 | no |
| 653.3 | 49 | PASS | 2.42 | 2.194 | 2.746 | 3.146 | 0.379 | 3.307 | 0.0000 | 294.3× | 0.0 | 90 | no |
| 1013.3 | 76 | PASS | 2.15 | 2.045 | 2.510 | 2.558 | 0.457 | 2.657 | 0.0000 | 489.8× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 13.3 | 1.912 | 48.7× | PASS |
| 2 | 26.7 | 1.907 | 48.8× | PASS |
| 4 | 53.3 | 1.909 | 48.8× | PASS |

### `dac44`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 23.2 | 2 | PASS | 3.15 | 3.101 | 3.497 | 3.971 | 0.169 | 7.050 | 0.0000 | 7.5× | 0.0 | 2550 | no |
| 46.4 | 4 | PASS | 3.14 | 3.062 | 3.267 | 3.431 | 0.098 | 3.753 | 0.0000 | 15.2× | 0.0 | 1260 | no |
| 81.3 | 7 | PASS | 3.13 | 3.088 | 3.252 | 3.525 | 0.095 | 3.955 | 0.0000 | 26.3× | 0.0 | 690 | no |
| 162.5 | 14 | PASS | 3.26 | 3.240 | 3.561 | 3.955 | 0.108 | 7.449 | 0.0000 | 50.1× | 0.0 | 330 | no |
| 325.1 | 28 | PASS | 3.63 | 3.617 | 3.994 | 4.159 | 0.127 | 4.523 | 0.0000 | 89.8× | 0.0 | 150 | no |
| 650.2 | 56 | PASS | 4.64 | 4.619 | 4.855 | 5.138 | 0.101 | 5.265 | 0.0000 | 140.6× | 0.0 | 90 | no |
| 1010.1 | 87 | PASS | 6.47 | 6.487 | 7.551 | 7.656 | 0.149 | 8.233 | 0.0000 | 155.8× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 11.6 | 3.104 | 26.2× | PASS |
| 2 | 23.2 | 3.114 | 26.1× | PASS |
| 4 | 46.4 | 3.289 | 24.7× | PASS |

### `dualcodec_12hz_v1`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.1 | 1 | PASS | 3.88 | 3.823 | 3.956 | 4.049 | 0.098 | 4.342 | 0.0000 | 20.9× | 0.0 | 720 | no |
| 160.2 | 2 | PASS | 3.95 | 3.891 | 4.137 | 4.365 | 0.141 | 4.855 | 0.0000 | 41.1× | 0.0 | 330 | no |
| 320.4 | 4 | PASS | 3.95 | 3.900 | 4.124 | 4.319 | 0.156 | 4.575 | 0.0000 | 81.8× | 0.0 | 150 | no |
| 640.8 | 8 | PASS | 3.96 | 3.903 | 5.100 | 5.721 | 0.147 | 6.364 | 0.0000 | 162.9× | 0.0 | 90 | no |
| 1041.3 | 13 | PASS | 4.02 | 3.963 | 4.151 | 4.304 | 0.122 | 4.311 | 0.0000 | 261.5× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 80.1 | 3.862 | 20.7× | PASS |
| 2 | 160.2 | 4.176 | 19.1× | PASS |
| 4 | 320.4 | 3.953 | 20.2× | PASS |

### `dualcodec_25hz_v1`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 40.1 | 1 | PASS | 3.50 | 3.456 | 3.604 | 3.752 | 0.096 | 4.470 | 0.0000 | 11.6× | 0.0 | 1470 | no |
| 80.1 | 2 | PASS | 3.56 | 3.475 | 3.697 | 4.021 | 0.116 | 4.452 | 0.0000 | 23.0× | 0.0 | 720 | no |
| 160.2 | 4 | PASS | 3.54 | 3.504 | 3.730 | 3.957 | 0.131 | 4.020 | 0.0000 | 45.6× | 0.0 | 330 | no |
| 320.4 | 8 | PASS | 3.64 | 3.617 | 4.284 | 4.530 | 0.115 | 4.935 | 0.0000 | 88.4× | 0.0 | 150 | no |
| 640.8 | 16 | PASS | 4.00 | 3.986 | 4.364 | 4.666 | 0.110 | 4.848 | 0.0000 | 160.5× | 0.0 | 90 | no |
| 1001.3 | 25 | PASS | 4.56 | 4.537 | 5.298 | 5.461 | 0.177 | 5.873 | 0.0000 | 220.1× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 40.1 | 3.514 | 22.8× | PASS |
| 2 | 80.1 | 3.489 | 22.9× | PASS |
| 4 | 160.2 | 3.539 | 22.6× | PASS |

### `qwen3_tts_tokenizer_12hz`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.0 | 1 | PASS | 16.00 | 15.902 | 16.523 | 17.394 | 0.345 | 208.105 | 0.0013 | 5.0× | 0.0 | 720 | no |
| 160.0 | 2 | PASS | 16.14 | 16.063 | 16.663 | 17.157 | 0.335 | 17.638 | 0.0000 | 10.0× | 0.0 | 330 | no |
| 320.0 | 4 | PASS | 15.90 | 15.882 | 16.431 | 17.265 | 0.258 | 17.425 | 0.0000 | 20.1× | 0.0 | 150 | no |
| 640.0 | 8 | PASS | 15.96 | 15.761 | 16.859 | 17.598 | 0.483 | 20.072 | 0.0000 | 40.4× | 0.0 | 90 | no |
| 1040.0 | 13 | PASS | 16.53 | 16.551 | 17.061 | 17.147 | 0.336 | 17.179 | 0.0000 | 62.9× | 0.0 | 90 | no |

**Underruns at:** 80.0 ms. **First underrun-free condition: 160.0 ms.**

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 80.0 | 16.111 | 5.0× | PASS |
| 2 | 160.0 | 15.970 | 5.0× | PASS |
| 4 | 320.0 | 15.871 | 5.0× | PASS |

### `fish_modified_dac`  ⛔ NOT COMPARABLE to decbench arms (§7.2)

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 46.4 | 1 | PASS | 10.15 | 10.071 | 13.383 | 16.352 | 1.192 | 21.816 | 0.0000 | 4.6× | 0.0 | 1260 | no |
| 92.9 | 2 | PASS | 11.22 | 11.630 | 14.431 | 16.184 | 1.532 | 25.947 | 0.0000 | 8.0× | 0.0 | 600 | no |
| 185.8 | 4 | PASS | 11.19 | 11.640 | 14.414 | 15.716 | 1.632 | 20.375 | 0.0000 | 16.0× | 0.0 | 270 | no |
| 325.1 | 7 | PASS | 12.75 | 12.705 | 14.535 | 21.946 | 0.272 | 25.952 | 0.0000 | 25.6× | 0.0 | 150 | no |
| 650.2 | 14 | PASS | 12.14 | 12.295 | 18.091 | 24.483 | 1.458 | 25.691 | 0.0000 | 53.0× | 0.0 | 90 | no |
| 1021.7 | 22 | PASS | 13.76 | 13.967 | 17.329 | 19.712 | 1.185 | 24.369 | 0.0000 | 73.4× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 46.4 | 12.662 | 7.3× | PASS |
| 2 | 92.9 | 12.698 | 7.3× | PASS |
| 4 | 185.8 | 12.660 | 7.3× | PASS |

### `melflow`

**Per-frame streaming — this arm's OWN decode granularity, 16 ms.** steady p50 74.895 ms · p95 83.035 · p99 95.873 · IQR 4.156 · max 118.113 · underrun 1.0000 · RT margin 0.21× (7560 steady-state frames).

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 32.0 | 2 | ⛔ None | NOT ESTABLISHED | 150.088 | 166.062 | 184.810 | 7.623 | 223.393 | 1.0000 | 0.2× | 0.0 | 3780 | yes |
| 48.0 | 3 | ⛔ None | NOT ESTABLISHED | 225.244 | 249.362 | 276.520 | 11.291 | 323.556 | 1.0000 | 0.2× | 0.0 | 2520 | yes |
| 80.0 | 5 | ⛔ None | NOT ESTABLISHED | 375.912 | 416.040 | 454.962 | 18.509 | 519.280 | 1.0000 | 0.2× | 0.0 | 1500 | yes |
| 160.0 | 10 | ⛔ None | NOT ESTABLISHED | 753.093 | 833.839 | 876.526 | 37.946 | 991.817 | 1.0000 | 0.2× | 0.0 | 750 | yes |
| 320.0 | 20 | ⛔ None | NOT ESTABLISHED | 1508.539 | 1659.040 | 1722.527 | 70.603 | 1797.739 | 1.0000 | 0.2× | 0.0 | 360 | yes |
| 640.0 | 40 | ⛔ None | NOT ESTABLISHED | 3025.810 | 3322.127 | 3390.825 | 119.882 | 3393.528 | 1.0000 | 0.2× | 0.0 | 180 | yes |
| 1008.0 | 63 | ⛔ None | NOT ESTABLISHED | 4765.833 | 5227.303 | 5321.803 | 183.569 | 5381.943 | 1.0000 | 0.2× | 0.0 | 120 | yes |

**1 cell(s) failed and are recorded, not dropped:**

- `ttfa` None — None

⛔ **TTFA NOT ESTABLISHED.** PROTOCOL amendment 9.7. §10.3 stops the clock at the first PLAYABLE PCM BLOCK passing §8. This arm emits spectrogram frames; producing PCM from a partial stream needs an overlap-add stage that amendment 8 records as NOT ESTABLISHED.

  Cell state: first block §8 **PASS**, 256 samples; split-iSTFT control **121.39%**, deficit 256 samples.

### `vocos_mel24`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 21.3 | 2 | ⛔ FAIL | 1.42 | 1.354 | 1.467 | 1.555 | 0.065 | 2.976 | 0.0000 | 15.8× | 0.0 | 2760 | no |
| 42.7 | 4 | ⛔ FAIL | 1.40 | 1.347 | 1.464 | 1.578 | 0.062 | 1.775 | 0.0000 | 31.6× | 0.0 | 1350 | no |
| 85.3 | 8 | ⛔ FAIL | 1.37 | 1.333 | 1.622 | 1.740 | 0.060 | 1.884 | 0.0000 | 64.0× | 0.0 | 660 | no |
| 160.0 | 15 | ⛔ FAIL | 1.39 | 1.344 | 1.566 | 1.885 | 0.071 | 3.849 | 0.0000 | 118.5× | 0.0 | 330 | no |
| 320.0 | 30 | ⛔ FAIL | 1.62 | 1.594 | 1.975 | 2.165 | 0.146 | 2.259 | 0.0000 | 199.9× | 0.0 | 150 | no |
| 640.0 | 60 | ⛔ FAIL | 1.86 | 1.803 | 2.359 | 2.614 | 0.374 | 2.888 | 0.0000 | 351.8× | 0.0 | 90 | no |
| 1002.7 | 94 | ⛔ FAIL | 1.59 | 1.538 | 1.860 | 2.122 | 0.136 | 2.348 | 0.0000 | 642.6× | 0.0 | 90 | no |

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 10.7 | 1.340 | 63.6× | FAIL |
| 2 | 21.3 | 1.339 | 63.6× | FAIL |
| 4 | 42.7 | 1.343 | 63.5× | FAIL |

⚠️ **Delay calibration is NOISE for this arm** — normalised peak correlation 0.259. The +7.67 ms estimate is recorded but **is not used as a fact anywhere in this study**.

### `bigvgan22`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 23.2 | 2 | PASS | 28.10 | 27.990 | 30.393 | 33.273 | 1.523 | 47.190 | 1.0000 | 0.8× | 0.0 | 2550 | no |
| 46.4 | 4 | PASS | 27.80 | 27.871 | 30.047 | 34.494 | 1.484 | 50.793 | 0.0008 | 1.7× | 0.0 | 1260 | no |
| 81.3 | 7 | PASS | 27.64 | 27.441 | 31.765 | 41.679 | 1.162 | 48.272 | 0.0000 | 3.0× | 0.0 | 690 | no |
| 162.5 | 14 | PASS | 28.51 | 27.877 | 30.364 | 36.023 | 1.592 | 40.069 | 0.0000 | 5.8× | 0.0 | 330 | no |
| 325.1 | 28 | PASS | 27.34 | 26.978 | 28.881 | 31.748 | 0.666 | 34.488 | 0.0000 | 12.0× | 0.0 | 150 | no |
| 650.2 | 56 | PASS | 26.82 | 26.642 | 28.058 | 29.140 | 0.520 | 29.506 | 0.0000 | 24.4× | 0.0 | 90 | no |
| 1010.1 | 87 | PASS | 27.57 | 27.255 | 29.306 | 30.629 | 1.708 | 32.574 | 0.0000 | 37.0× | 0.0 | 90 | no |

**Underruns at:** 23.2 ms, 46.4 ms. **First underrun-free condition: 81.3 ms.**

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 11.6 | 27.368 | 3.0× | PASS |
| 2 | 23.2 | 27.998 | 2.9× | PASS |
| 4 | 46.4 | 27.261 | 3.0× | PASS |

### `griffinlim`

| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | underrun | RT p50 | lookahead ms | n | composed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 42.7 | 4 | ⛔ FAIL | 11.26 | 11.153 | 11.582 | 11.808 | 0.254 | 17.850 | 0.0000 | 3.8× | 0.0 | 1350 | no |
| 85.3 | 8 | ⛔ FAIL | 11.27 | 11.125 | 11.418 | 11.589 | 0.228 | 11.748 | 0.0000 | 7.7× | 0.0 | 660 | no |
| 160.0 | 15 | ⛔ FAIL | 11.30 | 11.168 | 11.540 | 11.710 | 0.271 | 11.776 | 0.0000 | 14.3× | 0.0 | 330 | no |
| 320.0 | 30 | ⛔ FAIL | 11.26 | 11.180 | 11.623 | 11.740 | 0.305 | 12.048 | 0.0000 | 28.6× | 0.0 | 150 | no |
| 640.0 | 60 | ⛔ FAIL | 11.26 | 11.091 | 11.573 | 11.720 | 0.229 | 12.455 | 0.0000 | 57.5× | 0.0 | 90 | no |
| 1002.7 | 94 | ⛔ FAIL | 11.13 | 11.048 | 11.425 | 11.586 | 0.219 | 11.658 | 0.0000 | 90.6× | 0.0 | 90 | no |

**1 cell(s) failed and are recorded, not dropped:**

- `stream` {'requested_ms': 20.0, 'units': 2, 'effective_ms': 21.3334} — RuntimeError: Argument #4: Padding size should be less than the corresponding input dimension, but got: padding (512, 512) at dimension 2 of input [1, 1, 256]

**§10.2 chunked-with-overlap — the context this arm needs is part of its cost:**

| left context units | lookahead ms | steady p50 ms | RT margin | §8 |
|---|---|---|---|---|
| 1 | 10.7 | 11.176 | 7.6× | FAIL |
| 2 | 21.3 | 11.098 | 7.7× | FAIL |
| 4 | 42.7 | 11.138 | 7.7× | FAIL |

⚠️ **Delay calibration is NOISE for this arm** — normalised peak correlation 0.364. The +1.12 ms estimate is recorded but **is not used as a fact anywhere in this study**.

## Disposition of the §7.2 VRAM re-run rule

**Frozen rule:** §7.2: an arm whose before/after VRAM reading moves by more than 200 MiB is re-run and both runs are kept.

**167 of 366 cells exceed the threshold.** Disposition: **SUPERSEDED BY PROTOCOL AMENDMENT 10 - see PROTOCOL.md**.

The rule was written for a design in which one model stays resident. This harness holds a model cache of ONE and reloads on every arm switch, precisely so that max_memory_allocated is the arm's own working set rather than a co-resident model's weights. Under that design a >200 MiB before/after move is the EXPECTED signature of the intended unload/reload, not the contamination the rule was written to catch. Re-running on it would re-run most of the benchmark and would flag the same cells again, without testing anything.

**Replacement check:** What the rule existed to detect - a cell whose memory state was contaminated by another cell - is instead tested by the per-repetition `torch.cuda.reset_peak_memory_stats()` before every measured cell, so `peak_alloc_MiB` cannot inherit a previous cell's peak, and by the longrun VRAM-drift cell, which measures memory growth across a sustained run directly.

## Boundary integrity (§10.6) — each decoder against ITSELF

⚠️ **This measures what chunking cost a decoder relative to its own full-context output. It is not a quality ranking between decoders, and no output may present it as one. QUALITY COMPARISON NOT ESTABLISHED.**

| arm | chunk ms | seams | seam jump ratio (median) | max | local diff RMS | length deficit |
|---|---|---|---|---|---|---|
| `focalcodec_50hz_4k_causal` | 80.0 | 24 | 1.000 | 1.003 | 0.0006 | 0 |
| `focalcodec_50hz_4k_causal` | 160.0 | 11 | 1.000 | 1.001 | 0.0008 | 1920 |
| `focalcodec_50hz_4k_causal` | 320.0 | 5 | 1.000 | 1.001 | 0.0010 | 1920 |
| `focalcodec_50hz_4k_causal` | 640.0 | 2 | 1.002 | 1.003 | 0.0148 | 1920 |
| `focalcodec_50hz_2k_causal` | 80.0 | 24 | 1.000 | 1.001 | 0.0006 | 0 |
| `focalcodec_50hz_2k_causal` | 160.0 | 11 | 1.000 | 1.001 | 0.0008 | 1920 |
| `focalcodec_50hz_2k_causal` | 320.0 | 5 | 1.000 | 1.000 | 0.0008 | 1920 |
| `focalcodec_50hz_2k_causal` | 640.0 | 2 | 1.000 | 1.000 | 0.0038 | 1920 |
| `focalcodec_50hz_65k_causal` | 80.0 | 24 | 1.000 | 1.001 | 0.0006 | 0 |
| `focalcodec_50hz_65k_causal` | 160.0 | 11 | 1.000 | 1.003 | 0.0006 | 1920 |
| `focalcodec_50hz_65k_causal` | 320.0 | 5 | 1.000 | 1.003 | 0.0003 | 1920 |
| `focalcodec_50hz_65k_causal` | 640.0 | 2 | 1.002 | 1.004 | 0.0052 | 1920 |
| `focalcodec_50hz` | 80.1 | 24 | 0.870 | 24.630 | 1.4714 | 0 |
| `focalcodec_50hz` | 160.2 | 11 | 0.362 | 4.506 | 1.1148 | 1280 |
| `focalcodec_50hz` | 320.4 | 5 | 0.161 | 1.743 | 1.0932 | 1280 |
| `focalcodec_50hz` | 640.8 | 2 | 0.880 | 1.748 | 1.6675 | 1280 |
| `focalcodec_25hz` | 80.1 | 24 | 0.381 | 89.404 | 1.6984 | 0 |
| `focalcodec_25hz` | 160.2 | 11 | 0.320 | 43.386 | 1.1770 | 1280 |
| `focalcodec_25hz` | 320.4 | 5 | 0.128 | 24.992 | 1.0155 | 1280 |
| `focalcodec_25hz` | 640.8 | 2 | 0.372 | 0.530 | 1.0552 | 1280 |
| `focalcodec_12_5hz` | 80.1 | 24 | 0.218 | 11.583 | 1.0124 | 0 |
| `focalcodec_12_5hz` | 160.2 | 11 | 0.127 | 12.630 | 1.0131 | 1280 |
| `focalcodec_12_5hz` | 320.4 | 5 | 0.112 | 6.451 | 1.0002 | 1280 |
| `focalcodec_12_5hz` | 640.8 | 2 | 0.162 | 0.276 | 1.0094 | 1280 |
| `mimi_q8` | 79.7 | 24 | 1.843 | 108.012 | 1.4854 | 0 |
| `mimi_q8` | 159.4 | 11 | 1.239 | 76.323 | 1.0948 | 1920 |
| `mimi_q8` | 239.1 | 7 | 1.413 | 66.959 | 2.9673 | 1920 |
| `mimi_q8` | 398.5 | 4 | 1.081 | 91.027 | 0.9716 | 0 |
| `mimi_q8` | 717.3 | 1 | 1.000 | 1.000 | 0.8023 | 13440 |
| `mimi_q32` | 79.7 | 24 | 2.103 | 63.009 | 1.3013 | 0 |
| `mimi_q32` | 159.4 | 11 | 3.535 | 59.662 | 0.8677 | 1920 |
| `mimi_q32` | 239.1 | 7 | 1.210 | 57.902 | 2.2117 | 1920 |
| `mimi_q32` | 398.5 | 4 | 0.981 | 63.005 | 0.8380 | 0 |
| `mimi_q32` | 717.3 | 1 | 1.000 | 1.000 | 0.7579 | 13440 |
| `encodec24_q8` | 26.7 | 74 | 2.336 | 165.430 | 1.6277 | 0 |
| `encodec24_q8` | 53.3 | 36 | 2.314 | 112.938 | 1.4491 | 640 |
| `encodec24_q8` | 93.3 | 20 | 1.414 | 23.553 | 0.7340 | 960 |
| `encodec24_q8` | 173.3 | 10 | 2.541 | 18.954 | 0.4857 | 2240 |
| `encodec24_q8` | 333.3 | 5 | 0.986 | 21.799 | 0.7687 | 0 |
| `encodec24_q8` | 653.3 | 2 | 1.494 | 1.988 | 0.3960 | 960 |
| `encodec_vocos` | 26.7 | 74 | 2.457 | 41.855 | 1.9650 | 0 |
| `encodec_vocos` | 53.3 | 36 | 1.723 | 16.155 | 1.0402 | 640 |
| `encodec_vocos` | 93.3 | 20 | 1.478 | 12.980 | 1.0379 | 960 |
| `encodec_vocos` | 173.3 | 10 | 1.543 | 15.643 | 0.8737 | 2240 |
| `encodec_vocos` | 333.3 | 5 | 0.890 | 11.566 | 1.1867 | 0 |
| `encodec_vocos` | 653.3 | 2 | 1.547 | 2.139 | 0.6760 | 960 |
| `dac44` | 23.2 | 85 | 2.506 | 68.864 | 1.3696 | 0 |
| `dac44` | 46.4 | 42 | 1.972 | 62.408 | 1.1330 | 0 |
| `dac44` | 81.3 | 23 | 2.105 | 60.427 | 1.2780 | 2048 |
| `dac44` | 162.5 | 11 | 1.167 | 60.674 | 1.0101 | 2048 |
| `dac44` | 325.1 | 5 | 0.695 | 45.093 | 1.0101 | 2048 |
| `dac44` | 650.2 | 2 | 1.054 | 1.413 | 0.5869 | 2048 |
| `dualcodec_12hz_v1` | 80.1 | 24 | 2.216 | 31.361 | 1.6433 | 96 |
| `dualcodec_12hz_v1` | 160.2 | 11 | 2.328 | 13.021 | 1.4915 | 1964 |
| `dualcodec_12hz_v1` | 320.4 | 5 | 2.216 | 6.799 | 1.3274 | 1940 |
| `dualcodec_12hz_v1` | 640.8 | 2 | 2.305 | 2.658 | 1.4009 | 1928 |
| `dualcodec_25hz_v1` | 40.1 | 49 | 3.130 | 305.338 | 1.7810 | 196 |
| `dualcodec_25hz_v1` | 80.1 | 24 | 3.403 | 71.366 | 1.9112 | 96 |
| `dualcodec_25hz_v1` | 160.2 | 11 | 4.557 | 28.933 | 2.5496 | 1964 |
| `dualcodec_25hz_v1` | 320.4 | 5 | 2.725 | 7.592 | 1.9869 | 1940 |
| `dualcodec_25hz_v1` | 640.8 | 2 | 2.909 | 4.241 | 1.6296 | 1928 |
| `dualcodec_25hz_v1` | 1001.3 | 1 | 2.202 | 2.202 | 1.3446 | 4 |
| `qwen3_tts_tokenizer_12hz` | 80.0 | 24 | 1.380 | 8.116 | 1.0978 | 0 |
| `qwen3_tts_tokenizer_12hz` | 160.0 | 11 | 1.145 | 6.796 | 1.1945 | 1920 |
| `qwen3_tts_tokenizer_12hz` | 320.0 | 5 | 0.890 | 2.602 | 0.8984 | 1920 |
| `qwen3_tts_tokenizer_12hz` | 640.0 | 2 | 2.041 | 2.588 | 0.9763 | 1920 |
| `fish_modified_dac` | 46.4 | 42 | 1.225 | 15.760 | 1.0545 | 0 |
| `fish_modified_dac` | 92.9 | 20 | 2.335 | 13.458 | 1.0746 | 2048 |
| `fish_modified_dac` | 185.8 | 9 | 2.185 | 8.268 | 0.9318 | 6144 |
| `fish_modified_dac` | 325.1 | 5 | 1.250 | 4.226 | 0.7041 | 2048 |
| `fish_modified_dac` | 650.2 | 2 | 3.195 | 4.957 | 0.7851 | 2048 |
| `melflow` | whole stream | 0 | — | — | 0.2126% | — |
| `vocos_mel24` | 21.3 | 92 | 1.998 | 533.366 | 1.4799 | 23808 |
| `vocos_mel24` | 42.7 | 45 | 1.457 | 363.827 | 1.4862 | 12288 |
| `vocos_mel24` | 85.3 | 22 | 2.077 | 30.620 | 1.3776 | 6400 |
| `vocos_mel24` | 160.0 | 11 | 2.645 | 12.485 | 1.3182 | 4608 |
| `vocos_mel24` | 320.0 | 5 | 1.588 | 4.973 | 1.1401 | 3072 |
| `vocos_mel24` | 640.0 | 2 | 0.682 | 0.862 | 1.1630 | 2304 |
| `bigvgan22` | 23.2 | 85 | 1.037 | 12.877 | 1.3535 | 0 |
| `bigvgan22` | 46.4 | 42 | 1.161 | 9.993 | 1.3533 | 0 |
| `bigvgan22` | 81.3 | 23 | 1.292 | 10.436 | 1.3953 | 1024 |
| `bigvgan22` | 162.5 | 11 | 1.013 | 11.935 | 1.4743 | 1024 |
| `bigvgan22` | 325.1 | 5 | 1.216 | 3.361 | 1.4940 | 1024 |
| `bigvgan22` | 650.2 | 2 | 2.107 | 3.360 | 1.4923 | 1024 |
| `griffinlim` | 21.3 | — | — | — | — | FAILED: RuntimeError: Argument #4: Padding size should be  |
| `griffinlim` | 42.7 | 45 | 1.606 | 279.296 | 1.3316 | 12288 |
| `griffinlim` | 85.3 | 22 | 1.876 | 128.600 | 1.3798 | 6400 |
| `griffinlim` | 160.0 | 11 | 3.112 | 9.341 | 1.3368 | 4608 |
| `griffinlim` | 320.0 | 5 | 1.905 | 7.535 | 1.3237 | 3072 |
| `griffinlim` | 640.0 | 2 | 1.825 | 2.705 | 1.2891 | 2304 |

## Totals

```
MEASURED - CELLS COMPLETED AND ADMISSIBLE     19   focalcodec_50hz_4k_causal, focalcodec_50hz_2k_causal, focalcodec_50hz_65k_causal, focalcodec_50hz, focalcodec_25hz, focalcodec_12_5hz, mimi_q8, mimi_q32, encodec24_q8, encodec_vocos, dac44, dualcodec_12hz_v1, dualcodec_25hz_v1, qwen3_tts_tokenizer_12hz, fish_modified_dac, melflow, vocos_mel24, bigvgan22, griffinlim
BLOCKED - PLATFORM                             1   nanocodec
-------------------------------------------- ---
TOTAL                                         20
```

