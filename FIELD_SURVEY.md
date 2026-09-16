# FIELD SURVEY — streaming waveform representations, codecs, decoders and vocoders

**Pass 1. 2026-09-10. No GPU used. `PROTOCOL.md` is NOT frozen and no arm is
committed.** This document exists because `PROTOCOL.md` §16.3 says the local
estate cannot establish a 2026 architecture recommendation. The survey therefore
moved **in front of** the benchmark freeze.

**Order of work, revised and owner-approved:**
`FIELD SURVEY → candidate gate → download survivors → update AUDIT/PROTOCOL → freeze → GPU`

## Evidence rules for this document

Everything here is **`DOCUMENTED`** — it comes from a paper, repository or model
card. **Nothing in this file is `MEASURED`.** We have measured none of it.

⛔ **A published latency number is not comparable to ours and never will be**
unless the protocol matches, which it essentially never does. Vendor and paper
figures are recorded with their source and their stated hardware; where hardware
is not stated, that absence is recorded as a defect of the citation, not
smoothed over.

⛔ **Fame is not inclusion. Absence from disk is not exclusion.**

## The inclusion criterion — the actual product

> **mono · interactive · streaming · very low TTFA · stable chunking · high
> reconstruction quality · practical SDK/mobile deployment · a representation a
> from-scratch TTS generator can actually predict.**

⚠️ **We are not looking for "the best vocoder". We are looking for the Pareto
frontier of a system.** One codec may reconstruct beautifully and cost 80 ms of
algorithmic latency. Another may decode in 10 ms but force the generator to emit
100 frames per second. Another may offer 12.5 tokens per second and demand 32
depth predictions per frame. Another may decode cleanly and seam badly when
chunked. **The winner is the combination whose costs fit together**, and the
generator's share of the budget is decided by the representation the decoder
consumes. That is why the decoder choice is an architecture choice and not a
component swap.

---

## A. What the survey has already changed

**1. A published study already occupies part of our design space — on CPU.**
*Comparative Analysis of Fast and High-Fidelity Neural Vocoders for Low-Latency
Streaming Synthesis in Resource-Constrained Environments* (MS-Wavehax,
Interspeech 2025, arXiv 2506.03554) analyses **the latency–throughput trade-off
and chunk-size optimisation for streaming vocoders in a CPU-only environment**,
and names parameter-loading overhead, limited parallelism and inter-frame
dependency as the bottlenecks.

**It does not pre-empt this study — it is CPU, ours is GPU — but it does two
things to it.** Our chunk-size framing is now *published practice* and may not be
presented as our own idea. And it is the natural reference for the SDK/mobile axis,
where CPU is the deployment target anyway.

**2. The most relevant architecture paper reports a headline latency with no
hardware.** *An Ultra-Low Latency, End-to-End Streaming Speech Synthesis
Architecture via Block-Wise Generation and Depth-Wise Codec Decoding*
(arXiv 2604.12438, April 2026) builds directly in **Mimi's** discrete latent
space with a modified FastSpeech 2 backbone and progressive depth-wise decoding
over **32 layers of residual vector quantization**, reporting **48.99 ms average
time-to-first-byte** and a 10.6× speed-up over cascaded pipelines.

⚠️ **The abstract states no hardware for the 48.99 ms.** That is precisely the
citation defect our own protocol is built to avoid, and it is the reason we
cannot simply adopt their number as a target. **Study the architecture; do not
inherit the figure.**

It also answers part of our open question: Mimi is being driven with **32 RVQ
layers** in at least one serious streaming TTS, which bears on `AUDIT.md` §6.1.

**3. A standardised multi-codec API exists and may become our harness.**
`lucadellalib/audiocodecs` exposes FocalCodec-Stream, Mimi, AudioDec, BigCodec,
Stable Codec, WavTokenizer, X-Codec 2.0 and others behind one interface. If it
holds up, it removes a large share of both implementation risk and the
per-codec-glue comparability risk. **To be evaluated, not assumed.**

---

## B. Candidate matrix — pass 1

`✅` verified this session · `◻` researched next · fields left blank are not yet read.

### B.1 Codec-token route

