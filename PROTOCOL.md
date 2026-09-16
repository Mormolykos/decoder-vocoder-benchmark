# PROTOCOL — waveform decoder benchmark for a streaming TTS build decision

# ⛔ FROZEN 2026-09-11, on owner approval, BEFORE ANY TIMING RESULT EXISTED.

**Nothing above the amendment line is edited from this point. Every change
appends below it with a date and an explicit statement of whether any result had
already been seen — the `PROTOCOL_D.md` discipline.**

**No decode has been timed. No GPU measurement has been taken.** The only
measurements in existence are Gate Zero's structural validity results
(`MANIFEST.md`), all obtained on CPU, and they are what this freeze rests on.

The arm list is `MANIFEST.md`, frozen with this document.

Inputs to this document: `AUDIT.md` in this directory (the inventory and the
taxonomy), `orchestrator\METHODOLOGY.md` (rules cited by number),
`mcp\notchecked\README.md` (evidence states).

---

## 1. Question

> **Which waveform decoder should a from-scratch streaming TTS be built on, and
> what does each candidate cost in the way that streaming actually charges you —
> time to the first audible chunk, cost per chunk thereafter, variance between
> chunks, and damage at chunk boundaries?**

Secondary: full-utterance throughput and peak memory.

**These are not the same question and the answer may differ between them.** A
decoder can win full-utterance throughput and be unusable for streaming. If that
happens it is the headline result, not a footnote.

## 2. Scope and claim boundary — stated here and repeated in every output

**Measured: representation → waveform.** Nothing else.

**Not measured:** end-to-end TTS, text processing, AR token generation, network
transport, HTTP or server overhead, full voice-agent latency.

`OPTIMIZATION.md` shows why this boundary must be loud: on that system AR
generation was ~1.47 s while the entire decode route was ~65 ms. **A decode-only
number read as end-to-end TTS performance is a failed report.**

## 3. Candidates

Per `AUDIT.md`. Two routes, never merged into one ranking.

**The arm list is `MANIFEST.md`, frozen with this document.** Summarised here:

**Route A — codec tokens → waveform**

| arm | role | representation (MEASURED at Gate Zero) |
|---|---|---|
| `focalcodec_50hz_4k_causal` | ⭐ **full-path causal** | 50 Hz, 1 binary cb, 50 targets/s, 16 k → **24 k** |
| `focalcodec_50hz_2k_causal` | ⭐ **full-path causal** | 50 Hz, 1 binary cb, 50 targets/s, 16 k → **24 k** |
| `focalcodec_50hz` / `_25hz` / `_12_5hz` | non-causal controls | 49.94 / 24.97 / 12.48 Hz, 16 k → 16 k |
| **`mimi_q8`** | ⭐ **PRIMARY** | 12.547 Hz, **n_q=8**, 100.4 targets/s, **1.10 kbps** |
| **`mimi_q32`** | **SENSITIVITY ABLATION ONLY** | 12.547 Hz, **n_q=32**, 401.5 targets/s, 4.42 kbps |
| `encodec24_q8` | half of the controlled pair | 75 Hz, 8 cb, 600 targets/s |
| `encodec_vocos` | **the other half — identical token tensor** | codebooks verified bitwise identical, `AUDIT.md` §3.1 |
| `dualcodec_12hz_v1` / `_25hz_v1` | | 12.484 / 24.969 Hz, 8 cb (1 sem + 7 aco) |
| `qwen3_tts_tokenizer_12hz` | | 12.547 Hz, **16 cb**, 200.8 targets/s, Apache-2.0 |
| `dac44` | offline quality reference | 86 Hz, 9 cb, 775 targets/s, **non-causal** |
| `fish_modified_dac` | **the incumbent** | 21.564 Hz, 10 cb, 215.6 targets/s, 44.1 k |

⛔ **`mimi_q8` and `mimi_q32` results are NEVER merged, and n_q=32 is NEVER
described as "Mimi 1.1 kbps."** `mimi_q32` does not compete for the architecture
recommendation; it measures what representation **depth** costs with architecture,
temporal rate and decoder family held fixed. **`n_q` appears in every raw row,
every summary row and every Explorer evidence record for Mimi.**

**Route B — mel / continuous → waveform**

| arm | role | note |
|---|---|---|
| `melflow` | ⭐ causal cached mel vocoder | 16 kHz, 27,896,458 params, ⚠️ **AGPL — architecture evidence only** |
| `bigvgan22` · `vocos_mel24` · `griffinlim` | baselines and zero-parameter floor | non-causal |

**BLOCKED:** `nanocodec` — released NeMo tooling not runnable in this
Windows-native environment (`MANIFEST.md` §4). Reported as **BLOCKED**, never as
zero, never omitted.

**Route B — mel → waveform**

| arm | decoder | representation |
|---|---|---|
| `B_vocos_mel` | Vocos-mel | mel-100, 24 kHz, hop 256 |
| `B_bigvgan` | BigVGAN v2 | mel-80, 22.05 kHz, hop 256 |
| `B_griffinlim` | Griffin-Lim, fixed iterations | whichever mel config it is paired with |

`B_griffinlim` is a **zero-parameter reference** (R9 floor), run at both mel
configurations. It is never ranked as a production candidate.

**Excluded, with reasons recorded rather than omitted:** HiFi-GAN mel vocoder —
**NOT AVAILABLE**, no weights on disk. BedVibe EnCodec 48 kHz — **ARTIFACT TO
LOCATE**, weights and token corpus both missing. XTTS `HifiDecoder` — Route C,
consumes GPT latents, cannot be placed on Route B.

## 4. Gate zero — things that must be resolved before any timing run

A run started before these are settled produces numbers nobody can interpret.

**4.1 Mimi's true token rate and codebook count.** Config declares 12.5 Hz;
`upsampling_ratios` implies 25 Hz (`AUDIT.md` §6.1). Resolve by encoding a
clip of known length and counting tokens. **Recorded as MEASURED before it enters
any denominator.** If it cannot be resolved, `A_mimi` is dropped from
representation-normalised analysis and kept in deployment-normalised only.

