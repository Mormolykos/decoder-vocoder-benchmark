r"""Q5 STEPS 1 and 3 — INSTRUMENT VALIDATION. No reconstruction is opened here.

  --f1   SECTION 9.1 metric mechanics, on the 126 calibration recordings only.
         Records the shift and scale responses; gates nothing that needs a
         corpus statistic. Hard failures REMOVE an encoder.
  --f2   SECTION 9.3 calibrated tier gates. Requires Q5_CALIBRATION.json, which
         step 2 writes. Demotes an encoder to DETECTOR when its 1-sample or
         scale response exceeds 0.10 x G(e).

  --child  internal: one fresh-process embedding, for the cold-start probe.

Both write into Q5_FUZZ.json under "F1" / "F2". Never runs the two out of order:
--f2 refuses without an F1 section, and refuses without the calibration file.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

import q5_lib as Q

OUT = os.path.join(Q.HERE, "Q5_FUZZ.json")
CAL = os.path.join(Q.HERE, "Q5_CALIBRATION.json")
CACHE = os.path.join(Q.HERE, "Q5_EMBEDDINGS.npz")


def load_doc():
    return json.load(open(OUT, encoding="utf-8")) if os.path.isfile(OUT) else {}


def save_doc(d):
    json.dump(d, open(OUT, "w"), indent=1)


def probe_files(cells):
    """The 126 calibration recordings. SECTION 9.1."""
    out = []
    for c in cells["calibration"]:
        p = Q.source_path(c)
        if os.path.isfile(p):
            out.append((c, p))
    return out


def shift(x: np.ndarray, k: int) -> np.ndarray:
    """A delay of k samples: prepend zeros, keep the signal itself intact."""
    return np.concatenate([np.zeros(k, dtype=x.dtype), x])


def bandlimit(x: np.ndarray, hz: int) -> np.ndarray:
    import torch
    t = torch.from_numpy(x).float().unsqueeze(0)
    down = Q._resample(t, Q.SR, hz * 2)
    up = Q._resample(down, hz * 2, Q.SR)
    return up.squeeze(0).numpy()


def f1(panel_names, cells, rev):
    """SECTION 9.1, with SECTION 9.1's pre-declared single device retry."""
    res = {}
    files = probe_files(cells)
    usable = [(c, p) for c, p in files if float(c["duration_s"]) >= Q.MIN_DUR_S]
    print("F1: %d calibration recordings, %d at or above %.2f s"
          % (len(files), len(usable), Q.MIN_DUR_S))
    import torch
    default_dev = "cuda" if torch.cuda.is_available() else "cpu"

    for name in panel_names:
        r = probe_encoder(name, default_dev, usable)
        if not r["probes"]["cold_start"]["pass"] and default_dev != "cpu":
            # ⭐ SECTION 9.1: exactly ONE retry, on CPU, deterministic, 1 thread.
            print("  %-22s cold start failed on %s (max_abs_err=%s) -> the "
                  "pre-declared CPU retry"
                  % (name, default_dev,
                     r["probes"]["cold_start"].get("max_abs_err")))
            torch.set_num_threads(1)
            r2 = probe_encoder(name, "cpu", usable)
            r2["retry"] = {"first_device": default_dev,
                           "first_cold_start": r["probes"]["cold_start"],
                           "rule": "SECTION 9.1 device rule: one retry on CPU "
                                   "with deterministic algorithms and one thread"}
            r = r2 if r2["probes"]["cold_start"]["pass"] else {
                **r2, "verdict": "REMOVED",
                "hard_failures": sorted(set(r2["hard_failures"]) | {"cold_start"}),
                "retry": {**r2["retry"],
                          "outcome": "NEITHER DEVICE PASSED - REMOVED"}}
        res[name] = r
        p = r["probes"]
        print("  %-22s %-8s device=%-4s identity_cos_min=%s max_abs_err=%s "
              "cold=%s shift1=%s"
              % (name, r["verdict"], r["device_declared"],
                 None if p["identity"]["cos_min"] is None
                 else round(p["identity"]["cos_min"], 9),
                 p["identity"]["max_abs_err_max"],
                 "PASS" if p["cold_start"]["pass"] else "FAIL",
                 None if r["recorded"]["shift1"] is None
                 else round(r["recorded"]["shift1"], 6)))
    d = load_doc()
    d["spec"] = rev
    d["determinism"] = Q.DETERMINISM
    d["F1"] = {"what": "SECTION 9.1 metric mechanics. Calibration recordings only; "
                       "no reconstruction opened.",
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "reconstructions_opened": False,
               "encoders": res}
    save_doc(d)
    return res


