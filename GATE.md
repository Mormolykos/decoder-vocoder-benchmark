# CANDIDATE GATE — final classification before download and freeze

**2026-09-10. No GPU used. Nothing downloaded yet. `PROTOCOL.md` not frozen.**

Product design target, owner-set: **mono, 24 kHz output.**

⚠️ **24 kHz is the production target, NOT an exclusion criterion.** We are building
from scratch, so a 16 kHz published implementation can win the *architectural*
question and be adapted and trained at 24 kHz afterwards. Sample rate stays an
**ARCHITECTURAL VARIABLE** (`PROTOCOL.md` §6) — never normalised away, never
silently resampled into false equivalence. The design is deliberately three-point:

| band | role |
|---|---|
| **16 kHz** | the causal-streaming frontier — lowest-compute causal ideas |
| **22–24 kHz** | our intended production operating point |
| **48 kHz** | the high-bandwidth causal ceiling |

---

## ⭐ The finding that reshaped this gate

**For a TTS build, only the DECODER needs to be causal.**

The encoder runs at training time, on complete utterances, offline. At inference
the generator emits tokens directly — no encoder is in the serving path at all.
NVIDIA's NanoCodec makes the point concrete: **non-causal encoder, causal
HiFi-GAN decoder.**

So "this codec is non-causal" is the wrong question. The question is **"is its
decoder causal?"** — and several candidates previously carrying contrary
architectural evidence survive on that basis. This benchmark measures decoders,
which means it was already asking the right question; the survey nearly excluded
candidates for the wrong reason.

---

## MUST BENCHMARK

| arm | why | rate | licence | source |
|---|---|---|---|---|
| **NanoCodec 22 kHz** (NVIDIA NeMo) | **causal HiFi-GAN decoder** · FSQ, 4 codebooks × 4032 · 12.5 fps / 0.6 kbps and a 21.5 fps / 1.89 kbps variant · **22.05 kHz, nearest thing on the list to the 24 kHz target** | 22 050 Hz | **NVIDIA Open Model License — commercial permitted** ✅ | HF `nvidia/nemo-nano-codec-22khz-*` |
| **FocalCodec-Stream** | built for streaming via causal distillation · single codebook · 0.55–0.80 kbps · public causal checkpoint | ◻ confirm | ◻ confirm | `github.com/lucadellalib/focalcodec` |
| **Mimi** | 12.5 Hz · 1.1 kbps · streaming encoder–decoder · already on disk · PyTorch, MLX **and Rust** implementations | 24 000 Hz | **CC-BY** ✅ | on disk @ `89091b3e` |
| **MelFlow** | **the first public code and checkpoint for streamable mel vocoding** · frame-causal with cached inference · 32 ms algorithmic / 48 ms total · real-time on a consumer laptop GPU in practice · beats non-streaming baselines including HiFi-GAN on PESQ and SI-SDR | 16 000 Hz | ◻ confirm on repo | `github.com/sp-uhh/streamfm` |
| **Fish ModifiedDAC** | **the incumbent** — the thing a new choice must beat | 44 100 Hz | on disk | `codec.pth` |
| **EnCodec 24 kHz + Vocos-EnCodec** | **the controlled pair** — codebooks already verified bitwise identical (`AUDIT.md` §3.1), the only single-variable decoder comparison available | 24 000 Hz | on disk | HF, verified |

## USEFUL BASELINE

| arm | role |
|---|---|
| **Descript DAC 44 kHz** | high-rate offline quality reference; non-causal decoder |
| **BigVGAN v2** | offline quality ceiling for the mel route; contrary streaming evidence |
| **Vocos-mel** | fast non-causal spectral decoder control |
| **Griffin-Lim** | zero-parameter floor (R9), run at both mel configurations |

## LITERATURE ONLY — study the architecture, never an arm

| work | why not an arm |
|---|---|
| **UniStream** (2609.09866) | fully causal **48 kHz**, multi-expert RVQ, 12 / 22.5 kbps — **no code or checkpoint released.** The 48 kHz causal ceiling reference, and a reminder that high bandwidth costs ~10–20× Mimi's bitrate, which the generator pays for in sequence length |
| **VoCodec** (2606.05892) | fully causal, MDCT domain, voicing-driven quantization, ~27% bitrate saving — no checkpoint located |
| **Ultra-low-latency block-wise Mimi TTS** (2604.12438) | closest published system to what we want to build; 48.99 ms TTFB **with no hardware stated** |
| **X2Streaming-TTS · Chatterbox-Flash · CosyVoice causal modes** | complete-system references, not decoders |
| **HiFi-GAN** (2020) | historical baseline; BigVGAN v2 is its successor and is already on disk |