| candidate | date | rate / bitrate | streaming design | code + ckpt | status |
|---|---|---|---|---|---|
| **Mimi** (Kyutai) | 2024, production stack | 24 kHz · 12.5 Hz · ~1.1 kbps · 80 ms frame | **causal, explicit streaming cache**; PyTorch, MLX **and Rust** implementations | ✅ on disk | **MUST BENCHMARK** |
| **FocalCodec-Stream** | Sept 2025, ICASSP 2026 | **0.55–0.80 kbps**, single binary codebook | **built for streaming** — causal distillation of WavLM, lightweight refiner, **stated theoretical latency 80 ms**; paper claims it outperforms existing streamable codecs at comparable bitrates | ✅ public, `github.com/lucadellalib/focalcodec` | **MUST BENCHMARK** |
| **Fish ModifiedDAC** | in production here | 44.1 kHz · 21.533 Hz · 2.20 kbps | causal in inspected stages, no cache API found | ✅ on disk | **MUST BENCHMARK** — it is the incumbent |
| **Meta EnCodec 24 kHz** | 2022 | 24 kHz · 75 Hz | causal convs | ✅ on disk | **USEFUL BASELINE** + half of the controlled pair |
| **Vocos-EnCodec** | 2023 | consumes EnCodec codes | non-causal, centre padding | ✅ on disk | **MUST BENCHMARK** — the controlled pair |
| **Descript DAC 44 kHz** | 2023 | 44.1 kHz · 86.13 Hz · 7.75 kbps | **non-causal, no causal option in the module** | ✅ on disk | **USEFUL BASELINE** — offline reference |
| **TS3-Codec** | Nov 2024 | — | **transformer streaming codec by design**, claims lower compute than convolutional comparison | ◻ **checkpoint availability is the gate** | ◻ pending |
| **StreamCodec** | — | MDCT domain | **fully causal symmetric encoder–decoder** | ◻ | ◻ pending |
| **LILAC** | Aug 2026 | 24 kHz · **9.375 Hz** · 0.75 kbps | fully convolutional; **idempotent by construction** — re-encoding a decode returns the identical stream; UTMOS 4.14 / 4.24 | ◻ public per owner | ◻ pending — **and its RTF claim must be verified, not repeated** |
| **NVIDIA Low Frame-rate Speech Codec** | 2024 | low frame rate, for speech-LLM training/inference | ◻ | ◻ | ◻ pending — relevant given the NVIDIA connection |
| **DualCodec** | Interspeech 2025 | low frame rate, semantically enhanced | ◻ | ◻ | ◻ pending |
| **WavTokenizer · BigCodec · Stable Codec · X-Codec 2.0 · FocalCodec · AudioDec · TaDiCodec** | 2024–2025 | — | — | several via `audiocodecs` | ◻ pending |

### B.2 Mel / continuous route

| candidate | date | streaming design | on disk | status |
|---|---|---|---|---|
| **MelFlow** | Sept 2025 | ✅ verified — **frame-causal with a cached inference scheme**, 32 ms algorithmic / 48 ms total, **16 kHz** | ✗ | **MUST BENCHMARK** |
| **MS-Wavehax** | Interspeech 2025 | **low-latency streaming vocoder, aliasing-free, CPU-optimised, compact**; the paper *is* a chunk-size study | ✗ | ◻ **strong MUST BENCHMARK candidate**, especially for the SDK/mobile axis |
| **DLL-APNet** | Sept 2025 | **causal** low-latency vocoder, explicit amplitude + phase prediction, teacher distillation to recover the quality causality costs | ✗ | ◻ pending |
| **StreamingVocos** | community | causal CNN Vocos variant, 50 Hz mel in, 16 kHz out | ✗ | ◻ pending — **community replication, not a canonical release** |
| **StyleStream** | 2026 | causal vocoder + chunk-causal attention, distilled from a non-streaming teacher | ✗ | ◻ pending |
| **Pupu-Vocoder / Pupu-Codec** | Dec 2025 | aliasing-free synthesis; public checkpoints per owner | ✗ | ◻ pending |
| **BigVGAN v2** | v2 ckpts 2024 | **non-causal** — contrary architectural evidence | ✅ | **USEFUL BASELINE** — an excellent *offline* quality reference, not the production answer |
| **Vocos-mel** | 2023 | non-causal, centre padding | ✅ | **USEFUL BASELINE** |
| **Griffin-Lim** | classical | full-context only | ✅ | **USEFUL BASELINE** — zero-parameter floor |
| **HiFi-GAN** | **2020** | — | ✗ | **LITERATURE ONLY** — §C.1 |

