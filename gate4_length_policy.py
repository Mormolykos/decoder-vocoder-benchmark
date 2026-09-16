"""GATE 4 — D5. THE LENGTH-TOLERANCE POLICY, derived from FROZEN Gate 2 geometry.

⛔ NO GATE 4 OUTPUT IS CONSULTED. Every number here comes from
`gate2_matrix.json`, which is inside the Gate 3 freeze. The tolerance for an arm
is therefore fixed before that arm decodes anything, and cannot be widened after
a result is seen.

THE DEFECT THIS REPAIRS. `gate4_lib.DEFAULT_LENGTH_TOL = 0` and `_pair()` raises
correctly, but no PER-ARM tolerance was declared - while §8.3 simultaneously said
the offline quality of `vocos_mel24` and `griffinlim` "is fully admissible and is
measured normally". Those are exactly the two arms carrying a frozen
`b = -256 samples/chunk`. Left alone, either every one of their tier-B/C cells
becomes a LENGTH FAILURE, or somebody picks a tolerance at Stage 2 after outputs
exist.

THE POLICY:

  OFFLINE (full-context)  tolerance = samples_per_unit          (one frame)
  STREAMED                tolerance = n_chunks * |b| + samples_per_unit

Full-context decoding performs no chunking, so `b` cannot accumulate: the only
admissible discrepancy is the arm's own frame quantisation. Streaming
accumulates `b` once per chunk, and `b` is frozen.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_G2 = None


def _g2():
    global _G2
    if _G2 is None:
        d = json.load(open(os.path.join(HERE, "gate2_matrix.json")))
        _G2 = {m["arm"]: m for m in d["matrix"]}
    return _G2


def offline_tolerance(arm):
    """One frame of THAT arm. Never a constant shared across arms."""
    m = _g2()[arm]
    spu = m.get("samples_per_unit_measured")
    if spu is None:
        return None, "samples_per_unit NOT MEASURED for this arm"
    return int(spu), f"one frame of {arm} ({int(spu)} samples)"


def streamed_tolerance(arm, n_chunks):
    """n_chunks * |frozen b| + one frame. `b` is `per_chunk_offset_samples`."""
    m = _g2()[arm]
    spu = m.get("samples_per_unit_measured")
    b = m.get("per_chunk_offset_samples")
    if spu is None or b is None:
        return None, "samples_per_unit or per_chunk_offset NOT MEASURED"
    tol = int(n_chunks) * abs(int(b)) + int(spu)
    return tol, (f"{n_chunks} chunks x |b|={abs(int(b))} + one frame "
                 f"({int(spu)}) = {tol} samples")


def table():
    rows = []
    for arm, m in sorted(_g2().items()):
        spu = m.get("samples_per_unit_measured")
        b = m.get("per_chunk_offset_samples")
        off, _ = offline_tolerance(arm) if spu is not None else (None, None)
        rows.append({
            "arm": arm, "samples_per_unit": spu, "frozen_b": b,
            "offline_tolerance_samples": off,
            "streamed_tolerance_formula": (None if (spu is None or b is None)
                                           else f"n_chunks*{abs(int(b))}+{int(spu)}"),
        })
    return rows


if __name__ == "__main__":
    print("D5 LENGTH-TOLERANCE POLICY - derived from frozen gate2_matrix.json\n")
    print("%-28s %10s %8s %10s  %s" % ("arm", "spu", "frozen b", "offline", "streamed"))
    for r in table():
        print("%-28s %10s %8s %10s  %s" % (
            r["arm"], r["samples_per_unit"], r["frozen_b"],
            r["offline_tolerance_samples"], r["streamed_tolerance_formula"]))
    print("\n⛔ vocos_mel24 and griffinlim carry b = -256 but have "
          "E3 = NOT ACHIEVABLE,\n   so they have NO streamed cells at all. Their "
          "OFFLINE cells sit inside a\n   one-frame tolerance and are admissible "
          "exactly as §8.3 states.")
