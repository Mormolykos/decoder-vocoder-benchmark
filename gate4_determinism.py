r"""GATE 4 §7.2 — THE DETERMINISM GATE. The omission found by the Stage 2
results audit, run now, exactly as the frozen pre-registration specifies.

⛔ THIS ADDS NO NEW METRIC AND CHANGES NO FROZEN FILE. It runs a gate
`GATE4_PREREG.md` §7.2 already mandates and §11.1 condition 4 already requires,
and which `gate4_run.py` never performed.

    "Before any quality cell runs for an arm, that arm decodes the same
     representation twice and the two outputs are compared with
     `gate_lib.err()`. The arm proceeds only if `max_abs_err == 0.0` exactly,
     or the arm declares a seeded stochastic stage whose seed is pinned and
     whose repeat error is then required to be `0.0` under that pin."
     A non-zero residual is a recorded `DETERMINISM NOT ESTABLISHED` row, and
     that arm produces no quality number until it is resolved.

THE DECODE PATH IS NOT REWRITTEN. This module imports `gate4_run` and calls the
same `build_arm()` / `arm.encode()` / `arm.decode()` the Stage 1 study used, so a
PASS here is a statement about the path that actually produced the waveforms.

⚠️ ONE DECLARED DEVIATION, IN THE CONSERVATIVE DIRECTION. §7.2 requires ONE
representation decoded twice. This probes `N_PROBES` representations spanning
declared states and takes the WORST residual as the verdict. More probes can
only turn a PASS into a FAIL; they can never manufacture a PASS. The per-probe
residuals are all recorded, so the single-probe verdict is recoverable.

    <decbench>/python.exe gate4_determinism.py --env decbench
    <fish>/python.exe     gate4_determinism.py --env fish

⛔ ONE GPU PROCESS AT A TIME (§7.4).
"""
import argparse
import json
import os
import sys
import time
import traceback

import numpy as np
import soundfile as sf
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gate_lib as GL            # noqa: E402  frozen: err()
import gate4_lib as G4           # noqa: E402  frozen: the one resampler
import gate4_run as R1           # noqa: E402  frozen: the Stage 1 decode path

#: Declared BEFORE the run. Deterministic: the first cell of each state, in the
#: frozen corpus order produced by `gate4_run.cells()`. Quiet and loud extremes
#: plus the neutral reference.
PROBE_STATES = ("Neutral", "Whisper", "Shouting")
N_PROBES = len(PROBE_STATES)

PASS = "DETERMINISM PASS"
FAIL = "DETERMINISM NOT ESTABLISHED"


def probe_cells(C):
    """The first cell of each declared state, in frozen corpus order."""
    seen, out = set(), []
    for c in R1.cells(C):
        if c["state"] in PROBE_STATES and c["state"] not in seen:
            seen.add(c["state"])
            out.append(c)
        if len(out) == N_PROBES:
            break
    return out


def load_source(cell, sr_in):
    src, sr0 = sf.read(R1.source_path(cell), dtype="float64", always_2d=True)
    src = src.mean(axis=1)
    if cell["rung_s"]:
        src = src[:int(round(cell["rung_s"] * sr0))]
    x, prov = G4.resample(src, sr0, sr_in)
    return x, prov


