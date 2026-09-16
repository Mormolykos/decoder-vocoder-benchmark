"""Assemble the corrected Gate 2 matrix FROM ARTIFACTS ONLY.

GATE2_AUDIT §F items 9 and 10. Nothing in this file is transcribed from prose,
from MANIFEST.md or from console history: every cell is read out of a
`gate2_repaired_*.json` written by a run, and the totals are counted from those
rows. The one row that has no artifact - `nanocodec` - is carried explicitly as
BLOCKED, because an absence reported as nothing is R1's defect.

Writes `gate2_matrix.json` and `GATE2_MATRIX.md`.
"""

import glob
import json
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

ORDER = [
    "focalcodec_50hz_4k_causal", "focalcodec_50hz_2k_causal",
    "focalcodec_50hz_65k_causal", "focalcodec_50hz", "focalcodec_25hz",
    "focalcodec_12_5hz", "mimi_q8", "mimi_q32", "encodec24_q8", "encodec_vocos",
    "dac44", "dualcodec_12hz_v1", "dualcodec_25hz_v1", "qwen3_tts_tokenizer_12hz",
    "fish_modified_dac", "melflow", "vocos_mel24", "bigvgan22", "griffinlim",
    "nanocodec",
]

SOURCES = {
    "gate2_repaired_a.json": "decbench",
    "gate2_repaired_b.json": "decbench",
    "gate2_repaired_fish.json": "fish",
    "gate2_repaired_melflow.json": "decbench_melflow",
}

# ⚠️ COMMENTARY, NOT MEASUREMENT. Every other value in this file is read from a
# run artifact. These sentences are written by hand and are marked as such
# wherever they are rendered, so the boundary between what was measured and what
# was said about it stays visible.
ARM_NOTES = {
    "melflow": (
        "**KEEP, with its label scope corrected — do not rerun and do not "
        "withdraw.** The measurement is correct and was independently reproduced "
        "to the digit (stateful `3.036112e-06`), determinism is exact in both "
        "directions, and the carried state was shown load-bearing by four "
        "independent attacks (zeroed state, stale state, reset-every-5, "
        "reset-every-25, plus permuted frames at ~1800× baseline). What was wrong "
        "was the SCOPE of the label, not the number. The stateful error is "
        "identical at all four rows because the stateful branch is ONE continuous "
        "16 ms-granularity stream that is merely sliced — **C1 holds at one-frame "
        "granularity only**, and 5/10/25/50 are state-RESET intervals for the "
        "stateless null. For the same reason the length-drift decomposition does "
        "not apply: the decoder emits spectrogram frames and the inverse STFT is "
        "run once over the assembled spectrogram, so there is no per-chunk length "
        "accumulation to measure. **To earn an unqualified label this arm needs a "
        "streaming overlap-add stage that is written AND tested** — the delta "
        "audit's control shows naive chunking of that stage fails at 134.65%, so "
        "it may not be inferred (R13)."),
    "focalcodec_50hz_65k_causal": (
        "POST-FREEZE ARM, DECLARED 2026-09-11 (PROTOCOL amendment 3). Where one "
        "causal FocalCodec configuration must be named, that is "
        "`focalcodec_50hz_4k_causal`, which was frozen in PROTOCOL §3 before any "
        "result existed."),
    "griffinlim": (
        "Run with `rand_init=False` (PROTOCOL amendment 4). With torchaudio's "
        "default `rand_init=True` and no seed, self-vs-self error with NO "
        "chunking at all was 7.7404e-01 / 131.3% — larger than the chunking "
        "number it was reported as. R9 zero-parameter floor, never a production "
        "candidate."),
    "mimi_q32": (
        "SENSITIVITY ABLATION ONLY. Never merged with `mimi_q8`, and n_q=32 is "
        "never described as 'Mimi 1.1 kbps' — that figure belongs to n_q=8."),
}

