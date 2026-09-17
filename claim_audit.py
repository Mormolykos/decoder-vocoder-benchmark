r"""CLAIM AUDIT — every headline numeric claim in PAPER.md, re-checked against
the frozen artifact it came from.

A claim that cannot be traced to an artifact is a FAIL, not a warning. Read-only.
"""
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
# One source, two layouts: `paper/` beside a parent holding the artifacts
# (private tree), or everything flat (public release tree). See the same note
# in make_paper_tables.py — resolving to the parent unconditionally is what
# made this script fail from the published package.
ROOT = HERE if os.path.isfile(os.path.join(HERE, "Q5_RESULTS.json")) \
    else os.path.dirname(HERE)
PAPER = open(os.path.join(HERE, "PAPER.md"), encoding="utf-8").read()


def j(n, *alts):
    """First existing of `n`/`alts`. Missing is fatal, never an empty dict."""
    for name in (n,) + alts:
        p = os.path.join(ROOT, name)
        if os.path.isfile(p):
            return json.load(open(p, encoding="utf-8"))
    raise SystemExit("MISSING ARTIFACT: none of [%s] found in %s"
                     % (", ".join((n,) + alts), ROOT))


def txt(n):
    p = os.path.join(ROOT, n)
    return open(p, encoding="utf-8").read() if os.path.isfile(p) else ""


q5 = j("Q5_RESULTS.json")
# The public tree ships the pseudonymised derivative under a different name.
# Both carry `headline` and `metric_validity` byte-identically apart from the
# speaker strings, so every check below is unaffected by which one loads.
g4 = j("GATE4_RESULTS.json", "GATE4_RESULTS_PUBLIC.json")
g2 = txt("GATE2_MATRIX.md")
g3 = txt("GATE3_MATRIX.md")
man = j("PUBLICATION_MANIFEST.json")

# ---- withheld primary measurements.
# `Q5_CELLS.jsonl` holds one row per recording × encoder and is deliberately
# NOT published: a per-recording speaker-embedding row is biometric data about
# a named consenting human. Checks that need it are reported WITHHELD — neither
# PASS (nothing was verified) nor FAIL (nothing is wrong). v1.0.0 instead
# opened the file unconditionally and died with FileNotFoundError.
CELLS = os.path.join(ROOT, "Q5_CELLS.jsonl")
HAVE_CELLS = os.path.isfile(CELLS)
rows = ([json.loads(l) for l in open(CELLS, encoding="utf-8") if l.strip()]
        if HAVE_CELLS else [])

results = []


def check(claim, in_paper, ok, source, detail=""):
    present = in_paper in PAPER
    verdict = "PASS" if (present and ok) else ("NOT-IN-PAPER" if not present else "FAIL")
    results.append((verdict, claim, source, detail))


def withheld(claim, in_paper, source, detail=""):
    """A claim whose evidence is intentionally not in the public package.

    Still checks that the sentence is in the paper, so a withheld check cannot
    silently cover a claim that was quietly dropped or reworded.
    """
    v = "WITHHELD" if in_paper in PAPER else "NOT-IN-PAPER"
    results.append((v, claim, source, detail))


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
         "representation-level result stated as decoder-level identity"),
        # --- withdrawn 2026-09-16 by the post-publication review of v1.0.0.
        ("lose nothing", "S2 medians are small but non-zero; 'nothing' is false"),
        ("bears no relation",
         "a near-orthogonal embedding pair is not absence of all relation"),
        ("rules out an implementation error",
         "two implementations agreeing is corroboration, never proof"),
        ("iteratively minimises exactly",
         "Griffin-Lim optimises STFT magnitude consistency, not this cepstral distance"),
        ("A metric cannot rank decoders on a quantity one of them is an optimiser for",
         "categorical; optimising a related quantity does not itself disqualify a metric"),
        ("orders the arms consistently",
         "two verified pairwise reversals across the encoder panel"),
        ("frozen and hashed before the\ndata it governs existed",
         "false for Gate 4's analysis layer and Q5 revisions 4-6"),
        ("Every published number regenerates from the released artifacts",
         "the withheld support-cell counts do not; v1.0.0 overclaimed"),
        # --- withdrawn 2026-09-17 by the final adversarial recheck of v1.0.1.
        # Q5 establishes no minimum detectable streaming change and no
        # equivalence threshold; G is a reference-distribution separation, not
        # a detection floor for a paired within-arm delta.
        ("this instrument can resolve", "asserts a resolution limit Q5 never established"),
        ("large enough to measure", "asserts a detection threshold Q5 never established"),
        ("no measured loss", "reads as below-threshold; use near-zero median additional change"),
        ("the aggregated `Q5_RESULTS.json` did not",
         "false for revision 6, whose guard lists Q5_RESULTS.json as present")):
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
# TTFA is parsed out of the anchor table rather than string-matched, because
# the v1.0.0 defect was quoting a STEADY-STATE p50 as the top of a FIRST-AUDIO
# range. A substring check for "375.91" cannot catch that; recomputing the
# range over the arms that have a numerical TTFA can.
anchor = [l for l in g3.splitlines()
          if l.startswith("| `") and l.count("|") >= 16]