**4.2 Every arm produces correct audio at all.** Each decoder reconstructs one
fixed clip and passes the §8 validity gate before it is eligible to be timed.
An arm that cannot produce valid audio is **not timed**, and that is a reported
result, not a missing row.

**4.3 Fish ModifiedDAC dtype.** The checkpoint's stored precision is NOT MEASURED;
read it before setting the precision policy.

**4.4 The Vocos-EnCodec adapter.** Built from the checkpoint without instantiating
the Meta encoder (`AUDIT.md` §3.2). Its declared domain is written and property-
fuzzed **before** it is used, per R19.

## 5. Estimands — the quantities this study exists to produce

**This section replaces an earlier set of hypotheses that were withdrawn before
freeze.** H1 compared a rank-correlation *strength* against an implementation
*spread* — two quantities with different units, so it could not be evaluated at
all. H2 used an arbitrary IQR-overlap threshold. H4 was undefined for any
candidate that cannot stream. And the prediction named Mimi the first-chunk winner
on the strength of a 12.5 Hz token rate that **this protocol's own gate zero marks
NEEDS RESOLUTION** — R17's exact defect, a prediction about a quantity of unknown
value. A low token rate also does not imply low decoder compute; it describes
representation granularity, and generator timing is outside this study.

**Nothing is predicted here. These are the quantities to be estimated, each with
its uncertainty, each reported whatever it shows.**

**E1 — the controlled pair.** On byte-identical EnCodec tokens: the paired
difference **and** the ratio of decode latency between `A_encodec_native` and
`A_encodec_vocos`, per duration condition, with a paired interval. This is the
only estimand in the study where one variable moves.

**E2 — fixed cost versus marginal cost.** Per arm, the **intercept and slope** of
decode latency against produced audio duration, with intervals. The intercept is
what a short utterance pays; the slope is what a long one pays. Reported per arm,
never averaged across arms.

**E3 — minimum viable streaming configuration.** Per arm: the smallest chunk, and
the context and overlap, at which the arm still produces output passing the §8
validity gate. Reported in **frames/tokens and in equivalent audio milliseconds**.
For an arm where no such configuration exists, the estimand is `NOT ACHIEVABLE`
and that is a result.

**E4 — offline versus streaming ordering.** Whether the ranking by full-utterance
RTF differs from the ranking by TTFA, **computed only over the subset of arms for
which both quantities are defined**, with that subset named. If fewer than three
arms qualify, E4 is reported as underpowered rather than as an ordering.

**E5 — budget consumption.** Per arm at each chunk condition: milliseconds
consumed of a stated model-side first-audio budget, and required lookahead. §17.

**E6 — the environment effect.** §7.2.

⚠️ **R17 — stability before any quantity is treated as reproducible.** Every
estimand is measured on two clean runs before it is reported as a point. Anything
that moves between clean runs is reported as a range with an explicit void
condition. `Gate zero` (§4) must clear first — an unresolved constant may not
enter a denominator.

## 6. Variables

**CONTROLLED:** GPU (RTX 5080, sm_120, driver 610.47) · **torch 2.10.0+cu128 in
every arm** · batch size 1 · warm-up policy · allocator settings · timing code ·
input construction · machine state · measurement instrumentation.

**ARCHITECTURAL — declared, never "fixed":** output sample rate · token/frame rate
· codebook count and size · mel configuration · causality · channel count.

**DECLARED, NOT HELD:** `transformers` version, which differs by environment
(`AUDIT.md` §6.5) and is **measured** rather than assumed (§7.2).

**Precision:** fp32 for every arm in the primary, because every checkpoint on disk
is fp32. bf16 is a separate experiment, not an axis here.

## 7. Environment

**7.1** Two conda environments, both torch 2.10.0+cu128: `fish` (Fish ModifiedDAC,
EnCodec) and `chatterbox` (EnCodec, Descript DAC, Mimi, Vocos ×2, BigVGAN).
`ENVIRONMENT.json` records the full package set, driver, CUDA and GPU for each.

**7.2 The environment control.** `A_encodec_native` at a fixed duration is run in
**both** environments. The difference is the environment effect and is reported
whatever it shows. **If it is comparable in size to the between-decoder
differences, every cross-environment comparison in this study is reported as NOT
COMPARABLE** rather than caveated. This converts the confound into a measurement.

**7.3 Machine state.** `nvidia-smi` today shows 6 769 MiB of 16 303 MiB already
held at 0% utilisation by Chrome, Teams, VS Code, WhatsApp, Docker Desktop,
Telegram and the shell. Those are closed for primary runs.

**Recorded before and after every measured cell, into the raw data:** VRAM used,
**GPU temperature, SM and memory clocks, power draw, and utilisation**. Thermal
and clock state drift over a long session and would otherwise be absorbed into
whichever arm ran last — the confound that §11's block randomisation exists to
break, and this is the sensor that lets it be checked rather than assumed.

An arm whose before/after VRAM reading moves by more than 200 MiB is re-run and
**both runs are kept**. Clock or thermal state outside a declared band is recorded
on the row, not silently accepted and not silently discarded.

**7.4** One GPU process at a time. No concurrent GPU work from any other thread or
session while a primary arm is running.

## 8. The output-validity gate — schema first (R19)

Not a quality score. A timing number from malformed output is inadmissible.

**Declared domain, per field, written before any comparison:**

| field | predicate for the value to be usable |
|---|---|
| sample count | within ±1 hop of the expected duration for that arm's rate |
| sample rate | exactly the arm's declared output rate |
| finiteness | every sample finite — no NaN, no inf |
| peak amplitude | in `(0.0, 1.0]` — rejects digital silence and rejects clipping |
| dtype | float32 |
| channels | equals the arm's declared channel count |

**A value failing its predicate is treated exactly as absent. Absence is UNKNOWN.
UNKNOWN never becomes a pass** (R1 applied to input). A timing row whose gate is
UNKNOWN is inadmissible and stays visible in the raw data.

**Property fuzz before the gate is trusted**, per R19's corollary — truncated
output, wrong rate, all-zero, NaN, single sample, duplicated file, off-by-one
length. The write-up says *"survived N attacks"*, never *"closed"*. **I am the
author of this gate and therefore not its certifier.**