## EXCLUDE — with reason

| candidate | reason |
|---|---|
| **`nvidia/low-frame-rate-speech-codec-22khz`** | **NSCLv1 — research / non-commercial only.** Cannot ship in a product. Nearly identical to NanoCodec, which *is* commercially licensed — **benchmark the shippable one.** This is exactly what the licence gate exists to catch |
| **Any system claiming "real-time" without a causality audit** | a low real-time factor is not evidence of streaming; a full-context model can run many times faster than real time and still carry utterance-scale algorithmic latency |
| **Naïve chunking of Vocos / overlap-add BigVGAN presented as streaming** | useful engineering fallbacks, invalid as streaming *evidence* |

## PENDING — CLOSED 2026-09-10

Time-boxed triage on four questions only: **runnable official checkpoint? ·
licence for code and weights? · causal decoder on the synthesis side? ·
practically comparable?** No new survey was run.

### PROMOTED to MUST BENCHMARK

| arm | why it was promoted | rate |
|---|---|---|
| **Qwen3-TTS-Tokenizer-12Hz** | **public checkpoint** `Qwen/Qwen3-TTS-Tokenizer-12Hz` · 12.5 Hz · **lightweight causal ConvNet decoder** with immediate first-packet emission · a full open-source Qwen3-TTS repo exists with streaming support | ◻ confirm |
| **DualCodec** | **public checkpoints** `amphion/dualcodec` (12hz_v1, 25hz_v1) · **on PyPI**, so installation is trivial · 12.5 / 25 Hz, semantically enhanced via SSL features | ◻ confirm |
| **Wavehax / MS-Wavehax** | official repo `chomeyama/wavehax` · **under 5% of HiFi-GAN V1's MACs and parameters, over 4× faster CPU inference** · MS-Wavehax reaches near non-causal quality with a **single-frame lookahead** — the strongest SDK/mobile candidate found | ◻ confirm which weights are public |

⚠️ **Qwen carries the trap this benchmark exists to catch: 12.5 Hz sounds cheap,
but it is a 16-layer multi-codebook design — about 200 codebook predictions per
second for the generator.** A low frame rate is not a low generator cost. Recorded
before any measurement so the result cannot be framed as a surprise afterwards.

### LITERATURE ONLY — with reason

| candidate | reason |
|---|---|
| **StreamCodec2** | fully causal, 20 ms latency, 910 MFLOPs, 5.4 M params — **no public checkpoint or repository located.** The distillation-from-a-non-causal-teacher idea is directly relevant to our own from-scratch build and is kept as an architecture reference |
| **TaDiCodec** | checkpoints *are* public, but its decoder is a **text-guided diffusion decoder** — it requires **text at decode time** and runs iterative denoising. That is a different function signature from representation→waveform and **is not comparable within this benchmark's scope** (`PROTOCOL.md` §2). Excluded on comparability, not on quality |
| **FlexiCodec · U-Codec · ESDCodec · SACodec · PACodec · VibeVoice-Realtime · StyleStream · DLL-APNet** | not verified runnable within the time-box. Not rejected on merit — **the gate closed before they were checked**, and that is recorded honestly rather than dressed as a judgement |

### USEFUL BASELINE — cheap, because the harness already carries them

**WavTokenizer · BigCodec · Stable Codec · X-Codec 2.0 · AudioDec · SpeechTokenizer
· SemantiCodec · MagiCodec · HILCodec · BiCodec · PAST · DyCAST** — all exposed by
the pinned `audiocodecs` API. Predominantly non-streaming designs, so they are
baselines rather than streaming candidates, but they cost almost nothing to add
once the harness is in place.

**THE CANDIDATE UNIVERSE IS NOW CLOSED for this experiment.** It reopens only if a
hard implementation failure forces it.

---

## ⛔ LICENCE AUDIT — read before building anything on these

Queried from the repositories themselves, 2026-09-10, with commits pinned.

| repo | licence | pinned commit | consequence for a **shipped product** |
|---|---|---|---|
| `lucadellalib/audiocodecs` | **Apache-2.0** ✅ | `fe350cce8b51ee1331138590222ce4f42c39a7f4` | usable |
| `lucadellalib/focalcodec` | **Apache-2.0** ✅ | `912b7f2c0cd43d54a8aed296bbcc925dec7d4ea3` | usable |
| `sp-uhh/streamfm` (**MelFlow**) | ⚠️ **AGPL-3.0** | `ab2700c1154acc5c2ce67a5344182028336413f5` | **viral copyleft with a network clause.** Serving it over a network can oblige you to release your own source. **Not shippable in a closed product.** |
| `chomeyama/wavehax` | ⛔ **NO LICENCE** | `e084fc953499b76c79e4f2166fb2ac78f34c32e0` | **no licence means all rights reserved by default.** No grant to use, copy or redistribute. **Not shippable without written permission from the author.** |