ttfa = {}
for line in anchor:
    c = [x.strip() for x in line.strip("|").split("|")]
    arm = c[0].strip("`")
    try:
        ttfa[arm] = float(c[6])
    except ValueError:
        ttfa[arm] = None          # NOT ESTABLISHED / blocked
num = {a: v for a, v in ttfa.items() if v is not None}
lo, hi = (min(num.values()), max(num.values())) if num else (0, 0)
check("numerical TTFA range 1.37-27.64", "**first-audio latency (TTFA) spans 1.37 ms**",
      abs(lo - 1.37) < 5e-3 and abs(hi - 27.64) < 5e-3,
      "GATE3_MATRIX.md anchor table, recomputed", "%.2f-%.2f over %d arms"
      % (lo, hi, len(num)))
check("TTFA upper end is bigvgan22", "**to 27.64 ms** (`bigvgan22`)",
      max(num, key=num.get) == "bigvgan22", "GATE3_MATRIX.md recomputed",
      max(num, key=num.get))
check("melflow has no numerical TTFA", "its TTFA is **NOT\nESTABLISHED**",
      ttfa.get("melflow", 0) is None and "melflow" in ttfa,
      "GATE3_MATRIX.md melflow row")
check("melflow 375.91 is steady-state p50, not TTFA",
      "**375.91 ms is a steady-state p50**",
      "| `melflow` |" in g3 and "375.91" in g3 and ttfa.get("melflow") is None,
      "GATE3_MATRIX.md melflow row")
check("two arms fail EVERY tested size", "**Two** arms\nproduce streamed output",
      "(0/7 conditions)" in PAPER and "(0/6)" in PAPER,
      "GATE3_MATRIX.md E3 per-arm sweeps", "vocos_mel24 0/7, griffinlim 0/6")
check("focalcodec_12_5hz passes 2 of 5", "it passes **2 of 5** tested conditions",
      "640.8 ms" in g3, "GATE3_MATRIX.md E3")
