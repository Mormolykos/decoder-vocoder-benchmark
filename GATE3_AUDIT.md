# ⏩ RESUME HERE AFTER COMPACTION — GATE 3 AUDIT + REPAIR QUEUE

**Independent Gate 3 audit received 2026-09-11. Recorded here verbatim in
substance so it survives any context loss.**

**STATUS: GATE 4 NOT STARTED. No reconstruction quality, no listening, no
detectorproof. Repairs in progress.**

**Owner instruction:**

- **Do NOT rerun the full benchmark.** The timing measurements survived audit.
- **Do NOT start Gate 4.**
- Apply only the required Gate 3 repairs.
- **Only ONE new benchmark measurement is authorised: the §7.2 E6 environment
  control** — `encodec24_q8` at a fixed duration in the `fish` environment.

**Report at the end, ONLY:** E6 result and comparability consequence · repairs
applied · E1 paired result · E3/E4 results · disposition of the VRAM re-run rule
· corrected machine-generated Gate 3 matrix · remaining BLOCKING/MAJOR findings ·
`GATE 3 PERFORMANCE RESULTS CLEARED: YES/NO`.

---

## WHAT IS ALREADY ON DISK (nothing pending, no process running)

`GATE3_MATRIX.md` · `gate3_matrix.json` · `results/raw_runs.csv` (118 025 rows) ·
`results/summary.csv` (312 cells) · `results/gate3_raw_{a,b,fish,melflow}.jsonl`
· `results/gate3_cells_*.jsonl` · `results/gate3_header_*.json` ·
`results/gate3_log_*.txt`

Harness: `gate3_lib.py` · `gate3_arms.py` · `gate3_arms_b.py` ·
`gate3_arms_fish.py` · `gate3_run.py` · `gate3_run_melflow.py` ·
`make_gate3_matrix.py` · `check_gate3.py` · `export_gate3_csv.py`

Gate 2 (CLOSED, spot-checked, do not reopen): `GATE2_MATRIX.md` ·
`gate2_matrix.json` · `gate2_repaired_*.json` · `GATE2_AUDIT.md`

⚠️ **`decoder-bench` is NOT a git repository.** Two days of work, one disk, no
history.

---

## A. VERIFIED BY THE AUDIT — the apparatus is sound

The auditor recomputed every headline number from `results/raw_runs.csv` and
every one reproduced exactly. **No re-run of the 20 arms is required for
anything found.**

- `torch.cuda.synchronize()` before the start clock and before the stop clock,
  inside `Timer.__call__` and nowhere else, asserted structurally.
- **0 of 118 025 raw rows inadmissible. 0 rows missing `cuda_ms`** — no arm
  silently fell to CPU.
- N=30 warm + 3 cold, 5 warm-ups discarded, all 19 arms; `n_judged` matches the
  raw row count exactly.
- Block randomisation applied under the stored seed; four runners strictly
  sequential (amendment 9.11).
- The three causal Focal arms reproduce to the digit, VRAM included.
- E1 pair is genuinely controlled: token sha256 `7560f0cf7414e454…` identical
  across two separate processes, 2250 units each, same anchor, both §8 PASS.
- MelFlow per-frame p50 74.8948 ms over 7590 frames; TTFA `NOT ESTABLISHED` at
  all 7 conditions; eager mode declared as an UPPER BOUND.
- **Qwen's 208 ms event is genuine, isolated and device-side**: rep 24, index 15,
  `cuda_ms` 208.076 vs wall 208.105 — host overhead 0.03 ms. Second largest
  19.365 ms. Exactly 1/750 = the reported 0.0013.
- Griffin-Lim's 21.3 ms failure is structural: n_fft 1024 reflect-pads 512/side
  and cannot accept a 256-sample input.
- Guardrails hold: routes never merged, seam metrics self-referential, vendor
  anchors labelled, NanoCodec BLOCKED with no manufactured number, no
  "fastest/winner/best" language anywhere.

---

## B. BLOCKING

### B1. The §7.2 environment control (E6) was never run, yet the table contains cross-environment rows

Batches A and B ran in `decbench`; `fish_modified_dac` in `fish`
(transformers 4.35.2); `melflow` in `decbench_melflow` (5.17.0). §7.2 is frozen
and pre-commits that `encodec24_q8` at a fixed duration is run in **both**
environments, and that **if the environment effect is comparable in size to the
between-decoder differences, every cross-environment comparison is reported as
`NOT COMPARABLE`.**

