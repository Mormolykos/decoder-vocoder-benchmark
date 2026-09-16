# ⏩ RESUME HERE AFTER COMPACTION — THIS FILE IS THE AUTHORITATIVE CURRENT STATE

**Owner instruction, 2026-09-11:**

- Resume from this file. **Do NOT reconstruct history from memory.**
- **Do NOT redo candidate research.** The gate is closed.
- **Do NOT start Gate 3 / GPU timing.** Not automatically, not at the end.
- **Execute the repair queue in §F, top to bottom.**

**Objective — finish with all of:**

1. Griffin-Lim repaired or correctly withdrawn
2. MelFlow tested through its actual `forward_step(..., state)` streaming interface, or correctly withdrawn
3. Mimi evidence corrected (label stands, false statement deleted)
4. DualCodec re-run and persisted, drift recorded
5. `focal_50hz_65k_causal` formally amended or removed
6. Real frozen Gate Zero re-run for the four hardcoded-PASS arms
7. `ENVIRONMENT.json` created
8. All missing raw artifacts persisted
9. Corrected machine-generated Gate 2 matrix
10. Totals reconstructed **only from artifacts**

**Then report ONLY:** final corrected matrix · exact totals · remaining
BLOCKING/MAJOR findings · `GATE 3 READY: YES/NO`. **Then stop and wait.**

---

## ✅ EXECUTED 2026-09-11 — READ §F′ BELOW FOR THE OUTCOME

**All ten items are done. `GATE2_MATRIX.md` / `gate2_matrix.json` is the
authoritative matrix, machine-generated from run artifacts.**

⚠️ **§A–§E below are the audit AS RECEIVED and are left unedited**, so the
findings and the repairs can be read against each other. **§E's totals are the
audit's pre-repair reconstruction and are SUPERSEDED** — the post-repair totals
are in `GATE2_MATRIX.md` and in §F′.

**Project files:** `AUDIT.md` (inventory + Gate Zero) · `PROTOCOL.md` (FROZEN,
amendments append below the amendment line) · `MANIFEST.md` (arm list + results)
· `GATE.md` (candidate gate + licences) · `FIELD_SURVEY.md` · `gate2_results*.json`
· `gate_lib.py` + `gate_zero*.py` + `chunk_test*.py` + `close_gate2*.py`

**Environments:** `decbench` (torch 2.10.0+cu128, transformers 4.57.3 — FROZEN) ·
`decbench_melflow` (AGPL isolation) · `fish` (pre-existing, READ ONLY) ·
`decbench_nemo` (blocked). GPU: RTX 5080 sm_120, driver 610.47, CUDA 12.8.

---

# GATE 2 — INDEPENDENT ADVERSARIAL AUDIT + REPAIR QUEUE

**Audit received 2026-09-11 from an independent adversarial review. Treated as the
authoritative review of Gate 2. Findings recorded here verbatim in substance so
they survive any context loss.**

**STATUS: GATE 3 NOT STARTED. Repairs pending. No GPU timing has run.**

---

## A. WHAT IS SAFE — independently verified twice

**The three FocalCodec causal results survived an adversarial re-run in a separate
process, recomputed from raw representation to PCM.** Every published number
reproduced exactly, and the auditor's attack suite confirmed the state is real:

| attack | result |
|---|---|
| zeroed state | detected (rel 117.0–125.7%) |
| stale state | detected (rel 104.3–114.3%) |
| permuted chunks | detected (rel 49.1–122.5%) |
| perturbed token | detected (rel 81.7–118.7%) |
| dropped / duplicated token | detected (110.8% / 135.3%) |
| hidden full-context computation | ruled out |
| length drift | **0 samples/chunk at every condition** |
| C2 recomputed | **3 530× – 36 740×** vs threshold 10 |

**The TRUE_INCREMENTAL results are real** — not overlap artefacts, not hidden
full-context computation, and the carried state is load-bearing (21 tensors,
12 decompressor + 9 decoder).

**12 arms have persisted JSON artifacts and every deterministic number reproduced
exactly.** Nothing in the audit invalidates GPU timing for the 17 surviving arms.

---

## B. BLOCKING — measurements invalidated

### B1. `griffinlim` — WITHDRAWN
`torchaudio.transforms.GriffinLim` has `rand_init=True` and **no seed was set**.
Self-vs-self error (same spectrogram, decoded twice, no chunking at all):
**7.887e-01, rel 148.24%** — larger than the reported chunking error of
7.244e-01–7.637e-01 / 95.7–100.9%. The number measured random phase, not chunking.
**Do not reclassify until re-run with a fixed seed.**

