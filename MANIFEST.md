# RUNNABLE MANIFEST — for owner review before freeze

**2026-09-11. Gate Zero complete. Nothing timed. No GPU used for any measurement.**

⚠️ **Corrected 2026-09-11.** This line previously read *"13 arms pass Gate
Zero"* while the tables below listed 14, and four further arms carried a Gate
Zero `PASS` that **was never computed** — `close_gate2.py:258/282` and
`close_gate2b.py:53/92` wrote the literal string `"PASS (this run)"`.

> **19 arms have a COMPUTED Gate Zero record and all 19 PASS. 1 arm is BLOCKED
> with a documented cause.** The counts, and every cell behind them, are in
> `GATE2_MATRIX.md`, generated from run artifacts by `make_matrix.py`.

Every arm loaded, encoded and decoded the **same 15.860 s real-speech probe**
(`audiocodecs/example.wav`) and passed the frozen `PROTOCOL.md` §8 validity gate,
now evaluated for every field by the shared `gate_lib.gate_zero_record()`:
finite · peak in `(0,1]` · duration within one frame **of that arm** ·
**energy ratio 0.25–4.0** · **dtype float32** · **channel count**.

---

## 1. Environments — frozen

| env | torch | transformers | purpose |
|---|---|---|---|
| **`decbench`** | **2.10.0+cu128** | **4.57.3** | FocalCodec ×5, Mimi, EnCodec, Descript DAC, DualCodec ×2, Qwen |
| **`decbench_melflow`** | **2.10.0+cu128** | 5.17.0 | **MelFlow only — AGPL kept physically separate** |
| **`fish`** (pre-existing) | **2.10.0+cu128** | 4.35.2 | Fish ModifiedDAC. **READ, never modified** — it carries frozen production work |
| `decbench_nemo` | 2.10.0+cu128 | — | **BLOCKED**, see §4 |

**GPU: NVIDIA GeForce RTX 5080, sm_120 (capability 12.0), driver 610.47, CUDA 12.8.**

⭐ **torch is identical across every runnable environment.** Torch determines
kernel dispatch, so the one variable that matters most is held constant.
`transformers` differs by environment and is a **declared variable**, measured by
the environment control in `PROTOCOL.md` §7.2, never assumed to be zero.

⛔ **FROZEN. Any dependency operation that changes a pinned package invalidates
Gate Zero for the affected arms and requires revalidation.** This is not
hypothetical: installing `qwen-tts` silently downgraded transformers 5.17.0 →
4.57.3 *after* three arms had already passed under 5.17.0. All three were
re-validated under 4.57.3 and re-passed with byte-identical values.

---

## 2. Arms that PASS Gate Zero

### 2a. Codec-token route

⚠️ **The `streaming label` column below is the PROVISIONAL label recorded before
any chunk test ran, and it is SUPERSEDED.** The final labels, with C1, C2, the
C2 ratio and the Gate Zero verdict for every arm, are in **`GATE2_MATRIX.md`**.
Where this column and that file disagree, that file is right. The source · pin ·
rate · codebook columns are unchanged and remain correct.

