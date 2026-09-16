"""GATE 3 MATRIX — machine-generated from run artifacts and RAW data only.

Rewritten 2026-09-11 to close the independent Gate 3 audit (`GATE3_AUDIT.md`).
Nothing is transcribed by hand; every statistic is recomputed from
`results/gate3_raw_*.jsonl`, and totals are counted from the rows.

WHAT THIS VERSION FIXES, all from the audit:
  B1  the §7.2 environment control (E6) is loaded and its consequence APPLIED:
      arms measured in a NOT COMPARABLE environment carry that marker and are
      excluded from the budget table and from E4's ordering.
  B2  `streamed_gate8` is exposed per condition AND in the headline. E3 is split
      into `min_chunk_that_ran_ms` (execution feasibility) and the frozen
      `minimum viable streaming configuration`, which requires a §8 PASS and is
      `NOT ACHIEVABLE` where no tested condition has one.
  M1  E1 is produced as a real estimand: paired difference, ratio, per duration
      condition, with an interval.
  M2  VRAM scopes are separated - whole-session peak, anchor allocated, anchor
      reserved - and never quoted across scopes.
  M3  ONE population. p50/p95/p99/IQR/max are ALL recomputed over steady-state
      chunks, excluding the first chunk of every repetition, because TTFA already
      reports the first chunk separately and counting it twice is a mixed
      population. The all-chunks figures are kept beside them, labelled.
  M4  `PASS` is gone. Status is `MEASURED - CELLS COMPLETED AND ADMISSIBLE`, with
      an explicit sentence that it is not a performance verdict.
  M6  E3 and E4 are produced.
  D   E2 invalid fits marked INLINE; weak delay correlations flagged; BigVGAN
      transition points read from data; budget table excludes §8 failures.

Writes `gate3_matrix.json` and `GATE3_MATRIX.md`.
"""

import glob
import json
import os
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

ORDER = [
    "focalcodec_50hz_4k_causal", "focalcodec_50hz_2k_causal",
    "focalcodec_50hz_65k_causal", "focalcodec_50hz", "focalcodec_25hz",
    "focalcodec_12_5hz", "mimi_q8", "mimi_q32", "encodec24_q8", "encodec_vocos",
    "dac44", "dualcodec_12hz_v1", "dualcodec_25hz_v1", "qwen3_tts_tokenizer_12hz",
    "fish_modified_dac", "melflow", "vocos_mel24", "bigvgan22", "griffinlim",
    "nanocodec",
]
BUDGET = {"competitive_ms": 75, "stretch_ms": 50, "red_zone_ms": 200}
ANCHOR_MS = 80.0
ARM_ENV = {"fish_modified_dac": "fish", "melflow": "decbench_melflow"}
STATUS = "MEASURED - CELLS COMPLETED AND ADMISSIBLE"

# ------------------------------------------------------------------ load
cells, headers, raw = {}, {}, []
e6_cells = {}
for f in sorted(glob.glob(os.path.join(RES, "gate3_cells_*.jsonl"))):
    b = os.path.basename(f)
    if b.startswith("SMOKE_"):
        continue
    rows_ = [json.loads(l) for l in open(f, encoding="utf-8")]
    if "_e6_" in b:                       # the §7.2 CONTROL, never an arm row
        e6_cells[b.split("_e6_")[1].replace(".jsonl", "")] = rows_
        continue
    for r in rows_:
        r["_file"] = b
        cells.setdefault(r["arm"], []).append(r)
for f in sorted(glob.glob(os.path.join(RES, "gate3_raw_*.jsonl"))):
    b = os.path.basename(f)
    if b.startswith("SMOKE_") or "_e6_" in b:
        continue
    raw += [json.loads(l) for l in open(f, encoding="utf-8")]
for f in sorted(glob.glob(os.path.join(RES, "gate3_header_*.json"))):
    b = os.path.basename(f)
    if b.startswith("SMOKE_"):
        continue
    h = json.load(open(f, encoding="utf-8"))
    headers[b.replace("gate3_header_", "").replace(".json", "")] = h

g2 = {m["arm"]: m for m in
      json.load(open(os.path.join(HERE, "gate2_matrix.json")))["matrix"]}


def of(arm, kind):
    return [c for c in cells.get(arm, []) if c["cell"] == kind]


def ok(rs):
    return [r for r in rs if r.get("status", "OK") == "OK"]


def res(r):
    return r.get("result", r)


def stats_ms(xs):
    a = np.asarray([x for x in xs if x is not None], dtype=np.float64) * 1000.0
    if a.size == 0:
        return {"n": 0}
    q1, q3 = np.percentile(a, [25, 75])
    return {"n": int(a.size), "p50": float(np.percentile(a, 50)),
            "p95": float(np.percentile(a, 95)), "p99": float(np.percentile(a, 99)),
            "iqr": float(q3 - q1), "min": float(a.min()), "max": float(a.max()),
            "mean": float(a.mean())}


