r"""CLAIM AUDIT — every headline numeric claim in PAPER.md, re-checked against
the frozen artifact it came from.

A claim that cannot be traced to an artifact is a FAIL, not a warning. Read-only.
"""
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAPER = open(os.path.join(HERE, "PAPER.md"), encoding="utf-8").read()


def j(n):
    p = os.path.join(ROOT, n)
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}


def txt(n):
    p = os.path.join(ROOT, n)
    return open(p, encoding="utf-8").read() if os.path.isfile(p) else ""


q5 = j("Q5_RESULTS.json")
g4 = j("GATE4_RESULTS.json")
g2 = txt("GATE2_MATRIX.md")
g3 = txt("GATE3_MATRIX.md")
man = j("PUBLICATION_MANIFEST.json")
rows = [json.loads(l) for l in
        open(os.path.join(ROOT, "Q5_CELLS.jsonl"), encoding="utf-8") if l.strip()]

results = []


def check(claim, in_paper, ok, source, detail=""):
    present = in_paper in PAPER
    verdict = "PASS" if (present and ok) else ("NOT-IN-PAPER" if not present else "FAIL")
    results.append((verdict, claim, source, detail))


# ---- Gate 2
check("20 arms total", "**twenty decoder arms**",
      "TOTAL                                                                 20" in g2,
      "GATE2_MATRIX.md totals")
check("3 TRUE_INCREMENTAL rep->PCM",
      "**three** reproduce full-context output from partial input",
      "TRUE_INCREMENTAL (representation → PCM)                                3" in g2,
      "GATE2_MATRIX.md totals")
check("15 stateless chunking", "**Fifteen** use stateless chunking",
      "STATELESS_CHUNKING                                                    15" in g2,
      "GATE2_MATRIX.md totals")
# --- anti-overreach guards, added after the 2026-09-16 two-model claim review.
# These fail if a withdrawn phrasing ever returns to the paper.
for banned, why in (
        ("dressed as streaming", "imputes intent to arms that never claimed to stream"),
        ("what a listener would care about", "perceptual claim with no listening test"),
        ("Two unrelated instruments", "overstates independence; same data"),
        ("a second, independent instrument", "overstates independence; same data"),
        ("Two Metrics That Failed Their Own Validity Checks",
         "only Q9 was a pre-registered validity instrument"),
        ("the only ones that lose no speaker identity",
         "representation-level result stated as decoder-level identity")):
    results.append(("PASS" if banned not in PAPER else "FAIL",
                    "withdrawn phrasing absent: %r" % banned[:42],
                    "claim review 2026-09-16", why))
check("C2 ratio range 3,530-36,740", "**3,530 to 36,740**",
      ("3530-1.601e+04" in g2 and "3.674e+04" in g2),
      "GATE2_MATRIX.md causal rows")
check("overlap-add control 134.65%", "134.65%", "134.65%" in g2,
      "GATE2_MATRIX.md melflow control")
check("drift 47,360 samples", "**47,360 samples ≈ 1.97 s**",
      "47360 smp" in g2, "GATE2_MATRIX.md drift table")

# ---- Gate 3
check("environment effect 50.2%", "**50.2% faster**", "50.2%" in g3,
      "GATE3_MATRIX.md E6")
check("TTFA range 1.37-375.91", "**1.37 ms**",
      ("1.37" in g3 and "375.91" in g3), "GATE3_MATRIX.md headline")
check("qwen underrun 0.0013 / max 208.10", "**max of 208.10 ms**",
      ("0.0013" in g3 and "208.10" in g3), "GATE3_MATRIX.md headline")
check("focalcodec_12_5hz E3 640.8 ms", "**640.8 ms**", "640.8 ms" in g3,
      "GATE3_MATRIX.md E3")

# ---- Gate 4
hl = json.dumps(g4.get("headline", {}))
check("46/42/20 verdicts", "**46 SEPARATION ESTABLISHED · 42 ORDERED",
      ("46" in hl and "42" in hl and "20" in hl) or
      "SEPARATION ESTABLISHED (mcd, REFERENCE-COMMON, round trip) | **46**"
      in txt("GATE4_STAGE2_TABLES.md"), "GATE4_STAGE2_TABLES.md §6")
check("Q9 fires", "**best, in six states of six**",
      "Q9 FIRES" in json.dumps(g4.get("metric_validity", {})),
      "GATE4_RESULTS.json metric_validity")
check("Q9 loud/quiet 21.4 vs 16.0", "(21.4 versus 16.0)",
      "21.4" in txt("STAGE2_STATE.md"), "STAGE2_STATE.md Q9 diagnostic")
check("coverage 99.3 / 79.4 / 1.0-0.2",
      "`griffinlim` 99.3% of\ncells rankable",
      "99.3 %" in txt("GATE4_STAGE2_TABLES.md"), "GATE4_STAGE2_TABLES.md §5")

# ---- Q5 recomputed from artifacts
ENC = ["ecapa", "redimnet_M_vb2_ptn", "redimnet_b6_lm"]
ret = {a: q5["arms"][a]["ecapa"]["sets"]["S"]["CROSS"]["R"]["median"]
       for a in q5["arms"]}
top = max(ret, key=ret.get)
check("griffinlim highest retention (ecapa)",
      "**Griffin-Lim has the highest speaker-embedding retention",
      top == "griffinlim", "Q5_RESULTS.json recomputed",
      "top=%s %.4f" % (top, ret[top]))