| arm | source · pin | analysis SR | synth SR | rate (MEASURED) | codebooks | targets/s | energy | streaming label (SUPERSEDED) |
|---|---|---|---|---|---|---|---|---|
| ⭐ `focalcodec_50hz_4k_causal` | `lucadellalib/focalcodec` @ `912b7f2c` · Apache-2.0 | 16 000 | **24 000** | 50.000 Hz | **1** binary | **50** | 0.828 | ✅ **`TRUE_INCREMENTAL — MEASURED`** (§7) |
| ⭐ `focalcodec_50hz_2k_causal` | same | 16 000 | **24 000** | 50.000 Hz | **1** binary | **50** | 0.811 | **FULL-PATH CAUSAL**, same |
| ⚠️ `focalcodec_50hz_65k_causal` | same | 16 000 | **24 000** | 50.000 Hz | **1** binary | **50** | see `GATE2_MATRIX.md` | **POST-FREEZE ARM, DECLARED 2026-09-11** — `PROTOCOL.md` amendment 3. Added here because it was missing from every record while being reported as a headline result. |
| `focalcodec_50hz` | same | 16 000 | 16 000 | 49.937 Hz | 1 | 50 | 1.005 | non-causal, all 4 stages |
| `focalcodec_25hz` | same | 16 000 | 16 000 | 24.969 Hz | 1 | 25 | 1.105 | non-causal |
| `focalcodec_12_5hz` | same | 16 000 | 16 000 | 12.484 Hz | 1 | 12.5 | 1.021 | non-causal |
| ⭐ `mimi_q8` — **PRIMARY** | HF `kyutai/mimi` @ `89091b3e` · CC-BY | 24 000 | 24 000 | 12.547 Hz | **8** | **100.4** | 0.871 | causal convs + padding cache; **not established** |
| `mimi_q32` — **SENSITIVITY ABLATION** | same | 24 000 | 24 000 | 12.547 Hz | **32** | 401.5 | 0.934 | same architecture, depth only |
| `encodec24_q8` | HF `facebook/encodec_24khz` @ `c1dbe2ae` | 24 000 | 24 000 | 75.000 Hz | 8 | 600 | — | causal convs; not established |
| `dac44` | HF `descript/dac_44khz` @ `c1bc5216` | 44 100 | 44 100 | 86.000 Hz | 9 | 775 | — | **non-causal**, no causal option in module |
| `dualcodec_12hz_v1` | HF `amphion/dualcodec` · PyPI `dualcodec` 0.4.2 | 24 000 | 24 000 | 12.484 Hz | 8 (1 sem + 7 aco) | **99.9** | 1.099 | not established |
| `dualcodec_25hz_v1` | same | 24 000 | 24 000 | 24.969 Hz | 8 (1 sem + 7 aco) | 199.7 | 1.049 | not established |
| `qwen3_tts_tokenizer_12hz` | HF `Qwen/Qwen3-TTS-Tokenizer-12Hz` · **Apache-2.0** | 24 000 | 24 000 | 12.547 Hz | **16** | **200.8** | 0.939 | documented causal ConvNet; not established |
| `fish_modified_dac` — **incumbent** | `codec.pth`, hydra `modded_dac_vq` | 44 100 | 44 100 | 21.564 Hz | 10 | 215.6 | 0.984 | causal in inspected stages; not established |

**Fish loaded with 0 missing and 0 unexpected keys.** Worth stating because the
upstream loader uses `strict=False`, which can silently skip weights and still
appear to work. Nothing was skipped.

### ⭐ The two Mimi arms — one architecture, one variable

| arm | role | n_q | rate | targets/s | **measured bitrate** | energy ratio |
|---|---|---|---|---|---|---|
| **`mimi_q8`** | **PRIMARY / production-relevant** | 8 | 12.547 Hz | 100.4 | **1.10 kbps** | 0.871 |
| **`mimi_q32`** | **SENSITIVITY ABLATION** | 32 | 12.547 Hz | 401.5 | **4.42 kbps** | 0.934 |

**The measured 1.10 kbps at n_q=8 matches Mimi's published figure exactly**, which
closes the default-codebook trap with a measurement rather than an argument.

⛔ **Their results are never merged, and the n_q=32 configuration is never called
"Mimi 1.1 kbps."** That figure belongs to n_q=8 and to nothing else.

⛔ **`mimi_q32` is NOT a competing architecture candidate.** It exists to measure
what **representation depth** costs while architecture, temporal rate and decoder
family are all held fixed — a cleaner controlled comparison than any two unrelated
codecs can offer. It never competes for the architecture recommendation.

**`n_q` appears in every raw row, every summary row and every Explorer evidence
record for Mimi.** The energy-ratio gap already visible here (0.871 → 0.934) is
the first hint of what depth buys; whether it also costs latency, memory,
boundary integrity or detector shift is exactly what the ablation will measure.