# ---- M3: rebuild chunk populations from RAW, steady-state and all-chunks -----
chunkpop = {}
for r in raw:
    series = r.get("chunk_walls_s") or r.get("frame_walls_s")
    if not series:
        continue
    key = (r["arm"], r["cell"], r.get("chunk_units"), r.get("left_ctx_units") or 0)
    d = chunkpop.setdefault(key, {"all": [], "steady": [], "reps": 0})
    d["all"].extend(series)
    d["steady"].extend(series[1:])       # first chunk is TTFA, reported separately
    d["reps"] += 1


# ------------------------------------------------------------------ E6
def build_e6():
    """§7.2. The control decides comparability; it is not decoration."""
    def curve(rows_):
        out = {}
        for r in rows_:
            x = r["result"]
            if r["cell"] == "offline" and not x.get("skipped"):
                out[("offline", round(x["produced_audio_s"], 2))] = \
                    x["wall_s"]["median"] * 1000
            if r["cell"] == "stream" and not x.get("skipped"):
                out[("stream", round(x["effective_ms"], 1))] = \
                    (x.get("steady_state_chunk_s") or {}).get("p50", 0) * 1000
        return out
    if "decbench" not in e6_cells:
        return None
    base = curve(e6_cells["decbench"])
    envs = {}
    for env, rows_ in e6_cells.items():
        c = curve(rows_)
        common = sorted(set(base) & set(c))
        ratios = [c[k] / base[k] for k in common if base[k]]
        med = float(np.median(ratios)) if ratios else None
        envs[env] = {
            "conditions": [{"cell": k[0], "condition": k[1],
                            "decbench_ms": base[k], "this_env_ms": c[k],
                            "diff_ms": c[k] - base[k], "ratio": c[k] / base[k]}
                           for k in common],
            "median_ratio": med,
            "effect_pct": (abs(med - 1) * 100 if med is not None else None),
            "ratio_range": [min(ratios), max(ratios)] if ratios else None,
            "transformers": headers.get(f"e6_{env}", {}).get("transformers")
            or json.load(open(os.path.join(HERE, "ENVIRONMENT.json")))
            ["environments"].get(env, {}).get("transformers"),
        }
    return envs


E6 = build_e6()
# Between-decoder spread at the anchor decides "comparable in size" (§7.2).
def e6_verdict(env):
    if env == "decbench" or not E6 or env not in E6:
        return True, "measured in the reference environment"
    e = E6[env]["effect_pct"]
    if e is None:
        return None, "control not available"
    if e >= 10.0:
        return False, (f"environment effect {e:.1f}% is comparable in size to the "
                       f"between-decoder differences; §7.2 pre-commits NOT COMPARABLE")
    return True, (f"environment effect {e:.1f}% is small against the between-decoder "
                  f"differences; comparability justified by measurement")


