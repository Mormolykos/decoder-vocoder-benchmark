"""PROPERTY FUZZ of the repaired instrument, per PROTOCOL.md §8 and R19.

The repair queue replaced the Gate 2 classifier, the Gate Zero record and the
drift measurement with new shared code. New code is not trusted because it is
new. This file attacks it with outputs a decoder could plausibly produce and
with label combinations that MUST NOT earn TRUE_INCREMENTAL.

⛔ The write-up says "survived N attacks", never "closed". I am the author of
this gate and therefore not its certifier. A passing fuzz is a floor, not a
proof, and this file is itself unaudited.

Nothing is timed. No model is loaded. No GPU.
"""

import json
import os

import numpy as np
import torch

import gate_lib as G

SR = 24000
DUR = 2.0
FRAME_S = 0.02
N = int(SR * DUR)
rng = np.random.default_rng(20260911)

# a plausible "correct" reconstruction: real-ish speech-like signal
t = np.arange(N) / SR
good = (0.4 * np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
        + 0.05 * rng.standard_normal(N))
good = (good / np.abs(good).max() * 0.7).astype(np.float32)
SRC = torch.from_numpy(good.copy()).reshape(1, -1)
GOOD = torch.from_numpy(good.copy()).reshape(1, -1)

results = []


def check(name, condition, detail=""):
    results.append({"attack": name, "detected": bool(condition), "detail": detail})
    mark = "DETECTED" if condition else "⛔ MISSED"
    print(f"  {mark:<10} {name}   {detail}")


print("=== gate_zero_record: outputs that must not pass ===")
_, v = G.gate_zero_record(GOOD, SRC, SR, DUR, FRAME_S)
check("the honest control PASSES (a gate nothing passes is useless)", v == "PASS", v)

