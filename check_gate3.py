"""GATE 3 — integrity and schema checks. NO MODEL IS LOADED. NOTHING IS TIMED.

Rewritten 2026-09-11 for the post-audit schema. Confirms the generated matrix is
consistent with the run artifacts, that the frozen procedure was followed rather
than asserted, and that each of the audit's nine repairs actually landed.

⛔ Written by the same author as the harness it checks, so a clean run is a floor
and not a certification (R19).
"""

import collections
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
STATUS = "MEASURED - CELLS COMPLETED AND ADMISSIBLE"

doc = json.load(open(os.path.join(HERE, "gate3_matrix.json"), encoding="utf-8"))
arms = {a["arm"]: a for a in doc["arms"]}
g2 = {m["arm"]: m for m in
      json.load(open(os.path.join(HERE, "gate2_matrix.json")))["matrix"]}
md = open(os.path.join(HERE, "GATE3_MATRIX.md"), encoding="utf-8").read()

cells, raw, e6raw = [], [], []
for f in glob.glob(os.path.join(RES, "gate3_cells_*.jsonl")):
    if os.path.basename(f).startswith("SMOKE_"):
        continue
    (e6raw if "_e6_" in f else cells).extend(
        json.loads(l) for l in open(f, encoding="utf-8"))
for f in glob.glob(os.path.join(RES, "gate3_raw_*.jsonl")):
    b = os.path.basename(f)
    if b.startswith("SMOKE_") or "_e6_" in b:
        continue
    raw += [json.loads(l) for l in open(f, encoding="utf-8")]

fails = []


def ck(name, cond, detail=""):
    print(f"  {'PASS' if cond else '⛔ FAIL':<8} {name}   {detail}")
    if not cond:
        fails.append(f"{name}: {detail}")


print("=== coverage ===")
ck("every Gate 2 arm has a Gate 3 row", set(arms) == set(g2), str(set(g2) ^ set(arms)))
ck("20 rows", len(doc["arms"]) == 20, str(len(doc["arms"])))
ck("no artifacts missing", doc["missing_artifacts"] == [], str(doc["missing_artifacts"]))
ck("no header is in smoke mode",
   all(not h.get("smoke_mode_NOT_A_RESULT") for h in doc["headers"].values()))

print("\n=== the frozen procedure was followed, not just described ===")
by = collections.Counter((c["arm"], c.get("seconds"))
                         for c in raw if c.get("cell") == "offline")
ck("every offline cell recorded exactly N=30 warm repetitions",
   all(v == 30 for v in by.values()), f"distinct counts {sorted(set(by.values()))}")
bc = collections.Counter(c["arm"] for c in raw if c.get("cell") == "cold")
ck("every arm recorded exactly 3 cold repetitions",
   all(v == 3 for v in bc.values()), f"distinct counts {sorted(set(bc.values()))}")
adm = [c for c in raw if "admissible" in c]
ck("every timed row asserts BOTH cuda synchronizes structurally (§9.2)",
   all(c["admissible"] for c in adm),
   f"{sum(1 for c in adm if not c['admissible'])} inadmissible of {len(adm)}")
ck("raw per-repetition rows kept, not just summaries (§11)", len(raw) > 3000,
   f"{len(raw)} raw rows")
seq = [json.loads(l)["arm"] for l in
       open(os.path.join(RES, "gate3_cells_a.jsonl"), encoding="utf-8")]
runs = 1 + sum(1 for i in range(1, len(seq)) if seq[i] != seq[i - 1])
ck("execution order is block-randomised, not grouped by arm (§11)",
   runs > 3 * len(set(seq)),
   f"{runs} same-arm runs over {len(seq)} cells, {len(set(seq))} arms")

print("\n=== B1: the §7.2 environment control ===")
E6 = doc["E6_environment_control"]
ck("E6 exists and covers every environment that produced arm rows",
   E6 is not None and {"decbench", "fish", "decbench_melflow"} <= set(E6),
   ", ".join(sorted(E6 or {})))
ck("E6 artifacts exist for all three environments", len(
    glob.glob(os.path.join(RES, "gate3_cells_e6_*.jsonl"))) == 3)
ck("fish is marked NOT COMPARABLE",
   doc["E6_consequence"]["fish"]["comparable"] is False,
   f"effect {E6['fish']['effect_pct']:.1f}%")
ck("decbench_melflow is marked COMPARABLE by measurement",
   doc["E6_consequence"]["decbench_melflow"]["comparable"] is True,
   f"effect {E6['decbench_melflow']['effect_pct']:.1f}%")
ck("fish_modified_dac's row carries the NOT COMPARABLE marker",
   arms["fish_modified_dac"]["cross_env_comparable"] is False)
ck("fish_modified_dac is excluded from the budget table",
   not arms["fish_modified_dac"].get("budget_eligible"))
ck("fish_modified_dac is excluded from E4's ordering",
   "fish_modified_dac" not in (doc["E4_ordering"].get("subset") or []))