### B2. `melflow` — WITHDRAWN, four independent counts
1. **Non-deterministic** — self-vs-self max|err| **1.0117e+00, rel 142.09%**, exceeding its published range. `enhance()` has a `seed` parameter; it was never passed.
2. **Wrong representation** — `enhance(x, src_sr)` was fed a raw 16 kHz waveform, not mel. Every chunk recomputed its own STFT.
3. **Per-chunk gain** — `normalize_mode='noisy'` divides each chunk by its own `abs().amax()`. Measured per-chunk input peaks 0.0024 → 0.2772, a **115× gain spread**. Divergence was guaranteed by the instrument.
4. **The streaming API was never reached** — the backbone is `CausalNCSNpp`, a `CausalStreamingModule` with `forward_step(x, time_cond, aux_condition, *, state) -> (out, state)`, and **133 submodules implement that interface**. Only `enhance()`'s signature was checked.

⚠️ **This is the same class of error as the off-grid Focal run: the instrument
ignoring the model's own streaming contract — on the one arm whose entire
published contribution is streaming.** Weights are fine (0 missing / 0 unexpected);
the experiment is not.

---

## C. MAJOR — labels may stand, evidence needs repair

**C1. C2 was never applied by the classifier.** `close_gate2.py:134` reads
`if codec.causal and raws and max(raws) <= C1` — C2 appears only in a print.
Both TRUE_INCREMENTAL labels there were awarded on **C1 alone**, contradicting the
file's own docstring. **Recomputed by the auditor: C2 passes everywhere,
3 530×–36 740×. Labels survive; the evidence chain did not exist.**

**C2. Mimi's documented reason is FALSE and its evidence was a bug.**
`MANIFEST.md` §7 states *"MimiDecoderOutput contains only audio_values. It never
returns past_key_values."* In transformers 4.57.3:
`MimiDecoderOutput.__dataclass_fields__ = ['audio_values', 'decoder_past_key_values']`.
`chunk_test_mimi.py:66` read `getattr(out, "past_key_values", None)` — **a field
that does not exist** — so it passed `None` every iteration and the "stateful"
branch was byte-identical to stateless (`torch.equal` True). That is why the ratio
was 1.000.
**With `use_cache=True`, decode returns a real `DynamicCache` accumulating to
seq_len 398, and stateful ≠ stateless. C1 still fails (4.858e-01), C2 still fails
(1.18–1.52). The label is correct; the reason must be rewritten** to: the
convolutional padding cache (`MimiConv1d.forward(hidden_states, padding_cache=None)`)
is not threaded through `MimiModel.decode()`.
`mimi_q32` never had a stateful branch at all; its `state` field is an untested
assertion, now shown false.

**C3. `focal_50hz_65k_causal` is an UNDECLARED ARM.** It appears only in
`close_gate2.py` and `gate2_results.json` — in no Gate Zero record, not in
MANIFEST §2a, not in AUDIT.md §6.1e, not in PROTOCOL.md §3, with no amendment.
It is one of three headline TRUE_INCREMENTAL results. **Conversely
`focalcodec_50hz_4k_causal` — the arm that IS frozen — was not run in that batch.**

**C4. Cumulative length drift on Route B.** `vocos_mel24` and `griffinlim` emit
**one hop (256 samples) less per chunk** than expected — at 8-frame chunks that is
185 × 256 ≈ 47 000 samples (~2 s) of accumulated misalignment. `n = min(lengths)`
hides the missing tail. DualCodec loses 4 samples/chunk. **Their reported error is
substantially drift, not boundary damage.**

**C5. ⛔ THE METRIC IS A DETECTOR, NOT A SEVERITY SCALE.** Shift attack on
`encodec24_q8`:

| condition | rel error |
|---|---|
| **1-sample shift** | **34.07%** — inside the reported 31.0–50.4% band |
| 4-sample shift | 110.68% |
| **all-zero output** | **100.00%** |
| wrong utterance entirely | 118.01% |

**A one-sample misalignment is indistinguishable from genuine chunking damage.**
`max|full−chunked| / max|full|` supports *"chunking departs from full context"*
and **NOT** *"arm X departs more than arm Y."* All such rankings are withdrawn,
including Fish-vs-EnCodec.

**C6. `gate_zero: "PASS (this run)"` is a HARDCODED STRING** in
`close_gate2.py:258/282` and `close_gate2b.py:53/92` — never computed. Those arms
received only `valid()` (finite + peak), which is weaker than the frozen §8 gate
(no duration, no energy ratio, no dtype, no channels). **Four arms carry a Gate
Zero PASS that was never executed:** vocos_mel24, griffinlim, bigvgan22,
encodec_vocos.