## 9. Timing

**9.1** `torch.cuda.synchronize()` before starting and before stopping the clock.

**9.2 Two clocks measuring two different things — corrected before freeze.**

An earlier draft of this section said the two clocks must agree and voided the run
otherwise. **That was wrong and it would have discarded valid data.** They measure
different scopes and are *not* expected to match:

| clock | scope | role here |
|---|---|---|
| `time.perf_counter()` around a synchronized region | wall time including CPU/Python dispatch, launch and synchronization | **PRIMARY.** It is what the product actually waits for. |
| `torch.cuda.Event` elapsed | device-side execution only | **DIAGNOSTIC.** Decomposition, never the headline. |

**Their difference is itself a recorded measurement** — the host-side cost of
getting the work onto the GPU — and for a build decision it is worth knowing,
because it is the part a different serving language could remove.

**Disagreement between them never voids a run.** The only voiding condition is a
missing or failed `torch.cuda.synchronize()` around the timed region, which is
asserted structurally in the harness rather than inferred from the numbers.
The original concern behind the bad rule still stands and is met by the
synchronize, not by clock comparison: **a benchmark reporting only kernel-launch
time is invalid.**

**9.3** Three states kept separate and never mixed: **cold init** (process start
and weight load), **first decode**, **warm steady state**. Model loading is never
inside a steady-state number.

**9.4** Warm-up: 5 decodes discarded before any measured repetition.

## 10. Streaming measurement — the primary arm

**10.1 Chunkability is established before latency is measured — and a causal layer
does not establish it.** For each arm, trace the **complete inference path** and
record with code citations: every stage's causality · state/cache API present or
not · future-context requirement per stage · minimum practical chunk ·
overlap/crossfade requirement.

Every arm then carries one **provisional label**, and no label is upgraded by code
inspection alone:

`TRUE_INCREMENTAL — MEASURED` · `CHUNKABLE_WITH_OVERLAP` · `STATELESS_CHUNKING` ·
`FULL_CONTEXT_ONLY` · `STREAMING SUPPORT NOT ESTABLISHED`

**`TRUE_INCREMENTAL` requires both** a full-path trace that permits it **and** an
empirical chunk test showing the decoder emits correct audio from partial input
while retaining state. Static evidence may only ever be described as *supporting*
or *contrary*. Promoting a grep result to a capability claim is the R13 defect and
it is banned here by name.

**10.2 Arms that cannot stream are not excluded.** A non-causal decoder is
measured in **chunked-with-overlap** mode, and the overlap it needs is part of its
cost. That is the honest comparison: what would it actually take to stream this.

**10.3 TTFA — defined so a microscopic fragment cannot win it.**

An earlier draft defined first-chunk latency as time to the *first audio sample*.
**Withdrawn:** under that definition an arm that returns one sample beats an arm
that returns a usable block, which is an artefact of the definition rather than a
property of the decoder.

> **TTFA = wall time from the moment the minimum required representation input is
> available to the decoder, until the first PLAYABLE PCM BLOCK is returned.**

A **playable PCM block** is a contiguous buffer of at least the condition's
requested output duration (§10.4), at the arm's declared sample rate and channel
count, passing the §8 validity gate. Anything shorter is not a block and does not
stop the clock.

**Required lookahead is reported separately and never folded into TTFA**, in
**frames/tokens and equivalent audio milliseconds**. It is *not* converted into
wall-clock time, because producing those frames is generator work and **generator
timing is outside this study** (§2). Converting them would smuggle an
unmeasured component into a measured number.

**10.4 Chunk conditions — common audio-time anchors, snapped to native granularity.**

Requested output durations, frozen: **20, 40, 80, 160, 320, 640, 1000 ms.**

Each is **snapped upward** to the arm's native frame/token granularity; conditions
that collide after snapping are **deduplicated**; and the **actual effective
duration is recorded** in every row rather than the requested one. So an arm whose
quantum is 80 ms simply has no 20 or 40 ms condition — it is not penalised for
physics, and no arm is flattered by a unit choice.

**Additionally, one native-single-frame condition per arm** is measured and kept
as an architectural datum, reported separately from the common anchors.

**10.5 Measured per arm, per chunk condition:**

| metric | definition |
|---|---|
| TTFA | §10.3 |
| required lookahead | frames/tokens **and** equivalent audio ms, reported separately |
| steady-state chunk latency | median wall time per chunk after the first |
| jitter | p50, p95, p99, IQR and maximum of chunk latency |
| underrun rate | share of chunks whose wall time exceeded their audio duration |
| real-time margin | chunk audio duration ÷ chunk wall time |
| long-run stability | latency drift and VRAM drift over a sustained run |
| peak GPU allocated / reserved | `max_memory_allocated` / `_reserved`, reset per repetition |
| CPU / host RAM | recorded per arm |

**10.6 Boundary integrity — frozen now, before any output is heard.**

**Reference:** that same decoder's own full-context decode of the same tokens.
A self-comparison, so no external quality model is needed and no cross-decoder
quality claim is created.

Frozen before results, so none of it can be chosen to suit an outcome:

- **Alignment:** streamed and full-context output aligned by construction at sample index 0; any arm-specific constant delay is measured once on a fixed calibration clip and applied identically to every condition of that arm.
- **Overlap handling:** where an arm streams with overlap, the trimming or crossfade is part of that arm's declared streaming configuration and is applied before measurement, never after seeing the seam.
- **Seam window:** ±5 ms either side of each seam, at the arm's own sample rate.
- **Measure 1 — normalised seam jump:** the maximum absolute first-difference between adjacent samples inside the seam window, divided by the same statistic computed over the full-context output's corresponding window. A value of 1.0 means chunking added nothing.
- **Measure 2 — local difference:** RMS of the sample-wise difference between streamed and full-context output inside the seam window, normalised by the RMS of the full-context output in that window, and the same on a log-magnitude STFT with the arm's own frame parameters.
- Both reported per seam and aggregated as median and maximum across seams.

⚠️ **This measures what chunking cost a decoder relative to itself.** It is not a
quality ranking between decoders and no output may present it as one.
**QUALITY COMPARISON NOT ESTABLISHED** stands.