ck("GATE3_MATRIX.md says NOT COMPARABLE", "NOT COMPARABLE" in md)
ck("E6 appears in the markdown", "E6" in md)

print("\n=== B2: streamed §8 validity is exposed and E3 respects it ===")
ck("the markdown mentions the streamed §8 gate", "§8 streamed" in md)
for name in ("vocos_mel24", "griffinlim"):
    a = arms[name]
    ck(f"{name}: E3 is NOT ACHIEVABLE", a["e3_min_viable_streaming_ms"] == "NOT ACHIEVABLE",
       str(a["e3_min_viable_streaming_ms"]))
    ck(f"{name}: no §8 condition passes", a["streamed_gate8_any_pass"] is False,
       a["e3_conditions_passing_gate8"])
    ck(f"{name}: excluded from the budget table", not a.get("budget_eligible"))
a = arms["focalcodec_12_5hz"]
ck("focalcodec_12_5hz: anchor fails §8", a["anchor_streamed_gate8"] != "PASS",
   str(a["anchor_streamed_gate8"]))
ck("focalcodec_12_5hz: E3 is the first PASSING condition, not the anchor",
   a["e3_min_viable_streaming_ms"] not in (None, "NOT ACHIEVABLE")
   and a["e3_min_viable_streaming_ms"] > 600,
   str(a["e3_min_viable_streaming_ms"]))
ck("every arm reports min_chunk_that_ran_ms separately from E3",
   all("min_chunk_that_ran_ms" in x and "e3_min_viable_streaming_ms" in x
       for x in doc["arms"] if x["status"] == STATUS))
ck("the old asserting field name is gone", "min_viable_chunk_ms" not in json.dumps(doc))

print("\n=== M1/M2: E1 as a real estimand, memory scopes separated ===")
E1 = doc["E1_controlled_pair"]
ck("E1 exists", E1 is not None)
ck("E1 has per-condition rows", len(E1["conditions"]) >= 10, str(len(E1["conditions"])))
ck("every E1 condition carries a difference AND a ratio AND an interval",
   all(c.get("difference_ci95_ms") and c.get("ratio_ci95") for c in E1["conditions"]))
ck("E1 states the KIND of pairing", "not on the measurement occasion" in E1["pairing"])
# The spot-check defect: a MEDIAN point estimate with a MEAN bootstrap put the
# point outside its own interval in 5 of 7 streaming rows.
outside = [f"{c['cell']} {c['condition']}" for c in E1["conditions"]
           if not (c["difference_ci95_ms"][0] <= c["difference_ms"] <= c["difference_ci95_ms"][1])
           or not (c["ratio_ci95"][0] <= c["ratio"] <= c["ratio_ci95"][1])]
ck("EVERY E1 point estimate lies inside its own interval", not outside,
   "; ".join(outside[:4]) or f"{len(E1['conditions'])} conditions checked")
ck("E1 bootstraps the SAME statistic it reports (median)",
   all("MEDIAN bootstrap" in c.get("bootstrap", "") for c in E1["conditions"]))
ck("E1 resamples PAIR indices, no cap - every resample has exactly n pairs",
   all("exactly n pairs" in c.get("bootstrap", "") for c in E1["conditions"]))
ck("E1 pairing is exact: n_a == n_b == n_pairs at every condition",
   all(c["n_a"] == c["n_b"] == c["n_pairs"] for c in E1["conditions"]),
   ", ".join(str(c["n_pairs"]) for c in E1["conditions"]))
ck("E1 streaming conditions use the steady-state population (n > 30)",
   all(c["n_pairs"] > 30 for c in E1["conditions"]
       if c["cell"].startswith("stream")))
ck("VRAM scopes are named for what they cover",
   {"anchor_peak_allocated_MiB", "offline_sweep_peak_allocated_MiB",
    "session_peak_allocated_MiB", "anchor_peak_reserved_MiB",
    "offline_sweep_peak_reserved_MiB", "session_peak_reserved_MiB"}
   <= set(E1["memory_scopes_SEPARATED"]),
   ", ".join(sorted(E1["memory_scopes_SEPARATED"])))
ck("no VRAM key claims a scope it does not cover",
   not any("whole_session" in k for k in E1["memory_scopes_SEPARATED"]))
sc = E1["memory_scopes_SEPARATED"]
ck("E1 separates at least three memory scopes", len(
    [k for k in sc if k != "reserved_is_not_monotonic"]) >= 3, ", ".join(sc))
ck("E1 warns that reserved is not monotonic",
   "not monotonic" in sc["reserved_is_not_monotonic"]["warning"].lower())
ck("E1 reaches the markdown", "E1 —" in md or "E1 -" in md)

print("\n=== M3: ONE statistics population ===")
mixed = []
for a in doc["arms"]:
    for s in a.get("stream", []):
        if s["composed"]:
            continue
        st, al = s["steady"], s["all_chunks"]
        if st.get("n") and al.get("n") and st["n"] >= al["n"]:
            mixed.append(f"{a['arm']}@{s['effective_ms']}")
