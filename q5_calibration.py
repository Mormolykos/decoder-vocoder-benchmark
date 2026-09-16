r"""Q5 STEP 2 — SOURCE-ONLY CALIBRATION. No reconstruction is opened here.

SECTION 5.4.1 of GATE4_PREREG.md: "the calibration control is mandatory and is
computed on the SOURCE audio alone, before any decoded audio is scored". This
script is the whole of that control, plus the SECTION 9.2 separability gate and
G(e) for SECTION 9.3.

Produces, per encoder, per set (S, L):

  C_within(state)   median cosine between two DIFFERENT source recordings of the
                    same speaker in the same state         -> the ceiling
  C_cross           same speaker, DIFFERENT states                 -> cross ceiling
  F_src(state)      different speakers, same state                 -> the floor
  F_hi(state)       95th percentile of F_src, a point value, NOT bootstrapped
  gate(state)       C_within.lo > F_hi  -> else NOT COMPETENT ON THIS MATERIAL
  G(e)              median over Set S states of (C_within.median - F_hi)

Refuses to overwrite an existing Q5_CALIBRATION.json without --force.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

import q5_lib as Q

OUT = os.path.join(Q.HERE, "Q5_CALIBRATION.json")
CACHE = os.path.join(Q.HERE, "Q5_EMBEDDINGS.npz")


def embed_source(panel, cache, cells, verify_sha=True, progress=200):
    """Embed every source recording once per encoder. Returns items + counts."""
    items = {}                     # (set, key) -> dict
    counts = {"MEASURED": 0, Q.INADMISSIBLE: 0, Q.UNKNOWN: 0,
              Q.NOT_MEASURED: 0, Q.SHA_MISMATCH: 0}
    t0 = time.time()
    n = 0
    for setname in ("set_S", "set_L"):
        for cell in cells[setname]:
            n += 1
            p = Q.source_path(cell)
            state_all = Q.MEASURED
            sha = None
            if not os.path.isfile(p):
                state_all = Q.NOT_MEASURED
            else:
                sha = Q.sha256_file(p)
                if verify_sha and cell.get("sha256") and sha != cell["sha256"]:
                    state_all = Q.SHA_MISMATCH
            x = None
            dur = 0.0
            # SECTION 3 (revision 4): the calibration signal must be the signal the
            # measurement compares. Set L cells are 14 s top-rung decodes, so the
            # Set L ceiling and floor are computed on 14 s source prefixes. Set S
            # is untouched.
            variant = "full" if setname == "set_S" else "pre14s"
            if state_all == Q.MEASURED:
                x, st, dur = Q.load16(p)
                state_all = st
                if st == Q.MEASURED and variant != "full":
                    x = x[:int(round(14.0 * Q.SR))]
                    dur = len(x) / Q.SR
                    if dur < Q.MIN_DUR_S:
                        x, state_all = None, Q.INADMISSIBLE
            counts[state_all if state_all in counts else Q.UNKNOWN] += 1
            rec = {"set": "S" if setname == "set_S" else "L",
                   "speaker": cell["speaker"], "state": cell["state"],
                   "index": int(cell["index"]), "dur_s": dur,
                   "state_flag": state_all, "sha256": sha,
                   "device": {n: e.device for n, e in panel.items()},
                   "variant": variant, "emb": {}}
            if state_all == Q.MEASURED:
                for name, enc in panel.items():
                    k = cache.key(sha, enc, variant)
                    v = cache.get(k)
                    if v is None:
                        v = enc.embed_signal(x)
                        cache.put(k, v)
                    rec["emb"][name] = v
            items[(rec["set"], rec["speaker"], rec["state"], rec["index"])] = rec
            if progress and n % progress == 0:
                print("    source %d  (%.0fs)" % (n, time.time() - t0), flush=True)
    return items, counts


def _matrix(vecs):
    A = np.stack(vecs).astype(np.float64)
    return A @ A.T


def calibrate(items, encoder_names):
    out = {}
    for e in encoder_names:
        out[e] = {"sets": {}}
        for S in ("S", "L"):
            states = Q.STATES_S if S == "S" else Q.STATES_L
            blk = {"states": {}, "cross": None}
            # ---------------------------------------------- per state
            for st in states:
                sel = [r for r in items.values()
                       if r["set"] == S and r["state"] == st
                       and r["state_flag"] == Q.MEASURED and e in r["emb"]]
                if len(sel) < Q.MIN_RECORDINGS:
                    blk["states"][st] = {"refused": "TOO FEW ADMISSIBLE SOURCE "
                                                    "RECORDINGS (%d)" % len(sel)}
                    continue
                M = _matrix([r["emb"][e] for r in sel])
                spk = np.array([r["speaker"] for r in sel])
                txt = np.array([r["index"] for r in sel])
                recs = [(r["speaker"], r["state"], r["index"]) for r in sel]
                grp = [(r["speaker"], r["state"]) for r in sel]
                same_spk = spk[:, None] == spk[None, :]
                # SECTION 3 rule 4, revision 6: "Pairs cross texts, so no pair
                # shares a script line" binds EVERY pairing quantity - the
                # reference as much as the estimator (SECTION 8.2: identical
                # pairing rules). Within one state this constraint is already
                # implied, since one speaker holds one recording per index; it
                # is written out so the rule cannot be lost again.
                diff_txt = txt[:, None] != txt[None, :]
                # C_within: same speaker, different recording
                Cw = Q.boot_pair_median(M, recs, grp, (same_spk & diff_txt).copy())
                # F_src: different speakers, same state. Percentile, not bootstrapped.
                imp = np.triu(~same_spk & diff_txt, 1)
                gi, gj = np.nonzero(imp)
                fv = M[gi, gj]
                nspk = len(set(spk.tolist()))
                if nspk < Q.MIN_SPEAKERS_FOR_FLOOR or fv.size == 0:
                    F = {"refused": "FEWER THAN %d SPEAKERS"
                                    % Q.MIN_SPEAKERS_FOR_FLOOR}
                else:
                    F = {"n_pairs": int(fv.size), "n_speakers": nspk,
                         "median": float(np.median(fv)),
                         "p95": float(np.percentile(fv, 95)),
                         "max": float(fv.max())}
                gate = None
                if "lo" in Cw and "p95" in F:
                    gate = {"rule": "C_within.lo > F_hi",
                            "C_within_lo": Cw["lo"], "F_hi": F["p95"],
                            "pass": bool(Cw["lo"] > F["p95"])}
                blk["states"][st] = {"C_within": Cw, "F_src": F, "gate": gate}
            # ---------------------------------------------- cross-state
            sel = [r for r in items.values()
                   if r["set"] == S and r["state_flag"] == Q.MEASURED
                   and e in r["emb"]]
            if len(sel) >= Q.MIN_RECORDINGS:
                M = _matrix([r["emb"][e] for r in sel])
                spk = np.array([r["speaker"] for r in sel])
                stt = np.array([r["state"] for r in sel])
                txt = np.array([r["index"] for r in sel])
                recs = [(r["speaker"], r["state"], r["index"]) for r in sel]
                grp = [(r["speaker"], r["state"]) for r in sel]
                # ⛔ REVISION 6 - THE DEFECT AN INDEPENDENT AUDIT FOUND.
                # Revision 5 omitted the different-text constraint here while
                # q5_analyze.py applied it to the D this C is compared against,
                # so the ceiling admitted the SAME SCRIPT LINE spoken in two
                # states - the most similar cross-state pair that exists in a
                # parallel corpus - and was inflated toward DRIFTING.
                # Excess: 7 speakers x 15 state-pairs x 31 texts = 3,255 (Set S)
                # and 7 x 1 x 15 = 105 (Set L). Eight CROSS labels turned on it.
                ok = ((spk[:, None] == spk[None, :])
                      & (stt[:, None] != stt[None, :])
                      & (txt[:, None] != txt[None, :]))
                blk["cross"] = {
                    "C_cross": Q.boot_pair_median(M, recs, grp, ok),
                    "n_pairs_admitted": int(np.triu(ok, 1).sum()),
                    "pairing_rule": "same speaker; different state; DIFFERENT "
                                    "TEXT (SECTION 3 rule 4). Must equal the "
                                    "pair count q5_analyze.py forms for D_cross."}
            out[e]["sets"][S] = blk
        # ------------------------------------------------------- G(e), SECTION 9.3
        gs = []
        for st, v in out[e]["sets"]["S"]["states"].items():
            if isinstance(v, dict) and v.get("C_within", {}).get("median") is not None \
                    and v.get("F_src", {}).get("p95") is not None:
                gs.append(v["C_within"]["median"] - v["F_src"]["p95"])
        out[e]["G"] = float(np.median(gs)) if gs else None
        out[e]["G_terms"] = gs
        out[e]["G_definition"] = ("median over Set S states of "
                                  "(C_within.median - F_hi); SECTION 9.3")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-verify-sha", action="store_true")
    a = ap.parse_args()
    if os.path.exists(OUT) and not a.force:
        print("REFUSED: %s exists. --force to recompute." % os.path.basename(OUT))
        return 2

    rev = Q.spec_revision()
    print("Q5_SPEC.md %s (revision %d), frozen %s"
          % (rev["spec_sha256"][:16], rev["revisions"], rev["spec_frozen_utc"]))
    panel = Q.build_panel()
    cache = Q.Cache(CACHE, rev["spec_sha256"])
    C = Q.corpus()
    cells = C["cells"]
    print("SOURCE ONLY. %d Set S + %d Set L recordings, %d encoders."
          % (len(cells["set_S"]), len(cells["set_L"]), len(panel)))

    items, counts = embed_source(panel, cache, cells,
                                 verify_sha=not a.no_verify_sha)
    cache.save()
    print("admissibility:", json.dumps(counts))

    cal = calibrate(items, list(panel))
    doc = {
        "what": "Q5 SECTION 3 calibration: human within-speaker ceiling and "
                "between-speaker floor, SOURCE AUDIO ONLY. Plus the SECTION 9.2 "
                "separability gate and G(e) for SECTION 9.3.",
        "spec": rev,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": Q.SRC_ROOT,
        "resampler": {"params": Q.RESAMPLE,
                      "gate4_lib_sha256": Q._RS["gate4_lib_sha256"]},
        "min_duration_s": Q.MIN_DUR_S,
        "calibration_signal": {
            "S": "full source recording (2.54-13.50 s), as Set S cells measure",
            "L": "the first 14.0 s of each source recording (variant pre14s), "
                 "because Gate 4's Set L cells are 14 s top-rung decodes. "
                 "Revision 4 correction; revision 3 used full length and was "
                 "inflated by +0.020 to +0.055 cosine."},
        "F_rec": "NOT COMPUTED / UNUSED BY LABELS. SECTION 3 lists it as a "
                 "descriptor (between-speaker similarity among RECONSTRUCTIONS). "
                 "It was never implemented, no label or gate depends on it, and "
                 "it is declared absent here rather than invented to match prose.",
        "reconstructions_opened": False,
        "panel": {n: e.meta() for n, e in panel.items()},
        "source_counts": counts,
        "calibration": cal,
    }
    json.dump(doc, open(OUT, "w"), indent=1)
    print("\nwrote %s" % os.path.basename(OUT))
    for e in cal:
        print("  %-22s G=%s" % (e, None if cal[e]["G"] is None
                                else round(cal[e]["G"], 4)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