## 11. Durations and repetitions

**Durations:** 1, 2, 5, 10, 30 s, each cut to an **exact token count** per system
so the produced-audio denominator is exact rather than approximate. This is what
separates fixed overhead from duration-dependent cost (H3).

**Input construction:** encode a fixed set of real clips **once**, cache every
token tensor and every mel to disk, hash the cache, and decode from cache in every
arm. **The encoder is never inside a timed region.**

**Repetitions — frozen now, with no pilot.** **N = 30 measured warm repetitions
per cell, plus 3 cold.** House minimum is 8; 30 is chosen for stability and is
fixed here.

An earlier draft said 30 was "decided after a pilot" while §17 simultaneously
asserted no timing result informed this document. **Those could not both be true.**
No pilot has run, none will run before freeze, and N is frozen at 30 rather than
left to be justified later. **N is never reduced after variance is observed.**

Every individual run is kept — no means-only file. Exclusions follow §12 and stay
visible in `raw_runs.csv`.

**Execution order — block-randomised.** Arms and conditions are interleaved in a
randomised order under a **stored RNG seed**, rather than run arm-by-arm to
completion. Randomisation is **within environment**, so the §7.2 environment
control is not broken by it. This prevents thermal and clock drift over a long
session from being absorbed into whichever arm happened to run last, which would
be indistinguishable from a real difference.

## 12. Failure, OOM and exclusion

Every failure is a **recorded row carrying its state**, never a missing row. OOM
is a result. No outlier is discarded except by the rule frozen here, and any
exclusion reports the count it did not judge in the same object as the score
(R18 corollary) — in every output format, not only the human-readable one.

## 13. Statistics

**Descriptive as primary:** median, inter-quartile range, min, and all raw runs —
the kernelproof house style, appropriate because the unit that varies is the
repetition and the populations are small and fully enumerated.

**Paired comparison only where the input can be made identical:** the controlled
pair in Route A, and within-mel-config pairs in Route B.

**No multiplicity correction unless a declared family needs one.** Holm is not
applied because another BedVibe paper used it. Families are declared before
anything is computed.

**R18:** where a denominator is not forced from outside the system, every
candidate denominator is reported side by side and the choice is called unforced.

## 14. Outputs

`README.md` · this file · `ENVIRONMENT.json` · benchmark runner(s) · frozen input
manifest with hashes · `results/raw_runs.csv` · `results/summary.csv` ·
`RESULTS.md` · `LIMITATIONS.md` · plots generated from raw data · `paper/` only if
the result earns it. Exact reproduction commands. **Failed runs kept.**

Machine-readable `EVIDENCE.codecs` / `EVIDENCE.decoders` records at the end, every
field carrying its evidence state and source path, for the Explorer to consume
**after review**. This project does not edit the Explorer.

## 15. Claim withdrawal

Per `OPTIMIZATION.md` precedent: a claim that fails replication is marked
**WITHDRAWN** and kept in history with the original observation, the replication
result, and why it no longer survives. A negative replication is evidence.

## 16. What this benchmark decides, and what it does not

### 16.1 What it decides

> **Which representation→waveform routes are streaming-viable, and what each one
> costs in latency, lookahead, jitter, boundary integrity and memory, on this
> RTX 5080 at fp32.**

That is the whole claim. It is a real one and it is enough to shortlist.

### 16.2 What it does NOT decide — and this is the sentence that matters

⛔ **This study cannot select the TTS architecture on its own.** It measures one
consumer of the latency budget under one precision on one machine. Surviving
candidates advance to two further gates before any architectural recommendation:

1. **A reconstruction-quality study.** Matched inputs, a declared quality protocol. Until it exists, **QUALITY COMPARISON NOT ESTABLISHED** stands and no candidate may be recommended on speed alone.
2. **An end-to-end generator→decoder streaming study.** The decoder is one term in the budget; the generator is the other, and they interact.
3. **A production-precision gate.** fp32 is the Phase 1 comparability baseline because every checkpoint on disk is fp32. **A real build decision additionally requires bf16/fp16 or whatever precision ships**, and on Blackwell that interacts with SDPA backend selection. A candidate that wins at fp32 has not been shown to win in production precision.

### 16.3 The candidate scope is the local estate — Phase 1 only

⚠️ **Every candidate here was selected because it is already on this machine.**
That is a legitimate Phase 1 boundary and an illegitimate basis for "the best
architecture available in 2026". Without a deliberate survey, the winner of this
study is only **the best thing already installed on Panos's computer.**

**Required before any architectural recommendation: a literature and code audit**
naming the serious modern streaming codec, decoder and vocoder families, and
recording for each why it was included or excluded. That audit is a separate piece
of work and is not performed here.

### 16.4 Also not answered

1. **Perceptual quality.** No listening test. Which decoder *sounds* best is not measured and no sentence may imply it.
2. **Generalisation beyond this machine.** One RTX 5080, one driver, one torch version.
3. **End-to-end TTS latency.** §2.
4. **Behaviour at batch > 1.** Primary is batch 1.
5. **The BedVibe 48 kHz route.** Artifact missing; the arm is absent, not zero.
6. **HiFi-GAN.** No weights on disk. NOT AVAILABLE is not NOT MEASURED.
7. **Whether a decoder could be trained better.** This measures inference on published checkpoints.

## 17. The latency budget — how these numbers get used

The product target belongs to the **whole model**, not to the decoder. So the
decoder benchmark reports **budget consumption**, and is never scored pass/fail
against the product number.

**Model-side first-audio targets, as engineering goals:**
**competitive ≤ 75 ms · stretch ≤ 50 ms · red zone ≥ 200 ms for the TTS stage alone.**

⚠️ **Provenance of those figures: vendor-reported, from vendors' own systems and
own measurement conditions — market anchors, NOT measurements comparable to
anything produced here.** They are recorded with that label wherever they appear,
and no output of this project may present them as benchmark results or compare a
number from this study to them as though the protocols matched.

**What this study contributes to that budget, per arm and per chunk condition:**
milliseconds consumed, lookahead required, jitter distribution, and therefore
**milliseconds left over for text frontend, acoustic generation and serving.**