⚠️ **AGPL and "no licence" are not the same problem, and an earlier draft of this
file wrongly treated them as one.** It said internal evaluation is simply "a
different act from shipping". That is true for AGPL. It is **not** a safe
assumption for an unlicensed repository, where there is no affirmative copyright
grant of any kind — not to use, not to copy, not to run. Corrected by the owner
before any download. The distinction below is now the governing one.

### MelFlow — BENCHMARK, with a label attached to every result

**Owner decision: YES.** AGPL-3.0 does not restrict local research evaluation.
It runs in an isolated environment, and **every result it produces carries the
label:**

> `RESEARCH / ARCHITECTURE EVIDENCE — NOT SHIPPABLE AS A CLOSED-PRODUCT
> DEPENDENCY UNDER THE CURRENT LICENCE`

Its source is **never** integrated into BedVibe or Kiefer product code. Its
benchmark result is allowed to inform an architectural **reimplementation**
decision.

⚠️ **And a clean reimplementation answers copyright, not patents.** Avoiding
copied code does not by itself resolve patent or other IP exposure. That needs
separate review before anything ships, and it is not resolved by this benchmark.

### Wavehax / MS-Wavehax — CODE ON HOLD

**Owner decision: do not download or execute pending licence resolution.**

**Licence hunt completed 2026-09-11 — result: nothing found anywhere.**

| checked | result |
|---|---|
| repository root | no `LICENSE` file (`.gitignore`, `README.md`, `egs`, `requirements.txt`, `setup.py`, `wavehax`) |
| GitHub releases | none published |
| `setup.py` metadata | no `license` field, no licence classifier — only `author="Reo Yoneyama"`, Nagoya University |
| `README.md` | no licence, copyright or terms of any kind |

**Status: `DOCUMENTED ARCHITECTURE / BENCHMARK PENDING PERMISSION`.**

⛔ **Not dropped scientifically.** Its published results stay in the evidence
matrix — under 5% of HiFi-GAN V1's MACs and parameters, over 4× faster CPU
inference, and near non-causal quality at a single-frame lookahead — recorded as
**`DOCUMENTED`, author-reported. They are never treated as our measurements.**

**The only route to promotion is permission from the author.** An email may be
drafted for the owner to review; **nothing is sent without his explicit approval.**

## The harness

**`lucadellalib/audiocodecs`, Apache-2.0**, one API (`sig_to_toks` / `toks_to_sig`)
over **20 codecs** — including NanoCodec, Mimi, FocalCodec-Stream, EnCodec+Vocos,
DAC, BigCodec, Stable Codec, WavTokenizer, X-Codec 2.0 and AudioDec. Adopting it
removes a large amount of per-codec adapter glue, and adapter glue is not just
work — it is a comparability risk, because a hand-written adapter per codec is a
per-codec difference in the measurement path.

⛔ **Defect to fix before use: it pins nothing and installs from `@main`.** A
benchmark cannot depend on a moving branch. **We pin an exact commit ourselves and
record it in `ENVIRONMENT.json`.**

⚠️ **NanoCodec requires NeMo 2.0.0 and prefers Linux.** That is a real integration
cost on this machine and a real signal about SDK deployment. Whether it is reached
through NeMo or through `audiocodecs` is itself a decision to record, because they
are two different measurement paths to the same weights.

## Environment plan — freeze-first

⛔ **`chatterbox`, `fish`, `voxbench` and `BedVibe` are NOT modified.** They carry
frozen research work. A **new throwaway environment** is created for this
benchmark, and the existing ones are left exactly as they are.

## Open item carried forward

**Mimi's latency remains NEEDS RESOLUTION.** 12.5 Hz gives an 80 ms frame by
arithmetic; whether an additional ~80 ms acoustic delay applies is a Moshi-paper
claim not settled by the model card, and the two external surveys disagreed
(80 ms vs 160 ms). **No Mimi latency figure is quoted anywhere until this is read
at source or measured here.**

---

**Next: download the MUST BENCHMARK survivors with pinned revisions and hashes,
then update `AUDIT.md` and `PROTOCOL.md` with the runnable arms, then return both
for final review. GPU stays off until then.**
