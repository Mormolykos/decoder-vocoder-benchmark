# CLAIM AUDIT — decoder/vocoder benchmark paper

**Layers 1 and 2 ran 2026-09-16, before any publication action. Layer 3 ran
after v1.0.0 was published, against the published package.** Three layers: a
mechanical trace of every headline number to its frozen artifact, an independent
two-model review of title, abstract and conclusions for overreach, and a
post-publication adversarial review of the shipped package.

⚠️ **Layers 1 and 2 could not have caught what Layer 3 found.** Both ran inside
the private tree. The defects in §Layer 3 are defects of the *package* and of
claims about it — invisible from the tree it was built in. See
`CORRECTIONS_v1.0.1.md`.

---

## Layer 1 — numeric traceability, 55 of 55 traced (54 PASS, 1 WITHHELD)

Re-run for v1.0.1. The check count rose from 28 because the corrected claims are
checked more tightly than the ones they replace — the TTFA range is now
recomputed from the anchor table rather than substring-matched, the causal S1/S2
bounds are checked at full precision, and both encoder-ordering reversals are
recomputed.

`paper/claim_audit.py` re-derives each headline value from the frozen artifact
and fails closed if a claim cannot be traced. Run against
`PUBLICATION_MANIFEST.json` `1e93e28b9adb3b1f`.

| claim | source | result |
|---|---|---|
| 20 arms total · 3 TRUE_INCREMENTAL · 15 stateless chunking | `GATE2_MATRIX.md` totals | PASS |
| C2 ratio range 3,530–36,740 | `GATE2_MATRIX.md` causal rows | PASS |
| overlap-add control 134.65% | `GATE2_MATRIX.md` melflow control | PASS |
| chunk drift 47,360 samples ≈ 1.97 s | `GATE2_MATRIX.md` drift table | PASS |
| environment effect 50.2% | `GATE3_MATRIX.md` E6 | PASS |
| numerical TTFA range 1.37 – 27.64 ms, recomputed over the 18 arms that have one | `GATE3_MATRIX.md` anchor table | PASS |
| TTFA upper end is `bigvgan22`, not `melflow` | `GATE3_MATRIX.md` recomputed | PASS |
| `melflow` has no numerical TTFA (NOT ESTABLISHED) | `GATE3_MATRIX.md` melflow row | PASS |
| `melflow` 375.91 ms is a steady-state p50, not TTFA | `GATE3_MATRIX.md` melflow row | PASS |
| two arms fail every tested chunk size, not three | `GATE3_MATRIX.md` E3 sweeps | PASS |
| `focalcodec_12_5hz` passes 2 of 5 tested conditions | `GATE3_MATRIX.md` E3 | PASS |
| qwen underrun 0.0013, max 208.10 ms | `GATE3_MATRIX.md` headline | PASS |
| focalcodec_12_5hz E3 = 640.8 ms | `GATE3_MATRIX.md` E3 | PASS |
| 46 / 42 / 20 pairwise verdicts | `GATE4_STAGE2_TABLES.md` §6 | PASS |
| Q9 fires | `GATE4_RESULTS.json` `metric_validity` | PASS |
| Q9 loud/quiet diagnostic 21.4 vs 16.0 | `STAGE2_STATE.md` | PASS |
| coverage 99.3% / 79.4% / 1.0–0.2% | `GATE4_STAGE2_TABLES.md` §5 | PASS |
| griffinlim highest retention (ecapa 0.9952) | `Q5_RESULTS.json` recomputed | PASS |
| retention floor 0.4316 focalcodec_12_5hz | `Q5_RESULTS.json` | PASS |
| max per-encoder spread 0.1193 | `Q5_RESULTS.json` recomputed | PASS |
| 540 labels · 314 / 152 / 19 / 8 | `Q5_RESULTS.json` recomputed | PASS |
| causal S1 bounds 0.999866 – 0.999946 | `Q5_RESULTS.json` streaming detector | PASS |
| causal S2 bounds −3.882e-05 – −5.312e-06 | `Q5_RESULTS.json` streaming detector | PASS |
| all nine causal S2 medians strictly negative, so "lose nothing" is refused | `Q5_RESULTS.json` recomputed | PASS |
| `focalcodec_25hz` b6 S1 −0.013 stated as embedding-only | `Q5_RESULTS.json` | PASS |
| worst streaming loss −0.7420 dualcodec_25hz_v1 (S2) | `Q5_RESULTS.json` | PASS |
| best non-causal −0.0778 bigvgan22 (S2) | `Q5_RESULTS.json` | PASS |
| the −0.078…−0.742 range is labelled S2, never cosine | claim review finding 4 | PASS |
| encoder ordering reversal: `encodec24_q8` / `dualcodec_12hz_v1` | `Q5_RESULTS.json` recomputed | PASS |
| encoder ordering reversal: `encodec_vocos` / `mimi_q32` | `Q5_RESULTS.json` recomputed | PASS |
| 69 impostor-range markers | `Q5_RESULTS.json` recomputed | PASS |
| support counts (cells, not rows) | `Q5_CELLS.jsonl` — **withheld from the public package** | WITHHELD |
| 1,512 source recordings | `PUBLICATION_MANIFEST.json` | PASS |
| device delta ≤ 2.5e-04 | `Q5_DEVICE_EQUIVALENCE.json` | PASS |