def probe_encoder(name, device, usable):
        enc = Q.Enc(name, device)
        t0 = time.time()
        r = {"device_declared": enc.device, "probes": {}, "verdict": "OK",
             "n_probe_files": len(usable), "encoder_meta": enc.meta()}
        idc, idm = [], []
        s1, s4, s16, s256 = [], [], [], []
        sc05, sc20 = [], []
        b8, b4 = [], []
        for c, p in usable:
            x, st, dur = Q.load16(p)
            if st != Q.MEASURED:
                continue
            a = enc.embed_signal(x)
            b = enc.embed_signal(x)
            idc.append(Q.cos(a, b))
            idm.append(float(np.max(np.abs(a.astype(np.float64)
                                           - b.astype(np.float64)))))
            for k, acc in ((1, s1), (4, s4), (16, s16), (256, s256)):
                acc.append(1.0 - Q.cos(a, enc.embed_signal(shift(x, k))))
            sc05.append(1.0 - Q.cos(a, enc.embed_signal(x * 0.5)))
            sc20.append(1.0 - Q.cos(a, enc.embed_signal(x * 2.0)))
            b8.append(1.0 - Q.cos(a, enc.embed_signal(bandlimit(x, 8000))))
            b4.append(1.0 - Q.cos(a, enc.embed_signal(bandlimit(x, 4000))))

        def med(v):
            return float(np.median(v)) if v else None

        r["probes"]["identity"] = {
            "required": "cos == 1.0 (atol 1e-6) and max_abs_err == 0.0 exactly",
            "cos_median": med(idc), "cos_min": (min(idc) if idc else None),
            "max_abs_err_max": (max(idm) if idm else None),
            "pass": bool(idc) and abs(1.0 - min(idc)) <= 1e-6 and max(idm) == 0.0}

        # ---- NaN / inf, all-zero, truncation: state machine, not the model
        probe_x, _, _ = Q.load16(usable[0][1])
        tmp = os.path.join(Q.HERE, "_q5_probe_tmp.wav")
        import soundfile as sf

        def state_of(sig):
            sf.write(tmp, sig, Q.SR, subtype="FLOAT")
            _, st, _ = Q.load16(tmp)
            return st

        nan_state = state_of(np.concatenate([probe_x[:Q.SR], np.array([np.nan],
                                                                     np.float32),
                                             probe_x[Q.SR:]]).astype(np.float32))
        zero_state = state_of(np.zeros(int(Q.SR * 3), dtype=np.float32))
        trunc_state = state_of(probe_x[:int(Q.SR * 1.99)])
        os.remove(tmp)
        r["probes"]["nan_inf"] = {"required": Q.UNKNOWN, "got": nan_state,
                                  "pass": nan_state == Q.UNKNOWN}
        r["probes"]["all_zero"] = {"required": Q.UNKNOWN, "got": zero_state,
                                   "pass": zero_state == Q.UNKNOWN}
        r["probes"]["truncated_1p99s"] = {"required": Q.INADMISSIBLE,
                                          "got": trunc_state,
                                          "pass": trunc_state == Q.INADMISSIBLE}
        # ---- cold start: a genuinely fresh process
        c0, p0 = usable[0]
        child = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--child", enc.name, p0,
             enc.device],
            capture_output=True, text=True, cwd=Q.HERE)
        cold = None
        if child.returncode == 0:
            try:
                cold = np.array(json.loads(child.stdout.strip().splitlines()[-1]),
                                dtype=np.float32)
            except Exception:
                cold = None
        x0, _, _ = Q.load16(p0)
        warm = enc.embed_signal(x0)
        if cold is None:
            r["probes"]["cold_start"] = {"required": "max_abs_err == 0.0 exactly",
                                         "got": "CHILD FAILED",
                                         "stderr": child.stderr[-400:],
                                         "pass": False}
        else:
            e = float(np.max(np.abs(cold.astype(np.float64) - warm.astype(np.float64))))
            r["probes"]["cold_start"] = {"required": "max_abs_err == 0.0 exactly",
                                         "max_abs_err": e, "pass": e == 0.0}
        # ---- recorded, gated later in F2
        r["recorded"] = {
            "shift1": med(s1), "shift4": med(s4), "shift16": med(s16),
            "shift256": med(s256), "scale_0p5": med(sc05), "scale_2p0": med(sc20),
            "bandlimit_8k": med(b8), "bandlimit_4k": med(b4),
            "note": "1 - cos, median over probe recordings. shift = k-sample delay."}
        hard = [k for k, v in r["probes"].items() if not v["pass"]]
        r["hard_failures"] = hard
        r["verdict"] = "OK" if not hard else "REMOVED"
        r["seconds"] = round(time.time() - t0, 1)
        return r