rows = {}
missing_sources = []
for fn, env in SOURCES.items():
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        missing_sources.append(fn)
        continue
    for r in json.load(open(p)):
        # Fail closed on a truncated-probe artifact: MelFlow has a feasibility
        # mode that runs a few frames, and a matrix must never quietly inherit it.
        if r.get("truncated_probe"):
            r = {"arm": r["arm"], "classification": "ARTIFACT INVALID - truncated probe",
                 "gate_zero": "UNKNOWN",
                 "why": (f"artifact was written by a truncated feasibility run "
                         f"({r.get('frames_used')} frames of the probe); rerun on "
                         f"the whole probe before this row may be used")}
        r["_artifact"] = fn
        r.setdefault("env", env)
        rows[r["arm"]] = r

rows["nanocodec"] = {
    "arm": "nanocodec",
    "classification": "BLOCKED - PLATFORM",
    "why": ("The released NanoCodec / NeMo reference tooling is not runnable in our "
            "Windows-native benchmark environment. NOT evidence about the "
            "architecture; nothing here tested it."),
    "gate_zero": "NOT RUN - arm could not be loaded",
    "route": "A", "role": "closest candidate to the 24 kHz target",
    "env": "decbench_nemo", "_artifact": "none - see MANIFEST.md §4",
    "state_constructible": None, "state_note": "NOT MEASURED - arm not runnable",
}


def c12(r):
    if r["classification"] == "BLOCKED - PLATFORM":
        return "NOT MEASURED", "NOT MEASURED"
    conds = r.get("conditions") or []
    if not conds:
        return "NOT MEASURED", "NOT MEASURED"
    if not r.get("state_constructible"):
        # C1 compares a STATEFUL chunked decode against full context. With no
        # state to carry there is no stateful branch to evaluate, so C1 is NOT
        # CONSTRUCTIBLE - it is not a FAIL. Writing FAIL would assert a
        # measurement that was never taken (R1).
        return "NOT CONSTRUCTIBLE", "NOT CONSTRUCTIBLE"
    c1 = "PASS" if all(c["C1"] for c in conds) else "FAIL"
    c2 = "PASS" if all(bool(c["C2"]) for c in conds) else "FAIL"
    # An arm whose stateful branch is a single continuous stream at a finer
    # granularity than the chunk conditions has C1 established at THAT
    # granularity only. The identical stateful error on every row is the stream,
    # not four separate stateful decodes, and the column must not imply otherwise.
    sm = r.get("stateful_measurement")
    if sm and c1 == "PASS":
        c1 = f"PASS @ {sm['granularity_ms']:g} ms granularity"
    return c1, c2


def qualified_label(r):
    """THE label, with its SCOPE attached.

    PROTOCOL §10.1 is frozen and requires, for TRUE_INCREMENTAL, "an empirical
    chunk test showing the decoder emits correct audio FROM PARTIAL INPUT while
    retaining state", and §2 / §10.3 stop the claim boundary at a playable PCM
    block. `emits_pcm_from_partial_input` is that predicate, declared per arm on
    the artifact. An arm that streams its network but never emits PCM from
    partial input has NOT met the frozen criterion for the full chain, and its
    label may not read identically to one that has.
    """
    base = r.get("classification")
    scope = r.get("label_scope")
    if base == "TRUE_INCREMENTAL" and scope:
        if r.get("emits_pcm_from_partial_input"):
            return f"TRUE_INCREMENTAL ({scope})"
        return f"TRUE_INCREMENTAL — {scope}"
    return base