**C7. The `raw` column means two different things.** `raws[-1] = raw_sf`
overwrites stateless with stateful **only for causal arms**, so `raw` is the
stateful error on Focal rows and the stateless error everywhere else.

**C8. Seven of nineteen arms have no persisted artifact** — focal_50hz_4k_causal,
focal_50hz control, mimi_q8, encodec24_q8, fish_modified_dac exist only as prose
transcribed from lost console output; dualcodec ×2 have no recorded classification
anywhere. **`ENVIRONMENT.json`, required by PROTOCOL §7.1 and §14, does not exist.**

---

## D. MINOR

- `rel: "0.0-0.0%"` on both causal Focal rows — `.1f` rounds 0.0072% and 0.0358% to 0.0, destroying the signal.
- MANIFEST line 5 says 13 Gate Zero passes; its own tables list 14.
- MANIFEST §3 says "no arm carries a final streaming label"; §7 freezes four. §7 precedes §6.
- `grid_ms` is the full grid unit on Focal rows but one frame elsewhere, while conditions are 7× that.
- PROTOCOL §7.1 (frozen) names `fish` and `chatterbox`; work actually ran in `decbench` / `decbench_melflow` / `fish`. Unrecorded.
- MANIFEST §7 says Fish's KV-cache "is used by the windowed transformer"; `setup_caches()` is never called and **0 KVCache modules are instantiated** on this path. Conclusion right, description overstates.
- `.eval()` never called explicitly for Qwen or DualCodec (both measured deterministic; no defect realised).

---

## E. CORRECTED TOTALS — from artifacts, not prose

```
TRUE_INCREMENTAL      3   focal 4k / 2k / 65k causal  (verified; 65k undeclared)
STATELESS_CHUNKING   14   focal_50hz control, focal_25hz, focal_12_5hz, mimi_q8,
                          mimi_q32, encodec24_q8, dac44, qwen, vocos_mel24,
                          bigvgan22, encodec_vocos, fish, dualcodec x2
WITHDRAWN             2   griffinlim, melflow
BLOCKED               1   nanocodec
                     ---
TOTAL                20
```

**The previously reported "16 STATELESS_CHUNKING" reconstructs only by counting
the negative control plus both unrecorded DualCodec arms. Defensible recorded
count before the audit: 13. After: 14, with 2 withdrawn.**

Evidence inventory: **12 persisted artifact rows · 5 prose-only · 2 unrecorded ·
1 blocked.**

---

## F′. REPAIR EXECUTED — 2026-09-11

**The queue in §F below was executed top to bottom. Everything above this line is
the audit as received and is left unedited, so the findings and the repairs can
be read against each other.**

**The authoritative result is `GATE2_MATRIX.md` / `gate2_matrix.json`**, generated
by `make_matrix.py` from the run artifacts. Nothing in it is transcribed from
prose. Supporting artifacts: `gate2_repaired_a.json` · `_b.json` · `_fish.json` ·
`_melflow.json` · `ENVIRONMENT.json` · `fuzz_gate_lib.json`.

| # | item | status |
|---|---|---|
| 1 | `griffinlim` withdrawn, re-run seeded | **REPAIRED** — determinism probe recorded: `rand_init=True` self-vs-self **7.7404e-01 (131.3%)**, `rand_init=False` **0.000e+00**. Re-run deterministic. `PROTOCOL` amendment 4. |
| 2 | `melflow` through `forward_step(..., state)` | **REPAIRED, and the label CHANGES** — driven frame-synchronously through `init_state()` + `forward_step`, one state list per solver step, over all 992 frames of the probe. Determinism probe `0.000e+00`. **C1 passes: stateful error `3.036e-06`. C2 passes: `2.20e+05`–`3.55e+05`.** `STATELESS_CHUNKING` → **`TRUE_INCREMENTAL`**. Two upstream defects found that stop the shipped streaming path executing at all. Declared claim boundary and AGPL label unchanged. `PROTOCOL` amendment 7. |
| 3 | Mimi evidence corrected | **REPAIRED** — the `MimiDecoderOutput` statement was FALSE and is deleted. `decode()` has no `use_cache` argument; the cache is gated by `config.use_cache`, shipped `False`. With it enabled a live `DynamicCache` is returned and carrying it changes the output. Re-measured: **C1 fails (3.686e-01–4.858e-01), C2 fails (1.16–1.52)**. Label unchanged, evidence now real. |
| 4 | DualCodec re-run and persisted | **REPAIRED** — both configurations classified and persisted; **`b = −4` samples per chunk** recorded exactly. |
| 5 | `focalcodec_50hz_65k_causal` | **DECLARED** — `PROTOCOL` amendment 3, as a post-freeze arm, not deleted. `focalcodec_50hz_4k_causal` (the frozen arm, absent from that batch) run through the identical harness. |
| 6 | three causal Focal results preserved | **PRESERVED** — re-run only to persist artifacts, and every number reproduced: stateful `1.913e-05`–`1.571e-04`, **C2 `3 530×`–`36 740×`**, matching the auditor's independent re-run digit for digit. Drift **0 samples/chunk** at every condition. |
| 7 | Route-B reporting corrected | **REPAIRED** — length drift measured exactly (`L(u) = a·u + b`, residual `0.0`): `vocos_mel24` and `griffinlim` **`b = −256`**, ≈47 000 samples (~2.0 s) at the 8-frame condition. Severity rankings withdrawn (`PROTOCOL` amendment 6). |
| 8 | real Gate Zero for the four hardcoded arms | **REPAIRED** — `"PASS (this run)"` string literals removed; the full §8 gate including dtype and channel count is now computed for **all 19 runnable arms**, by one shared function. |
| 9 | persist everything | **DONE** — `ENVIRONMENT.json` created (4 environments, full package sets, GPU, driver); one artifact row per arm; corrected machine-generated matrix; `PROTOCOL` amendments 3–7. |
| 10 | totals from artifacts | **DONE** — `make_matrix.py` counts the rows it read. No total is typed by hand. |