### 2b. Mel / continuous route

| arm | source · pin | SR | params | energy | licence |
|---|---|---|---|---|---|
| `melflow` | `sp-uhh/streamfm` @ `ab2700c1`; ckpt sha256 `c47a1e85…f2333` | 16 000 | **27,896,458** | 0.974 | ⚠️ **AGPL-3.0** |

⚠️ **MelFlow results carry a permanent label:** `RESEARCH / ARCHITECTURE
EVIDENCE — NOT SHIPPABLE AS A CLOSED-PRODUCT DEPENDENCY UNDER THE CURRENT
LICENCE`. Source never enters product code. A clean reimplementation answers
copyright, **not patents** — separate review required before shipping.

**Three deviations declared for this arm, none hidden:**

1. **torch** — streamfm pins `2.7.0+cu128`; we run the controlled `2.10.0+cu128`. Keeping the controlled variable was the deliberate choice.
2. **Checkpoint provenance** — Google Drive via `gdown`. **No revision, no content addressing.** Our own sha256 is the only pin, and this is the weakest provenance of any arm.
3. **CUDA assert bypassed** — upstream `inference.py` hard-asserts `torch.cuda.is_available()`. That assert guards their CLI, not the model; the model was constructed directly and ran on CPU, proving the assert is not a property of the architecture.

---

## 3. Provisional streaming labels — none upgraded by code inspection

Per `PROTOCOL.md` §10.1, `TRUE_INCREMENTAL` requires a full-path trace **and** an
empirical chunk test. **Only FocalCodec's causal configs have the trace.**

⚠️ **Superseded 2026-09-11.** This section closed with *"no arm carries a final
streaming label"*, which §7 below then contradicted by freezing four. It was
written before the chunk tests ran and describes the state at that moment.
**The current labels are in `GATE2_MATRIX.md`, machine-generated from the run
artifacts; where this section and that file disagree, that file is right.**

---

## 4. BLOCKED — NanoCodec

**NVIDIA NanoCodec 22 kHz. Commercially licensed, causal HiFi-GAN decoder,
22.05 kHz — the closest candidate to the 24 kHz target. It cannot be run here.**

It ships only a `.nemo` archive (no safetensors, no standalone config), so it
requires NeMo. Four versions were attempted:

| version | failure |
|---|---|
| `nemo_toolkit[tts]` | `pynini` wheel build fails — OpenFst wrapper, effectively Linux-only |
| `nemo_toolkit` 3.0.0 | `nv_one_logger` — **published on no public index**, incl. `pypi.nvidia.com` |
| `nemo_toolkit` 2.7.3 | same, via a deeper import path |
| `nemo_toolkit` 2.0.0 (the version its model card names) | needs older Lightning; with `pytorch-lightning==2.4.0` pinned it fails on **`signal.SIGKILL`, which does not exist on Windows** |

**`signal.SIGKILL` is POSIX-only. This is not a dependency to pin around.**

⛔ **THE CLAIM IS BOUNDED TO WHAT WAS OBSERVED. The exact wording, and it may not
drift:**

> **The released NanoCodec / NeMo reference tooling is not runnable in our
> Windows-native benchmark environment.**

**That is a released-tooling and platform-portability cost. It is NOT evidence
that the NanoCodec architecture inherently requires Linux, and NOT evidence that
a standalone Windows decoder could not be written.** Nothing here tested the
architecture — only NVIDIA's shipped runtime path. **No output of this project may
render this as "NanoCodec cannot run on Windows."**

⚠️ **WSL/Linux would not rescue it for *this* benchmark.** A Linux measurement
carries a different OS, scheduler and CUDA path, so its numbers could not sit in
the same table as the Windows-native arms. Forcing it would produce a number that
looks comparable and is not.

**Classification: `MUST BENCHMARK` → `BLOCKED — PLATFORM`.** It stays in the
evidence record with its documented properties, and its absence is reported as
**BLOCKED**, never as zero and never as omitted.

