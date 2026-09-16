# GATE 4 — STAGE 2 ANALYSIS SPECIFICATION

**A POST-HOC DECLARED ANALYSIS SPECIFICATION.** Written 2026-09-13, after four
audits of the results. Frozen by `freeze_gate4_stage2.py`.

⛔ **REVISION 4 CORRECTION (audit 3, M5).** This document previously opened
*"BEFORE the aggregation code it governs was changed"*, and the freeze tool
claimed the two-stage hashing **proved** that ordering. **The claim is
WITHDRAWN.** No implementation hash is taken at spec-freeze time, both timestamps
are local and unanchored, this tree is not a git repository, and the claim was
measurably **false** for `gate4_determinism.py`, whose mtime precedes the spec
freeze by 2 h 25 m and which was never changed to match this document. **What is
claimed now, and all that is claimed: the declared specification and
implementation are fixed, hashed and auditable.** This is the answer to BLOCKING finding B1:
the layer that turns measured cells into published labels had no frozen
specification, and its defect-discovery rate had not converged — four audit
rounds, four new findings, each in the same ~600 unfrozen lines, each after the
author declared the previous list complete.

---

## 0. ⛔ WHAT THIS DOCUMENT IS, AND WHAT IT CANNOT BE

**This is a SPECIFICATION FREEZE. It is NOT a pre-registration, and it must
never be described as one.**

`GATE4_PREREG.md` was written before any decoder output existed. **This document
is written after four audits of the results.** Every constant in §7 was chosen by
an author who has seen the data those constants classify. Freezing them now makes
them **declared, fixed and auditable**; it does not make them blind, and nothing
done later can make them blind.

> ⭐ **THE PERMANENT LIMITATION, STATED ONCE AND NEVER REMOVED:** the Stage 2
> classification taxonomy was specified with knowledge of the results. It may
> therefore be reported as **a declared and reproducible way of reading the
> numbers**, and never as an independent confirmation of them. The frozen
> **verdicts** (§6) do not depend on it — they come from `GATE4_PREREG.md`
> §11.1 alone.

**Scope.** This document governs `gate4_metrics.py --aggregate`, `--prove`,
`gate4_determinism.py`, `gate4_retro_sha.py`, and the evidence-package
generator. ⛔ **It governs nothing inside the Gate 4 freeze.** `gate4_lib.py`,
`gate4_support.py`, the instrument floors, the corpus and the pre-registration
are frozen elsewhere, verify at drift 0, and **are not reopened.**

**Precedence.** `GATE4_PREREG.md` **outranks this document on every point.**
Where this document appears to differ, the pre-registration wins and this
document is the defect.

---

## 1. THE EXPERIMENTAL UNIT — S1

> **`recording = (speaker, state, index)`**

⛔ **This repairs MAJOR-1.** The shipped code used `(speaker, index, rung_s)`,
which is wrong in both halves:

- **`state` was omitted.** The corpus is **parallel** — the same 31 texts are
  performed in all six states — so `(speaker, index)` silently merged
  performances the pre-registration defines as **different recordings**.
  §11.2.1: *"one performance of one text, by one speaker, in one state."*
  ⛔ **REVISION 6: THE CORPUS-KEY COUNT IS WITHDRAWN.** Revisions 3–5 quoted a
  descriptive statistic here ("343 span all six states", then "238 span all six;
  343 span more than one"). **It was computed ad-hoc, persisted in no artifact,
  and is not replaced with another hand-computed pair.** An unpersisted
  descriptive number must not support a methodology decision.

  **The repair rests on the frozen text and on a reproduced check, which is
  sufficient:** §11.2.1 DEFINES the unit as one performance by one speaker in
  one state, so `state` belongs in the key; §11.2.2 REQUIRES a recording's
  ladder cells to travel together, so `rung_s` must not split a cluster; and the
  repaired clustering reproduces independently — `dac44｜mimi_q8` 340 → **731**,
  `bigvgan22｜griffinlim` 434 → **1416**, with **0 recordings mapping to more
  than one stratum**.
- **`rung_s` was included**, splitting one recording's duration-ladder cells
  into five separate clusters. §11.2.2: *"a recording that carries five ladder
  cells contributes all five or none."* **Measured: 56 ladder recordings were
  split five ways each.**

> **S1.1 LADDER RUNGS TRAVEL TOGETHER.** Every cell sharing a `recording` key —
> every ladder rung of that performance — belongs to that one cluster and is
> drawn with it or not at all. `rung_s` is **never** part of a cluster key.

> **S1.2** A cluster's cells are reduced to **one value per recording** (the
> median over its cells) before that recording enters any higher level. Cells
> are repeated measures, never independent observations.