### B.3 Architecture references — study, do not benchmark

| work | why |
|---|---|
| **Ultra-Low-Latency block-wise / depth-wise Mimi TTS** (2604.12438) | closest published thing to the system we want to build |
| **VoXtream** (2509.15969) | full-stream TTS, incremental decoder-only transformer, monotonic alignment, limited look-ahead |
| **VoiceChat-TTS** (2608.13831, Aug 2026) | low-latency continuous synthesis for interactive agents |
| **Fish Audio S2 technical report** (2603.08823, March 2026) | the incumbent stack's own successor — directly relevant |
| **SpeakStream**, **TQCodec**, **RSVQ streamable codec** (2504.06561) | adjacent streaming designs |

---

## C. Decisions this survey already supports

**C.1 Do not download HiFi-GAN to fill the empty slot.** The paper is from 2020.
It remains a legitimate *historical* baseline and nothing more, and BigVGAN v2 —
its successor lineage — is already on disk and covers that family. Downloading it
would spend benchmark time filling a slot rather than answering a question.
**Classified LITERATURE ONLY.** It can be added later if a controlled baseline
specifically requires it.

**C.2 BigVGAN v2 is probably an offline reference, not the production answer.**
Its architectural evidence is contrary to incremental streaming. That does not
demote it — a high-quality non-causal reference is exactly what the
reconstruction-quality gate will need.

**C.3 The three strongest new candidates are streaming-native by design:**
**FocalCodec-Stream**, **MS-Wavehax**, **DLL-APNet** — plus **Mimi**, which we
already hold. Every one of them was built for the problem we actually have, which
none of the on-disk incumbents were.

**C.4 A low token rate still does not imply low decoder latency.** LILAC at
9.375 Hz and the 32-layer depth-wise Mimi decoding are the two clearest
illustrations: fewer tokens per second can mean more work per token, and more
depth predictions per frame. **This is the single most important thing the
benchmark exists to catch**, and it is why no candidate is admitted on its
headline rate.

---

---

## C-bis. Two external AI surveys — triage, 2026-09-10

Two AI-generated surveys (Perplexity, Gemini) were supplied. **They are treated as
LEADS, not evidence.** Candidate *names* from them are valuable; every *number*
and every citation is verified at source before it enters this file.

### Verified at source ✅

| candidate | verified facts | classification |
|---|---|---|
| **MelFlow** — *Real-Time Streaming Mel Vocoding with Generative Flow Matching*, Welker/Peer/Gerkmann, arXiv **2509.15085** | **16 kHz** · **32 ms algorithmic, 48 ms total latency** · generative interpolating flow matching · mel-filterbank pseudoinverse + STFT phase retrieval · **efficiently cached inference scheme for causal DNNs** · real-time demonstrated on a consumer laptop GPU **in practice, not only theory** · better PESQ and SI-SDR than non-streaming baselines **including HiFi-GAN** | **MUST BENCHMARK** — a genuine omission from pass 1, and squarely in this project's scope |
| **VoCodec** — *A Low-bitrate Streamable Neural Speech Codec with Voicing-driven Quantization*, arXiv **2606.05892**, June 2026 | **fully causal** encoder–quantizer–decoder · embedded voicing detector · RSVQ for voiced frames, scalar quantization for unvoiced · **MDCT domain + inverse MDCT** · inherits **StreamCodec's** causal conv encoder–decoder · **16 kHz** LibriTTS · 1.1 kbps · **~27% bitrate reduction** vs uniform quantization | **MUST INVESTIGATE** |

### Citation defects found while verifying ⚠️

1. **VoCodec was cited under two different arXiv IDs in one document** — `2601.13055` and `2606.05892`. **Only 2606.05892 resolves to this paper.** The other is recorded as a bad citation and must not propagate.
2. **Mimi latency is stated inconsistently between the two surveys** — one gives an 80 ms frame, the other 160 ms total (80 ms frame + 80 ms acoustic delay). **NEEDS RESOLUTION at source before Mimi's latency is quoted anywhere.**
3. **FocalCodec-Stream's codebook is described as "4096-entry"** in one survey; the paper describes a **single binary codebook**. NEEDS RESOLUTION.