check("qwen underrun 0.0013 / max 208.10", "**max\nof 208.10 ms**",
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
check("retention floor 0.4316 focalcodec_12_5hz", "down to **0.4316**",
      abs(ret["focalcodec_12_5hz"] - 0.4316) < 5e-5, "Q5_RESULTS.json",
      "%.4f" % ret["focalcodec_12_5hz"])
# The two encoder-ordering reversals that replaced "orders the arms consistently".
S_ = lambda a, e: q5["arms"][a][e]["sets"]["S"]["CROSS"]["R"]["median"]
rev1 = (S_("encodec24_q8", "ecapa") > S_("dualcodec_12hz_v1", "ecapa")
        and S_("encodec24_q8", "redimnet_M_vb2_ptn") < S_("dualcodec_12hz_v1", "redimnet_M_vb2_ptn")
        and S_("encodec24_q8", "redimnet_b6_lm") < S_("dualcodec_12hz_v1", "redimnet_b6_lm"))
rev2 = (S_("encodec_vocos", "ecapa") > S_("mimi_q32", "ecapa")
        and S_("encodec_vocos", "redimnet_M_vb2_ptn") > S_("mimi_q32", "redimnet_M_vb2_ptn")
        and S_("encodec_vocos", "redimnet_b6_lm") < S_("mimi_q32", "redimnet_b6_lm"))
check("encoder ordering reversal 1 (encodec24_q8 / dualcodec_12hz_v1)",
      "**The three encoders show broadly similar ordering, with\nsome pairwise reversals**",
      rev1, "Q5_RESULTS.json recomputed", "0.8781 vs 0.8621 under ecapa, reversed under both ReDimNets")
check("encoder ordering reversal 2 (encodec_vocos / mimi_q32)",
      "trails it under `redimnet_b6_lm` (0.8546 versus 0.8581)",
      rev2, "Q5_RESULTS.json recomputed", "reverses under redimnet_b6_lm only")
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
# v1.0.0 rounded these to "0.9999" and "−0.0000" and then called the result
# "lose nothing". The bounds are quoted at full precision now, and the audit
# checks the bounds rather than the rounding.
cs1 = [sd[a][e]["S1_offline_vs_streamed_median"] for a in causal for e in ENC]
cs2 = [sd[a][e]["S2_retention_delta_median"] for a in causal for e in ENC]
check("causal S1 bounds 0.999866-0.999946", "**0.999866–0.999946**",
      abs(min(cs1) - 0.999866) < 5e-7 and abs(max(cs1) - 0.999946) < 5e-7,
      "Q5_RESULTS.json streaming_detector", "%.6f-%.6f" % (min(cs1), max(cs1)))
check("causal S2 bounds -3.9e-5 to -5.3e-6",
      "**−3.9×10⁻⁵ to −5.3×10⁻⁶**",
      abs(min(cs2) + 3.882e-05) < 1e-8 and abs(max(cs2) + 5.312e-06) < 1e-8,
      "Q5_RESULTS.json streaming_detector", "%.3e-%.3e" % (min(cs2), max(cs2)))
check("S2 medians are non-zero, so 'lose nothing' is refused",
      "Nothing is claimed to be lost, and nothing is claimed to be preserved.",
      all(v < 0 for v in cs2),
      "Q5_RESULTS.json recomputed", "all 9 medians strictly negative")
check("no detection threshold is claimed",
      "establishes no minimum detectable streaming change\nand no equivalence threshold",
      True, "final adversarial recheck 2026-09-17")
check("focalcodec_25hz b6 S1 -0.013 stated as embedding-only",
      "*in this embedding\nspace*",
      abs(sd["focalcodec_25hz"]["redimnet_b6_lm"]["S1_offline_vs_streamed_median"]
          + 0.013) < 5e-4, "Q5_RESULTS.json", "-0.0130")
check("abstract states near-zero median change, not identity preserved",
      "show\n**near-zero median additional change** when streamed", True,
      "claim review finding 5")
check("abstract declares shared data limit",
      "**not** in *data*", True, "claim review finding 2")
s2 = {a: sd[a]["ecapa"]["S2_retention_delta_median"] for a in sd
      if sd[a]["ecapa"]["S2_retention_delta_median"] is not None and a not in causal}
check("worst streaming loss -0.742 dualcodec_25hz_v1",
      "**−0.742** (`dualcodec_25hz_v1`,\n`ecapa`)",
      min(s2, key=s2.get) == "dualcodec_25hz_v1" and abs(s2[min(s2, key=s2.get)] + 0.742) < 5e-4,
      "Q5_RESULTS.json", "%.4f" % s2[min(s2, key=s2.get)])
check("best non-causal -0.078 bigvgan22", "**−0.078** (`bigvgan22`, `ecapa`)",
      max(s2, key=s2.get) == "bigvgan22" and abs(s2[max(s2, key=s2.get)] + 0.078) < 5e-4,
      "Q5_RESULTS.json", "%.4f" % s2[max(s2, key=s2.get)])
check("the -0.078..-0.742 range is labelled as S2, not cosine",
      "*on the retention delta*", True, "claim review 2026-09-16 finding 4")

mk = sum(1 for a, per in q5["arms"].items() for e, blk in per.items()
         for S, sb in blk["sets"].items() for st, v in sb.items() if v["marker"])
check("69 impostor-range markers", "69 `APPROACHES IMPOSTOR RANGE` markers",
      mk == 69, "Q5_RESULTS.json recomputed", str(mk))

# support counts, recomputed from the withheld per-recording rows
CLAIM_SUPPORT = ("**17,020 of 31,248 offline cells and 26,147 of 27,776 "
                 "streamed cells")
if HAVE_CELLS:
    sup = {}
    for cond in ("offline", "streamed"):
        sub = [r for r in rows if r["condition"] == cond]
        c = collections.Counter(str(r["support_mcd"]) for r in sub)
        sup[cond] = (c["NOT COMPARABLE - OUTSIDE VALIDATED SUPPORT"] // 3,
                     len(sub) // 3, c["MEASURED"] // 3)
    check("support counts are CELLS not rows", CLAIM_SUPPORT,
          sup["offline"][:2] == (17020, 31248)
          and sup["streamed"][:2] == (26147, 27776),
          "Q5_CELLS.jsonl recomputed", str(sup))
else:
    withheld("support counts are CELLS not rows", CLAIM_SUPPORT,
             "Q5_CELLS.jsonl (withheld)",
             "needs per-recording rows; not reconstructible from aggregates")

check("1,512 source recordings", "**1,512\ndistinct source recordings**",
      man["corpus"]["counts"]["distinct_recordings"] == 1512,
      "PUBLICATION_MANIFEST.json")
check("device delta <= 2.5e-04", "≤ 2.5e-04",
      os.path.isfile(os.path.join(ROOT, "Q5_DEVICE_EQUIVALENCE.json")),
      "Q5_DEVICE_EQUIVALENCE.json")

# ---- report
print("CLAIM AUDIT — PAPER.md against frozen artifacts\n")
print("artifact root: %s" % ROOT)
print("per-recording rows (Q5_CELLS.jsonl): %s\n"
      % ("present" if HAVE_CELLS else "WITHHELD - not published"))
w = collections.Counter(r[0] for r in results)
for v, c, s, d in results:
    print("%-13s %-44s %-34s %s" % (v, c, s, d))
print("\n%s" % dict(w))
print("\nFAIL or NOT-IN-PAPER means the claim could not be traced; both block release.")
if w["WITHHELD"]:
    print("WITHHELD means the claim's evidence is intentionally not published.")
    print("  It is NOT a pass. Re-running inside the private tree checks it.")
raise SystemExit(1 if (w["FAIL"] or w["NOT-IN-PAPER"]) else 0)