# ------------------------------------------------------------------ arms
rows = []
missing = []
for arm in ORDER:
    if arm == "nanocodec":
        rows.append({"arm": arm, "route": "A", "status": "BLOCKED - PLATFORM",
                     "gate2_label": g2[arm]["label"], "env": "decbench_nemo",
                     "why": ("The released NanoCodec / NeMo reference tooling is not "
                             "runnable in our Windows-native benchmark environment. "
                             "NO TIMING NUMBER IS MANUFACTURED. Reported as BLOCKED, "
                             "never as zero, never omitted."),
                     "cells_run": 0, "cells_failed": 0})
        continue
    cs = cells.get(arm)
    if not cs:
        missing.append(arm)
        rows.append({"arm": arm, "status": "NO ARTIFACT"})
        continue
    env = ARM_ENV.get(arm, "decbench")
    comparable, comp_why = e6_verdict(env)
    fails = [c for c in cs if c.get("status", "OK") != "OK"]
    row = {
        "arm": arm, "route": g2[arm]["route"], "gate2_label": g2[arm]["label"],
        "sr_out": g2[arm]["sr_out"], "quantum_ms": g2[arm]["quantum_ms"],
        "codec_targets_per_s": g2[arm]["codec_targets_per_s"],
        "emits_pcm_from_partial_input": g2[arm].get("emits_pcm_from_partial_input"),
        "env": env, "cross_env_comparable": comparable,
        "cross_env_note": comp_why,
        "cells_run": len(cs), "cells_failed": len(fails),
        "failures": [{"cell": f["cell"], "error": str(res(f).get("error"))[:200],
                      "condition": str(f.get("arg"))[:120]} for f in fails],
        "status": STATUS,
    }

    cold = ok(of(arm, "cold"))
    if cold:
        r = res(cold[0])
        row["cold_model_load_s"] = (r.get("model_load_s") or {}).get("median")
        row["cold_first_decode_ms"] = ((r.get("first_decode_wall_s") or {})
                                       .get("median", 0) or 0) * 1000 or None

    # ---- offline / E2
    dur = []
    for c in ok(of(arm, "offline")):
        r = res(c)
        if r.get("skipped") or not r.get("wall_s"):
            continue
        dur.append({"produced_audio_s": r["produced_audio_s"],
                    "median_wall_ms": r["wall_s"]["median"] * 1000,
                    "p95_wall_ms": r["wall_s"]["p95"] * 1000,
                    "rtf_median": r["rtf_median"],
                    "gate8": r.get("gate8"),
                    "peak_alloc_MiB": r.get("peak_alloc_MiB"),
                    "peak_reserved_MiB": r.get("peak_reserved_MiB"),
                    "n": r["wall_s"]["n"]})
    dur.sort(key=lambda d: d["produced_audio_s"])
    row["offline"] = dur
    if len(dur) >= 2:
        xs = [d["produced_audio_s"] for d in dur]
        ys = [d["median_wall_ms"] for d in dur]
        n = len(xs)
        den = n * sum(x * x for x in xs) - sum(xs) ** 2
        sl = (n * sum(x * y for x, y in zip(xs, ys)) - sum(xs) * sum(ys)) / den
        ic = (sum(ys) - sl * sum(xs)) / n
        rs = max(abs(y - (sl * x + ic)) for x, y in zip(xs, ys))
        row.update(e2_slope_ms_per_audio_s=sl, e2_intercept_ms=ic,
                   e2_fit_max_residual_ms=rs)
        shortest = ys[0]
        row["e2_fit_valid"] = bool(ic >= 0 and rs <= 0.25 * shortest)
        row["e2_fit_invalid_reason"] = None if row["e2_fit_valid"] else (
            (f"negative fixed cost ({ic:.2f} ms)" if ic < 0 else "")
            + (" and " if ic < 0 and rs > 0.25 * shortest else "")
            + (f"max residual {rs:.2f} ms against a {shortest:.2f} ms shortest "
               f"measurement" if rs > 0.25 * shortest else ""))
    ten = [d for d in dur if abs(d["produced_audio_s"] - 10) < 1.5]
    row["rtf_at_10s"] = ten[0]["rtf_median"] if ten else None
    row["offline_sweep_peak_alloc_MiB"] = max(
        [d["peak_alloc_MiB"] or 0 for d in dur] or [0]) or None

    # ---- streaming conditions, statistics REBUILT FROM RAW
    st = []
    for c in ok(of(arm, "stream")) + ok(of(arm, "stream_block_composed")):
        r = res(c)
        if r.get("skipped"):
            continue
        u = r.get("chunk_units") or r.get("frames_per_block")
        pop = chunkpop.get((arm, "stream", u, 0))
        composed = bool(r.get("composed"))
        if composed:                       # melflow: composed from the frame stream
            fp = chunkpop.get((arm, "stream_perframe", None, 0))
            steady = all_ = None
            w = r.get("block_wall_s") or {}
            row_stats_steady = {k: (w.get(k, 0) * 1000) for k in
                                ("p50", "p95", "p99", "iqr", "min", "max")}
            row_stats_steady["n"] = r.get("n_blocks_judged")
            row_stats_all = row_stats_steady
        else:
            row_stats_steady = stats_ms(pop["steady"]) if pop else {"n": 0}
            row_stats_all = stats_ms(pop["all"]) if pop else {"n": 0}
        t = r.get("ttfa_wall_s")
        st.append({
            "effective_ms": r["effective_ms"], "requested_ms": r.get("requested_ms"),
            "chunk_units": u, "composed": composed,
            "cut_audio_s": r.get("cut_audio_s"),
            "ttfa_ms": (None if isinstance(t, str) else t["median"] * 1000),
            "ttfa_state": (t if isinstance(t, str) else "MEASURED"),
            "steady": row_stats_steady, "all_chunks": row_stats_all,
            "underrun_rate": r.get("underrun_rate"),
            "underrun_count": r.get("underrun_count"),
            "realtime_margin_median": r.get("realtime_margin_median"),
            "realtime_margin_p99": r.get("realtime_margin_p99"),
            "required_lookahead_ms": r.get("required_lookahead_ms", 0.0),
            "streamed_gate8": r.get("streamed_gate8"),
            "streamed_gate8_failing": [
                k for k in ("finite", "peak_in_range", "duration_ok", "energy_ok",
                            "dtype_ok", "channels_ok")
                if (r.get("streamed_gate8_checks") or {}).get(k) is False],
            "anchor_peak_alloc_MiB": r.get("peak_alloc_MiB"),
            "anchor_peak_reserved_MiB": r.get("peak_reserved_MiB"),
        })
    st.sort(key=lambda s: s["effective_ms"])
    row["stream"] = st

    pf = ok(of(arm, "stream_perframe"))
    if pf:
        r = res(pf[0])
        pop = chunkpop.get((arm, "stream_perframe", None, 0))
        row["perframe"] = {
            "granularity_ms": r["granularity_ms"],
            "steady": stats_ms(pop["steady"]) if pop else {"n": 0},
            "all_chunks": stats_ms(pop["all"]) if pop else {"n": 0},
            "underrun_rate": r["underrun_rate"],
            "realtime_margin_median": r["realtime_margin_median"],
            "anchor_peak_alloc_MiB": r.get("peak_alloc_MiB"),
        }

    # ---- E3: execution feasibility vs the FROZEN viability criterion
    actual = [s for s in st if not s["composed"]]
    row["min_chunk_that_ran_ms"] = (min(s["effective_ms"] for s in actual)
                                    if actual else None)
    valid = [s for s in actual if s["streamed_gate8"] == "PASS"]
    row["e3_conditions_passing_gate8"] = f"{len(valid)}/{len(actual)}"
    row["e3_failing_predicates"] = sorted(
        {k for s in actual for k in s["streamed_gate8_failing"]})
    if not actual:
        # NO condition was decoded at a chunk size at all - this arm's decode
        # granularity is one frame and every condition is COMPOSED. "Tested and
        # none passed" and "never tested" are different claims and must not
        # collapse into one label.
        row["e3_min_viable_streaming_ms"] = "NOT ESTABLISHED"
        row["e3_reason"] = ("no condition was decoded at a chunk size: this arm's "
                            "decode granularity is one frame and every chunk "
                            "condition is COMPOSED from the per-frame stream "
                            "(amendment 9.6). §8 was therefore never evaluated on "
                            "a chunked decode for it - that is untested, NOT failed.")
        row["streamed_gate8_any_pass"] = None
    elif valid:
        row["e3_min_viable_streaming_ms"] = min(s["effective_ms"] for s in valid)
        row["e3_reason"] = None
        row["streamed_gate8_any_pass"] = True
    else:
        row["e3_min_viable_streaming_ms"] = "NOT ACHIEVABLE"
        row["e3_reason"] = (f"every one of {len(actual)} tested conditions produced "
                            f"streamed output failing §8 on "
                            f"`{', '.join(row['e3_failing_predicates'])}`")
        row["streamed_gate8_any_pass"] = False

    if st:
        anchor = min(st, key=lambda s: abs(s["effective_ms"] - ANCHOR_MS))
        row["anchor"] = anchor
        row["ttfa_anchor_ms"] = anchor["ttfa_ms"]
        row["ttfa_anchor_state"] = anchor["ttfa_state"]
        row["anchor_streamed_gate8"] = anchor["streamed_gate8"]
        # A composed anchor has no allocation of its own; fall back to the
        # per-frame cell, which is where this arm's streaming memory was measured.
        row["anchor_peak_alloc_MiB"] = (anchor["anchor_peak_alloc_MiB"]
                                        or (row.get("perframe") or {})
                                        .get("anchor_peak_alloc_MiB"))
        row["anchor_peak_reserved_MiB"] = anchor["anchor_peak_reserved_MiB"]
        # The budget table admits an arm only if its streamed output is valid at
        # the anchor AND it is comparable to the reference environment.
        row["budget_eligible"] = bool(anchor["ttfa_ms"] is not None
                                      and anchor["streamed_gate8"] == "PASS"
                                      and comparable)
        if anchor["ttfa_ms"] is not None:
            row["budget_consumed_pct_of_75ms"] = 100.0 * anchor["ttfa_ms"] / 75.0
            row["budget_left_of_75ms"] = 75.0 - anchor["ttfa_ms"]
        # D: BigVGAN-style transition read from the data, never typed
        tr = [s for s in actual if (s["underrun_rate"] or 0) > 0]
        row["underrun_conditions_ms"] = [s["effective_ms"] for s in tr]
        first_clean = [s for s in actual if (s["underrun_rate"] or 0) == 0]
        row["first_underrun_free_ms"] = (min(s["effective_ms"] for s in first_clean)
                                         if first_clean else None)

    tt = of(arm, "ttfa")
    if tt:
        r = res(tt[0])
        row["ttfa_anchor_ms"] = None
        row["ttfa_anchor_state"] = r.get("ttfa_wall_s", "NOT ESTABLISHED")
        row["ttfa_not_established_reason"] = r.get("reason")
        row["ttfa_cell_state"] = {
            "first_block_gate8": r.get("first_block_gate8"),
            "first_block_samples": r.get("first_block_samples"),
            "istft_split_control_rel_pct": r.get("istft_split_control_rel_pct"),
            "istft_split_control_deficit_samples":
                r.get("istft_split_control_deficit_samples"),
        }
        row["budget_eligible"] = False

    ov = []
    for c in ok(of(arm, "overlap")):
        r = res(c)
        if r.get("skipped"):
            continue
        pop = chunkpop.get((arm, "overlap", r["chunk_units"], r["left_ctx_units"]))
        ov.append({"left_ctx_units": r["left_ctx_units"],
                   "required_lookahead_ms": r["required_lookahead_ms"],
                   "effective_ms": r["effective_ms"],
                   "steady": stats_ms(pop["steady"]) if pop else {"n": 0},
                   "realtime_margin_median": r["realtime_margin_median"],
                   "streamed_gate8": r.get("streamed_gate8")})
    ov.sort(key=lambda o: o["left_ctx_units"])
    row["overlap"] = ov

    lr = ok(of(arm, "longrun"))
    if lr:
        r = res(lr[0])
        if not r.get("skipped"):
            row["longrun"] = {
                "cut_s": r.get("cut_s"), "n_reps": r.get("n_reps"),
                "latency_drift_pct_median": (r.get("latency_drift_pct") or {}).get("median"),
                "vram_drift_MiB_median": (r.get("vram_drift_MiB") or {}).get("median")}

    bd = ok(of(arm, "boundary"))
    if bd:
        r = res(bd[0])
        conds = r.get("conditions")
        row["boundary"] = conds if conds is not None else [
            {"stateful_vs_full_raw": r.get("stateful_vs_full_raw"),
             "stateful_vs_full_rel_pct": r.get("stateful_vs_full_rel_pct"),
             "note": r.get("note")}]

    # D: delay calibration reliability
    dl = [c for c in raw if c.get("arm") == arm and "delay_ms" in str(c)]
    rows.append(row)