The shape of the eventual answer — reportable only once the numbers exist:

> *"The model has a 75 ms first-audio budget. This decoder consumes N ms warm at
> the required chunk size, needs K frames of context, holds real-time margin with
> this jitter distribution, and shows this seam penalty. That leaves 75 − N ms for
> everything else."*

## 18. Freeze

Nothing in this document was written with knowledge of any timing result. The only
quantities measured before this line are **static**: file sizes, config constants,
code properties, and the codebook identity check in `AUDIT.md` §3.1 — all of which
appear there so every constant here can be checked without running anything.

**No decode has been timed. No GPU run has occurred.**

---

## AMENDMENT LINE — everything below appends, with a date. Nothing above is edited.

### 2026-09-11, amendment 1 — streaming chunk tests must respect each arm's native quantum

**Results had been observed for one arm when this was written, and that must be
stated plainly.** It is nonetheless a **schema/validity correction, not a
result-driven one**: it is justified independently by the model's own explicit
streaming contract (`codec.chunk_size`), which exists in the library and in the
model card regardless of any measurement.

**The defect.** `chunk_test.py` first ran FocalCodec at chunk sizes of 1, 5, 10
and 25 tokens and every arm failed. FocalCodec declares
`chunk_size = 1280` input samples at 16 kHz = **80 ms = 4 codec frames at 50 Hz**,
the same 80 ms its model card publishes as latency. **None of 1/5/10/25 is a
multiple of 4**, so every chunk straddled the model's atomic streaming block.
Those runs are **VOID** and remain documented as an instrument failure
(`MANIFEST.md` §7).

**THE RULE, frozen:**

> **Valid chunk conditions are DERIVED FROM THE MODEL OR RUNTIME FIRST, never
> chosen arbitrarily. Every tested chunk size must be an integer multiple of that
> arm's declared or native streaming quantum. Splitting an architecture's atomic
> streaming block and reporting the result as a streaming failure is an instrument
> error, not a finding.**
>
> **If an arm's native quantum cannot be established, its streaming
> classification is `NEEDS RESOLUTION` — never `FULL_CONTEXT_ONLY` by default.**
> Inability to determine the quantum is not evidence that no quantum exists.

**This is the same defect as the fixed 50 ms duration tolerance that failed Qwen
for obeying its own 80 ms frame quantum** (`MANIFEST.md` §5.2): the instrument
imposing a grid the architecture never claimed. Two instances, one root cause.

**Guard against misuse:** this correction may not be invoked to re-run an arm at
new chunk sizes after seeing an unfavourable result. The quantum is read from the
model's own contract **before** its test, and recorded with the result.

### 2026-09-11, amendment 2 — two claim boundaries around FocalCodec's result

Written when FocalCodec's streaming result was known. Neither expands a claim;
both restrict one.

1. **50 codec targets/s is a property of the representation.** It is **not** "50 Transformer evaluations per second". Generator factorisation is a separate, later experiment and nothing here measures it.
2. **The 80 ms streaming quantum is not measured end-to-end TTFA.** It is the decoder's atomic block. Decoder TTFA and generator latency remain separate measurements, per §2.

---

**Amendments 3–7 were all written on 2026-09-11 in response to an independent
adversarial audit of Gate 2 (`GATE2_AUDIT.md`). RESULTS HAD BEEN SEEN FOR EVERY
ARM WHEN THEY WERE WRITTEN, and that is stated once here rather than repeated.
None of them expands a claim. Every one either declares something that was
already true and undeclared, restricts an interpretation, or records a defect.**

### 2026-09-11, amendment 3 — `focalcodec_50hz_65k_causal` is a declared post-freeze arm

`focalcodec_50hz_65k_causal` was run in the Gate 2 batch and reported as one of
three headline `TRUE_INCREMENTAL` results while appearing **in no Gate Zero
record, not in `MANIFEST.md` §2a, not in `AUDIT.md` §6.1e and not in §3 of this
document.** It entered the study after the freeze with no amendment. That is the
defect; this is the declaration.

- **The arm is DECLARED, not deleted.** Its numbers reproduced exactly under an
  independent adversarial re-run in a separate process, and deleting a result
  because its paperwork was late would discard evidence rather than correct a
  record.
- **It carries the label `POST-FREEZE ARM — DECLARED 2026-09-11`** wherever it
  appears, alongside `focalcodec_50hz_4k_causal` and `focalcodec_50hz_2k_causal`,
  which were frozen in §3 before any result existed.
- **It is not the primary FocalCodec result.** Where one causal FocalCodec
  configuration must be named, that is `focalcodec_50hz_4k_causal`.

`focalcodec_50hz_4k_causal` — the arm that IS frozen in §3 — was absent from that
same batch and has now been run through the identical harness, so both the frozen
arm and the post-freeze arm sit on one artifact with one classifier.

### 2026-09-11, amendment 4 — Griffin-Lim runs with deterministic phase initialisation

`torchaudio.transforms.GriffinLim` defaults to `rand_init=True`, and no seed was
set. **Measured self-vs-self error — the same spectrogram decoded twice with no
chunking at all — was `7.7404e-01`, `131.3%` of peak.** The published chunking
band for this arm was `7.244e-01–7.637e-01`. The number measured random phase,
not chunking, and it is **WITHDRAWN**.

> **`griffinlim` is run with `rand_init=False`. Measured self-vs-self error under
> that configuration is `0.000e+00`.** With random initialisation the decoder is
> not a function of its input, and no chunking measurement is defined for it.

The determinism probe is recorded on the arm's own artifact row, both
configurations, so the reason for the declared configuration travels with the
result. `griffinlim` remains an **R9 zero-parameter floor and never a production
candidate**, so this changes no recommendation.

### 2026-09-11, amendment 5 — the environment record, and the §7.1 divergence

§7.1 is frozen and names two environments, `fish` and `chatterbox`. **The
measurements actually ran in `decbench`, `decbench_melflow` and `fish`, with
`decbench_nemo` blocked.** §7.1 is above the amendment line and is not edited.