def length_model(r):
    """Per-chunk LENGTH DRIFT, measured exactly instead of assumed.

    For every arm the observed per-chunk output length L(u) is EXACTLY linear in
    the chunk size u (maximum residual 0.0 for all 18 measured arms), so
    `L(u) = a*u + b` decomposes it without approximation:

      a = samples the decoder actually emits per unit
      b = the CONSTANT offset each chunk carries, which accumulates n_chunks
          times across a chunked decode

    `b` is the quantity GATE2_AUDIT §C4 named. It is computed here rather than
    taken from the run's own `drift_per_chunk_samples`, because that column
    compared against an assumed samples-per-unit (the arm's measured token rate),
    which carries a rate-estimation residue on any arm whose rate is not an exact
    divisor of its sample rate. This fit assumes nothing.
    """
    cs = r.get("conditions") or []
    if len(cs) < 2:
        return None, None, None
    # An artifact may declare that the decomposition does not apply to it at all
    # - melflow emits spectrogram frames and inverts once over the assembled
    # spectrogram, so there is no per-chunk length accumulation to measure. A
    # regression through those points produces a number with no referent, and a
    # number with no referent is worse than a blank.
    if r.get("samples_per_unit") is None and "NOT APPLICABLE" in str(
            r.get("samples_per_unit_source", "")):
        return None, None, None
    pts = [(c["chunk_units"], c["chunked_samples"] / c["n_chunks"]) for c in cs]
    n = len(pts)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum(p[0] ** 2 for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    den = n * sxx - sx * sx
    if den == 0:
        return None, None, None
    a = (n * sxy - sx * sy) / den
    b = (sy - a * sx) / n
    resid = max(abs(p[1] - (a * p[0] + b)) for p in pts)
    return round(a, 6), round(b, 6), resid


def targets(r):
    """codec targets/s = token rate x codebooks. A property of the REPRESENTATION
    only. It is NOT generator decisions/s and NOT Transformer evaluations per
    second; generator factorisation is unmeasured by this study.

    Undefined on Route B, where the representation is continuous. Returned as an
    explicit string rather than left blank: a blank never means unknown here."""
    if r.get("route") == "B":
        return "n/a — continuous representation"
    cb = r.get("codebooks")
    rate = r.get("measured_rate_hz")
    if cb is None or rate is None:
        return None
    return round(rate * cb, 3)


def drift_agrees(r, fitted_b):
    """Cross-check: the artifact's per-condition drift must agree with the fit.

    The delta audit found the artifact column contaminated - it derived
    samples-per-unit from the MEASURED token rate, so `mimi_q8` read +7.24 to
    +72.37 samples/chunk where the true hop is exactly 1920 and the real drift is
    zero. `correct_artifacts.py` recomputed it on the true integer hop. This
    function is the standing check that the two never diverge again.
    """
    conds = r.get("conditions") or []
    if not conds or fitted_b is None:
        return None
    vals = [c.get("drift_per_chunk_samples") for c in conds]
    if any(v is None for v in vals):
        return None
    return all(abs(v - fitted_b) <= 1e-6 for v in vals)


matrix = []
for arm in ORDER:
    r = rows.get(arm)
    if r is None:
        matrix.append({"arm": arm, "classification": "ARTIFACT MISSING",
                       "gate_zero": "UNKNOWN"})
        continue
    c1, c2 = c12(r)
    a, b, resid = length_model(r)
    worst_cum = None
    if b is not None and b != 0:
        worst_cum = max(int(round(abs(b) * c["n_chunks"]))
                        for c in (r.get("conditions") or []))
    matrix.append({
        "arm": arm,
        "route": r.get("route"),
        "role": r.get("role"),
        "env": r.get("env"),
        "artifact": r.get("_artifact"),
        "gate_zero": r.get("gate_zero"),
        "measured_rate_hz": r.get("measured_rate_hz"),
        "codebooks": r.get("codebooks"),
        "codec_targets_per_s": targets(r),
        "sr_out": r.get("sr_out"),
        "quantum_ms": r.get("quantum_ms"),
        "chunk_conditions_ms": [c["chunk_ms"] for c in (r.get("conditions") or [])],
        "state_constructible": r.get("state_constructible"),
        "negative_control": r.get("negative_control", False),
        "C1": c1,
        "C2": c2,
        "stateful_raw_band": r.get("stateful_raw_band"),
        "stateless_raw_band": r.get("stateless_raw_band"),
        "stateless_rel_pct_band": r.get("stateless_rel_pct_band"),
        "c2_ratio_band": r.get("c2_ratio_band"),
        "samples_per_unit_measured": a,
        "per_chunk_offset_samples": b,
        "length_fit_max_residual": resid,
        "worst_cumulative_offset_samples": worst_cum,
        "artifact_drift_per_chunk_band": r.get("drift_per_chunk_band"),
        "drift_artifact_agrees_with_fit": drift_agrees(r, b),
        "classification": r.get("classification"),
        "label": qualified_label(r),
        "label_scope": r.get("label_scope"),
        "emits_pcm_from_partial_input": r.get("emits_pcm_from_partial_input"),
        "emits_pcm_from_partial_input_reason":
            r.get("emits_pcm_from_partial_input_reason"),
        "stateful_measurement": r.get("stateful_measurement"),
        "upstream_patches": r.get("upstream_patches"),
        "claim_boundary": r.get("claim_boundary"),
        "licence": r.get("licence"),
        "why": r.get("why"),
        "state_note": r.get("state_note"),
    })

totals = {}
for m in matrix:
    totals[m["label"]] = totals.get(m["label"], 0) + 1

gz = {}
for m in matrix:
    gz[m["gate_zero"]] = gz.get(m["gate_zero"], 0) + 1

doc = {
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "generated_by": "make_matrix.py - every cell read from a run artifact",
    "sources": {k: v for k, v in SOURCES.items()},
    "missing_sources": missing_sources,
    "superseded_artifacts": {
        "gate2_results.json": "close_gate2.py - C2 never applied, hardcoded Gate "
                              "Zero PASS, unseeded griffinlim, ambiguous `raw` column",
        "gate2_results_b.json": "close_gate2b.py - hardcoded Gate Zero PASS",
        "gate2_results_c.json": "close_gate2c.py - melflow measured through "
                                "enhance() on raw waveform chunks; WITHDRAWN",
        "note": ("KEPT, not deleted: they are the provenance of the withdrawn "
                 "claims. They are not inputs to this matrix and must not be "
                 "quoted as results."),
    },
    "n_arms": len(matrix),
    "totals_by_classification": totals,
    "totals_by_gate_zero": gz,
    "criteria": {
        "C1": "stateful chunked decode reproduces full context, max|err| <= 1e-3",
        "C2": "state is load-bearing, stateless err >= 10x stateful err",
        "note": ("BOTH are conjuncts of TRUE_INCREMENTAL. In close_gate2.py C2 "
                 "appeared only in a print statement and both labels in that batch "
                 "were awarded on C1 alone."),
    },
    "withdrawn": [
        ("Cross-arm severity rankings from the normalised error, including "
         "'Fish departs more than EnCodec'. On encodec24_q8 a ONE-SAMPLE shift "
         "produces 34.07%, inside the band reported for genuine chunking damage, "
         "and an all-zero output produces exactly 100.00%. The metric is a "
         "DETECTOR of departure from full context, not a severity scale."),
        ("The first griffinlim measurement (7.244e-01-7.637e-01 / 95.7-100.9%), "
         "taken with torchaudio's default rand_init=True and no seed."),
        ("The first melflow measurement (7.112e-01-1.072e+00 / 91.3-137.6%), taken "
         "through enhance() on raw waveform chunks with per-chunk gain "
         "normalisation and no seed."),
        ("The statement that MimiDecoderOutput contains only audio_values and never "
         "returns past_key_values. It contains audio_values AND "
         "decoder_past_key_values."),
    ],
    "matrix": matrix,
}

with open(os.path.join(HERE, "gate2_matrix.json"), "w") as f:
    json.dump(doc, f, indent=2)


def cell(v):
    return "—" if v is None else str(v)


lines = []
lines.append("# GATE 2 — CORRECTED STREAMING-CLASSIFICATION MATRIX")
lines.append("")
lines.append(f"**Machine-generated by `make_matrix.py` on "
             f"{doc['generated_utc']}. Every cell is read from a run artifact; "
             f"nothing here is transcribed from prose.** Nothing was timed. No GPU "
             f"was used for any measurement.")
lines.append("")
lines.append("**Criteria, both conjuncts of `TRUE_INCREMENTAL`:** "
             "**C1** stateful chunked decode reproduces full context, "
             "`max|err| ≤ 1e-3` · **C2** state is load-bearing, "
             "`stateless err ≥ 10× stateful err`.")
lines.append("")
lines.append("**Scope column `PCM?` is the frozen PROTOCOL §10.1 predicate** — "
             "*does this arm emit correct audio FROM PARTIAL INPUT while retaining "
             "state?* §2 and §10.3 stop the claim boundary at a playable PCM block. "
             "**An arm that streams its network but never emits PCM from partial "
             "input has not met the frozen criterion for the full chain, and its "
             "label says so.**")
lines.append("")
lines.append("| arm | route | gate zero | rate Hz | cb | targets/s | quantum ms | "
             "state | PCM? | C1 | C2 | C2 ratio | label |")
lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for m in matrix:
    st = ("yes" if m["state_constructible"] else
          ("—" if m["state_constructible"] is None else "no"))
    pcm = {True: "yes", False: "**NO**", None: "—"}[m.get("emits_pcm_from_partial_input")]
    lines.append(
        f"| `{m['arm']}` | {cell(m['route'])} | {cell(m['gate_zero'])} | "
        f"{cell(m['measured_rate_hz'])} | {cell(m['codebooks'])} | "
        f"{cell(m['codec_targets_per_s'])} | {cell(m['quantum_ms'])} | {st} | "
        f"{pcm} | {cell(m['C1'])} | {cell(m['C2'])} | {cell(m['c2_ratio_band'])} | "
        f"**{m['label']}** |")
lines.append("")

scoped = [m for m in matrix if m.get("emits_pcm_from_partial_input") is False]
for m in scoped:
    lines.append(f"⛔ **`{m['arm']}` does NOT satisfy PROTOCOL §10.1 for the full "
                 f"chain.** {m['emits_pcm_from_partial_input_reason']} Its label is "
                 f"qualified accordingly and **it is counted in its own total, never "
                 f"together with arms that do emit PCM from partial input.**")
    if m.get("claim_boundary"):
        lines.append("")
        lines.append(f"> **Declared claim boundary.** {m['claim_boundary']}")
    lines.append("")
patched = [m for m in matrix if m.get("upstream_patches")]
if patched:
    lines.append("## ⚠️ Arms that required LOCAL REPAIRS to their upstream "
                 "dependency")
    lines.append("")
    lines.append("**The released streaming path of these dependencies DOES NOT "
                 "EXECUTE AS-IS.** The study's strongest new claim on such an arm "
                 "rests on code that was locally repaired here, and that has to be "
                 "on the face of the deliverable, not only in an amendment.")
    lines.append("")
    for m in patched:
        src = rows.get(m["arm"], {})
        lines.append(f"**`{m['arm']}`** — {len(m['upstream_patches'])} structural "
                     f"repairs to upstream revision `ab2700c1`:")
        lines.append("")
        for i, p in enumerate(m["upstream_patches"], 1):
            lines.append(f"{i}. {p}")
        lines.append("")
        lines.append("**An independent delta audit verified both patches are "
                     "INERT**: it confirmed that neither referenced attribute exists "
                     "anywhere in the class, that the non-streaming `forward()` path "
                     "has no pointwise branch (so `False` is the only value making "
                     "`forward_step` agree with `forward`), that `state_se` occurs at "
                     "exactly two lines — the unpack and the repack — and is never "
                     "read or written, and that **no weight and no arithmetic "
                     "operation is touched by either.**")
        lines.append("")
        ctl = src.get("istft_stage_control")
        if ctl:
            lines.append(f"⛔ **The untested stage on this arm is not free.** "
                         f"A control from the {ctl['source']} — {ctl['procedure']} — "
                         f"measured **raw {ctl['raw']:.6g} / {ctl['rel_pct']}%**, "
                         f"{ctl['deficit_samples']} samples short "
                         f"({ctl['length_naive']} vs {ctl['length_whole']}). "
                         f"*(Externally sourced; reproduced in this harness: "
                         f"{ctl['reproduced_in_this_harness']}.)* {ctl['conclusion']}")
            lines.append("")

ncs = [m for m in matrix if m.get("negative_control")]
if ncs:
    lines.append("## Negative controls — the rows that make the positives mean "
                 "something")
    lines.append("")
    lines.append("`toks_to_sig(..., decompressor_state, decoder_state, "
                 "return_state=True)` is the SAME method on every FocalCodec "
                 "config, so the non-causal configs are run through the identical "
                 "stateful branch. **If carrying state changes nothing on a "
                 "non-causal config, C2 lands at ~1.0 — and that is the evidence "
                 "that the harness's state plumbing is not manufacturing the "
                 "passes on the causal configs.** Had a negative control passed, "
                 "the experiment would be void rather than the arm promoted.")
    lines.append("")
    lines.append("| negative control | C2 ratio (threshold 10) | C1 | label |")
    lines.append("|---|---|---|---|")
    for m in ncs:
        lines.append(f"| `{m['arm']}` | **{cell(m['c2_ratio_band'])}** | "
                     f"{cell(m['C1'])} | {m['classification']} |")
    lines.append("")

EXACT_TOL = 1e-6
fitted = [m for m in matrix if m.get("samples_per_unit_measured") is not None]
exact = [m for m in fitted if m["length_fit_max_residual"] <= EXACT_TOL]
inexact = [m for m in fitted if m["length_fit_max_residual"] > EXACT_TOL]
drifting = [m for m in exact if m["per_chunk_offset_samples"] != 0]

lines.append("## Chunked-decode length drift — measured, not assumed")
lines.append("")
lines.append(f"Per-chunk output length `L(u)` is fitted against chunk size `u` as "
             f"`L(u) = a·u + b`. **The fit is EXACT (residual 0.0) for "
             f"{len(exact)} of {len(fitted)} fitted arms**, so for those `b` is the "
             f"constant offset every chunk carries and it accumulates once per "
             f"chunk. `n = min(lengths)` hides it, which is why part of the "
             f"reported error on the arms with `b ≠ 0` is misalignment rather than "
             f"boundary damage.")
lines.append("")
if drifting:
    lines.append("**Arms that drift:** " + " · ".join(
        f"`{m['arm']}` **b = {m['per_chunk_offset_samples']:+g}**"
        for m in drifting) + ". Every other exactly-fitted arm has **b = 0**.")
    lines.append("")
for m in inexact:
    lines.append(f"⚠️ **`{m['arm']}` does not fit the linear model exactly** "
                 f"(residual {m['length_fit_max_residual']:.2g}). Its `b` is a "
                 f"regression residue and **must not be read as per-chunk drift**; "
                 f"see the commentary section for why the decomposition does not "
                 f"apply to this arm.")
    lines.append("")
for arm, src in rows.items():
    if (src.get("conditions") and src.get("samples_per_unit") is None
            and "NOT APPLICABLE" in str(src.get("samples_per_unit_source", ""))):
        lines.append(f"⚠️ **`{arm}` is absent from the drift table by declaration, "
                     f"not by omission.** {src['samples_per_unit_source']}")
        lines.append("")
lines.append("| arm | a · samples per unit | b · offset per chunk | worst cumulative "
             "offset | fit residual | artifact agrees |")
lines.append("|---|---|---|---|---|---|")
for m in matrix:
    if m.get("samples_per_unit_measured") is None:
        continue
    worst = m["worst_cumulative_offset_samples"]
    sr = m.get("sr_out") or 0
    ws = (f"{worst} smp ≈ {worst / sr:.3f} s" if worst and sr else "0")
    ag = {True: "yes", False: "⛔ **NO**", None: "n/a"}[m["drift_artifact_agrees_with_fit"]]
    lines.append(f"| `{m['arm']}` | {m['samples_per_unit_measured']:g} | "
                 f"**{m['per_chunk_offset_samples']:+g}** | {ws} | "
                 f"{m['length_fit_max_residual']:.1e} | {ag} |")
lines.append("")
disagree = [m for m in matrix if m.get("drift_artifact_agrees_with_fit") is False]
if disagree:
    lines.append("⛔ **DRIFT MISMATCH between artifact and fit on: " +
                 ", ".join(f"`{m['arm']}`" for m in disagree) +
                 "** — the artifacts must be corrected before these rows are used.")
else:
    lines.append("**Every fitted arm's per-condition `drift_per_chunk_samples` in "
                 "the artifact now agrees with the fit.** The delta audit found that "
                 "column contaminated — it derived samples-per-unit from the measured "
                 "token rate, so `mimi_q8` read +7.24 to +72.37 samples/chunk where "
                 "the true hop is exactly 1920 and the real drift is zero. "
                 "`correct_artifacts.py` recomputed it on the true integer hop and "
                 "kept every superseded value beside it.")
lines.append("")
lines.append("## Totals — counted from the rows above, SPLIT BY SCOPE")
lines.append("")
lines.append("**`TRUE_INCREMENTAL` is split by the frozen §10.1 predicate.** Arms "
             "that emit PCM from partial input are never counted together with an "
             "arm that only streams its network.")
lines.append("")
W = max(len(k) for k in totals) + 2
lines.append("```")
for k in sorted(totals, key=lambda x: (-totals[x], x)):
    members = ", ".join(m["arm"] for m in matrix if m["label"] == k)
    lines.append(f"{k:<{W}} {totals[k]:>3}   {members}")
lines.append(f"{'-' * W} {'-' * 3}")
lines.append(f"{'TOTAL':<{W}} {len(matrix):>3}")
lines.append("```")
lines.append("")
lines.append("**Gate Zero, computed for every arm by the shared "
             "`gate_lib.gate_zero_record()` (finite · peak ∈ (0,1] · duration within "
             "one frame of that arm · energy ratio 0.25–4.0 · dtype float32 · channel "
             "count):**")
lines.append("")
lines.append("```")
for k in sorted(gz, key=lambda x: -gz[x]):
    lines.append(f"{str(k):<40} {gz[k]:>3}")
lines.append("```")
lines.append("")
lines.append("## Withdrawn by this repair")
lines.append("")
for w in doc["withdrawn"]:
    lines.append(f"- {w}")
lines.append("")
lines.append("## Superseded artifacts — kept, never quoted")
lines.append("")
for k, v in doc["superseded_artifacts"].items():
    if k == "note":
        continue
    lines.append(f"- `{k}` — {v}")
lines.append("")
lines.append(f"**{doc['superseded_artifacts']['note']}**")
lines.append("")
lines.append("## The instrument was fuzzed before it was trusted")
lines.append("")
lines.append("`fuzz_gate_lib.py` attacks the shared Gate Zero record, the error "
             "metric, the classifier, the chunk-grid function and the layout "
             "resolver — outputs a decoder could plausibly produce, and label "
             "combinations that must not earn `TRUE_INCREMENTAL`. Results in "
             "`fuzz_gate_lib.json`. **It found one latent defect in `native_grid` "
             "(Python's banker's rounding: `round(0.5) == 0`), which was fixed; "
             "no arm's grid was affected, verified condition by condition against "
             "the exact frame period each run used.** ⛔ The instrument SURVIVED "
             "these attacks. It is not closed, and its author is not its "
             "certifier (R19).")
lines.append("")
lines.append("## Per-arm state findings — read from the artifacts")
lines.append("")
for m in matrix:
    if m.get("state_note"):
        lines.append(f"**`{m['arm']}`** — {m['state_note']}")
        lines.append("")
lines.append("## Commentary — written by hand, NOT measured")
lines.append("")
lines.append("*Everything above this heading is read from a run artifact. "
             "Everything below is interpretation.*")
lines.append("")
for arm, note in ARM_NOTES.items():
    lines.append(f"**`{arm}`** — {note}")
    lines.append("")

with open(os.path.join(HERE, "GATE2_MATRIX.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("\n".join(lines[:12]))
print(f"\ntotals: {totals}")
print(f"gate zero: {gz}")
if missing_sources:
    print(f"⚠️ MISSING SOURCES: {missing_sources}")
print("\nwritten: gate2_matrix.json, GATE2_MATRIX.md")