**The portability cost is itself a finding.** A codec whose reference tooling
cannot be stood up on a developer machine without a Linux-only toolchain carries a
real integration cost, and that belongs in an architecture decision rather than
being filed as our bad luck — but it is a cost of the *tooling as released*, which
is a different claim from a limitation of the codec.

---

## 5. Three defects found in Gate Zero itself

All in the instrument, none in a candidate, all caught before any result was kept.

1. **Sine-tone probe** passed near-silent reconstructions — a peak check cannot separate "reconstructed" from "quiet noise". **Run VOID.** Replaced by real speech + an energy-ratio predicate.
2. **Fixed 50 ms duration tolerance** failed Qwen for obeying its own 80 ms frame quantum. **Tolerance is now one frame of the arm under test.**
3. **Assumed a single code-tensor layout.** Qwen returns `[time, codebooks]`; transformers codecs return `[codebooks, time]`. Reading by position would have reported Qwen as *16 Hz × 199 codebooks* — respectable-looking and inverted. **The resolver now scores both axes against expected frame count and expected codebook count, lives in one shared module (`gate_lib.py`), and returns `NEEDS RESOLUTION` rather than guessing.** Property-tested against square, near-square, 1-D and 3-D inputs; it refuses all of them.

---

## 7. ⭐ EMPIRICAL CHUNK / STATE TEST — the first earned streaming label

**2026-09-11, CPU, nothing timed.** Criteria were declared before the run
(`chunk_test.py`) so the result could fail:

- **C1** — stateful chunked decode reproduces full-context decode: `max|err| ≤ 1e-3`
- **C2** — state is load-bearing: stateless error ≥ **10×** the stateful error

C1 alone is insufficient. If discarding state also reproduced full-context
output, there would be no temporal context to carry and "streaming" would be a
property of the test rather than the model. C2 is the control that separates them.

### `focalcodec_50hz_4k_causal` — PASSES BOTH, at every chunk size

| chunk | stateful err | stateless err | ratio | verdict |
|---|---|---|---|---|
| 4 tok (**80 ms**) | **4.580e-05** | 7.563e-01 | **16 515×** | ✅ TRUE_INCREMENTAL |
| 8 tok (160 ms) | 4.530e-05 | 7.179e-01 | 15 848× | ✅ |
| 20 tok (400 ms) | 5.893e-05 | 5.704e-01 | 9 679× | ✅ |
| 40 tok (800 ms) | **1.913e-05** | 5.858e-01 | **30 627×** | ✅ |

Stateful error sits at **float32 numerical noise** — 20–60 microunits against a
threshold of 1000. C2 clears by three to four orders of magnitude.

### Negative control behaved exactly as required

`focalcodec_50hz` (non-causal) **fails C1 at every chunk size**, and its stateful
and stateless errors are **identical to the digit** (ratio 1.000) — it ignores the
state entirely, because it has none to keep. **Had the control passed, the test
would have been measuring nothing and the experiment would be void.** It did not.

### ⚠️ A defect in the test, found by running it — the third of its kind

The first run used chunk sizes of **1, 5, 10 and 25 tokens, and every arm
"failed."** That verdict was wrong and the cause was mine.

FocalCodec exposes **`codec.chunk_size = 1280` samples at 16 kHz = exactly 80 ms
= 4 tokens at 50 Hz** — the same 80 ms its model card declares as latency.
**None of 1, 5, 10 or 25 is a multiple of 4**, so every chunk was a fragment
straddling the model's streaming quantum.

**Feeding a streaming model off-grid fragments and concluding it cannot stream is
the same defect as the fixed 50 ms duration tolerance that failed Qwen for obeying
its own 80 ms frame size.** Both were the instrument imposing a grid the
architecture never claimed. The first run is **VOID**; only the native-grid
numbers above are used.

**How it was caught:** the failure pattern was wrong for a genuine failure —
stateful and stateless errors were nearly equal on a *causal* arm, which cannot
happen if state is doing anything. Isolating to a single 50-token sequence decoded
one-pass versus two-chunk showed chunk 0 matching at 6.7e-04 and chunk 1 diverging,
which pointed at the grid rather than the plumbing.