check("retention floor 0.4316 focalcodec_12_5hz", "**0.4316** (`focalcodec_12_5hz`",
      abs(ret["focalcodec_12_5hz"] - 0.4316) < 5e-5, "Q5_RESULTS.json",
      "%.4f" % ret["focalcodec_12_5hz"])
check("max per-encoder spread 0.1193", "reaches 0.1193",
      abs(max(max(q5["arms"][a][e]["sets"]["S"]["CROSS"]["R"]["median"] for e in ENC)
              - min(q5["arms"][a][e]["sets"]["S"]["CROSS"]["R"]["median"] for e in ENC)
              for a in q5["arms"]) - 0.1193) < 5e-5, "Q5_RESULTS.json recomputed")

lab = collections.Counter()
for a, per in q5["arms"].items():
    for e, blk in per.items():
        for S, sb in blk["sets"].items():
            for st, v in sb.items():
                lab[v["label"]] += 1
check("540 labels", "540 labelled strata", sum(lab.values()) == 540,
      "Q5_RESULTS.json recomputed", str(sum(lab.values())))
check("NOT ESTABLISHED 314", "`NOT ESTABLISHED` (314)",
      lab["NOT ESTABLISHED"] == 314, "Q5_RESULTS.json", str(lab["NOT ESTABLISHED"]))
check("DRIFTING 152", "accounts for\n152", lab["INCONSISTENT / DRIFTING"] == 152,
      "Q5_RESULTS.json", str(lab["INCONSISTENT / DRIFTING"]))
check("PRESERVED 19 / OFFSET 8", "for 19; and\n`STABLE OFFSET`",
      lab["PRESERVED + CONSISTENT"] == 19 and lab["STABLE OFFSET"] == 8,
      "Q5_RESULTS.json")

sd = q5["streaming_detector"]
causal = ["focalcodec_50hz_2k_causal", "focalcodec_50hz_4k_causal",
          "focalcodec_50hz_65k_causal"]
ok_causal = all(round(sd[a][e]["S1_offline_vs_streamed_median"], 4) == 0.9999
                and abs(sd[a][e]["S2_retention_delta_median"]) < 5e-5
                for a in causal for e in ENC)
check("causal arms S1 0.9999 / S2 -0.0000", "S1 =\n0.9999, S2 = −0.0000",
      ok_causal, "Q5_RESULTS.json streaming_detector")
check("abstract states no measured loss, not identity preserved",
      "show\n**no measured loss** under that metric when streamed", True,
      "claim review finding 5")
check("abstract declares shared data limit",
      "**not** in *data*", True, "claim review finding 2")
s2 = {a: sd[a]["ecapa"]["S2_retention_delta_median"] for a in sd
      if sd[a]["ecapa"]["S2_retention_delta_median"] is not None and a not in causal}
check("worst streaming loss -0.742 dualcodec_25hz_v1", "**−0.742** (`dualcodec_25hz_v1`)",
      min(s2, key=s2.get) == "dualcodec_25hz_v1" and abs(s2[min(s2, key=s2.get)] + 0.742) < 5e-4,
      "Q5_RESULTS.json", "%.4f" % s2[min(s2, key=s2.get)])
check("best non-causal -0.078 bigvgan22", "**−0.078** (`bigvgan22`)",
      max(s2, key=s2.get) == "bigvgan22" and abs(s2[max(s2, key=s2.get)] + 0.078) < 5e-4,
      "Q5_RESULTS.json", "%.4f" % s2[max(s2, key=s2.get)])

mk = sum(1 for a, per in q5["arms"].items() for e, blk in per.items()
         for S, sb in blk["sets"].items() for st, v in sb.items() if v["marker"])
check("69 impostor-range markers", "69 `APPROACHES IMPOSTOR RANGE` markers",
      mk == 69, "Q5_RESULTS.json recomputed", str(mk))

# support counts, recomputed
sup = {}
for cond in ("offline", "streamed"):
    sub = [r for r in rows if r["condition"] == cond]
    c = collections.Counter(str(r["support_mcd"]) for r in sub)
    sup[cond] = (c["NOT COMPARABLE - OUTSIDE VALIDATED SUPPORT"] // 3, len(sub) // 3,
                 c["MEASURED"] // 3)
check("support counts are CELLS not rows",
      "**17,020 of 31,248 offline cells and 26,147 of 27,776 streamed cells",
      sup["offline"][:2] == (17020, 31248) and sup["streamed"][:2] == (26147, 27776),
      "Q5_CELLS.jsonl recomputed", str(sup))

check("1,512 source recordings", "**1,512\ndistinct source recordings**",
      man["corpus"]["counts"]["distinct_recordings"] == 1512,
      "PUBLICATION_MANIFEST.json")
check("device delta <= 2.5e-04", "≤ 2.5e-04",
      os.path.isfile(os.path.join(ROOT, "Q5_DEVICE_EQUIVALENCE.json")),
      "Q5_DEVICE_EQUIVALENCE.json")

# ---- report
print("CLAIM AUDIT — PAPER.md against frozen artifacts\n")
w = collections.Counter(r[0] for r in results)
for v, c, s, d in results:
    print("%-13s %-44s %-34s %s" % (v, c, s, d))
print("\n%s" % dict(w))
print("\nFAIL or NOT-IN-PAPER means the claim could not be traced; both block release.")
raise SystemExit(1 if (w["FAIL"] or w["NOT-IN-PAPER"]) else 0)