**On the WITHHELD row.** Run inside the private tree, where `Q5_CELLS.jsonl`
exists, that check recomputes the counts and passes — 55 of 55 PASS. Run from
the public package it reports `WITHHELD`, because the per-recording rows are
biometric data and are not published. `WITHHELD` is **not** a pass: it records
that the claim's evidence is intentionally absent. The check still verifies that
the sentence is present in the paper, so a withheld check cannot cover a claim
that was quietly dropped.

⭐ **One error was caught by this layer and fixed before review.** The paper
read *"51,060 of 93,744 offline cells"*. Those are **rows** (cells × 3
encoders), not cells. Corrected to **17,020 of 31,248 offline cells and 26,147
of 27,776 streamed cells** (14,083 and 781 inside support). Recomputed from
`Q5_CELLS.jsonl`: 51,060 / 3 = 17,020 exactly.

## Layer 2 — independent two-model review

Both models were asked for defects only, on title, abstract and conclusions,
with four of my own suspicions named as focus. **The two critiques are reported
separately and never merged.**

**All five findings ACCEPTED.** Four were confirmations of suspicions I had
already formed; the fifth was new.

### 1. "wrong as proxies for what a listener would care about" — Gemini + ChatGPT

**ACCEPTED.** No listening test was run, so the sentence asserts what listeners
care about. ⚠️ I **rejected Gemini's proposed replacement** ("failed as proxies
for decoder quality") — *decoder quality* is equally undefined without
perception, so that fix substitutes one unsupported claim for another.
**Applied:** the conclusion now states that each measurement was computed
correctly, that **neither establishes perceptual quality**, and that the study
cannot say what either costs a listener.

### 2. "independent" / "unrelated" instruments — Gemini + ChatGPT

**ACCEPTED, with a correction to both proposed fixes.** ChatGPT's "complementary
measurements with different representations" discards a fact that is true and
load-bearing: the two share **no implementation**. What they share is the
**data**. **Applied:** the paper now says the measurements are independent in
construction but not in data, and states explicitly that their agreement rules
out an implementation error in either, **not** an artefact of the material both
were computed on.

### 3. "dressed as streaming" — Gemini + ChatGPT

**ACCEPTED.** It imputes intent to arms that never claimed to stream.
**Applied:** "Fifteen use stateless chunking rather than load-bearing streaming
state", plus an explicit sentence that the classification measures what the arms
do and is not a charge against what they advertised.

### 4. Title overstates — Gemini + ChatGPT

**ACCEPTED.** Only the mel-cepstral metric had a pre-registered validity
instrument (Q9); the speaker-embedding side had no analogous pre-registered
check, so it did not "fail" one. **Applied:** the title is now
**"… and a Metric That Failed Its Own Validity Check"** (singular).