### `mimi_q8` — STATELESS_CHUNKING via this implementation path

**Chunk grid established before testing: the 80 ms codec-frame grid.** Mimi runs
at 12.5 Hz, so one codec frame is 80 ms. Chunk conditions 1, 2, 5, 10 frames —
all integer multiples, per amendment 1.

⚠️ **Deliberately called a codec-frame grid, not a "streaming quantum."** Mimi has
no working decoder streaming state through this path, so naming its frame period a
*streaming* quantum would assert a capability the evidence does not support. The
frame period is a fact about the representation; a streaming quantum is a claim
about the runtime.

| chunk | stateful err | stateless err | ratio | verdict |
|---|---|---|---|---|
| 1 frame (80 ms) | 5.727e-01 | 5.727e-01 | **1.000** | C1 fail |
| 2 frame (160 ms) | 5.602e-01 | 5.602e-01 | **1.000** | C1 fail |
| 5 frame (400 ms) | 5.727e-01 | 5.727e-01 | **1.000** | C1 fail |
| 10 frame (800 ms) | 5.602e-01 | 5.602e-01 | **1.000** | C1 fail |

**Stateful and stateless were identical to the digit.** That was checked rather
than assumed — and the stated cause was **WRONG**, corrected 2026-09-11 after the
adversarial audit.

> ⛔ **WITHDRAWN, and it was false:** *"`MimiDecoderOutput` contains only
> `audio_values`. It never returns `past_key_values`."*
>
> In transformers 4.57.3,
> `MimiDecoderOutput.__dataclass_fields__ = ['audio_values',
> 'decoder_past_key_values']`. The harness read
> `getattr(out, "past_key_values", None)` — **a field that does not exist on that
> class** — so it passed `None` on every iteration and the "stateful" branch was
> byte-identical to the stateless one. The ratio of 1.000 measured the bug.

**The corrected, measured account.** `decode()` has **no `use_cache` argument**;
the cache is gated by `config.use_cache`, which `kyutai/mimi` ships as `False`.
With it enabled, `decode()` returns a live `DynamicCache`, and carrying it
**changes the output** (`torch.equal(stateful, stateless)` is `False`, verified
on a held-out pair of chunks before the sweep). A real stateful branch therefore
exists and was measured:

| chunk | stateful err | stateless err | C2 ratio | C1 | verdict |
|---|---|---|---|---|---|
| 1 frame (79.7 ms) | 4.858e-01 | 5.727e-01 | **1.2** | fail | C1 and C2 both fail |
| 2 frame (159.4 ms) | 4.823e-01 | 5.602e-01 | **1.2** | fail | " |
| 5 frame (398.5 ms) | 4.294e-01 | 5.727e-01 | **1.3** | fail | " |
| 10 frame (797.0 ms) | 3.686e-01 | 5.602e-01 | **1.5** | fail | " |

**The label is unchanged. The evidence behind it is now real.** What the cache
carries is the decoder **transformer's** K/V, not the state that matters here:

> **The convolutional padding cache is the missing piece.**
> `MimiConv1d.forward(hidden_states, padding_cache=None)` exists in the same
> module, and `MimiModel.decode()` never threads it through. The API asymmetry is
> exact: `encode()` accepts `padding_cache` **and** `use_streaming`;
> `decode(audio_codes, padding_mask, decoder_past_key_values, return_dict)`
> accepts **neither**.

⛔ **THIS IS A PROPERTY OF THE IMPLEMENTATION PATH, NOT OF THE MIMI
ARCHITECTURE.** Kyutai ship PyTorch, Rust and MLX implementations with real
streaming, and Mimi's own config declares causal convolutions and a padding cache.
**Nothing here tests those.** What is established is narrower and must stay
narrow:

> **Mimi's decoder cannot be driven incrementally with carried state through
> `transformers` 4.57.3, because the decode API returns no state to carry.**