`ENVIRONMENT.json`, required by §7.1 and §14, **did not exist** and now does. It
records, per environment: interpreter, full package set with versions, torch and
its CUDA build, cuDNN, GPU name, capability, memory and SM count, and the live
`nvidia-smi` row.

**torch is `2.10.0+cu128` in all four environments** — the controlled variable is
held. **`transformers` differs (4.57.3 · 5.17.0 · 4.35.2 · 4.57.6) and remains a
DECLARED VARIABLE** measured by the §7.2 environment control, never assumed to be
zero.

### 2026-09-11, amendment 6 — the chunking metric is a DETECTOR, not a severity scale

The chunking metric is `max|full − chunked| / max|full|`, computed against each
arm's own full-context reconstruction. An attack suite run on `encodec24_q8`
measured:

| condition | value |
|---|---|
| **one-sample shift** | **34.07%** |
| four-sample shift | 110.68% |
| **all-zero output** | **100.00%** |
| a different utterance entirely | 118.01% |

**A one-sample misalignment is indistinguishable from genuine chunking damage on
this metric, and an all-zero output scores better than a four-sample shift.**

> **The metric supports "chunked decoding departs from full-context decoding" and
> **NOT** "arm X departs more than arm Y". Every cross-arm severity ranking built
> on it is WITHDRAWN, including "Fish departs more than EnCodec".**

**Cumulative length drift is now a recorded column.** Per-chunk output length is
exactly linear in chunk size for every measured arm — `L(u) = a·u + b`, maximum
residual `0.0` — so `b` is the constant offset each chunk carries and it
accumulates once per chunk. Measured: **`vocos_mel24` and `griffinlim` `b = −256`
samples** (≈47 000 samples, ~2.0 s, at the 8-frame condition), **DualCodec both
configurations `b = −4`**, every other arm `b = 0`. `n = min(lengths)` hides
this, so part of the error reported for the two `b = −256` arms is misalignment
rather than boundary damage.

### 2026-09-11, amendment 7 — MelFlow is measured through its own streaming contract, with a declared boundary

The first MelFlow measurement is **WITHDRAWN** on four counts: it was
non-deterministic (self-vs-self `1.0117e+00`, `142.09%`), it fed raw waveform
chunks rather than the mel-derived representation, each chunk was divided by its
own peak under `normalize_mode='noisy'` (measured 115× gain spread), and **the
streaming API was never reached** — only `enhance()`'s signature was checked,
while the backbone `CausalNCSNpp` is a `CausalStreamingModule` whose contract is
`init_state()` + `forward_step(x, time_cond, aux_condition, *, state)`.

The repository ships **no streaming driver**; its README directs the reader to
build one from those two functions. One was written. Flow noise is drawn once
under a fixed seed and shared by every condition; the conditioning features are
computed once over the whole utterance; normalisation happens once; and one state
list is carried **per solver step**, because the network is evaluated N times per
frame and each of those N call sequences is its own causal stream.

**Two upstream defects were found and are declared, not hidden.** Both are dead
code in the streaming path, and neither changes a weight or any arithmetic:

1. `CausalConv2d.forward_step` reads `self.depthwise_separable` and
   `self.pointwise_conv`; `CausalConv2d.__init__` defines **neither** — they
   belong to the separate `CausalDecoupledConv2d` compression class. Every
   `forward_step` call raises `AttributeError` on an uncompressed model. Set to
   `False`, the only value consistent with a class that has no pointwise conv.
2. `CausalResnetBlockBigGANpp.init_state` returns a 5-tuple while its own
   `forward_step` unpacks 6 (`state_se`). The block raises `ValueError` on the
   first call. `state_se` is unpacked and repacked and **never read or written**
   anywhere in the body. A sixth element `None` is appended.

> **This is a released-tooling finding, in the same class as the NanoCodec/NeMo
> blocker: the shipped streaming path of revision `ab2700c1` does not execute as
> released. It is NOT a finding about the MelFlow architecture**, which streams
> correctly once the two dead references are satisfied.

**THE RESULT, and the label changes.** Over all 992 frames of the probe:
determinism probe `0.000e+00` · **C1 passes, stateful error `3.036e-06`** ·
**C2 passes, `2.20e+05×`–`3.55e+05×`** against a threshold of 10 · Gate Zero
`PASS`. **`STATELESS_CHUNKING` → `TRUE_INCREMENTAL`.** The stateful error is
identical at every condition because this arm's stateful branch is
frame-synchronous and does not depend on the chunk condition; **the chunk
condition parameterises the stateless null only.**

**DECLARED CLAIM BOUNDARY FOR THIS ARM.** What is driven incrementally is the
**neural decoder**: N solver steps per STFT frame, each with its own carried
state, one frame at a time. The **inverse STFT / overlap-add is performed once
over the assembled spectrogram.** This establishes that the network runs
frame-synchronously with carried state; it does **NOT** establish a streaming
overlap-add stage, and no output may read it that way. For the same reason the
length-drift decomposition does not apply to this arm and its fitted offset is a
regression residue, not per-chunk drift.

⚠️ **The AGPL-3.0 label is unchanged and unconditional:** `RESEARCH /
ARCHITECTURE EVIDENCE — NOT SHIPPABLE AS A CLOSED-PRODUCT DEPENDENCY UNDER THE
CURRENT LICENCE.`

### 2026-09-11, amendment 8 — `TRUE_INCREMENTAL` is recorded WITH ITS SCOPE

**Written after an independent delta audit, with all results seen. It restricts a
claim and expands none.** The audit reproduced every repaired measurement,
required no re-measurement, and raised one BLOCKING defect: amendment 7 gave
`melflow` an **unqualified** `TRUE_INCREMENTAL`, presented in the matrix and the
headline total identically to the three causal FocalCodec arms.

§10.1 is frozen and says `TRUE_INCREMENTAL` requires *"an empirical chunk test
showing the decoder emits correct audio **from partial input** while retaining
state"*, reinforced by §2 (*measured: representation → waveform*) and §10.3
(TTFA stops at *the first PLAYABLE PCM BLOCK*). **MelFlow's repaired test never
emits audio from partial input.** It emits spectrogram frames incrementally and
inverts once over the assembled spectrogram.