### 5. "the only ones that lose no speaker identity" — ChatGPT only

**ACCEPTED, and this one I had not spotted.** The phrasing implies decoder-level
identity preservation from a representation-level measurement. **Applied:** "the
same three show **no measured loss under our speaker-embedding metric**", with
an added sentence that this is a representation-level result from three
encoders, not a claim about how a listener would judge identity.

### Where the two models differed

They did not disagree on any finding. ChatGPT produced one finding Gemini did
not (#5) and gave more precise replacement wording on #1 and #2; Gemini's
wording on #1 introduced a new unsupported term. **Neither model was accepted
verbatim.**

## Layer 3 — post-publication adversarial review of the published package

Ran 2026-09-16 against the v1.0.0 GitHub package, its PDF, the article, the
release notes and the DataCite metadata. Six substantive findings and two minor
ones. **Every finding was independently verified against the frozen evidence
before being accepted**, and one sub-point was rejected on the evidence.

| finding | verdict | numeric impact |
|---|---|---|
| The advertised public reproduction commands do not run | **CONFIRMED** by execution — `TypeError`, `FileNotFoundError`, 26/32 drift | none |
| Freeze chronology overstated; one record contradicts itself | **CONFIRMED**, narrower than reported: the per-revision records are honest, the top-level summary is stale | none |
| Gate 3 range mixes TTFA with steady-state p50; failure count wrong | **CONFIRMED**, with the qualifier that the paper did label 375.91 as steady-state | reported range and count change; no table entry changes |
| Release headline compares S1 cosine against S2 delta as one metric | **CONFIRMED** — defect is in the release notes, not the paper body | none |
| "lose nothing" · "bears no relation" · "rules out an implementation error" | **CONFIRMED** — all three verbatim in the paper | none |
| …the same finding's claim that Q1 is mis-described | **REJECTED** — Q1 appears once, described as error at % of peak, which is what a maximum error relative to peak is | none |
| Griffin-Lim "minimises exactly" the released metric | **CONFIRMED** — Griffin-Lim optimises STFT magnitude consistency, not this cepstral distance | none; Q9's result and trigger stand |
| Residual local paths in `ENVIRONMENT.json` | **CONFIRMED** — 8 occurrences | none |
| "orders the arms consistently" | **CONFIRMED, and understated** — two reversals, not one | none |

**What the review reconciled and found correct**, independently: the 108 Gate 4
verdicts (46 + 42 + 20), all 540 Q5 labels (314 + 152 + 24 + 23 + 19 + 8), the
Gate 2 three-incremental-PCM-path classification, and Q5's same-arm
same-recording pairing with retention differences computed separately per
encoder. **No measurement was found to be wrong.**

Every correction is itemised in `CORRECTIONS_v1.0.1.md` with the original
wording beside the corrected wording.

## Residual risks the audit did NOT clear

1. **No listening test exists.** Every quality-adjacent sentence is a statement
   about a metric, and the paper must never be summarised as "Griffin-Lim is
   good".
2. **Both measurements share their input.** A corpus- or reconstruction-level
   artefact would move both, and their agreement cannot exclude it.
3. **Route A has no zero-parameter control**, so Q9's validity check is
   `NOT ESTABLISHED` there — not passed.
4. **FocalCodec dispersion and band-limiting are inseparable** in this design.
5. **Seven speakers, one studio, one chain, English.** External validity is
   asserted nowhere.
6. The **incumbent's environment is not numerically comparable** to the
   reference environment.
7. `melflow` results rest on **locally repaired upstream code**.
8. **The public package cannot be independently reconstructed.** Regenerating a
   table from a published aggregate is a consistency check, not reconstruction;
   the aggregates and their intervals need the withheld per-recording rows and
   embeddings. This was stated too strongly in v1.0.0 and is corrected.
9. **A sixth audit round would be against this correction, and has not run.**
   Layer 3 found what four earlier rounds had not, purely by changing what it
   attacked. The author is not the certifier.