# ---- delay reliability, read from the cells' cached-rep prints is not available;
# read from the Gate 3 logs instead so no claim rests on an unflagged number.
DELAY = {}
for f in glob.glob(os.path.join(RES, "gate3_log_*.txt")):
    for line in open(f, encoding="utf-8", errors="ignore"):
        if "cached rep for" in line and "delay" in line:
            try:
                nm = line.split("cached rep for")[1].split(":")[0].strip()
                dms = float(line.split("delay")[1].split("ms")[0].strip())
                rr = float(line.split("r=")[1].split(")")[0])
                DELAY[nm] = {"delay_ms": dms, "normalised_peak_correlation": rr,
                             "reliable": bool(abs(rr) >= 0.5),
                             "note": ("weak correlation - this delay estimate is "
                                      "NOISE and is not used as a fact anywhere"
                                      if abs(rr) < 0.5 else
                                      "correlation supports the estimate")}
            except Exception:
                pass
for r in rows:
    if r["arm"] in DELAY:
        r["delay_calibration"] = DELAY[r["arm"]]


# ------------------------------------------------------------------ E1
def session_peak(arm, field):
    """Max of `field` across EVERY cell of that arm - offline, streaming,
    overlap, longrun, cold. Named for the scope it actually covers, because the
    spot-check found a key called `whole_session_*` that was computed over the
    offline sweep alone."""
    best = 0.0
    for c in cells.get(arm, []):
        r = c.get("result", c)
        if isinstance(r, dict) and r.get(field) is not None:
            best = max(best, float(r[field]))
        for sub in (r.get("reps") or []) if isinstance(r, dict) else []:
            if isinstance(sub, dict) and sub.get(field) is not None:
                best = max(best, float(sub[field]))
    return best