**The untested stage is not free.** A control measured by the delta audit — naive
split-in-two inverse STFT, then concatenate — gives **raw `1.036108e+00` /
`134.65%` of peak, 256 samples short** (253 440 vs 253 696). Streaming it
therefore does not follow from the neural decoder streaming, and **R13 forbids
upgrading it by inspection.**

**THE RULE, frozen:**

> **Every arm records the §10.1 predicate explicitly as
> `emits_pcm_from_partial_input`, and `TRUE_INCREMENTAL` is never written
> unqualified.** It is recorded as **`TRUE_INCREMENTAL (representation → PCM)`**
> where that predicate holds, and as **`TRUE_INCREMENTAL — <the stage that is
> established>; <the stage that is not> NOT ESTABLISHED`** where it does not.
>
> **The two are never summed into one total.** A headline count that merges them
> asserts for one arm a capability only the others demonstrated.

Applied: three causal FocalCodec arms → `TRUE_INCREMENTAL (representation → PCM)`.
`melflow` → **`TRUE_INCREMENTAL — NEURAL DECODER; iSTFT STREAMING NOT
ESTABLISHED`**, with C1 recorded as `PASS @ 16 ms granularity` because its
stateful branch is one continuous frame-synchronous stream, not four separate
stateful decodes at four chunk sizes.

**This is a scope correction, not a measurement correction. Nothing was re-run,
nothing is withdrawn, and no number changed.** The path to the unqualified label
is open and stated: write a streaming overlap-add stage and **test** it.

### 2026-09-11, amendment 9 — Gate 3 execution declarations

⛔ **WRITTEN BEFORE ANY TIMING RESULT EXISTS.** No GPU measurement had been taken
when this was written. Every item is a construction or a deviation declared in
advance so that none of it can be chosen to suit an outcome.

**9.1 §7.3 machine state — COMPLIED WITH, residual recorded.** Chrome, Teams,
Discord, Telegram, WhatsApp, Docker Desktop, ChatGPT and Copilot were closed by
the owner before the run. Measured baseline: **VRAM used 7 340 MiB → 1 341 MiB,
free 8 638 MiB → 14 637 MiB; host RAM free 14 278 MB → 18 670 MB.** The residual
1 341 MiB is the Windows desktop compositor, `explorer.exe`, shell components and
**VS Code, which hosts the session that runs the benchmark and therefore cannot
be closed.** That residual is declared, not eliminated, and `nvidia-smi` is
sampled before and after every cell per §7.2.

**9.2 Input construction.** The frozen probe is one real-speech clip,
`audiocodecs/example.wav`, **15.860 s @ 16 kHz mono** — the same clip every Gate
Zero and Gate 2 measurement used. §11's durations are constructed from it:

- **1, 2, 5, 10 s** are **prefixes** of that clip.
- **30 s exceeds the source**, so it is the clip **tiled to exactly 30.000 s**,
  introducing **one artificial seam at 15.860 s**. Declared, not hidden.

This is a timing benchmark whose denominator is produced-audio duration, which is
exact regardless of content, and §11's requirement that each duration be cut to
an **exact token count** is met by truncating each arm's cached representation to
exactly the unit count for that duration. **No quality claim rests on the tiled
clip, and none may be made from it.**

**9.3 Cold initialisation is decomposed, not merged.** §9.3 defines cold init as
"process start and weight load". Running 3 fresh OS processes for each of 19 arms
would spend most of its time in the Python interpreter and the torch import,
which is not a property of any arm. Cold init is therefore recorded as **three
separately reported components**, never summed into one headline:

- `process_start_s` — interpreter start to torch imported. Measured **once per
  runner process** and attributed to no arm.
- `model_load_s` — construction plus weight load plus transfer to device, **3
  repetitions**, a fresh object each time with the allocator cache emptied.
- `first_decode_s` — the first decode after a fresh load, **3 repetitions**.

**9.4 Streaming cut lengths.** The chunk-condition sweep runs on the **2 s** cut,
which yields 100 chunks at the finest condition — enough for a latency
distribution — and the sustained-run cell runs on the **30 s** cut. `N = 30` warm
repetitions is unchanged for every distribution cell.

**9.5 The sustained-run cell is `N = 3`, declared here before any result.** It
estimates **drift within a run** — latency and VRAM at the start of a 30 s stream
versus at the end — not a distribution across repetitions, so repetitions are not
its unit of variation. §11 forbids **reducing N after variance is observed**;
this N is fixed in advance, for a different estimand, and is reported under its
own name (`longrun`) rather than beside the `N = 30` cells.

**9.6 `melflow` — decode granularity is fixed by the architecture.** Its decoder
consumes **one STFT frame per call** with carried state; a chunk condition does
not change the decode call, it changes how many frames are buffered before an
emit. Its per-frame stream is therefore measured once per repetition and block
latencies are composed from that measured stream. **Composition is stated on
every affected row; no per-condition decode is claimed that was not run.**

⛔ **9.7 `melflow` TTFA is NOT ESTABLISHED and no number may be reported for
it.** §10.3 stops the clock at the first **playable PCM block**, which must pass
the §8 validity gate. MelFlow emits spectrogram frames; producing PCM from a
partial stream requires an overlap-add stage that amendment 8 records as **not
established**, and the delta audit measured naive chunking of it at **134.65%**.
The harness still runs that path and **records the §8 verdict it produces**; if
the buffer fails the gate, the row is **inadmissible** per §8 and TTFA is
reported as `NOT ESTABLISHED`, never as a number and never as a blank.

**9.8 §10.2 overlap, for arms with no constructible decode state.** Chunked-
with-overlap is measured as **left context of 0, 1, 2 and 4 quanta at the 80 ms
anchor only**, rather than crossed with every condition. The overlap is part of
that arm's cost and is reported as such; boundary integrity (§10.6) is reported
per condition alongside it.

**9.10 EVERY arm is timed in EAGER mode. No `torch.compile`, no CUDA graphs, no
quantisation, no fusion, for any arm.** This is a uniformity choice, in force
from the first cell, not a result-driven one.