**The instrument was fuzzed before it was trusted** (`fuzz_gate_lib.py`, 38
attacks, results in `fuzz_gate_lib.json`). It found **one latent defect** — Python
banker's rounding in `native_grid`, where `round(0.5) == 0` could collapse two
chunk conditions into one. Fixed. **No arm's grid was affected**, verified
condition by condition against the exact frame period each run used. ⛔ The
instrument survived these attacks; it is not closed, and its author is not its
certifier (R19).

---

## F. REPAIR QUEUE — owner-directed, in order

1. ☐ WITHDRAW `griffinlim`; do not reclassify until re-run with fixed seed under the frozen protocol.
2. ☐ WITHDRAW `melflow`; reconstruct from its real streaming contract (`forward_step(..., state)`, mel input, seeded, gain handled) before any new classification.
3. ☐ Correct Mimi: keep `STATELESS_CHUNKING` (C1/C2 independently confirmed failing), **delete the false `MimiDecoderOutput` statement**, record the real `decoder_past_key_values` behaviour and the padding-cache limitation.
4. ☐ Re-run and PERSIST DualCodec 12 Hz and 25 Hz; record the −4 samples/chunk drift explicitly.
5. ☐ `focal_50hz_65k_causal`: dated protocol amendment declaring post-freeze introduction, or remove from the primary frozen matrix. Preserve that its numbers independently reproduced.
6. ☐ Preserve the three causal Focal results; persist missing raw artifacts only. **Do not re-run to obtain a different answer.**
7. ☐ Correct Route-B reporting: record cumulative length drift; stop using rel error as a severity ranking.
8. ☐ Re-run the **real frozen Gate Zero** for the four arms with hardcoded PASS.
9. ☐ Persist: `ENVIRONMENT.json`, raw artifacts for all prose-only arms, DualCodec classifications, corrected machine-generated matrix, protocol amendments.
10. ☐ Recompute Gate 2 totals **from artifacts, not prose**.

**GATE 3 READY: NO.** Blocked on items 1, 2, 5, 8, 9.

---

## F″. INDEPENDENT DELTA AUDIT — received and applied, 2026-09-11

**A second, independent adversarial audit reviewed the repaired state. It
reproduced every repaired measurement and required NO re-measurement anywhere.**
It reproduced MelFlow's stateful error to the digit (`3.036112e-06`), confirmed
determinism `0.000e+00` in both directions, showed the carried state is real and
load-bearing under four further attacks (zeroed state, stale state,
reset-every-5, reset-every-25, plus permuted frames at ~1800× baseline), verified
**both MelFlow patches are genuinely inert**, reproduced Griffin-Lim to 7
significant figures, reproduced Mimi's C1/C2 exactly, and recomputed all totals
and all 19 classifications from the raw artifacts without importing our code —
agreeing exactly.

**It raised one BLOCKING defect and three schema defects. All are now fixed by
EDIT. No model measurement was re-run.**