def f2(rev):
    d = load_doc()
    if "F1" not in d:
        print("REFUSED: no F1 section. SECTION 9.0 fixes the order: F1, then "
              "calibration, then F2.")
        return 2
    if not os.path.isfile(CAL):
        print("REFUSED: %s does not exist. F2 consumes the source-measured "
              "ranges that step 2 produces." % os.path.basename(CAL))
        return 2
    cal = json.load(open(CAL, encoding="utf-8"))
    res = {}
    for name, r in d["F1"]["encoders"].items():
        G = cal["calibration"][name]["G"]
        rec = r["recorded"]
        out = {"G": G, "bound": None if G is None else Q.TIER_FRACTION * G,
               "tier_fraction": Q.TIER_FRACTION, "gates": {}}
        if r["verdict"] == "REMOVED":
            out["verdict"] = "REMOVED"
            out["reason"] = "SECTION 9.1 hard failure: %s" % ", ".join(r["hard_failures"])
            res[name] = out
            continue
        if G is None:
            out["verdict"] = "NOT ESTABLISHED"
            out["reason"] = "G(e) could not be computed from calibration"
            res[name] = out
            continue
        bound = Q.TIER_FRACTION * G
        tier = {"rule": "shift1 > 0.10 x G(e)", "shift1": rec["shift1"],
                "bound": bound, "demote": bool(rec["shift1"] > bound)}
        scale_resp = max(rec["scale_0p5"], rec["scale_2p0"])
        sc = {"rule": "max(scale response) > 0.10 x G(e)",
              "scale_response": scale_resp, "bound": bound,
              "demote": bool(scale_resp > bound)}
        out["gates"] = {"tier_test": tier, "scale_invariance": sc}
        demoted = [k for k, v in out["gates"].items() if v["demote"]]
        out["verdict"] = "DEMOTED TO DETECTOR" if demoted else "OK"
        out["reason"] = ("SECTION 9.3 %s exceeded 0.10 x G" % ", ".join(demoted)
                        ) if demoted else "both SECTION 9.3 gates inside 0.10 x G"
        res[name] = out
        print("  %-22s %-20s shift1=%.3g scale=%.3g bound=%.3g (G=%.4f)"
              % (name, out["verdict"], rec["shift1"], scale_resp, bound, G))
    # SECTION 9.2 separability, carried forward from calibration
    sep = {}
    for name in d["F1"]["encoders"]:
        blk = cal["calibration"][name]["sets"]
        sep[name] = {S: {st: (v.get("gate") or {}).get("pass")
                         for st, v in blk[S]["states"].items()}
                     for S in blk}
    d["F2"] = {"what": "SECTION 9.3 calibrated tier gates + SECTION 9.2 "
                       "separability, carried from Q5_CALIBRATION.json.",
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "reconstructions_opened": False,
               "encoders": res, "separability": sep,
               "spec": rev}
    save_doc(d)
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        name, path = sys.argv[2], sys.argv[3]
        dev = sys.argv[4] if len(sys.argv) > 4 else (
            "cuda" if __import__("torch").cuda.is_available() else "cpu")
        if dev == "cpu":
            __import__("torch").set_num_threads(1)
        enc = Q.Enc(name, dev)
        x, st, _ = Q.load16(path)
        print(json.dumps(enc.embed_signal(x).tolist()))
        return 0
    ap = argparse.ArgumentParser()
    ap.add_argument("--f1", action="store_true")
    ap.add_argument("--f2", action="store_true")
    a = ap.parse_args()
    rev = Q.spec_revision()
    if a.f1:
        f1(Q.ENCODERS, Q.corpus()["cells"], rev)
        return 0
    if a.f2:
        return f2(rev)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