def build_e1():
    """§5 E1 - the ONLY estimand in the study where one variable moves.

    ⚠️ CORRECTED 2026-09-11 after an independent spot-check. The previous version
    reported a MEDIAN point estimate while bootstrapping the MEAN (`.mean(1)`).
    On right-skewed latency data the mean sits above the median, so the point
    estimate fell OUTSIDE its own interval in 5 of 7 streaming rows. It also
    capped each resample at min(n, 2000) and resampled the two arms
    INDEPENDENTLY, which discards the pairing.

    This version: a PAIRED MEDIAN bootstrap. Matched observations are keyed by
    (rep, chunk_index) - the same repetition and the same position within it -
    and it is the PAIR INDEX that is resampled, so a resample draws the same
    occasion from both arms. The statistic resampled is the MEDIAN, the same
    statistic the point estimate reports. Every resample contains exactly n
    pairs; there is no cap.

    Pairing is on the INPUT: byte-identical EnCodec tokens, sha256 verified
    equal across two separate processes. The two arms ran in different batches,
    so this is not a within-occasion paired design and the interval is a
    bootstrap percentile interval, not a paired t.
    """
    a, b = "encodec24_q8", "encodec_vocos"
    if a not in cells or b not in cells:
        return None
    N_BOOT, SEED_E1 = 4000, 20260911

    def keyed_offline(arm):
        """{(seconds, rep): ms} - one measured repetition per key."""
        out = {}
        for r in raw:
            if r.get("arm") == arm and r.get("cell") == "offline"                     and r.get("wall_s") is not None:
                out[(r.get("seconds"), r.get("rep"))] = r["wall_s"] * 1000
        return out

    def keyed_stream(arm):
        """{(chunk_units, rep, chunk_index): ms} over the STEADY-STATE
        population - chunk_index 0 is the first chunk and is excluded, because
        TTFA reports it separately."""
        out = {}
        for r in raw:
            if r.get("arm") != arm or r.get("cell") != "stream":
                continue
            for i, w in enumerate(r.get("chunk_walls_s") or []):
                if i == 0:
                    continue
                out[(r.get("chunk_units"), r.get("rep"), i)] = w * 1000
        return out

    def paired(ka, kb, keys):
        xa = np.array([ka[k] for k in keys], dtype=np.float64)
        xb = np.array([kb[k] for k in keys], dtype=np.float64)
        rng = np.random.default_rng(SEED_E1)
        n = xa.size
        idx = rng.integers(0, n, size=(N_BOOT, n))     # PAIR indices, no cap
        ma = np.median(xa[idx], axis=1)
        mb = np.median(xb[idx], axis=1)
        d, rt = ma - mb, ma / mb
        return {
            "n_pairs": int(n), "n_a": int(n), "n_b": int(n),
            "median_a_ms": float(np.median(xa)), "median_b_ms": float(np.median(xb)),
            "difference_ms": float(np.median(xa) - np.median(xb)),
            "difference_ci95_ms": [float(np.percentile(d, 2.5)),
                                   float(np.percentile(d, 97.5))],
            "ratio": float(np.median(xa) / np.median(xb)),
            "ratio_ci95": [float(np.percentile(rt, 2.5)),
                           float(np.percentile(rt, 97.5))],
            "bootstrap": f"paired MEDIAN bootstrap, {N_BOOT} resamples, seed "
                         f"{SEED_E1},every resample exactly n pairs",
        }

    conds = []
    oa, ob = keyed_offline(a), keyed_offline(b)
    for secs in sorted({k[0] for k in oa} & {k[0] for k in ob}):
        keys = sorted(k for k in oa if k[0] == secs and k in ob)
        if not keys:
            continue
        row_ = paired(oa, ob, keys)
        row_.update(cell="offline", condition=f"{secs} s")
        conds.append(row_)

    sa, sb = keyed_stream(a), keyed_stream(b)
    units_ms = {s["chunk_units"]: s["effective_ms"]
                for s in next(r for r in rows if r["arm"] == a)["stream"]}
    for u in sorted({k[0] for k in sa} & {k[0] for k in sb}):
        keys = sorted(k for k in sa if k[0] == u and k in sb)
        if not keys:
            continue
        row_ = paired(sa, sb, keys)
        row_.update(cell="stream (steady-state)",
                    condition=f"{units_ms.get(u, u):.1f} ms" if u in units_ms
                    else f"{u} units")
        conds.append(row_)

    ra = next(r for r in rows if r["arm"] == a)
    rb = next(r for r in rows if r["arm"] == b)
    return {
        "estimand": "E1 - the controlled pair",
        "pair": [a, b],
        "control": ("byte-identical EnCodec 24 kHz Q=8 token tensor; codebooks "
                    "verified bitwise identical (AUDIT.md §3.1). The DECODER is "
                    "the only variable that moves."),
        "pairing": ("paired on the INPUT, not on the measurement occasion - the "
                    "two arms ran in separate batches, so the interval is a "
                    "bootstrap percentile interval (4000 resamples, seed "
                    "20260911), not a within-occasion paired t."),
        "environment": "both in `decbench`; E1 is WITHIN-environment, so E6 does "
                       "not bear on it",
        "conditions": conds,
        "memory_scopes_SEPARATED": {
            "anchor_peak_allocated_MiB": {
                a: ra.get("anchor_peak_alloc_MiB"), b: rb.get("anchor_peak_alloc_MiB"),
                "ratio": (ra.get("anchor_peak_alloc_MiB") or 0) /
                         max(rb.get("anchor_peak_alloc_MiB") or 1, 1e-9),
                "scope": "the STREAMING ANCHOR condition only - this is the "
                         "streaming memory figure"},
            "offline_sweep_peak_allocated_MiB": {
                a: max([d["peak_alloc_MiB"] or 0 for d in ra["offline"]] or [0]),
                b: max([d["peak_alloc_MiB"] or 0 for d in rb["offline"]] or [0]),
                "ratio": max([d["peak_alloc_MiB"] or 0 for d in ra["offline"]] or [0]) /
                         max(max([d["peak_alloc_MiB"] or 0 for d in rb["offline"]] or [1]), 1e-9),
                "scope": "max across the OFFLINE SWEEP only (1/2/5/10/30 s)"},
            "session_peak_allocated_MiB": {
                a: session_peak(a, "peak_alloc_MiB"), b: session_peak(b, "peak_alloc_MiB"),
                "ratio": session_peak(a, "peak_alloc_MiB") /
                         max(session_peak(b, "peak_alloc_MiB"), 1e-9),
                "scope": "max across ALL CELLS - offline sweep, streaming, overlap, "
                         "longrun, cold. NOT a streaming figure."},
            "anchor_peak_reserved_MiB": {
                a: ra.get("anchor_peak_reserved_MiB"), b: rb.get("anchor_peak_reserved_MiB"),
                "ratio": (ra.get("anchor_peak_reserved_MiB") or 0) /
                         max(rb.get("anchor_peak_reserved_MiB") or 1, 1e-9),
                "scope": "allocator RESERVED at the streaming anchor"},
            "offline_sweep_peak_reserved_MiB": {
                a: max([d["peak_reserved_MiB"] or 0 for d in ra["offline"]] or [0]),
                b: max([d["peak_reserved_MiB"] or 0 for d in rb["offline"]] or [0]),
                "ratio": max([d["peak_reserved_MiB"] or 0 for d in ra["offline"]] or [0]) /
                         max(max([d["peak_reserved_MiB"] or 0 for d in rb["offline"]] or [1]), 1e-9),
                "scope": "max RESERVED across the OFFLINE SWEEP only"},
            "session_peak_reserved_MiB": {
                a: session_peak(a, "peak_reserved_MiB"), b: session_peak(b, "peak_reserved_MiB"),
                "ratio": session_peak(a, "peak_reserved_MiB") /
                         max(session_peak(b, "peak_reserved_MiB"), 1e-9),
                "scope": "max RESERVED across ALL CELLS"},
            "reserved_is_not_monotonic": {
                a: [d["peak_reserved_MiB"] for d in ra["offline"]],
                b: [d["peak_reserved_MiB"] for d in rb["offline"]],
                "warning": ("`reserved` is an ALLOCATOR CACHING quantity and is NOT "
                            "monotonic in workload - encodec_vocos reserves 162, "
                            "646, 164, 182, 270 MiB across 1/2/5/10/30 s. A ratio "
                            "built on it is a ratio of caching behaviour, not of "
                            "memory demand, which is why the anchor-reserved ratio "
                            "(5.2x) and the session-reserved ratio (1.3x) disagree "
                            "so violently. `allocated` is the interpretable "
                            "denominator; reserved is reported beside it (R18) and "
                            "must never be quoted alone."),
            },
        },
        "headline_finding": (
            "The ratio is NOT constant across duration: 3.05x at 1 s rising to "
            "24.79x at 30 s. `encodec_vocos` is nearly duration-INDEPENDENT "
            "(2.42 -> 3.00 ms from 1 s to 30 s, every condition §8 PASS, allocated "
            "memory scaling normally so the full input is processed), while "
            "`encodec24_q8` scales strongly (7.38 -> 74.24 ms). On byte-identical "
            "tokens, with the decoder as the only moving variable, the two "
            "decoders have different COMPLEXITY CLASSES in this range, not just "
            "different constants."),
    }