**Classification: `STATELESS_CHUNKING` (this path).** Not `FULL_CONTEXT_ONLY` —
that would be a claim about the architecture, and this experiment does not support
one. **Using Mimi for streaming would require Kyutai's own implementation, which
is a different integration and a different measurement.**

⚠️ **Consequence for the build decision, stated plainly:** the PRIMARY Mimi arm
is a strong representation — 100 codec targets/s at 1.10 kbps, 24 kHz — that we
**cannot currently stream through the library we are benchmarking**. That is an
integration cost, and it is exactly the kind of thing the Explorer should surface
rather than hide behind a latency number.

### `encodec24_q8` — STATELESS_CHUNKING via this implementation path

**Chunk grid from the implementation:** upsampling `[8,5,4,2]` → hop 320 → 75 Hz
→ one codec frame = **13.333 ms**. Conditions 6 / 12 / 30 / 60 frames.

| chunk | stateless err | % of own full-context peak |
|---|---|---|
| 6 fr (80 ms) | 3.254e-01 | 50.4% |
| 12 fr (160 ms) | 2.423e-01 | 37.5% |
| 30 fr (400 ms) | 2.921e-01 | 45.2% |
| 60 fr (800 ms) | 2.002e-01 | 31.0% |

**C2 not constructible, established before measurement:**
`decode(audio_codes, audio_scales, padding_mask, return_dict, last_frame_pad_length)`
carries **no state parameter of any kind**. Config also sets `chunk_length_s=None`
and `overlap=None` — this checkpoint defines no chunked operating mode (the 48 kHz
EnCodec does).

`use_causal_conv=True` is **architectural evidence only** and is not promoted to a
capability (R13).

### `fish_modified_dac` — STATELESS_CHUNKING via the benchmarked decode path

**Chunk grid from the implementation:** `frame_length = hop 512 × 4 = 2048`
samples at 44 100 Hz → one codec frame = **46.44 ms**, matching the measured
21.564 Hz. Conditions 1 / 2 / 4 / 8 / 16 tokens.

| chunk | stateless err | % of own full-context peak |
|---|---|---|
| 1 tok (46.4 ms) | 1.060e+00 | **151.9%** |
| 2 tok (92.9 ms) | 1.060e+00 | 151.9% |
| 4 tok (185.8 ms) | 9.111e-01 | 130.6% |
| 8 tok (371.5 ms) | 9.111e-01 | 130.6% |
| 16 tok (743.0 ms) | 7.873e-01 | **112.8%** |

**What this measures, stated exactly:** the **maximum sample-wise deviation** from
this arm's own full-context reconstruction is **112.8–151.9% of that
reconstruction's peak amplitude**, demonstrating **severe departure from
full-context reconstruction under stateless chunking.**

⛔ **It does NOT establish that the output is "a different waveform."** A maximum
deviation exceeding the reference peak is a statement about the largest
single-sample difference, not about global waveform identity. No output may
upgrade it into one.

**C2 not constructible, established before measurement:**
`decode(indices, feature_lengths)` takes no state. KV-cache machinery exists in
the module tree (`KVCache`, `setup_caches`, `clear_cache`, `use_kv_cache` default
`False`) and is **not threaded through `decode()`**.

> ⚠️ **Corrected 2026-09-11.** An earlier sentence here said that machinery *"is
> used by the windowed transformer in the decoder's first block."* **That
> overstated what was checked.** `setup_caches()` is never called on this path
> and **0 `KVCache` modules are instantiated** — counted by walking
> `model.named_modules()`. The conclusion was right; the description asserted a
> live cache that does not exist.

### Cross-arm comparison — WITHDRAWN

⛔ **The permission granted here on 2026-09-11 is WITHDRAWN the same day.** It
read: *"Fish vs EnCodec is permitted… On that metric Fish departs far more
(112.8–151.9%) than EnCodec (31.0–50.4%)."*