def run_arm(arm_name, C, g2, g3, dev, manifest):
    """One arm. Every outcome is a RECORDED ROW (§12)."""
    def record(row):
        row["arm"] = arm_name
        row["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        manifest.write(json.dumps(row) + "\n")
        manifest.flush()
        return row

    m3 = g3.get(arm_name)
    if m3 is None or str(m3.get("status", "")).startswith("BLOCKED"):
        return record({"verdict": "BLOCKED - PLATFORM",
                       "note": "released tooling not runnable here; the "
                               "determinism gate is not applicable and no "
                               "number is manufactured"})
    if arm_name in R1.NO_ADAPTER:
        lab, why = R1.NO_ADAPTER[arm_name]
        return record({"verdict": lab, "note": why})

    arm = R1.build_arm(arm_name)
    if arm is None:
        return record({"verdict": "NOT ADMISSIBLE - NO ADAPTER IN THIS "
                                  "ENVIRONMENT",
                       "note": "build_arm() found no frozen adapter here"})

    try:
        arm.load(dev)
    except Exception as e:
        return record({"verdict": FAIL, "note": "adapter failed to load: %s" % e,
                       "traceback": traceback.format_exc()[-1200:]})

    sr_in = int(getattr(arm, "sr_in", g2[arm_name]["sr_out"]))
    probes, worst = [], 0.0
    try:
        for cell in probe_cells(C):
            x, prov = load_source(cell, sr_in)
            wav = torch.from_numpy(np.ascontiguousarray(x)).float()
            wav = wav.reshape(1, -1).to(dev)

            # ⭐ ENCODE ONCE. §7.2 is about decoding THE SAME REPRESENTATION
            # twice, so the representation must not be recomputed between the
            # two decodes.
            rep = arm.encode(wav)

            a = arm.decode(rep).detach().float().cpu().reshape(-1)
            b = arm.decode(rep).detach().float().cpu().reshape(-1)

            raw, rel = GL.err(a, b)
            worst = max(worst, float(raw))
            probes.append({
                "speaker": cell["speaker"], "state": cell["state"],
                "index": cell["index"], "rung_s": cell["rung_s"],
                "source_file": cell["file"], "sr_in": sr_in,
                "resampler": prov,
                "samples_a": int(a.numel()), "samples_b": int(b.numel()),
                "length_equal": bool(a.numel() == b.numel()),
                "max_abs_err": float(raw),
                "rel_pct": 100.0 * float(rel),
                "exactly_zero": bool(float(raw) == 0.0),
            })
    except Exception as e:
        return record({"verdict": FAIL, "probes": probes,
                       "note": "decode raised during the probe: %s" % e,
                       "traceback": traceback.format_exc()[-1200:]})

    all_zero = bool(probes) and all(p["exactly_zero"] for p in probes)
    same_len = all(p["length_equal"] for p in probes)
    return record({
        "verdict": PASS if (all_zero and same_len) else FAIL,
        "n_probes": len(probes),
        "probe_states": list(PROBE_STATES),
        "worst_max_abs_err": worst,
        "rule": "PASS requires max_abs_err == 0.0 EXACTLY on every probe "
                "(GATE4_PREREG.md 7.2). No tolerance is introduced.",
        "seeded_stochastic_stage_declared": bool(
            getattr(arm, "seeded_stochastic_stage", False)),
        "probes": probes,
    })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--arms", default="")
    a = ap.parse_args()

    C, g2, g3 = R1.frozen()
    arms = [x for x in a.arms.split(",") if x] or R1.ENV_ARMS.get(a.env, [])
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    out = os.path.join(HERE, "results", "gate4_determinism_%s.jsonl" % a.env)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    print("GATE 4 SECTION 7.2 DETERMINISM GATE  env=%s device=%s arms=%d "
          "probes/arm=%d" % (a.env, dev, len(arms), N_PROBES), flush=True)
    npass = nfail = nother = 0
    with open(out, "w") as mf:
        for name in arms:
            t0 = time.time()
            row = run_arm(name, C, g2, g3, dev, mf)
            v = row["verdict"]
            if v == PASS:
                npass += 1
            elif v == FAIL:
                nfail += 1
            else:
                nother += 1
            print("  %-28s %-34s worst=%s  %.1fs"
                  % (name, v,
                     ("%.6e" % row["worst_max_abs_err"])
                     if "worst_max_abs_err" in row else "-",
                     time.time() - t0), flush=True)
    print("\nPASS=%d  NOT ESTABLISHED=%d  not applicable=%d  manifest=%s"
          % (npass, nfail, nother, out), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