`E6` appears **zero times** in `GATE3_MATRIX.md`. **The incumbent — the arm a new
choice must beat — sits in the headline and budget tables beside 17 arms measured
under a different package set**, with neither the control nor the label. No
amendment declares the omission.

### B2. Three arms fail the §8 streamed validity gate and the matrix never says so

`streamed_gate8` occurs **zero times** in `GATE3_MATRIX.md`.

| arm | streamed §8 | failing predicate | headline reads |
|---|---|---|---|
| `vocos_mel24` | **FAIL 7/7** | `duration_ok` | TTFA 1.37 ms · RT 64.0× · PASS |
| `griffinlim` | **FAIL 6/6** | `duration_ok` | TTFA 11.27 ms · RT 7.7× · PASS |
| `focalcodec_12_5hz` | **FAIL 3/5, anchor FAIL** | `energy_ok` | TTFA 2.99 ms · RT 27.3× · PASS |

**Diagnosed:** the two `duration_ok` failures ARE the Gate 2 length drift —
`b = −256 samples per chunk` — surfacing in Gate 3. `focalcodec_12_5hz` fails
`energy_ok` at 0.1033 / 0.1025 / 0.2224 against the 0.25 floor and passes only at
640.8 ms (0.5100). `focalcodec_25hz` also fails one condition (4/5 pass).

`vocos_mel24` reads as the fastest arm in the study while its streamed output is
inadmissible under the study's own frozen gate at every chunk size tested.
**§5's E3 is defined by that gate, so for these arms E3 is `NOT ACHIEVABLE`** and
is instead reported as a millisecond figure.

---

## C. MAJOR

**M1. E1 — the study's only controlled estimand — is not in the deliverable.**
`E1` occurs 0 times in `GATE3_MATRIX.md` and 0 times in `gate3_matrix.json`. §5
requires *"the paired difference and the ratio… per duration condition, with a
paired interval"*. What exists is one anchor condition, unpaired, no interval.

**M2. The 2.16× VRAM ratio mixes scopes.** `peak_alloc_MiB` is the max across all
13 cells, not the streaming anchor:

```
whole-session peak_alloc : 511.20 / 236.17 = 2.16x
anchor peak_alloc        : 188.14 / 145.65 = 1.29x
anchor peak_reserved     : 826.00 / 646.00 = 1.28x
```

Quoting 2.16× beside an 80 ms TTFA ratio implies a streaming memory cost the
anchor data does not show. R18 also asks for candidate denominators side by side.

**M3. One headline row mixes two populations.** `steady p50` excludes the first
chunk; `p95`, `p99`, `IQR`, `max` in the same row include it. Material:
`focalcodec_25hz` max 3.817 (all) vs 3.288 (steady); `focalcodec_12_5hz` 3.986 vs
3.514. The first chunk is already reported separately as TTFA, so it is counted
twice. No column legend states which population each statistic uses.

**M4. "PASS" is never defined.** `make_gate3_matrix.py:293-298` sets it purely on
completeness (`has_offline and has_stream`). Correct semantics, but no sentence
says so, and it sits one column from underrun and RT margin. `melflow` carries
underrun 1.0000 and RT 0.2× and reads PASS; `griffinlim` fails §8 at every
condition and reads PASS.

**M5. §7.2's VRAM re-run rule was neither applied nor amended.** *"An arm whose
before/after VRAM reading moves by more than 200 MiB is re-run and both runs are
kept."* **162 of 312 cells exceed it** (up to +5270 MiB on `dualcodec_12hz_v1`).
No re-runs exist. The rule is probably unsuited to a block-randomised design that
unloads and reloads models — but it is frozen, and amendment 9 does not address
it.

**M6. E3 and E4 are not produced.** `min_viable_chunk_ms` is `min(effective_ms)`
over non-composed conditions — the minimum chunk that RAN. The Markdown says so
honestly; the JSON field name asserts viability, and frozen E3 requires the §8
gate. **E4 (offline vs streaming ordering) appears nowhere.**

---

## D. MINOR

