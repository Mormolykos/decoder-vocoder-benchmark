"""INTEGRITY / SCHEMA CHECKS ONLY. NO MODEL IS LOADED. NOTHING IS MEASURED.

Confirms that the regenerated deliverables are internally consistent with the
run artifacts they claim to be generated from, and that the delta audit's four
corrections actually landed. Every check either passes or names what is wrong;
nothing here can turn a failure into a pass.

⛔ This file is written by the same author as the files it checks, so a clean
run is a floor and not a certification (R19).
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["gate2_repaired_a.json", "gate2_repaired_b.json",
         "gate2_repaired_fish.json", "gate2_repaired_melflow.json"]

arts = {}
for fn in FILES:
    for r in json.load(open(os.path.join(HERE, fn))):
        r["_artifact"] = fn
        arts[r["arm"]] = r
doc = json.load(open(os.path.join(HERE, "gate2_matrix.json")))
matrix = {m["arm"]: m for m in doc["matrix"]}
md = open(os.path.join(HERE, "GATE2_MATRIX.md"), encoding="utf-8").read()
env = json.load(open(os.path.join(HERE, "ENVIRONMENT.json")))

fails = []


def ck(name, ok, detail=""):
    print(f"  {'PASS' if ok else '⛔ FAIL':<8} {name}   {detail}")
    if not ok:
        fails.append(f"{name}: {detail}")


print("=== A1: label scope — the BLOCKING finding ===")
for arm, m in matrix.items():
    if m["classification"] != "TRUE_INCREMENTAL":
        continue
    pcm = m.get("emits_pcm_from_partial_input")
    ck(f"{arm}: §10.1 predicate is declared", pcm is not None, f"value={pcm}")
    if pcm:
        ck(f"{arm}: label says representation → PCM",
           m["label"] == "TRUE_INCREMENTAL (representation → PCM)", m["label"])
    else:
        ck(f"{arm}: label carries its scope and is NOT unqualified",
           m["label"] != "TRUE_INCREMENTAL" and "NOT ESTABLISHED" in m["label"],
           m["label"])

ti = {k: v for k, v in doc["totals_by_classification"].items()
      if k.startswith("TRUE_INCREMENTAL")}
ck("TRUE_INCREMENTAL is split into more than one bucket", len(ti) >= 2, json.dumps(ti))
ck("no bucket is an unqualified 'TRUE_INCREMENTAL'",
   "TRUE_INCREMENTAL" not in doc["totals_by_classification"],
   ", ".join(doc["totals_by_classification"]))
ck("representation → PCM bucket holds exactly the 3 causal FocalCodec arms",
   sorted(m["arm"] for m in doc["matrix"]
          if m["label"] == "TRUE_INCREMENTAL (representation → PCM)") ==
   ["focalcodec_50hz_2k_causal", "focalcodec_50hz_4k_causal",
    "focalcodec_50hz_65k_causal"])
ck("melflow is alone in the neural-decoder-only bucket",
   [m["arm"] for m in doc["matrix"] if m["label"].startswith("TRUE_INCREMENTAL —")]
   == ["melflow"])
ck("the markdown label cell is qualified too",
   "TRUE_INCREMENTAL — NEURAL DECODER; iSTFT STREAMING NOT ESTABLISHED" in md)

print("\n=== B1: upstream-patch disclosure reaches the deliverables ===")
ck("gate2_matrix.json carries melflow's upstream_patches",
   len(matrix["melflow"].get("upstream_patches") or []) == 2,
   str(len(matrix["melflow"].get("upstream_patches") or [])))
for phrase in ("LOCAL REPAIRS", "DOES NOT EXECUTE AS-IS", "INERT", "ab2700c1"):
    ck(f"GATE2_MATRIX.md contains {phrase!r}", phrase in md)
ck("the iSTFT-stage control is in the matrix", "134.65" in md)
ck("the control is attributed and marked not reproduced here",
   arts["melflow"]["istft_stage_control"]["reproduced_in_this_harness"] is False)
man = open(os.path.join(HERE, "MANIFEST.md"), encoding="utf-8").read()
ck("MANIFEST.md discloses the local repairs",
   "does not execute as released" in man.lower() or "locally repaired" in man.lower())

print("\n=== B2: drift fields use the true integer hop and agree with the fit ===")
for arm, m in matrix.items():
    if m.get("samples_per_unit_measured") is None:
        continue
    ck(f"{arm}: artifact drift agrees with the fit",
       m["drift_artifact_agrees_with_fit"] is True,
       f"fit b={m['per_chunk_offset_samples']}")
    a = arts[arm]
    ck(f"{arm}: samples_per_unit is the exact integer hop",
       a["samples_per_unit"] == float(int(a["samples_per_unit"])),
       str(a["samples_per_unit"]))
    ck(f"{arm}: the superseded value is preserved",
       "samples_per_unit_superseded" in a)
ck("mimi_q8 drift is 0, not the contaminated +7.24…+72.37",
   all(c["drift_per_chunk_samples"] == 0 for c in arts["mimi_q8"]["conditions"]),
   arts["mimi_q8"]["drift_per_chunk_band"])
ck("dualcodec_12hz_v1 drift is exactly -4",
   arts["dualcodec_12hz_v1"]["drift_per_chunk_band"] == "-4")
ck("melflow drift fields are NOT APPLICABLE, not a number",
   all(c["drift_per_chunk_samples"] is None
       for c in arts["melflow"]["conditions"]))

print("\n=== B3: melflow's stateful granularity is machine-readable ===")
sm = arts["melflow"].get("stateful_measurement")
ck("stateful_measurement block exists", sm is not None)
ck("granularity is 1 frame / 16 ms", sm["granularity_units"] == 1
   and sm["granularity_ms"] == 16.0, f"{sm['granularity_units']} / {sm['granularity_ms']}")
ck("it records that the value is identical across conditions",
   sm["identical_across_all_conditions"] is True)
ck("every condition row is labelled a state-RESET interval",
   all("RESET" in c["chunk_role"] for c in arts["melflow"]["conditions"]))
ck("every condition row carries C1_scope",
   all(c["C1_scope"] for c in arts["melflow"]["conditions"]))
ck("the matrix C1 cell shows the granularity, not a bare PASS",
   matrix["melflow"]["C1"] == "PASS @ 16 ms granularity", matrix["melflow"]["C1"])

print("\n=== C: minor corrections ===")
ck("ENVIRONMENT.json exposes transformers at the top of every env record",
   all(e.get("transformers") not in (None, "NOT INSTALLED")
       for e in env["environments"].values()),
   ", ".join(f"{k}={v.get('transformers')}" for k, v in env["environments"].items()))
gl = arts["griffinlim"]
ck("griffinlim's state note describes the configuration THIS ROW ran",
   "rand_init=False" in gl["state_note"] and "WITHDRAWN" in gl["state_note"])
ck("the superseded griffinlim note is preserved",
   "state_note_superseded" in gl)
ck("griffinlim determinism probe keeps BOTH configurations",
   set(gl["determinism_probe"]) == {"rand_init=True", "rand_init=False"})
nc = matrix["nanocodec"]
ck("nanocodec is still BLOCKED, never zero and never omitted",
   nc["classification"] == "BLOCKED - PLATFORM"
   and nc["gate_zero"] == "NOT RUN - arm could not be loaded")
ck("nanocodec's missing artifact is disclosed, not hidden",
   "none" in str(nc.get("artifact")).lower())

print("\n=== totals and provenance recomputed independently ===")
recount = {}
for m in doc["matrix"]:
    recount[m["label"]] = recount.get(m["label"], 0) + 1
ck("totals equal an independent recount of the rows",
   recount == doc["totals_by_classification"], json.dumps(recount))
ck("row count is 20", len(doc["matrix"]) == 20, str(len(doc["matrix"])))
ck("19 of 20 rows trace to a named artifact",
   sum(1 for m in doc["matrix"] if m.get("artifact")
       and m["artifact"] in FILES) == 19)
ck("no source artifact is missing", doc["missing_sources"] == [],
   str(doc["missing_sources"]))
ck("no arm is left with an ARTIFACT INVALID or ARTIFACT MISSING row",
   not any("ARTIFACT" in m["classification"] for m in doc["matrix"]))
ck("melflow used the whole probe, not a feasibility slice",
   arts["melflow"]["truncated_probe"] is False
   and arts["melflow"]["frames_used"] == 992,
   f"{arts['melflow']['frames_used']} frames")

print("\n=== measured values were NOT altered by the corrections ===")
ck("melflow stateful error is unchanged at 3.036111593e-06",
   abs(arts["melflow"]["conditions"][0]["stateful_raw"] - 3.03611159324646e-06)
   < 1e-18)
ck("focal 4k stateful band unchanged",
   arts["focalcodec_50hz_4k_causal"]["stateful_raw_band"] == "1.913e-05-5.893e-05",
   arts["focalcodec_50hz_4k_causal"]["stateful_raw_band"])
ck("the three non-causal FocalCodec negative controls still sit at C2 = 1.000000",
   all(all(c["c2_ratio"] == 1.0 for c in arts[a]["conditions"])
       for a in ("focalcodec_50hz", "focalcodec_25hz", "focalcodec_12_5hz")))
ck("all 19 measured arms still carry a computed Gate Zero record",
   sum(1 for a in arts.values()
       if isinstance(a.get("gate_zero_checks"), dict)
       and all(k in a["gate_zero_checks"] for k in
               ("finite", "peak_in_range", "duration_ok", "energy_ok",
                "dtype_ok", "channels_ok"))) == 19)

print(f"\n=================== CONSISTENCY SUMMARY ===================")
print(f"failures: {len(fails)}")
for f in fails:
    print(f"   ⛔ {f}")
print("\nNO MODEL WAS LOADED. NOTHING WAS MEASURED. NOTHING WAS TIMED.")
print("⛔ A clean run here is a floor, not a certification (R19).")