⚠️ **It is not neutral for `melflow`, and that must be said rather than left
implicit.** Its backbone decorates `forward_step` with
`@torch.compile(fullgraph=True, max_autotune=True)`, which this harness disables
(`TORCHDYNAMO_DISABLE=1`), and its upstream README explicitly recommends **CUDA
graphs** for streaming speed, citing the paper's own optimisation section.

> **MelFlow's Gate 3 latency is therefore an EAGER-MODE figure. It is an upper
> bound on that architecture's latency, not an estimate of its best achievable
> latency, and no output may present it as the latter.** The same disclaimer
> applies to any other arm that ships a compiled path; none of the others does.

**9.11 §7.4 — one GPU process at a time.** The four runner processes
(`decbench` batch A, `decbench` batch B, `fish`, `decbench_melflow`) execute
**strictly sequentially**. No concurrent GPU work from any other thread or
session runs while a primary arm is being measured.

**9.9 Nothing here changes an estimand, a criterion, a threshold or a label.**

### 2026-09-11, amendment 10 — the E6 environment control, and the §7.2 VRAM re-run rule

⛔ **Written AFTER Gate 3's timing results were seen, in response to an
independent audit. It restricts claims and repairs an instrument rule; it
expands nothing.**

**10.1 E6 WAS MISSING AND HAS NOW BEEN RUN.** §7.2 pre-commits that
`encodec24_q8` at a fixed duration is run in **both** environments. It was not,
and Gate 3's first matrix placed `fish_modified_dac` — the incumbent — in one
table beside 17 arms measured under a different package set, with neither the
control nor the label §7.2 reserves for that case. **That was a protocol
violation, not an oversight of presentation.**

The control has now been run **in all three environments that produced arm rows**,
as a single arm on every side (the arm rows were block-randomised among 14 other
arms, so comparing an interleaved run against a solo run would confound the
environment effect with run context):

| environment | transformers | median ratio vs `decbench` | effect |
|---|---|---|---|
| `decbench` | 4.57.3 | 1.000 | reference |
| `decbench_melflow` | 5.17.0 | 1.005 | **0.5%** |
| `fish` | 4.35.2 | 0.498 | **50.2%** |

**The effect is a near-constant 3.0–4.0 ms offset and it is DEVICE-SIDE.** At the
2 s offline condition, host overhead is 0.022 ms in `decbench` and 0.024 ms in
`fish`, while CUDA time is **10.344 ms versus 6.328 ms**. torch is identical
everywhere (2.10.0+cu128). **The two `transformers` versions launch different GPU
work for the same decode.** This is not dispatch overhead and not noise.

**THE FROZEN RULE FIRES.** Between-decoder differences at the anchor span roughly
1.9 ms to 27.6 ms, and most arms sit between 1.9 and 16 ms; a 3.0–4.0 ms offset
is larger than the gap between many pairs of arms.

> **`fish` is NOT COMPARABLE. `fish_modified_dac` may not be compared numerically
> against any `decbench` arm, is excluded from the §17 budget table and from E4's
> ordering, and carries the marker on its row. `decbench_melflow` IS comparable,
> and that is now justified by measurement rather than assumed.**

⚠️ **The direction must not be mis-stated.** `fish` is FASTER — the incumbent's
environment flatters it by ~3.5 ms per call. **Nothing here says Fish ModifiedDAC
is fast or slow. It says its number and theirs cannot be put in one ranking.**

**10.2 §7.2's VRAM re-run rule is SUPERSEDED, with a replacement check.** The
rule reads: *"An arm whose before/after VRAM reading moves by more than 200 MiB
is re-run and both runs are kept."* **167 of 366 cells exceed that threshold and
no re-runs exist.**

The rule was written for a design in which one model stays resident. **This
harness deliberately holds a model cache of ONE and reloads on every arm switch**,
precisely so `max_memory_allocated` is the arm's own working set rather than a
co-resident model's weights — and §11's block randomisation interleaves arms, so
switches are constant. Under that design **a >200 MiB before/after move is the
EXPECTED SIGNATURE OF THE INTENDED UNLOAD/RELOAD**, not the contamination the
rule exists to catch. Re-running on it would re-run most of the benchmark and
would flag the same cells again, testing nothing.

> **Replacement check, in force from the first Gate 3 cell:** what the rule
> existed to detect — a cell whose memory reading was contaminated by another
> cell — is tested instead by `torch.cuda.reset_peak_memory_stats()` **before
> every measured cell**, so `peak_alloc_MiB` cannot inherit a previous cell's
> peak; and by the **`longrun` VRAM-drift cell**, which measures memory growth
> across a sustained run directly, at `N = 3` on the 30 s cut.

**No measured value is altered by this amendment.** The before/after readings and
the >200 MiB flag remain on every cell in `results/gate3_cells_*.jsonl`.

**10.3 Reporting corrections required by the same audit, applied.** Jitter
statistics are computed over **one population** — steady state, excluding the
first chunk of every repetition, since TTFA reports the first chunk separately;
the all-chunks population is kept beside it and the two are never mixed in a row.
`PASS` is replaced by **`MEASURED — CELLS COMPLETED AND ADMISSIBLE`** with an
explicit statement that it is not a performance verdict. **§8 streamed-output
validity is exposed on the headline**, and E3's *minimum viable streaming
configuration* now requires a §8 PASS — reported as **`NOT ACHIEVABLE`** where no
tested condition has one. E1 and E4 are produced as estimands rather than prose.
Memory ratios are reported **per scope** and never across scopes.
Every item is an execution construction. `nanocodec` remains `BLOCKED —
PLATFORM`; **no timing number will be manufactured for it**, and its absence is
reported as BLOCKED, never as zero and never as omitted.

⚠️ **Also required by the same audit, and applied:** the local repairs to
`ab2700c1` are disclosed in the authoritative matrix and in `MANIFEST.md`, not
only here; per-condition drift is recomputed on each arm's **true integer hop**
rather than its measured token rate (which had `mimi_q8` reading +7.24 to +72.37
samples/chunk where the true hop is exactly 1920 and the real drift is **0**);
and every superseded value is kept beside its replacement.