### ⭐ A pattern neither survey named, and it is a problem

**MelFlow is 16 kHz. VoCodec is 16 kHz. StreamCodec2 is 16 kHz.** Much of the
newest genuinely-causal streaming work is at **16 kHz**, while the incumbents on
disk are 44.1 kHz (Fish, Descript DAC) and 24 kHz (EnCodec, Mimi, Vocos).

**A 16 kHz ceiling is a product decision, not a footnote.** If the frontier of
causal streaming decoding sits at 16 kHz, then "best streaming latency" and "best
output bandwidth" may be in direct tension, and that tension has to be surfaced to
the owner rather than resolved silently by whichever candidate wins a latency
table.

### ⭐ A candidate my own search found that neither survey listed

**UniStream** — *Multi-Expert Residual Vector Quantization for **48 kHz Causal
Streaming** Audio Coding*, arXiv **2609.09866**, September 2026. It addresses
exactly the tension named above: causal streaming **at 48 kHz**. ◻ To be verified
in pass 2. Also surfaced: **ClariCodec** (200 bps, RL-optimised, 2604.14654) and
**PURE Codec** (2511.22687).

### Unverified leads adopted into the pass-2 queue

Names only; no number from either survey is carried forward until checked.

**Codec / representation:** StreamCodec2 (`2509.13670` — this one *did* appear in
my own first search) · TaDiCodec (6.25 Hz claimed) · FlexiCodec · U-Codec (5 Hz
claimed) · ESDCodec · SACodec · PACodec · VARSTok · HH-Codec · SpecTokenizer ·
WavTokenizer · Single-Codec · VibeVoice-Realtime 7.5 Hz tokenizer ·
Qwen-TTS-Tokenizer-12Hz.

**Waveform decoder:** StreamingVocos · StyleStream · Flow2GAN ·
PeriodWave-Turbo · StreamFlow.

**Complete-system controls:** X2Streaming-TTS · Chatterbox-Flash ·
CosyVoice 2/3 causal and chunk-causal modes · StreamMel.

### Two methodological additions adopted from the surveys

**1. The four-way streaming taxonomy** replaces my two-way framing, and it is
strictly better: `TRUE STATEFUL/CAUSAL` · `CHUNKABLE WITH LOOKAHEAD/OVERLAP` ·
`OFFLINE / FULL-CONTEXT` · `UNKNOWN`. It maps cleanly onto the provisional labels
already frozen in `PROTOCOL.md` §10.1.

**2. Four versions of every latency number, never merged into one leaderboard:**

| # | version | evidence state |
|---|---|---|
| 1 | reported by the authors | `DOCUMENTED` |
| 2 | reproduced on the authors' reference hardware | `MEASURED` (if we ever do it) |
| 3 | reproduced on our target GPU | `MEASURED` |
| 4 | reproduced on our target mobile/CPU device | `MEASURED` |

**And the rule that goes with it:** a 15.8 ms first-*token* claim may still yield
no playable waveform for far longer, while a 50 ms decoder may emit smooth audio
immediately. **A low real-time factor is not evidence of streaming** — a
full-context model can run many times faster than real time and still carry
utterance-scale algorithmic latency.

---

## D. Still to do in pass 2

1. Verify checkpoints and **licences — code and weights separately** — for every `◻` row. A permissive paper with non-commercial weights is not usable in a product and must be caught here, not after benchmarking.
2. Resolve TS3-Codec: usable public checkpoint, or LITERATURE ONLY.
3. Evaluate `audiocodecs` as the harness.
4. Read Fish Audio S2 — the incumbent's own successor.
5. Verify LILAC's RTF claim at source.
6. Search deliberately for anything 2026 the citation trail has not surfaced.
7. Competitor architecture intelligence — including Cartesia's published design — recorded as `DOCUMENTED`, never as a benchmark comparison.
8. Produce the final gate: `MUST BENCHMARK` / `USEFUL BASELINE` / `LITERATURE ONLY` / `EXCLUDE — reason`, for owner review.

**Nothing is downloaded, nothing is frozen, and no GPU has run.**