cases = {
    "all-zero output": torch.zeros_like(GOOD),
    "digital silence at float epsilon": torch.full_like(GOOD, 1e-12),
    "NaN injected": GOOD.clone().index_fill_(1, torch.tensor([5]), float("nan")),
    "inf injected": GOOD.clone().index_fill_(1, torch.tensor([5]), float("inf")),
    "clipping (peak 1.5)": GOOD * (1.5 / 0.7),
    "truncated to half": GOOD[:, : N // 2],
    "duplicated to double": torch.cat([GOOD, GOOD], dim=1),
    "near-silent (energy ratio 0.01)": GOOD * 0.01,
    "gain x100 (energy ratio 100)": (GOOD * 100).clamp(-1, 1) * 0.99,
    "two channels": GOOD.repeat(2, 1),
    "float64 dtype": GOOD.double(),
    "float16 dtype": GOOD.half(),
    "empty tensor": GOOD[:, :0],
    "a python list, not a tensor": [0.1, 0.2, 0.3],
}
for nm, w in cases.items():
    try:
        c, v = G.gate_zero_record(w, SRC, SR, DUR, FRAME_S)
    except Exception as e:
        check(nm, True, f"raised {type(e).__name__} (fails closed)")
        continue
    check(nm, v != "PASS", f"verdict={v}")

# off-by-one length must still pass: one sample is inside one frame of tolerance
c, v = G.gate_zero_record(GOOD[:, :-1], SRC, SR, DUR, FRAME_S)
check("off-by-one sample is NOT rejected (tolerance is one frame, by design)",
      v == "PASS", f"verdict={v}")

print("\n=== measure_condition: the error metric ===")
row = G.measure_condition(GOOD, GOOD.clone(), 1, 20.0, 480.0, 100)
check("identical signals give exactly zero error", row["stateless_raw"] == 0.0,
      f"raw={row['stateless_raw']}")

shifted = torch.roll(GOOD, 1, dims=1)
row = G.measure_condition(GOOD, shifted, 1, 20.0, 480.0, 100)
check("a ONE-SAMPLE SHIFT registers as large error — the metric is a detector, "
      "not a severity scale", row["stateless_rel_pct"] > 1.0,
      f"rel={row['stateless_rel_pct']:.2f}% on a shift of one sample")

row = G.measure_condition(GOOD, torch.zeros_like(GOOD), 1, 20.0, 480.0, 100)
check("an ALL-ZERO output scores ~100%, i.e. better than some real damage",
      abs(row["stateless_rel_pct"] - 100.0) < 1e-6,
      f"rel={row['stateless_rel_pct']}% — recorded as a limit of the metric")

short = GOOD[:, : N - 100 * 7]
row = G.measure_condition(GOOD, short, 1, 20.0, 480.0, 100)
check("length drift is measured, not hidden by n=min(lengths)",
      row["drift_per_chunk_samples"] != 0,
      f"drift/chunk={row['drift_per_chunk_samples']}")

row = G.measure_condition(GOOD, GOOD.clone(), 1, 20.0, 480.0, 100,
                          stateful=GOOD.clone())
check("C2 with a zero stateful error does not divide by zero",
      row["c2_ratio"] is not None and np.isfinite(row["c2_ratio"]),
      f"ratio={row['c2_ratio']}")

print("\n=== classify: label combinations that MUST NOT earn TRUE_INCREMENTAL ===")


def mkrow(c1, c2, valid=True):
    return {"C1": c1, "C2": c2, "valid_pcm": valid,
            "stateless_raw": 1.0, "stateful_raw": 1e-9, "c2_ratio": 1e9}


cl, _ = G.classify([mkrow(True, True)] * 4, True, "state carried")
check("the honest control EARNS TRUE_INCREMENTAL", cl == "TRUE_INCREMENTAL", cl)

cl, _ = G.classify([mkrow(True, False)] * 4, True, "state carried")
check("C1 passes, C2 FAILS at every condition -> must not be TRUE_INCREMENTAL",
      cl != "TRUE_INCREMENTAL", cl)

cl, _ = G.classify([mkrow(True, True)] * 3 + [mkrow(True, False)], True, "x")
check("C2 fails at ONE condition out of four -> must not be TRUE_INCREMENTAL",
      cl != "TRUE_INCREMENTAL", cl)

cl, _ = G.classify([mkrow(True, True)] * 3 + [mkrow(False, True)], True, "x")
check("C1 fails at ONE condition out of four -> must not be TRUE_INCREMENTAL",
      cl != "TRUE_INCREMENTAL", cl)

cl, _ = G.classify([mkrow(True, True)] * 4, False, "no state parameter")
check("state NOT constructible -> must not be TRUE_INCREMENTAL whatever the rows say",
      cl != "TRUE_INCREMENTAL", cl)

cl, _ = G.classify([], True, "x")
check("no conditions -> STREAMING SUPPORT NOT ESTABLISHED, never a failure label",
      cl == "STREAMING SUPPORT NOT ESTABLISHED", cl)

cl, _ = G.classify([mkrow(True, True, valid=False)] * 4, False, "x")
check("invalid PCM with no state -> FULL_CONTEXT_ONLY", cl == "FULL_CONTEXT_ONLY", cl)

print("\n=== native_grid: every condition on the arm's own quantum ===")
for q in (1, 2, 4, 7):
    for fms in (10.667, 11.61, 13.333, 16.0, 20.0, 46.44, 80.0):
        g = G.native_grid(fms, q)
        ok = all(x % q == 0 and x >= q for x in g)
        if not ok:
            check(f"grid off quantum q={q} frame={fms}", False, str(g))
            break
    else:
        continue
    break
else:
    check("every generated chunk size is an integer multiple of the quantum",
          True, "28 (quantum, frame) combinations")

# A quantum of 4 frames at 20 ms is FocalCodec's real case: 80 ms atomic block.
check("FocalCodec's real quantum reproduces the frozen 80/160/400/800 ms grid",
      G.native_grid(20.0, 4) == [4, 8, 20, 40], str(G.native_grid(20.0, 4)))
# A quantum COARSER than a target must never round down to zero conditions, and
# must never silently collapse two distinct targets. round() alone did both:
# round(0.5)==0 and round(2.5)==2 under banker's rounding.
_g = G.native_grid(80.0, 4)   # q_ms = 320 ms, coarser than three of four targets
check("a quantum coarser than a target rounds HALF UP, never to zero, and the "
      "conditions it CAN represent stay distinct",
      _g == sorted(set(_g)) and all(v >= 4 and v % 4 == 0 for v in _g),
      str(_g) + "  [banker's-rounding defect found by this file, fixed 2026-09-11]")

print("\n=== resolve_layout: must fail closed, not guess ===")
lay, f, c = G.resolve_layout((199, 199), expected_frames=199, expected_codebooks=199)
check("square tensor -> NEEDS RESOLUTION", lay == "NEEDS RESOLUTION", lay)
lay, f, c = G.resolve_layout((199, 16), expected_frames=None, expected_codebooks=None)
check("no expectation given -> NEEDS RESOLUTION", lay == "NEEDS RESOLUTION", lay)
lay, f, c = G.resolve_layout((16, 199, 3), expected_frames=199, expected_codebooks=16)
check("3-D tensor -> NEEDS RESOLUTION", lay == "NEEDS RESOLUTION", lay)
lay, f, c = G.resolve_layout((199,), expected_frames=199, expected_codebooks=16)
check("1-D tensor -> NEEDS RESOLUTION", lay == "NEEDS RESOLUTION", lay)
lay, f, c = G.resolve_layout((199, 16), expected_frames=199, expected_codebooks=16)
check("the honest case IS resolved (a resolver that resolves nothing is useless)",
      lay == "[time, codebooks]" and f == 199 and c == 16, f"{lay} {f} {c}")
lay, f, c = G.resolve_layout((16, 199), expected_frames=199, expected_codebooks=16)
check("the transposed honest case is resolved the other way",
      lay == "[codebooks, time]" and f == 199 and c == 16, f"{lay} {f} {c}")

print("\n=== band: rounding must not destroy a signal ===")
b = G.band([{"x": 7.2e-05}, {"x": 3.58e-04}], "x")
check("a 7.2e-05 to 3.58e-04 band does not render as '0.0-0.0'",
      b is not None and "0.0-0.0" not in b, b)

n = len(results)
missed = [r for r in results if not r["detected"]]
print(f"\n=================== FUZZ SUMMARY ===================")
print(f"attacks run      : {n}")
print(f"survived         : {n - len(missed)}")
print(f"MISSED           : {len(missed)}")
for m in missed:
    print(f"   ⛔ {m['attack']}  {m['detail']}")
print("\n⛔ This says the instrument SURVIVED these attacks. It does not say it is "
      "closed. The author of a gate is not its certifier (R19).")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuzz_gate_lib.json")
with open(out, "w") as f:
    json.dump({"attacks_run": n, "survived": n - len(missed),
               "missed": len(missed), "results": results}, f,
              indent=2, default=G.json_default)
print(f"written: {out}")