ck("steady-state population is strictly smaller than all-chunks everywhere",
   not mixed, "; ".join(mixed[:3]))
ck("the markdown declares the population", "STEADY-STATE" in md)
ck("a claim boundary states the population rule",
   any("STEADY-STATE" in c for c in doc["claim_boundaries"]))

print("\n=== M4: status terminology ===")
ck("no row says PASS", not any(a["status"] == "PASS" for a in doc["arms"]))
ck("status is the explicit measured wording",
   doc["totals_by_status"].get(STATUS) == 19, json.dumps(doc["totals_by_status"]))
ck("the definition says it is NOT a performance verdict",
   "NOT A PERFORMANCE VERDICT" in doc["status_definition"])
ck("the definition reaches the markdown", "not a performance verdict" in md.lower())

print("\n=== M5: VRAM re-run rule disposition ===")
v = doc["vram_rerun_rule_disposition"]
ck("the rule's disposition is recorded", "AMENDMENT 10" in v["disposition"].upper())
ck("the flagged count is reported, not hidden", v["cells_flagged"] > 0,
   f"{v['cells_flagged']}/{v['cells_total']}")
ck("a replacement validity check is named", "reset_peak_memory_stats" in v["replacement_check"])
proto = open(os.path.join(HERE, "PROTOCOL.md"), encoding="utf-8").read()
ck("PROTOCOL carries amendment 10", "amendment 10" in proto)
ck("amendment 10 covers BOTH E6 and the VRAM rule",
   "E6" in proto.split("amendment 10")[1][:4000]
   and "200 MiB" in proto.split("amendment 10")[1][:6000])

print("\n=== M6: E3 and E4 produced ===")
E4 = doc["E4_ordering"]
ck("E4 exists and is computed or explicitly underpowered",
   E4.get("status") in ("COMPUTED", "UNDERPOWERED"), str(E4.get("status")))
if E4.get("status") == "COMPUTED":
    ck("E4 names its subset", len(E4["subset"]) == E4["n_qualifying"])
    ck("E4 names what it excluded and why", bool(E4["excluded"]))
    ck("E4 reports a rank correlation", E4.get("spearman_rho_rtf_vs_ttfa") is not None)
ck("E4 reaches the markdown", "E4" in md)

print("\n=== D: remaining reporting defects ===")
for n in ("dac44", "melflow", "bigvgan22"):
    ck(f"{n}: E2 fit marked invalid", arms[n].get("e2_fit_valid") is False)
ck("invalid E2 fits are marked INLINE in the markdown",
   "NOT INTERPRETABLE" in md)
weak = [a["arm"] for a in doc["arms"]
        if (a.get("delay_calibration") or {}).get("reliable") is False]
ck("weak delay calibrations are flagged", len(weak) > 0, ", ".join(weak))
ck("weak delay estimates are declared unused", "is not used as a fact" in md)
mf = arms["melflow"]
ck("melflow's TTFA cell carries its state", bool(mf.get("ttfa_cell_state")),
   json.dumps(mf.get("ttfa_cell_state"))[:90])
bg = arms["bigvgan22"]
ck("BigVGAN transition points come from data, not prose",
   bg.get("first_underrun_free_ms") is not None,
   f"underruns at {bg.get('underrun_conditions_ms')}, first clean "
   f"{bg.get('first_underrun_free_ms')}")
ck("a claim boundary covers GPU preemption",
   any("preemption" in c for c in doc["claim_boundaries"]))

print("\n=== nanocodec and totals ===")
nano = arms["nanocodec"]
ck("nanocodec carries NO timing number",
   not any(k in nano for k in ("offline", "stream", "anchor", "ttfa_anchor_ms",
                               "perframe", "offline_sweep_peak_alloc_MiB")))
ck("nanocodec is BLOCKED - PLATFORM", nano["status"] == "BLOCKED - PLATFORM")
rec = collections.Counter(a["status"] for a in doc["arms"])
ck("totals equal an independent recount", dict(rec) == doc["totals_by_status"],
   json.dumps(dict(rec)))
ck("every failed cell is a RECORDED row (§12)",
   all(len(a.get("failures", [])) == a.get("cells_failed", 0)
       for a in doc["arms"] if "cells_failed" in a))

ov = sorted(c["host_overhead_ms"] for c in raw if c.get("host_overhead_ms") is not None)
if ov:
    print(f"\n  host overhead ms (wall - cuda): median {ov[len(ov)//2]:.4f}  "
          f"min {ov[0]:.4f}  max {ov[-1]:.4f}  n={len(ov)}")

print(f"\n=================== GATE 3 CONSISTENCY SUMMARY ===================")
print(f"failures: {len(fails)}")
for x in fails:
    print(f"   ⛔ {x}")
print("\nNO MODEL WAS LOADED. NOTHING WAS TIMED.")
print("⛔ A clean run here is a floor, not a certification (R19).")