An attack suite on `encodec24_q8` measured **34.07% for a ONE-SAMPLE SHIFT** —
inside the band this metric reported for genuine chunking damage — and **exactly
100.00% for an all-zero output**, which is a better score than a four-sample
shift (110.68%).

> **`max|full − chunked| / max|full|` is a DETECTOR of departure from
> full-context decoding, not a severity scale. It supports "chunked decoding
> departs from full context" and NOT "arm X departs more than arm Y". Every
> cross-arm severity ranking built on it is withdrawn.** (`PROTOCOL.md`
> amendment 6.)

**Classifications: see `GATE2_MATRIX.md`**, which is machine-generated from the
run artifacts by `make_matrix.py` and is the authoritative matrix. Every label in
this section was recomputed there by a classifier that applies **both** C1 and
C2; the earlier batch applied C1 alone.

---

## 7b. ⭐ THE REST OF GATE 2 — added 2026-09-11 by the audit repair

`GATE2_AUDIT.md` §C8 found that **seven of nineteen arms had no persisted
artifact** — they existed only as prose transcribed from console output that no
longer exists — and that **two DualCodec arms had no recorded classification
anywhere.** Every arm has now been run through one harness that writes one
artifact row per arm.

**The authoritative matrix is `GATE2_MATRIX.md`**, generated by `make_matrix.py`
from `gate2_repaired_a.json` · `_b.json` · `_fish.json` · `_melflow.json`.
Nothing in it is transcribed from prose. It is not duplicated here, because two
copies of a number is one copy too many.

**What changed in the instrument, all of it in shared code (`gate_lib.py`) so a
fix cannot reach one arm and miss another:**

1. **C2 is now a conjunct of the label.** `close_gate2.py:134` read
   `if codec.causal and raws and max(raws) <= C1` — **C2 appeared only inside a
   print statement**, so both `TRUE_INCREMENTAL` labels in that batch were
   awarded on C1 alone, contradicting the file's own docstring. Recomputed with
   C2 applied, **all three causal FocalCodec arms still pass, C2 ratio
   3 530×–36 740×** against a threshold of 10.
2. **Gate Zero is computed, never asserted.** The four `"PASS (this run)"` string
   literals are gone; every arm now runs the full §8 gate including dtype and
   channel count.
3. **The `raw` column no longer means two things.** It previously held the
   stateful error on causal rows and the stateless error everywhere else.
   Stateful, stateless and the C2 ratio are now separate named fields.
4. **`rel: "0.0-0.0%"` is gone.** A `.1f` format was rounding 0.0072% and 0.0358%
   to zero on the two rows where the signal mattered most.
5. **Length drift is recorded.** Per-chunk output length is exactly linear in
   chunk size for every measured arm (`L(u) = a·u + b`, maximum residual `0.0`),
   so `b` is the constant offset each chunk carries. **`vocos_mel24` and
   `griffinlim`: `b = −256` samples**, ≈47 000 samples (~2.0 s) accumulated at
   the 8-frame condition. **DualCodec, both configurations: `b = −4`.** Every
   other arm: `b = 0`. `n = min(lengths)` had been hiding it.

**Two arms were withdrawn and re-measured rather than re-labelled:**

- **`griffinlim`** — unseeded random phase initialisation; self-vs-self error
  `7.7404e-01` (131.3%) with **no chunking at all**, larger than its published
  chunking band. Re-run with `rand_init=False`, self-vs-self `0.000e+00`.
  `PROTOCOL.md` amendment 4.
- **`melflow`** — non-deterministic, fed the wrong representation, gain-normalised
  per chunk, and **its streaming API was never reached**. Re-measured through the
  actual `init_state()` + `forward_step(…, state)` contract, against a declared
  claim boundary, and against **two declared upstream defects that stop the
  shipped streaming path executing at all**. `PROTOCOL.md` amendment 7.
  ⭐ **Its label changed: `STATELESS_CHUNKING` → `TRUE_INCREMENTAL — NEURAL
  DECODER; iSTFT STREAMING NOT ESTABLISHED`.** Over all 992 frames of the probe,
  stateful error **`3.036e-06`** at **16 ms / one-frame granularity**, C2
  **`2.20e+05×`–`3.55e+05×`**, determinism probe `0.000e+00`.

