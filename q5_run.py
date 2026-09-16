r"""Q5 STEPS 4 and 5 — the per-cell pass over the EXISTING Gate 4 WAVs.

Nothing here regenerates, copies, moves or deletes audio. Every file is opened
read-only, and the only thing written is embeddings plus one JSONL row per
(cell x encoder).

REFUSES TO START unless SECTION 9.0's order has been honoured:
  * Q5_FUZZ.json has BOTH an F1 and an F2 section
  * Q5_CALIBRATION.json exists
  * per encoder: not REMOVED by F1 (a DEMOTED encoder still runs - it is
    reported, it simply assigns no label in SECTION 8)

Cell enumeration comes from each arm's own Stage 2 rows, so Q5 measures exactly
the cells Gate 4 measured and cannot silently drift from them. Stage 2 is read,
never written.

  --condition offline|streamed   default offline (step 4). streamed is step 5.
  --arm NAME                     one arm; default every arm present on disk
  --limit N                      smoke limit, recorded in the row as non-study
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import time

import numpy as np

import q5_lib as Q

CELLS = os.path.join(Q.HERE, "Q5_CELLS.jsonl")
CACHE = os.path.join(Q.HERE, "Q5_EMBEDDINGS.npz")
FUZZ = os.path.join(Q.HERE, "Q5_FUZZ.json")
CAL = os.path.join(Q.HERE, "Q5_CALIBRATION.json")


def gate_or_die():
    if not os.path.isfile(FUZZ):
        raise SystemExit("REFUSED: Q5_FUZZ.json missing. SECTION 9.0 step 1 first.")
    d = json.load(open(FUZZ, encoding="utf-8"))
    for s in ("F1", "F2"):
        if s not in d:
            raise SystemExit("REFUSED: Q5_FUZZ.json has no %s section. "
                             "SECTION 9.0 order is F1, calibration, F2, then "
                             "this script." % s)
    if not os.path.isfile(CAL):
        raise SystemExit("REFUSED: Q5_CALIBRATION.json missing. The ceiling and "
                         "floor are computed on source audio BEFORE any "
                         "reconstruction is opened (SECTION 5.4.1).")
    removed = [n for n, r in d["F1"]["encoders"].items() if r["verdict"] == "REMOVED"]
    demoted = [n for n, r in d["F2"]["encoders"].items()
               if r["verdict"] == "DEMOTED TO DETECTOR"]
    return removed, demoted


def stage2_rows(arm: str) -> list[dict]:
    p = os.path.join(Q.HERE, "results", "gate4_stage2_%s.jsonl" % arm)
    if not os.path.isfile(p):
        raise SystemExit("REFUSED: no Stage 2 rows for arm %r (%s). Q5 measures "
                         "the cells Gate 4 measured." % (arm, os.path.basename(p)))
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def length_states() -> dict:
    """offline_length_state per cell key, from Stage 1 if it recorded one."""
    out = {}
    p = os.path.join(Q.HERE, "results", "gate4_stage1_decbench.jsonl")
    if not os.path.isfile(p):
        return out
    for line in open(p, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if "key" in r and "offline_length_state" in r:
            out[r["key"]] = r["offline_length_state"]
    return out


def prefix(x: np.ndarray, rung_s) -> np.ndarray:
    """The source side of a ladder cell is the SAME prefix length as the rung."""
    if rung_s is None:
        return x
    n = int(round(float(rung_s) * Q.SR))
    return x[:n]


def done_keys(spec_sha: str, allow_respec: bool) -> set:
    """SECTION 10.1: a measured cell is never re-measured because the SPEC
    revision moved. The revision id is part of the cache key, so a naive re-run
    under a new revision would re-embed everything; that is forbidden - the
    measurement is frozen evidence a later revision CONSUMES."""
    if not os.path.isfile(CELLS):
        return set()
    out, other = set(), collections.Counter()
    for line in open(CELLS, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        out.add((r["arm"], r["condition"], r["key"], r["encoder"]))
        if r.get("spec_sha256") and r["spec_sha256"] != spec_sha[:16]:
            other[r["spec_sha256"]] += 1
    if other and not allow_respec:
        print("SECTION 10.1: %d row(s) were measured under another spec revision "
              "(%s). They are FROZEN EVIDENCE and will NOT be re-measured."
              % (sum(other.values()), ", ".join(other)))
        print("              Pass --allow-respec only if you intend to spend "
              "that measurement again.")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", choices=("offline", "streamed"),
                    default="offline")
    ap.add_argument("--arm", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--allow-respec", action="store_true",
                    help="SECTION 10.1: permit re-measuring cells recorded under "
                         "a different spec revision. Costs the whole pass again.")
    a = ap.parse_args()

    rev = Q.spec_revision()
    removed, demoted = gate_or_die()
    panel = {n: e for n, e in Q.build_panel().items() if n not in removed}
    if not panel:
        raise SystemExit("REFUSED: every encoder was REMOVED by F1.")
    print("Q5 %s pass. encoders: %s%s" % (
        a.condition, ", ".join(panel),
        "" if not demoted else "  (DETECTOR-only: %s)" % ", ".join(demoted)))

    cache = Q.Cache(CACHE, rev["spec_sha256"])
    lens = length_states()
    todo = [a.arm] if a.arm else Q.arms(a.condition)
    already = done_keys(rev["spec_sha256"], a.allow_respec)
    out = open(CELLS, "a", encoding="utf-8")
    t0 = time.time()
    n_rows = 0

    for arm in todo:
        rows = stage2_rows(arm)
        if a.limit:
            rows = rows[:a.limit]
        for r in rows:
            cell_key = r["key"]
            rung = r.get("rung_s")
            setdir = r["set"]
            spath = os.path.join(Q.SRC_ROOT, Q.SEX[r["speaker"]], r["speaker"],
                                 "English", r["state"], r["source_file"])
            rpath = Q.recon_path(arm, setdir, r["speaker"], r["state"],
                                 int(r["index"]), rung, a.condition)
            src_x, src_state, src_dur = (None, Q.NOT_MEASURED, 0.0)
            if os.path.isfile(spath):
                src_x, src_state, src_dur = Q.load16(spath)
                if src_state == Q.MEASURED and rung is not None:
                    src_x = prefix(src_x, rung)
                    src_dur = len(src_x) / Q.SR
                    if src_dur < Q.MIN_DUR_S:
                        src_x, src_state = None, Q.INADMISSIBLE
            rec_x, rec_state, rec_dur = Q.load16(rpath)
            sha_s = Q.sha256_file(spath) if os.path.isfile(spath) else None
            sha_r = Q.sha256_file(rpath) if os.path.isfile(rpath) else None
            cell_state = Q.worse(src_state, rec_state)
            var = "full" if rung is None else "pre%gs" % float(rung)
            sup = (r.get(a.condition) or {}).get("support_state")

            for name, enc in panel.items():
                if (arm, a.condition, cell_key, name) in already:
                    continue
                row = {"arm": arm, "condition": a.condition, "key": cell_key,
                       "set": setdir, "speaker": r["speaker"], "state": r["state"],
                       "index": int(r["index"]), "rung_s": rung,
                       "encoder": name, "device": enc.device,
                       "spec_sha256": rev["spec_sha256"][:16],
                       "source_sha256": sha_s, "recon_sha256": sha_r,
                       "source_variant": var,
                       "source_state": src_state, "recon_state": rec_state,
                       "cell_state": cell_state,
                       "source_dur_s": round(src_dur, 4),
                       "recon_dur_s": round(rec_dur, 4),
                       "support_mcd": sup,
                       "offline_length_state": lens.get(cell_key, "NOT RECORDED"),
                       "R": None, "src_emb_key": None, "rec_emb_key": None,
                       "detector_only": name in demoted,
                       "study_status": "SMOKE" if a.limit else "STUDY"}
                if cell_state == Q.MEASURED:
                    ks = cache.key(sha_s, enc, var)
                    kr = cache.key(sha_r, enc, "full")
                    vs = cache.get(ks)
                    if vs is None:
                        vs = enc.embed_signal(src_x)
                        cache.put(ks, vs)
                    vr = cache.get(kr)
                    if vr is None:
                        vr = enc.embed_signal(rec_x)
                        cache.put(kr, vr)
                    row["R"] = Q.cos(vs, vr)
                    row["src_emb_key"] = ks
                    row["rec_emb_key"] = kr
                out.write(json.dumps(row) + "\n")
                n_rows += 1
            if n_rows and n_rows % 600 == 0:
                out.flush()
                cache.save()
                print("    %s %d rows  (%.0fs)" % (arm, n_rows, time.time() - t0),
                      flush=True)
        print("  %-28s done  rows=%d  (%.0fs)" % (arm, n_rows, time.time() - t0),
              flush=True)
    out.close()
    cache.save()
    print("wrote %d rows to %s" % (n_rows, os.path.basename(CELLS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