---

## 2. THE STRATUM — S2

> **`group = (speaker, state)`**, derived from the recording key, never assigned
> separately.

⛔ The shipped code stored `grp_of[recording] = group` as **last-write-wins**, so
a merged cluster's stratum label was an artifact of sort order. Deriving the
group from S1's key removes the possibility by construction: a recording belongs
to exactly one `(speaker, state)` because `state` is part of its identity.

---

## 3. THE AGGREGATION HIERARCHY — S3

> **`cell → recording → (speaker × state) → arm`** (`GATE4_PREREG.md` §11.2.3),
> **median at every level.**

1. **cell → recording:** median of the recording's cells (S1.2).
2. **recording → (speaker × state):** median of the recording values in the
   group.
3. **(speaker × state) → arm:** median across groups.

⛔ **No flat median over cells anywhere in the primary analysis.** The flat
value is retained per estimate as `deviation_flat_median_cells` for the record.

---

## 4. THE INTERVAL PROCEDURE — S4

Inherited verbatim from `GATE4_PREREG.md` §11.2.2 and **not restated as a new
rule**: cluster bootstrap over **recordings** with replacement,
`n_resamples = 4000`, `seed = 20260911`, **95 % percentile**, point estimate the
**median**. Paired estimands draw the recording **once** and take both arms from
that draw.

**S4.1** Every resample recomputes the full S3 hierarchy. The point estimate is
S3 applied to the observed clusters.

---

## 5. REFUSAL AND DEGENERACY — S5

A pair is refused, as a **first-class recorded state**, never a blank:

| rule | condition | verdict |
|---|---|---|
| **S5.1 no data** | no paired admissible cell exists | `QUALITY COMPARISON NOT ESTABLISHED` |
| **S5.2 degenerate interval** | `n_recordings < 3` **or** `n_groups < 2` | `QUALITY COMPARISON NOT ESTABLISHED` |

**S5.3 Why degeneracy fails CLOSED and may never be labelled `ORDERED`.** With
one or two clusters every resample redraws the same data, the percentile interval
collapses, and §11.1 condition 5(a) would be satisfied **by arithmetic rather
than by evidence**. §11.1 defines `ORDERED, SEPARATION NOT ESTABLISHED` as a
state that **displays its interval**; a pair with no usable interval cannot wear
that label.

**S5.4** `n_groups < 2` is declared here as a rule of this specification.
**MEASURED: it has never fired** — it is retained because S1's repair changes the
group structure and it is the guard for the case S2 describes.

⛔ **S5.5 THERE IS NO MINIMUM-CELL REFUSAL IN THE PRIMARY ANALYSIS.** The
withdrawn `n >= 10` rule stays withdrawn, reported only as a labelled post-hoc
sensitivity block.

---

## 6. THE VERDICTS — S6. INHERITED, NOT REDEFINED

> **`GATE4_PREREG.md` §11.1 conditions 1–6 are applied literally and are the
> ONLY source of a verdict.** In particular condition 5(b) tests the **effect
> magnitude** — the **point estimate** — against the floor. **This
> specification does NOT strengthen it to require the interval**, because
> tightening a frozen rule after seeing the data is the same defect as
> loosening it.