- Focal delay calibration is noise recorded as fact: normalised peak correlations 0.08–0.19, and three architecturally near-identical causal configs return −19.33, +14.96 and +27.79 ms. Not referenced by `make_gate3_matrix.py`, so no reported claim rests on it — but it is in the artifacts at full precision with no weak-correlation flag.
- Invalid E2 fits print as ordinary numbers in the headline (`dac44` −1.33, `melflow` −39.46, `bigvgan22` −44.10 ms); `e2_fit_valid: false` is disclosed ~460 lines later.
- MelFlow's failed TTFA cell carries no state: `{'cell': 'ttfa', 'error': 'None'}`. §12 requires a failure row to carry its state.
- **BigVGAN transition points are 23.2 / 46.4 / 81.3 ms, not 93 ms.** BigVGAN has no 93 ms condition; 93.3 ms is the EnCodec-pair anchor.
- Qwen's 208 ms spike must keep the caveat that device timing cannot distinguish model work from GPU preemption; §7.4 is declared but not instrumented per cell.
- The 75 ms budget table must exclude or clearly mark arms failing streamed §8.

---

## E. REPAIR QUEUE — owner-directed, in order

1. ☐ **Run the missing E6 environment control.** `encodec24_q8` at a fixed duration in `fish`, same condition as `decbench`. Apply the frozen rule: if the environment effect is comparable to between-decoder differences → mark affected cross-environment comparisons `NOT COMPARABLE`; otherwise record the control and justify comparability. **Until E6 is complete, do not compare `fish_modified_dac` or `melflow` numerically against decbench arms.**
2. ☐ **Repair streamed-validity reporting.** No re-measurement. Expose `streamed_gate8` in the matrix. Split E3: `min_chunk_that_ran_ms` (execution feasibility) vs **minimum viable streaming configuration (requires §8 PASS)**; `NOT ACHIEVABLE` where no tested condition satisfies §8.
3. ☐ **Repair status terminology.** `PASS` → `MEASURED — CELLS COMPLETED AND ADMISSIBLE`, with an explicit sentence that it is not a performance verdict and implies neither real-time capability nor valid streamed reconstruction.
4. ☐ **Fix the statistics population.** Recompute p50/p95/p99/IQR/max over steady-state chunks excluding the first (preferred, since TTFA already reports the first chunk), or label every statistic `all chunks` vs `steady-state`. **Regenerate from raw data only.**
5. ☐ **Produce E1 properly** from existing paired data: paired difference, ratio, per duration condition, paired interval (§5). Separate VRAM scopes (whole-session 2.16× · anchor allocated 1.29× · anchor reserved 1.28×).
6. ☐ **Resolve the §7.2 VRAM re-run rule.** Either execute the re-runs the frozen rule requires, or — if the rule is demonstrably incompatible with the block-randomised unload/reload design — record a **dated protocol amendment** explaining why and what replacement validity check is used. **Do not alter measured values.**
7. ☐ **Produce E4** (offline vs streaming ordering) from existing measurements.
8. ☐ **Clean remaining reporting defects** (all of §D above).
9. ☐ **Regenerate all Gate 3 deliverables from artifacts/raw data. No manual transcription.** Then run consistency checks.

**GATE 3 PERFORMANCE RESULTS CLEARED: NO.** Blocked on B1 (one cell) and B2 (a
disclosure column, not a re-measurement). The MAJOR items are reporting and
estimand-coverage repairs, except M1, which needs a paired analysis computed from
data that already exists.

---

## F. PROGRESS

**ALL NINE ITEMS APPLIED, 2026-09-11. `check_gate3.py`: 0 failures.**