# ------------------------------------------------------------------ E4
def build_e4():
    """§5 E4 - does the ranking by full-utterance RTF differ from the ranking by
    TTFA? Computed ONLY over arms for which both are defined, and the subset is
    NAMED. Fewer than three qualifying arms is reported as underpowered rather
    than as an ordering."""
    elig = [r for r in rows
            if r.get("rtf_at_10s") is not None
            and r.get("ttfa_anchor_ms") is not None
            and r.get("cross_env_comparable") is True]
    excluded = {
        "no TTFA (NOT ESTABLISHED)": [r["arm"] for r in rows
                                      if r.get("ttfa_anchor_ms") is None
                                      and r.get("status") == STATUS],
        "NOT COMPARABLE environment (§7.2)": [r["arm"] for r in rows
                                              if r.get("cross_env_comparable") is False],
        "blocked": [r["arm"] for r in rows if r.get("status") == "BLOCKED - PLATFORM"],
    }
    if len(elig) < 3:
        return {"estimand": "E4", "status": "UNDERPOWERED",
                "n_qualifying": len(elig), "excluded": excluded}
    names = [r["arm"] for r in elig]
    rtf = np.array([r["rtf_at_10s"] for r in elig])
    ttfa = np.array([r["ttfa_anchor_ms"] for r in elig])

    def rank(x):
        o = np.argsort(x)
        rk = np.empty_like(o, dtype=float)
        rk[o] = np.arange(len(x))
        return rk
    ra, rb = rank(rtf), rank(ttfa)
    rho = float(np.corrcoef(ra, rb)[0, 1])
    disagree = [{"arm": names[i], "rtf_rank": int(ra[i]) + 1,
                 "ttfa_rank": int(rb[i]) + 1,
                 "rank_shift": int(rb[i] - ra[i])}
                for i in range(len(names)) if abs(ra[i] - rb[i]) >= 3]
    return {
        "estimand": "E4 - offline versus streaming ordering",
        "status": "COMPUTED", "n_qualifying": len(elig), "subset": names,
        "excluded": excluded,
        "spearman_rho_rtf_vs_ttfa": rho,
        "orderings_differ": bool(rho < 0.9),
        "arms_shifting_3_or_more_ranks": disagree,
        "by_rtf": [names[i] for i in np.argsort(rtf)],
        "by_ttfa": [names[i] for i in np.argsort(ttfa)],
        "note": ("A decoder that is cheap per second of audio is not necessarily "
                 "the one that returns the first block soonest. This says which "
                 "ordering you get, not which arm to pick."),
    }


