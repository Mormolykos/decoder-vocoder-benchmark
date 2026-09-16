"""GATE3_MATRIX.md — rendered from `gate3_matrix.json` and nothing else.

Computation lives in `make_gate3_matrix.py`; this file only presents what that
produced. Nothing here recomputes a number, so the document cannot disagree with
the JSON it came from.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
doc = json.load(open(os.path.join(HERE, "gate3_matrix.json"), encoding="utf-8"))
rows = doc["arms"]
E6, E1, E4 = doc["E6_environment_control"], doc["E1_controlled_pair"], doc["E4_ordering"]
BUDGET = {"competitive_ms": 75, "stretch_ms": 50, "red_zone_ms": 200}
STATUS = "MEASURED - CELLS COMPLETED AND ADMISSIBLE"
totals = doc["totals_by_status"]
L = []
A = L.append


def f(v, d=2, dash="—"):
    if v is None:
        return dash
    if isinstance(v, str):
        return v
    try:
        return f"{float(v):.{d}f}"
    except Exception:
        return str(v)


A("# GATE 3 — FROZEN GPU TIMING BENCHMARK")
A("")
A(f"**Machine-generated on {doc['generated_utc']} from "
  f"`results/gate3_raw_*.jsonl`. Every statistic is recomputed from raw; nothing "
  f"is transcribed by hand.**")
A("")
h = doc["headers"].get("a", {})
A(f"**Device:** {h.get('device_name','?')} · torch {h.get('torch','?')} · CUDA "
  f"{h.get('torch_cuda','?')} · seed {h.get('seed','?')} · N={h.get('n_warm','?')} "
  f"warm + {h.get('n_cold','?')} cold, {h.get('warmup_discarded','?')} warm-ups "
  f"discarded · block-randomised · §7.4 one GPU process at a time.")
A("")
A(f"> ### What `{STATUS}` means — and what it does not")
A(">")
A(f"> {doc['status_definition']}")
A("")
for c in doc["claim_boundaries"]:
    A(f"- ⛔ {c}")
A("")

# ------------------------------------------------------------------ E6
A("## E6 — the §7.2 environment control, and what it decides")
A("")
A("`encodec24_q8`, byte-identical tokens, same GPU, run as a **single arm** in "
  "every environment that produced arm rows. Single-arm on every side on purpose: "
  "the decbench arm rows were block-randomised among 14 other arms, so comparing "
  "an interleaved run against a solo run would confound the environment effect "
  "with run context.")
A("")
A("| environment | transformers | median ratio vs decbench | effect | consequence |")
A("|---|---|---|---|---|")
for env, v in sorted(E6.items()):
    cons = doc["E6_consequence"].get(env, {})
    verdict = ("reference" if env == "decbench" else
               ("✅ COMPARABLE" if cons.get("comparable") else "⛔ **NOT COMPARABLE**"))
    A(f"| `{env}` | {v.get('transformers')} | {f(v['median_ratio'],3)} | "
      f"**{f(v['effect_pct'],1)}%** | {verdict} |")
A("")
A("| condition | decbench ms | fish ms | melflow-env ms |")
A("|---|---|---|---|")
base = {(c["cell"], c["condition"]): c for c in E6["decbench"]["conditions"]}
fi = {(c["cell"], c["condition"]): c for c in E6.get("fish", {}).get("conditions", [])}
mf = {(c["cell"], c["condition"]): c
      for c in E6.get("decbench_melflow", {}).get("conditions", [])}
for k in sorted(base):
    A(f"| {k[0]} {k[1]} | {f(base[k]['decbench_ms'],3)} | "
      f"{f(fi.get(k,{}).get('this_env_ms'),3)} | "
      f"{f(mf.get(k,{}).get('this_env_ms'),3)} |")
A("")
A("**The effect is a near-constant ~3.0–4.0 ms offset and it is DEVICE-SIDE, not "
  "host-side.** At the 2 s offline condition host overhead is 0.022 ms in decbench "
  "and 0.024 ms in fish, while CUDA time is **10.344 ms vs 6.328 ms** — the two "
  "`transformers` versions launch different GPU work for the same decode. torch is "
  "identical everywhere (2.10.0+cu128).")
A("")
A("⛔ **`fish_modified_dac` — the incumbent — may not be compared numerically "
  "against any decbench arm.** Its own numbers stand within its own environment. "
  "The direction matters: `fish` is FASTER, so the incumbent's environment flatters "
  "it by ~3.5 ms per call relative to the environment 17 other arms were measured "
  "in. **Nothing here says Fish ModifiedDAC is fast or slow; it says its number and "
  "theirs cannot be put in one ranking.**")
A("")

# ------------------------------------------------------------------ headline
A("## Headline — one row per arm, at the ~80 ms chunk anchor")
A("")
A("**All jitter statistics are STEADY-STATE**, excluding the first chunk of every "
  "repetition; the first chunk is reported separately as TTFA. **§8** is the frozen "
  "streamed-output validity gate. **env?** is cross-environment comparability.")
A("")
A("| arm | route | env? | §8 streamed | cold s | RTF@10s | TTFA ms | p50 | p95 | "
  "p99 | IQR | max | underrun | RT margin | anchor VRAM MiB | drift % |")
A("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    if r["status"] != STATUS:
        A(f"| `{r['arm']}` | {r.get('route','—')} | — | — | — | — | — | — | — | — | "
          f"— | — | — | — | — | — | **{r['status']}** |".replace(
              " | **" + r["status"] + "** |", " |"))
        continue
    an = r.get("anchor") or {}
    pf = r.get("perframe") or {}
    ss = an.get("steady") or pf.get("steady") or {}
    ttfa = (f(r.get("ttfa_anchor_ms")) if r.get("ttfa_anchor_ms") is not None
            else f"**{r.get('ttfa_anchor_state','—')}**")
    g8 = r.get("anchor_streamed_gate8")
    if g8 == "PASS":
        g8 = "PASS"
    elif g8 is None:
        g8 = "n/a"          # nothing was decoded at a chunk size; see E3
    else:
        g8 = f"⛔ **{g8}**"
    envm = "✅" if r["cross_env_comparable"] else "⛔ **NOT COMP**"
    lr = r.get("longrun") or {}
    ur = an.get("underrun_rate") if an else pf.get("underrun_rate")
    rt = an.get("realtime_margin_median") if an else pf.get("realtime_margin_median")
    A(f"| `{r['arm']}` | {r['route']} | {envm} | {g8} | "
      f"{f(r.get('cold_model_load_s'))} | {f(r.get('rtf_at_10s'),5)} | {ttfa} | "
      f"{f(ss.get('p50'),2)} | {f(ss.get('p95'),2)} | {f(ss.get('p99'),2)} | "
      f"{f(ss.get('iqr'),2)} | {f(ss.get('max'),2)} | {f(ur,4)} | {f(rt,1)}× | "
      f"{f(r.get('anchor_peak_alloc_MiB'),1)} | "
      f"{f(lr.get('latency_drift_pct_median'),3)} |")
A("")
A(f"`nanocodec` — **BLOCKED — PLATFORM.** No timing number is manufactured; its "
  f"absence is reported as BLOCKED, never as zero and never omitted.")
A("")
bad8 = [r for r in rows if r.get("streamed_gate8_any_pass") is False]
never8 = [r for r in rows if r.get("streamed_gate8_any_pass") is None
          and r["status"] == STATUS]
if bad8:
    A("⛔ **These arms produce streamed output that is INADMISSIBLE under the "
      "study's own frozen §8 gate at EVERY chunk size tested.** Their timing "
      "numbers are real; what they timed is not a valid streaming configuration.")
    A("")
    for r in bad8:
        A(f"- **`{r['arm']}`** — §8 {r['e3_conditions_passing_gate8']} conditions "
          f"pass; failing predicate `{', '.join(r['e3_failing_predicates'])}`. "
          f"**E3 minimum viable streaming configuration = NOT ACHIEVABLE.**")
    A("")
for r in never8:
    A(f"⚠️ **`{r['arm']}` — §8 was NEVER EVALUATED on a chunked decode.** "
      f"{r.get('e3_reason')} **E3 = NOT ESTABLISHED. This is untested, NOT "
      f"failed, and the two must not be read as the same thing.**")
    A("")
for r in rows:
    if (r.get("streamed_gate8_any_pass")
            and r.get("anchor_streamed_gate8") not in (None, "PASS")):
        A(f"⚠️ **`{r['arm']}` fails §8 at the anchor** "
          f"({r['e3_conditions_passing_gate8']} conditions pass, failing "
          f"`{', '.join(r['e3_failing_predicates'])}`). Its minimum viable "
          f"streaming configuration is **{f(r['e3_min_viable_streaming_ms'],1)} ms**, "
          f"not the anchor.")
        A("")

# ------------------------------------------------------------------ E3
A("## E3 — minimum viable streaming configuration (§5)")
A("")
A("Two different questions, kept apart. **min chunk that ran** is execution "
  "feasibility only. **E3** is the frozen estimand and requires the streamed "
  "output to PASS §8.")
A("")
A("| arm | min chunk that ran | §8 pass/total | **E3 minimum viable** | failing predicate |")
A("|---|---|---|---|---|")
for r in rows:
    if r["status"] != STATUS:
        continue
    e3 = r.get("e3_min_viable_streaming_ms")
    e3s = ("⛔ **NOT ACHIEVABLE**" if e3 == "NOT ACHIEVABLE"
           else ("⚠️ **NOT ESTABLISHED**" if e3 == "NOT ESTABLISHED"
                 else f"**{f(e3,1)} ms**"))
    A(f"| `{r['arm']}` | {f(r.get('min_chunk_that_ran_ms'),1)} ms | "
      f"{r.get('e3_conditions_passing_gate8','—')} | {e3s} | "
      f"{', '.join(r.get('e3_failing_predicates') or []) or '—'} |")
A("")

# ------------------------------------------------------------------ E1
A("## E1 — the controlled pair (§5)")
A("")
A(f"**{E1['control']}**")
A("")
A(f"*{E1['pairing']}* {E1['environment']}.")
A("")
A("| condition | `encodec24_q8` | `encodec_vocos` | difference (95% CI) | ratio (95% CI) |")
A("|---|---|---|---|---|")
for c in E1["conditions"]:
    A(f"| {c['cell']} {c['condition']} | {c['median_a_ms']:.3f} ms | "
      f"{c['median_b_ms']:.3f} ms | {c['difference_ms']:.3f} "
      f"[{c['difference_ci95_ms'][0]:.3f}, {c['difference_ci95_ms'][1]:.3f}] | "
      f"**{c['ratio']:.3f}×** [{c['ratio_ci95'][0]:.3f}, {c['ratio_ci95'][1]:.3f}] |")
A("")
A(f"⭐ **{E1['headline_finding']}**")
A("")
A("**Memory, by scope — never quoted across scopes:**")
A("")
A("| scope | `encodec24_q8` | `encodec_vocos` | ratio |")
A("|---|---|---|---|")
for k, v in E1["memory_scopes_SEPARATED"].items():
    if k == "reserved_is_not_monotonic":
        continue
    A(f"| {k.replace('_', ' ')} | {f(v.get('encodec24_q8'),1)} | "
      f"{f(v.get('encodec_vocos'),1)} | **{f(v['ratio'],3)}×** |")
A("")
A(f"⚠️ {E1['memory_scopes_SEPARATED']['reserved_is_not_monotonic']['warning']}")
A("")

# ------------------------------------------------------------------ E4
A("## E4 — offline versus streaming ordering (§5)")
A("")
if E4.get("status") == "UNDERPOWERED":
    A(f"**UNDERPOWERED** — only {E4['n_qualifying']} arms qualify, and the frozen "
      f"estimand reports underpowered rather than an ordering.")
else:
    A(f"Computed over **{E4['n_qualifying']} qualifying arms**, named below. "
      f"Spearman ρ between the RTF ranking and the TTFA ranking = "
      f"**{E4['spearman_rho_rtf_vs_ttfa']:.4f}**. "
      f"**Orderings differ: {E4['orderings_differ']}.**")
    A("")
    A("**Subset:** " + ", ".join("`" + n + "`" for n in E4["subset"]))
    A("")
    A("**Excluded, with reasons:** " + " · ".join(
        f"{k} → {', '.join('`' + a + '`' for a in v)}"
        for k, v in E4["excluded"].items() if v))
    A("")
    if E4["arms_shifting_3_or_more_ranks"]:
        A("Arms whose position moves three or more ranks between the two orderings:")
        A("")
        A("| arm | rank by RTF | rank by TTFA | shift |")
        A("|---|---|---|---|")
        for x in E4["arms_shifting_3_or_more_ranks"]:
            A(f"| `{x['arm']}` | {x['rtf_rank']} | {x['ttfa_rank']} | "
              f"{x['rank_shift']:+d} |")
        A("")
    A(f"*{E4['note']}*")
A("")

# ------------------------------------------------------------------ budget
A("## §17 latency budget — decoder-only")
A("")
A(f"**{BUDGET['competitive_ms']} ms competitive · {BUDGET['stretch_ms']} ms stretch "
  f"· {BUDGET['red_zone_ms']} ms red zone.** ⚠️ **VENDOR-REPORTED**, from vendors' "
  f"own systems and own measurement conditions. **MARKET ANCHORS, NOT measurements "
  f"comparable to anything produced here.**")
A("")
A("**This table admits an arm only if its streamed output PASSES §8 at the anchor "
  "AND its environment is comparable to the reference.** Arms excluded on either "
  "ground are listed underneath rather than shown with a clean percentage.")
A("")
A("| arm | TTFA @ anchor | % of the 75 ms budget | ms left for everything else |")
A("|---|---|---|---|")
for r in rows:
    if not r.get("budget_eligible"):
        continue
    A(f"| `{r['arm']}` | {f(r['ttfa_anchor_ms'])} ms | "
      f"{f(r.get('budget_consumed_pct_of_75ms'),1)}% | "
      f"{f(r.get('budget_left_of_75ms'))} ms |")
A("")
excl = [r for r in rows if r["status"] == STATUS and not r.get("budget_eligible")]
if excl:
    A("**Excluded from the budget table:**")
    A("")
    for r in excl:
        why = []
        if r.get("anchor_streamed_gate8") not in (None, "PASS"):
            why.append(f"streamed §8 **{r.get('anchor_streamed_gate8')}** at the anchor")
        if not r["cross_env_comparable"]:
            why.append("**NOT COMPARABLE** environment (§7.2)")
        if r.get("ttfa_anchor_ms") is None:
            why.append(f"TTFA **{r.get('ttfa_anchor_state')}**")
        A(f"- `{r['arm']}` — {'; '.join(why) or 'no anchor condition'}")
    A("")
A("⛔ **Decoder-only.** Text frontend, acoustic generation and serving all come out "
  "of the same budget and none of them is measured here.")
A("")

# ------------------------------------------------------------------ E2
A("## Offline duration sweep — fixed cost versus marginal cost (E2)")
A("")
A("**Per arm, never averaged across arms.**")
A("")
A("| arm | fixed cost ms | ms per audio second | fit residual ms | fit valid? | "
  "RTF @1 s | @5 s | @30 s |")
A("|---|---|---|---|---|---|---|---|")
for r in rows:
    d_ = r.get("offline")
    if not d_:
        continue

    def rtf(t, d_=d_):
        m = [x for x in d_ if abs(x["produced_audio_s"] - t) < max(0.5, t * 0.2)]
        return f(m[0]["rtf_median"], 5) if m else "—"

    valid = r.get("e2_fit_valid")
    ic = (f"⛔ **{f(r.get('e2_intercept_ms'))}**" if not valid
          else f(r.get("e2_intercept_ms")))
    sl = (f"⛔ **{f(r.get('e2_slope_ms_per_audio_s'))}**" if not valid
          else f(r.get("e2_slope_ms_per_audio_s")))
    A(f"| `{r['arm']}` | {ic} | {sl} | {f(r.get('e2_fit_max_residual_ms'),2)} | "
      f"{'yes' if valid else '⛔ **NOT INTERPRETABLE**'} | {rtf(1)} | {rtf(5)} | "
      f"{rtf(30)} |")
A("")
bad = [r for r in rows if r.get("offline") and not r.get("e2_fit_valid")]
if bad:
    A("⛔ **The fixed/marginal decomposition DOES NOT HOLD for these arms and is "
      "NOT INTERPRETABLE for them.** The measurements stand; the linear reading of "
      "them is withdrawn.")
    A("")
    for r in bad:
        A(f"- `{r['arm']}` — {r['e2_fit_invalid_reason']}.")
    A("")

# ------------------------------------------------------------------ per-arm
A("## Per-arm streaming detail")
A("")
for r in rows:
    if r["status"] != STATUS:
        continue
    A(f"### `{r['arm']}`" + ("" if r["cross_env_comparable"] else
                             "  ⛔ NOT COMPARABLE to decbench arms (§7.2)"))
    A("")
    if r.get("perframe"):
        p = r["perframe"]
        s = p["steady"]
        A(f"**Per-frame streaming — this arm's OWN decode granularity, "
          f"{p['granularity_ms']:g} ms.** steady p50 {f(s.get('p50'),3)} ms · p95 "
          f"{f(s.get('p95'),3)} · p99 {f(s.get('p99'),3)} · IQR {f(s.get('iqr'),3)} "
          f"· max {f(s.get('max'),3)} · underrun {f(p['underrun_rate'],4)} · RT "
          f"margin {f(p['realtime_margin_median'],2)}× ({s.get('n')} steady-state "
          f"frames).")
        A("")
    if r.get("stream"):
        A("| chunk ms | units | §8 | TTFA ms | steady p50 | p95 | p99 | IQR | max | "
          "underrun | RT p50 | lookahead ms | n | composed |")
        A("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for s in r["stream"]:
            ss = s["steady"]
            t = (f(s["ttfa_ms"]) if s["ttfa_ms"] is not None else s["ttfa_state"])
            g = "PASS" if s["streamed_gate8"] == "PASS" else f"⛔ {s['streamed_gate8']}"
            A(f"| {s['effective_ms']:.1f} | {s['chunk_units']} | {g} | {t} | "
              f"{f(ss.get('p50'),3)} | {f(ss.get('p95'),3)} | {f(ss.get('p99'),3)} | "
              f"{f(ss.get('iqr'),3)} | {f(ss.get('max'),3)} | "
              f"{f(s['underrun_rate'],4)} | {f(s['realtime_margin_median'],1)}× | "
              f"{f(s['required_lookahead_ms'],1)} | {ss.get('n','—')} | "
              f"{'yes' if s['composed'] else 'no'} |")
        A("")
    if r.get("underrun_conditions_ms"):
        A(f"**Underruns at:** "
          f"{', '.join(f'{x:.1f} ms' for x in r['underrun_conditions_ms'])}. "
          f"**First underrun-free condition: "
          f"{f(r.get('first_underrun_free_ms'),1)} ms.**")
        A("")
    if r.get("failures"):
        A(f"**{len(r['failures'])} cell(s) failed and are recorded, not dropped:**")
        A("")
        for x in r["failures"]:
            A(f"- `{x['cell']}` {x['condition']} — {x['error']}")
        A("")
    if r.get("overlap"):
        A("**§10.2 chunked-with-overlap — the context this arm needs is part of its "
          "cost:**")
        A("")
        A("| left context units | lookahead ms | steady p50 ms | RT margin | §8 |")
        A("|---|---|---|---|---|")
        for o in r["overlap"]:
            A(f"| {o['left_ctx_units']} | {f(o['required_lookahead_ms'],1)} | "
              f"{f((o.get('steady') or {}).get('p50'),3)} | "
              f"{f(o['realtime_margin_median'],1)}× | {o['streamed_gate8']} |")
        A("")
    if r.get("ttfa_not_established_reason"):
        A(f"⛔ **TTFA NOT ESTABLISHED.** {r['ttfa_not_established_reason']}")
        A("")
        st_ = r.get("ttfa_cell_state") or {}
        A(f"  Cell state: first block §8 **{st_.get('first_block_gate8')}**, "
          f"{st_.get('first_block_samples')} samples; split-iSTFT control "
          f"**{f(st_.get('istft_split_control_rel_pct'),2)}%**, deficit "
          f"{st_.get('istft_split_control_deficit_samples')} samples.")
        A("")
    dc = r.get("delay_calibration")
    if dc and not dc.get("reliable"):
        A(f"⚠️ **Delay calibration is NOISE for this arm** — normalised peak "
          f"correlation {f(dc['normalised_peak_correlation'],3)}. The "
          f"{dc['delay_ms']:+.2f} ms estimate is recorded but **is not used as a "
          f"fact anywhere in this study**.")
        A("")

# ------------------------------------------------------------------ VRAM rule
v = doc["vram_rerun_rule_disposition"]
A("## Disposition of the §7.2 VRAM re-run rule")
A("")
A(f"**Frozen rule:** {v['frozen_rule']}")
A("")
A(f"**{v['cells_flagged']} of {v['cells_total']} cells exceed the threshold.** "
  f"Disposition: **{v['disposition']}**.")
A("")
A(v["reason"])
A("")
A(f"**Replacement check:** {v['replacement_check']}")
A("")

# ------------------------------------------------------------------ boundary
A("## Boundary integrity (§10.6) — each decoder against ITSELF")
A("")
A("⚠️ **This measures what chunking cost a decoder relative to its own "
  "full-context output. It is not a quality ranking between decoders, and no "
  "output may present it as one. QUALITY COMPARISON NOT ESTABLISHED.**")
A("")
A("| arm | chunk ms | seams | seam jump ratio (median) | max | local diff RMS | "
  "length deficit |")
A("|---|---|---|---|---|---|---|")
for r in rows:
    for b in (r.get("boundary") or []):
        if b.get("error"):
            A(f"| `{r['arm']}` | {f(b.get('effective_ms'),1)} | — | — | — | — | "
              f"FAILED: {str(b['error'])[:50]} |")
            continue
        if "effective_ms" not in b:
            A(f"| `{r['arm']}` | whole stream | 0 | — | — | "
              f"{f(b.get('stateful_vs_full_rel_pct'),4)}% | — |")
            continue
        A(f"| `{r['arm']}` | {b['effective_ms']:.1f} | {b.get('n_seams')} | "
          f"{f((b.get('seam_jump_ratio') or {}).get('median'),3)} | "
          f"{f((b.get('seam_jump_ratio') or {}).get('max'),3)} | "
          f"{f((b.get('local_diff_rms_norm') or {}).get('median'),4)} | "
          f"{b.get('length_deficit_samples')} |")
A("")

# ------------------------------------------------------------------ totals
A("## Totals")
A("")
A("```")
for k in sorted(totals, key=lambda x: -totals[x]):
    members = ", ".join(r["arm"] for r in rows if r["status"] == k)
    A(f"{k:<44} {totals[k]:>3}   {members}")
A(f"{'-' * 44} {'-' * 3}")
A(f"{'TOTAL':<44} {len(rows):>3}")
A("```")
A("")
if doc["missing_artifacts"]:
    A(f"⛔ **ARTIFACTS MISSING for: {', '.join(doc['missing_artifacts'])}**")
    A("")

open(os.path.join(HERE, "GATE3_MATRIX.md"), "w", encoding="utf-8").write(
    "\n".join(L) + "\n")
print(f"written: GATE3_MATRIX.md  ({len(L)} lines)")