| # | item | status |
|---|---|---|
| 1 | E6 environment control | ☑ **MEASURED in all three environments.** The frozen §7.2 rule FIRES — see §G. `fish` **NOT COMPARABLE** (50.2%); `decbench_melflow` comparable (0.5%), now by measurement. |
| 2 | streamed-validity reporting | ☑ `streamed_gate8` on the headline and per condition. E3 split into `min_chunk_that_ran_ms` (execution feasibility) and the frozen **minimum viable streaming configuration** requiring a §8 PASS. |
| 3 | status terminology | ☑ `PASS` → **`MEASURED — CELLS COMPLETED AND ADMISSIBLE`**, with an explicit definition stating it is not a performance verdict and implies neither real-time capability nor valid streamed reconstruction. |
| 4 | statistics population | ☑ p50/p95/p99/IQR/max **all recomputed from raw over the steady-state population**, excluding the first chunk of every repetition. All-chunks kept beside it, labelled. Never mixed in a row. |
| 5 | E1 produced properly | ☑ 12 conditions, paired difference + ratio + bootstrap 95% interval each, memory scopes separated. |
| 6 | §7.2 VRAM re-run rule | ☑ **SUPERSEDED by PROTOCOL amendment 10.2**, with a named replacement check. 167/366 flagged cells reported, not hidden. No measured value altered. |
| 7 | E4 produced | ☑ COMPUTED over 17 qualifying arms, subset and exclusions named. |
| 8 | remaining reporting defects | ☑ E2 invalid fits marked inline; weak delay correlations flagged and declared unused; MelFlow's TTFA cell carries its state; BigVGAN transition points read from data; Qwen preemption caveat added as a claim boundary; budget table excludes §8 failures and NOT COMPARABLE arms. |
| 9 | regenerate + checks | ☑ `gate3_matrix.json`, `GATE3_MATRIX.md`, `results/raw_runs.csv`, `results/summary.csv` all regenerated from artifacts. Rendering split into `render_gate3_md.py` so the document cannot disagree with the JSON. |

### ☑ FINAL SPOT-CHECK REPAIR — E1 interval only, 2026-09-11

**The independent spot-check returned FAIL on one defect: the E1 bootstrap
estimated a MEAN while every reported point estimate was a MEDIAN.** On
right-skewed latency data the mean sits above the median, so the point fell
outside its own interval in 5 of 7 streaming rows and in the 30 s offline ratio.
Two smaller defects in the same function: the resample was capped at
`min(n, 2000)`, and the two arms were resampled INDEPENDENTLY, discarding the
pairing.

**Fixed:** a **paired median bootstrap**. Observations are keyed by
`(rep, chunk_index)` for streaming and `(seconds, rep)` for offline; it is the
**pair index** that is resampled, so each draw takes the same occasion from both
arms. The statistic resampled is the **median** — the one the point estimate
reports. 4000 resamples, seed 20260911, **every resample exactly n pairs, no
cap**. Point estimates unchanged; only the intervals moved.

**All 12 conditions now contain their own point estimate.** Measured-value
differences against a pre-fix snapshot of every timing, §8, E6, E4 and exclusion
field: **0**.

**VRAM field naming also corrected** — six explicitly scoped keys replace the
ambiguous `whole_session_*`: anchor allocated **1.2917×** · offline-sweep
allocated **2.1646×** · session allocated **2.1646×** · anchor reserved
**5.2152×** · offline-sweep reserved **1.2786×** · session reserved **1.2817×**.
The 5.2× anchor-reserved figure is allocator caching, not memory demand, and is
flagged as such.

**One defect found in my own repair and fixed before reporting:** the first pass
lumped `melflow` in with `vocos_mel24` and `griffinlim` as "§8 fails at every
chunk size tested" and printed *"0/0 conditions pass"*. MelFlow has **zero
non-composed conditions** — its decode granularity is one frame, so §8 was never
evaluated on a chunked decode for it. **`NOT ACHIEVABLE` (tested, all failed) and
`NOT ESTABLISHED` (never tested) are different claims** and are now separate
labels.

---

## G. ⭐ E6 — THE §7.2 ENVIRONMENT CONTROL, MEASURED 2026-09-11

**`encodec24_q8`, byte-identical tokens, same RTX 5080, run as a SINGLE ARM in
all three environments that produced arm rows.** Run single-arm on every side on
purpose: the decbench arm rows were block-randomised among 14 other arms, so
comparing an interleaved run against a solo run would confound the environment
effect with run context.

Artifacts: `results/gate3_cells_e6_{decbench,fish,decbench_melflow}.jsonl` ·
`results/gate3_raw_e6_*.jsonl` · `results/gate3_header_e6_*.json`. 18 cells each,
0 failures.