| verdict | when |
|---|---|
| `SEPARATION ESTABLISHED (mcd, REFERENCE-COMMON, round trip)` | conditions 1–6 all hold and the pair is not refused under S5 |
| `ORDERED, SEPARATION NOT ESTABLISHED` | a usable interval exists and condition 5(a) or 5(b) fails |
| `QUALITY COMPARISON NOT ESTABLISHED` | refused under S5, or condition 4 (determinism) unmet |

**S6.1** The floor is the **MAXIMUM ABSOLUTE** floor over contributing states
(M1), never a fraction, never a mean. An unknown state **fails closed**.

---

## 7. THE CLASSIFICATION TAXONOMY — S7. DECLARATIVE, AND NOT A VERDICT

⛔ **Every constant below is declared here because it was previously undeclared.
None of them changes a §6 verdict. They classify the STRENGTH OF EVIDENCE behind
a verdict that has already been reached.** Read §0 before using any of them.

### 7.1 The constants

| name | value | what it is | why this value |
|---|---|---|---|
| `WELL_POWERED_MIN_PAIRED` | **100** | paired cells below which a separation is called thin | ⚠️ **chosen by the author after seeing the data.** The observed distribution is bimodal with nothing between **17 and 714**, so any value in that gap yields the identical partition. 100 is the round number inside it. **Declared, not derived.** |
| `LOW_COVERAGE_PCT` | **5.0** | support coverage below which an arm's admitted cells are treated as selection-conditioned | ⚠️ **chosen by the author after seeing the data.** The observed distribution is bimodal with nothing between **1.0 % and 31.3 %**; any value in that gap yields the identical partition. **Declared, not derived.** |
| `FLOOR_UNCERTAINTY_QUANTILES` | **(2.5, 97.5)** | the floor's own 95 % interval | matches the study's declared CI |
| `FLOOR_BOOT_RESAMPLES`, `FLOOR_BOOT_SEED` | **4000**, **20260911** | bootstrap of the floor draws | the study's frozen resample count and seed |

⭐ **The bimodality is what makes these two constants honest rather than tuned:
there is no value in either gap that produces a different answer.** That is
stated as a measured property, and it is not a claim that the constants were
chosen blind. They were not.

### 7.2 The floor's own uncertainty — derived, not invented

`GATE4_PREREG.md` §6.1.4 limitation 5 already declares the instrument floor to be
**a quantile of 16 deterministic draws**, with per-state hi/lo spanning
**1.3×–2.2×**. That declared uncertainty is used directly:

> **S7.2** Bootstrap the state's own 16 frozen draws from `fuzz_gate4_lib.json`
> (`FLOOR_BOOT_RESAMPLES`, `FLOOR_BOOT_SEED`), take the same 0.95 quantile inside
> each resample, and read the **97.5th percentile** as `floor_hi`.
> **MEASURED, pooled (Scared): floor 105.07, 95 % CI [71.37, 120.81].**

⚠️ **Revision 3 of this document printed `[70.74, 120.81]`. The lower bound did
not reproduce** — `floor_uncertainty()` returns **71.3740**. The 70.74 came from
an exploratory run that seeded the generator once for all six states; the frozen
function seeds per state. It was a hand-typed literal, persisted in no artifact —
**the exact defect class S9.1 exists to prevent, recurring inside the revision
that declared it fixed.** Every value is now written to
`GATE4_RESULTS.json → floor_uncertainty`.

⛔ **S7.2.1 — `floor_hi` IS SATURATED, AND THE HEADLINE TURNS ON IT.**
**MEASURED: `floor_hi` equals the MAXIMUM of the 16 draws exactly, in all six
states.** A 0.95 quantile of a resample cannot exceed the sample maximum, so the
bootstrap is **pinned by construction**: SD 0.0000 across 41 seeds, identical
under all five numpy quantile methods. **`FLOOR_BOOT_RESAMPLES` and
`FLOOR_BOOT_SEED` therefore change nothing — two of the four §7.1 constants are
decorative.** The ROBUST / FLOOR_FRAGILE boundary is **one extreme fuzz draw,
not a distribution**, and the published split rests on headroom over it:

| pair | headroom over `floor_hi` |
|---|---|
| `dac44｜mimi_q8` | +25.03 |
| `fish_modified_dac｜mimi_q8` | +8.42 |
| `mimi_q8｜qwen3_tts_tokenizer_12hz` | ⚠️ **+2.00** |
| `dualcodec_25hz_v1｜mimi_q8` | **−6.07** (FLOOR_FRAGILE) |

⚠️ **`mimi_q8｜qwen3_tts_tokenizer_12hz` is ROBUST by +2.00 units of a single
draw, on an effect of magnitude 123.** Its Whisper state also rests on 18 cells
from 17 recordings at an interval margin of **+1.12**. **Both gates separating it
from the downgraded pair are razor-thin. This is published beside the label, and
no per-state power condition is added now — that would be another post-hoc tune.**

⛔ **`floor_hi` NEVER changes a §6 verdict.** The frozen floor is the frozen
floor. `floor_hi` classifies only.

**S7.2.2** `floor_uncertainty()` creates its generator **inside** the per-state
loop, so all six states draw identical resample indices. **Recorded, not
changed:** the statistic is saturated, so it alters nothing, and changing the
method after seeing the results is the defect this audit chain exists to catch.

### 7.3 The labels

An **established** pair receives exactly one label, tested in this order:

1. **`THIN_OR_SELECTION_CONDITIONED`** — `n_paired < WELL_POWERED_MIN_PAIRED`
   **or** either arm's support coverage `< LOW_COVERAGE_PCT`.
   *The surviving cells are not a random sample; they are the cells where a
   low-coverage arm happened to retain broadband energy.*