| # | finding | severity | fix |
|---|---|---|---|
| A1 | `melflow` carried an **unqualified** `TRUE_INCREMENTAL`, presented identically to the three FocalCodec arms, when the frozen §10.1 criterion requires the decoder to emit **audio from partial input** — MelFlow emits spectrogram frames and inverts once over the assembled spectrogram | **BLOCKING** | Every arm now records the §10.1 predicate as `emits_pcm_from_partial_input`. Label → **`TRUE_INCREMENTAL — NEURAL DECODER; iSTFT STREAMING NOT ESTABLISHED`**; totals split by scope and never summed. `PROTOCOL` amendment 8. |
| B1 | the generated matrix never disclosed that MelFlow ran on a **locally repaired** implementation whose released streaming path does not execute at all | MAJOR | `GATE2_MATRIX.md`, `gate2_matrix.json` and `MANIFEST.md` now carry both patches, the "does not execute as released" statement, and the audit's inertness verification. |
| B2 | two contradictory drift numbers per arm — the per-condition column derived samples-per-unit from the **measured token rate**, so `mimi_q8` read `+7.24…+72.37` where the true hop is exactly 1920 and the real drift is **0** | MAJOR | `correct_artifacts.py` recomputed every derived drift field on the **true integer hop** recovered exactly from `L(u) = a·u + b`. Superseded values kept beside them. A standing cross-check now fails the matrix if artifact and fit ever diverge. |
| B3 | MelFlow's rows asserted four stateful chunk sizes; the stateful pass is **one continuous 16 ms stream** merely sliced, and the identical `3.036e-06` appeared on all four | MAJOR | `stateful_measurement` block added; conditions relabelled **state-RESET intervals**; every row carries `C1_scope`; the matrix C1 cell reads `PASS @ 16 ms granularity`. |
| C | `ENVIRONMENT.json` exposed `transformers: null` at each env's top level (data present, extraction cosmetic) · `griffinlim`'s state note described the **withdrawn** configuration on a row that ran the repaired one · `nanocodec` must stay BLOCKED | MINOR | All three fixed; `nanocodec` preserved as `BLOCKED — PLATFORM` with its missing artifact disclosed. |

**The audit's control on the untested stage, recorded and attributed:** naive
split-in-two inverse STFT then concatenate gives **raw `1.036108e+00` /
`134.65%`, 256 samples short**. The overlap-add stage is therefore **not free**,
so streaming it may not be inferred from the neural decoder streaming (R13).

**`check_consistency.py` — integrity and schema only, no model loaded — passes
all checks**, including that no measured value was altered by any correction.

---

## CLOSING STATUS — 2026-09-11, after the repair

**The line above is the audit's verdict as received and is left unedited. Items
1, 2, 5, 8 and 9 are all now closed** (§F′), and no item in the queue is
outstanding.

> **GATE 3 READY: YES.** Nothing in the repaired evidence blocks GPU timing.

**Updated 2026-09-11 after the independent delta audit (§F″). Its one BLOCKING
finding — MelFlow's unqualified label — is fixed, and every other repair passed
independent verification.**

**What remains open, and none of it blocks Gate 3:**

1. ⚠️ **`melflow`'s label is scoped, and the scope is the open work.** The neural
   decoder streams, verified independently to the digit. The **inverse STFT /
   overlap-add is NOT established as streaming**, and the delta audit's control
   shows naive chunking of that stage fails at **134.65%** — so it cannot be
   inferred. **Earning the unqualified label requires writing AND testing a
   streaming overlap-add stage.** Until then the arm is never counted with the
   three FocalCodec arms.
2. ⚠️ **`melflow` runs on a locally repaired dependency.** The streaming path of
   `ab2700c1` does not execute as released. Both patches were independently
   verified inert — no weight, no arithmetic — but the arm's numbers are numbers
   from a repaired implementation and every deliverable now says so.
3. ⚠️ **The repaired instrument is self-certified by its author, twice over.**
   `gate_lib.py` and `fuzz_gate_lib.py` and `check_consistency.py` were all
   written here. The delta audit did attack `gate_lib.py` independently and it
   survived every break attempt — but a clean run of one's own checker is a floor,
   never a certification (R19).
4. **Mimi's decoder remains unmeasured through Kyutai's own implementation.** The
   claim stays bounded to `transformers` 4.57.3.
5. **`nanocodec` stays BLOCKED — PLATFORM**, reported as blocked, never as zero.
6. **`focalcodec_50hz_65k_causal` is a declared post-freeze arm**, not one frozen
   in advance.
7. **PROTOCOL §7.2's environment control has not run.** It is a timing
   measurement, so it belongs to Gate 3 — but until it does, no cross-environment
   comparison may be made, and `fish` and `decbench_melflow` arms sit in different
   `transformers` versions from `decbench`.