### ⚠️ MelFlow ran on a LOCALLY REPAIRED implementation — disclosed, not buried

**The streaming path of `sp-uhh/streamfm` at revision `ab2700c1` DOES NOT EXECUTE
AS RELEASED.** Two structural repairs were required before `forward_step` would
run at all, and both are declared on the artifact, in `GATE2_MATRIX.md` and in
`PROTOCOL.md` amendment 7:

1. `CausalConv2d.forward_step` reads `self.depthwise_separable` and
   `self.pointwise_conv`; `CausalConv2d.__init__` defines **neither**. Every call
   raises `AttributeError` on an uncompressed model.
2. `CausalResnetBlockBigGANpp.init_state` returns a 5-tuple while its own
   `forward_step` unpacks 6 (`state_se`). The block raises `ValueError` on the
   first call.

**An independent delta audit verified both patches are INERT** — neither
attribute exists anywhere in the class, the non-streaming `forward()` path has no
pointwise branch (so `False` is the only value that makes `forward_step` agree
with `forward`), `state_se` occurs at exactly two lines and is never read or
written, and **no weight and no arithmetic operation is touched by either.**

⛔ **This is a released-tooling finding, in the same class as the NanoCodec/NeMo
blocker. It is NOT a finding about the MelFlow architecture**, which streams
correctly once the two dead references are satisfied.

### ⭐ What the corrected matrix says, and what it does not

**Three arms earn `TRUE_INCREMENTAL (representation → PCM)`** — the three causal
FocalCodec configurations, which emit PCM from partial input as `PROTOCOL.md`
§10.1 requires. **One arm, `melflow`, earns `TRUE_INCREMENTAL — NEURAL DECODER;
iSTFT STREAMING NOT ESTABLISHED`, and is NEVER counted with them.**

⛔ **Why MelFlow's label is qualified.** §10.1 is frozen and requires an
empirical chunk test *"showing the decoder emits correct audio from partial input
while retaining state"*; §2 and §10.3 stop the claim boundary at a playable PCM
block. MelFlow's repaired test emits **spectrogram frames** incrementally, and
the inverse STFT is run **once over the assembled spectrogram**. That stage is
not free: a control from the independent delta audit — naive split-in-two iSTFT
then concatenate — measured **raw `1.036108e+00` / `134.65%`, 256 samples short**.
So streaming it does not follow from the neural decoder streaming, and R13
forbids upgrading it by inspection. **Earning the unqualified label requires
writing AND testing a streaming overlap-add stage.**

⛔ **The two routes are not merged into one ranking, and nothing here ranks these
arms against each other.** Gate 2 classifies streaming behaviour. It measures no
latency, no throughput and no reconstruction quality — **Gate 3 has not started
and no GPU has been used for any measurement in this study.**

⛔ **`TRUE_INCREMENTAL` is not a recommendation.** `melflow` carries a permanent
AGPL-3.0 label, a qualified scope and a locally repaired dependency;
`focalcodec` is 16 kHz in and 24 kHz out with a single binary codebook. Those are
facts about the arms, not a verdict about either.

⚠️ **`focalcodec_50hz_65k_causal` was an undeclared post-freeze arm** and is now
declared as one (`PROTOCOL.md` amendment 3). Its numbers reproduced exactly under
an independent adversarial re-run, so it is declared rather than deleted — but
where one causal FocalCodec configuration must be named, that is
**`focalcodec_50hz_4k_causal`**, the arm frozen in `PROTOCOL.md` §3 before any
result existed. That arm was absent from the batch in question and has now been
run through the identical harness.

---

## 6. What freeze means

On approval: `PROTOCOL.md` is frozen, this manifest becomes the arm list, and
amendments append below the amendment line with a date and a statement of whether
any result had been seen.

**Then, and only then, the GPU runs.**