| condition | decbench ms | fish ms | melflow-env ms | fish/db | mf/db |
|---|---|---|---|---|---|
| offline 1 s | 8.171 | 4.372 | 7.530 | **0.535** | 0.922 |
| offline 2 s | 10.367 | 6.353 | 9.953 | **0.613** | 0.960 |
| offline 5 s | 15.373 | 12.175 | 15.819 | 0.792 | 1.029 |
| offline 10 s | 26.964 | 23.486 | 27.968 | 0.871 | 1.037 |
| offline 30 s | 74.726 | 71.875 | 76.372 | 0.962 | 1.022 |
| stream 26.7 ms | 5.570 | 1.978 | 5.523 | **0.355** | 0.992 |
| stream 53.3 ms | 5.457 | 2.018 | 5.781 | **0.370** | 1.059 |
| stream 93.3 ms | 5.976 | 2.067 | 5.540 | **0.346** | 0.927 |
| stream 173.3 ms | 5.705 | 2.272 | 5.869 | **0.398** | 1.029 |
| stream 333.3 ms | 6.587 | 2.596 | 6.108 | **0.394** | 0.927 |
| stream 653.3 ms | 7.089 | 3.262 | 6.722 | **0.460** | 0.948 |
| stream 1013.3 ms | 7.326 | 4.247 | 7.466 | **0.580** | 1.019 |

```
fish            vs decbench : median ratio 0.498  -> ENVIRONMENT EFFECT 50.2%   (range 0.346-0.962)
decbench_melflow vs decbench: median ratio 1.005  -> ENVIRONMENT EFFECT  0.5%   (range 0.922-1.059)
```

**The effect is a near-constant ~3.0–4.0 ms offset**, and it is **DEVICE-SIDE, not
host-side**: at the 2 s offline condition, host overhead is 0.022 ms in decbench
and 0.024 ms in fish, while CUDA time is **10.344 ms vs 6.328 ms**. The two
`transformers` versions launch **different GPU work for the same decode**. This
is not dispatch overhead and not measurement noise.

torch is identical everywhere (2.10.0+cu128). The moving variable is
`transformers`: **4.57.3** (decbench) · **4.35.2** (fish) · **5.17.0**
(decbench_melflow).

### The frozen rule and what it decides

> §7.2: *"If it is comparable in size to the between-decoder differences, every
> cross-environment comparison in this study is reported as NOT COMPARABLE."*

Between-decoder differences at the anchor span roughly **1.9 ms to 27.6 ms**, and
most arms sit between 1.9 and 16 ms. A **3.0–4.0 ms** environment offset is
larger than the gap between many pairs of arms — `encodec_vocos` (1.90 ms) and
`focalcodec_50hz_4k_causal` (3.07 ms) differ by 1.17 ms, roughly a third of it.

| environment | effect | consequence |
|---|---|---|
| `fish` (transformers 4.35.2) | **50.2%** | ⛔ **NOT COMPARABLE.** `fish_modified_dac` — the incumbent — may not be compared numerically against any decbench arm. Its own numbers stand within its own environment. |
| `decbench_melflow` (5.17.0) | **0.5%** | ✅ **COMPARABLE**, and now justified by measurement rather than assumed. `melflow` may sit in the same table as the decbench arms. |

⚠️ **The direction matters and must not be mis-stated.** `fish` is FASTER. The
incumbent's environment flatters it by roughly 3.5 ms per call relative to the
environment 17 other arms were measured in. **Nothing here says Fish ModifiedDAC
is fast or slow; it says its number and theirs cannot be put in one ranking.**

**Streamed §8 survey, computed 2026-09-11 (PASS/total, min §8-PASS condition):**

```
bigvgan22        7/7  23.2ms    dac44              7/7  23.2ms
dualcodec_12hz   5/5  80.1ms    dualcodec_25hz     6/6  40.1ms
encodec24_q8     7/7  26.7ms    encodec_vocos      7/7  26.7ms
fish_modified    6/6  46.4ms    focalcodec_50hz    5/5  80.1ms
focal_4k_causal  5/5  80.0ms    focal_2k_causal    5/5  80.0ms
focal_65k_causal 5/5  80.0ms    mimi_q8            6/6  79.7ms
mimi_q32         6/6  79.7ms    qwen3_12hz         5/5  80.0ms
focalcodec_25hz  4/5  80.1ms    focalcodec_12_5hz  2/5  640.8ms
griffinlim       0/6  NOT ACHIEVABLE
vocos_mel24      0/7  NOT ACHIEVABLE
```