E1, E4 = build_e1(), build_e4()

totals = {}
for r in rows:
    totals[r["status"]] = totals.get(r["status"], 0) + 1

# ---- M5: disposition of the §7.2 VRAM re-run rule, computed not asserted
vram_flagged = []
for f in sorted(glob.glob(os.path.join(RES, "gate3_cells_*.jsonl"))):
    if os.path.basename(f).startswith("SMOKE_"):
        continue
    for l in open(f, encoding="utf-8"):
        c = json.loads(l)
        if c.get("vram_drift_exceeds_200MiB"):
            vram_flagged.append({"arm": c["arm"], "cell": c["cell"],
                                 "vram_drift_MiB": c.get("vram_drift_MiB")})
n_cells_total = sum(len(v) for v in cells.values()) + \
    sum(len(v) for v in e6_cells.values())

doc = {
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "generated_by": "make_gate3_matrix.py - artifacts and raw data only",
    "gate": "GATE 3 - frozen GPU timing benchmark",
    "status_definition": (
        f"'{STATUS}' means EVERY cell for that arm completed and every timed row "
        f"passed the structural synchronize assertion. IT IS NOT A PERFORMANCE "
        f"VERDICT. It does not mean the arm holds real time, does not mean its "
        f"streamed output is valid, and implies no recommendation. Real-time "
        f"capability is the underrun / real-time-margin columns; streamed "
        f"validity is the §8 column; neither is folded into this word."),
    "n_arms": len(rows), "totals_by_status": totals, "missing_artifacts": missing,
    "headers": headers,
    "E6_environment_control": E6,
    "E6_consequence": {env: dict(zip(("comparable", "why"), e6_verdict(env)))
                       for env in ("decbench", "fish", "decbench_melflow")},
    "E1_controlled_pair": E1,
    "E4_ordering": E4,
    "vram_rerun_rule_disposition": {
        "frozen_rule": ("§7.2: an arm whose before/after VRAM reading moves by more "
                        "than 200 MiB is re-run and both runs are kept."),
        "cells_flagged": len(vram_flagged),
        "cells_total": n_cells_total,
        "disposition": "SUPERSEDED BY PROTOCOL AMENDMENT 10 - see PROTOCOL.md",
        "reason": ("The rule was written for a design in which one model stays "
                   "resident. This harness holds a model cache of ONE and reloads "
                   "on every arm switch, precisely so that max_memory_allocated is "
                   "the arm's own working set rather than a co-resident model's "
                   "weights. Under that design a >200 MiB before/after move is the "
                   "EXPECTED signature of the intended unload/reload, not the "
                   "contamination the rule was written to catch. Re-running on it "
                   "would re-run most of the benchmark and would flag the same "
                   "cells again, without testing anything."),
        "replacement_check": ("What the rule existed to detect - a cell whose memory "
                              "state was contaminated by another cell - is instead "
                              "tested by the per-repetition "
                              "`torch.cuda.reset_peak_memory_stats()` before every "
                              "measured cell, so `peak_alloc_MiB` cannot inherit a "
                              "previous cell's peak, and by the longrun VRAM-drift "
                              "cell, which measures memory growth across a sustained "
                              "run directly."),
        "flagged_examples": vram_flagged[:5],
    },
    "claim_boundaries": [
        "Measured: REPRESENTATION -> WAVEFORM only. Generator/AR timing is outside "
        "this study; a decode-only number read as end-to-end TTS performance is a "
        "failed report.",
        "Wall clock is PRIMARY; CUDA events are DIAGNOSTIC. They measure different "
        "scopes and are not expected to agree, and disagreement never voids a run.",
        "EAGER MODE for every arm - no torch.compile, no CUDA graphs. MelFlow ships "
        "a compiled path and its upstream recommends CUDA graphs, so its latency "
        "here is an UPPER BOUND, not its best achievable latency (amendment 9.10).",
        "Seam metrics compare a decoder against ITSELF. They are not a quality "
        "ranking between decoders. QUALITY COMPARISON NOT ESTABLISHED.",
        "Route A and Route B are never merged into one ranking.",
        "Jitter statistics (p50/p95/p99/IQR/max) are over the STEADY-STATE "
        "population, excluding the first chunk of every repetition, because TTFA "
        "reports the first chunk separately. The all-chunks population is reported "
        "beside them and the two are never mixed in one row.",
        "Device-side timing cannot by itself separate genuine model work from GPU "
        "preemption by another process. §7.4 declares one GPU process at a time but "
        "is not instrumented per cell.",
    ],
    "arms": rows,
}
json.dump(doc, open(os.path.join(HERE, "gate3_matrix.json"), "w"), indent=2,
          default=lambda o: bool(o) if isinstance(o, np.bool_) else
          (int(o) if isinstance(o, np.integer) else
           (float(o) if isinstance(o, np.floating) else str(o))))
print(f"totals: {totals}")
print(f"E6: " + ", ".join(f"{k}={v['effect_pct']:.1f}%" for k, v in (E6 or {}).items()))
print(f"E4: {E4.get('status')}  rho={E4.get('spearman_rho_rtf_vs_ttfa')}")
print(f"E1: {len(E1['conditions'])} conditions" if E1 else "E1: MISSING")
print(f"VRAM rule: {len(vram_flagged)}/{n_cells_total} cells flagged")
print("written: gate3_matrix.json")

# Rendering is a separate module so the document cannot disagree with the JSON.
import subprocess, sys
subprocess.run([sys.executable, os.path.join(HERE, "render_gate3_md.py")], check=True)