2. **`FLOOR_FRAGILE`** — otherwise, if **either**
   (a) `|effect| <= floor_hi` — the effect lies inside the instrument floor's own
   uncertainty; **or**
   (b) any contributing state's paired interval fails to clear **that state's**
   absolute floor (§11.1's single-state rule, applied to the interval).
   ⛔ **A DEGENERATE state interval NEVER counts as clearing.** S5.2's criterion
   applies at the state level too: `n_recordings < 3` or `n_groups < 2` fails
   that state closed. Revision 3 omitted this and published **75 of 147**
   per-state intervals as `clears = True` off one or two recordings — one off a
   **single cell** with a margin of `+112.5`. S5.3's own reasoning —
   *"satisfied by arithmetic rather than by evidence"* — was written for exactly
   this and was not carried to the level it had been extended to.
3. **`ROBUST`** — otherwise.

⚠️ **S7.3.1 — WHAT RULE 2(b) ACTUALLY DOES.** Revision 3 of this document
predicted it "is expected to move pairs that the pooled margin alone would call
robust". **MEASURED: it determines ZERO labels.** Every pair it fires on is
already `THIN` under rule 1, which is tested first — including after the
degeneracy guard above was added. **It is retained as a recorded diagnostic, not
as an effective safeguard, and this document no longer claims otherwise.** The
pair the first audit directed to floor-fragile is placed there by rule 2(a)
alone; all six of its states clear their own floors. `rule_2b_effect` in
`GATE4_RESULTS.json` reports what it fired on and what it decided.

⛔ **S7.3.2 NO PAIR IS EVER NAMED IN CODE.** The hardcoded
`AUDIT_FRAGILE = ("dualcodec_25hz_v1|mimi_q8",)` — a pair name selected after
seeing the result and compiled into the path that labels it — is **DELETED**. If
the declared rules do not reproduce an audit's disposition, **the disagreement is
reported, not hardcoded.**

---

## 8. Q9 — THE METRIC-VALIDITY INSTRUMENT — S8

**S8.1** Route B membership is **derived from the frozen `gate2_matrix.json`
route field**, never hardcoded. The shipped
`learned = ('bigvgan22','vocos_mel24')` literal is deleted.

**S8.2** Q9 fires when `griffinlim` — zero trained parameters — achieves a lower
(better) `mcd` than **every** learned Route B arm **in a state**. The states in
which it fires are counted and listed; the verdict is stated in
`GATE4_RESULTS.json`, not only in prose.

**S8.3** Every Q9 figure is the **S3 hierarchical** estimate.
⛔ **The flat median is never printed in a headline table** — that was MAJOR-2.

**S8.4** ⛔ **No replacement ranking metric is introduced.** Choosing a ruler
after the winner is known is the defect Q9 exists to catch. Q9's consequence is
declared in `GATE4_PREREG.md` §5 and is reported as written.

**S8.5** Q9's instrument exists **only in Route B**. Route A has no
zero-parameter control, so the check is **NOT ESTABLISHED** there — which is not
the same as *unaffected*, and is never reported as though it were.

---

## 9. REQUIRED CONTENTS OF `GATE4_RESULTS.json` — S9

The artifact is the **single source of every published number**. It must carry,
at minimum:

- `spec_version` and the SHA-256 of this document
- the full admissibility ledger
- per arm × state: `n_cells`, `n_rankable`, bootstrap, floor
- **per pair: `n_paired`, `n_recordings`, `n_groups`, the interval,
  `deviation_flat_median_cells`, `degenerate` + reason, determinism for both
  arms, floor, `floor_hi`, label — and the PER-STATE paired breakdown**
  (median, interval, state floor, margin) that §7.3 rule 2(b) requires
- `support_coverage` per arm and per state
- `metric_validity` (Q9) and `power_and_coverage_caveats`
- every declared constant in §7.1, by name and value
- the streaming detector totals, computed over the whole cell set

⛔ **S9.1** A quantity that appears in the evidence package and **not** in this
artifact is a defect. Per-state paired margins were quoted in revision 2 and
stored nowhere — one of them (`+7.3`) did not reproduce.

---

## 10. THE EVIDENCE PACKAGE IS GENERATED, NOT TYPED — S10

⛔ **S10.1** Every number in `GATE4_STAGE2_EVIDENCE.md` §4, §6 and §9 is
**emitted by `gate4_report.py` from `GATE4_RESULTS.json`**. Hand-transcribed
figures are how revision 2 shipped a headline table of pre-M2 flat medians, a
streamed count that reproduced under no definition, and six miscounts.

**S10.2** Prose that interprets a number may be written by hand. The number
itself may not.

---

## 11. REPRODUCTION — S11

Every artifact the conclusions rest on must be re-derivable from the persisted
Stage 1 cells with no GPU decode of the study set:

```
freeze_gate3.py --verify           56 artifacts, drift 0
freeze_gate4.py --verify           18 artifacts, drift 0
freeze_gate4_stage2.py --verify    this spec + the analysis layer
gate4_metrics.py --prove           structural checks
gate4_metrics.py --aggregate       rebuilds GATE4_RESULTS.json
gate4_report.py                    regenerates the evidence package tables
```

**S11.1** `gate4_determinism.py` and `gate4_retro_sha.py` are part of this list.
They were omitted from revision 2's reproduce block, leaving the two artifacts
that condition 4 and M3 rest on non-re-derivable from the stated commands.

**S11.2 The cold-start probe must cover every arm.** `gate4_retro_sha.py`
decodes each arm's **actual first Stage 1 cell as the very first inference after
`arm.load()`**, hashes it, and compares against the persisted waveform — for
**every arm**, as a **recorded row**, not a docstring. Revision 2's bound rested
on one arm and one un-persisted manual check, and the probe sample covered
**0 of 216** of the only exposed cell.

**S11.3** `--prove` check 5 must test the sole-door property by **parsing the
module**, not by asserting that a string appears in its own source — which is
true even inside a comment.

---

## 12. WHAT THIS SPECIFICATION DOES NOT FIX

- It does not make the §7 constants blind. **Read §0.**
- It does not re-open the frozen apparatus, and it cannot repair anything inside
  it.
- It does not address Q9's consequence. **Q9 fired; that is a finding about the
  metric, and no analysis rule can answer it.**
- It does not make the §7.2 determinism gate prospective. **It was run post-hoc
  and that is permanent.**
