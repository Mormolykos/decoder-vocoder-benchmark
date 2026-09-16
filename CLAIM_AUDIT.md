# CLAIM AUDIT — decoder/vocoder benchmark paper

**Run 2026-09-16, before any publication action.** Two layers: a mechanical
trace of every headline number to its frozen artifact, and an independent
two-model review of title, abstract and conclusions for overreach.

⛔ **No irreversible external action was taken.** Nothing published, no
repository created, no DOI minted.

---

## Layer 1 — numeric traceability, 28 of 28 PASS

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
| TTFA range 1.37 – 375.91 ms | `GATE3_MATRIX.md` headline | PASS |
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
| causal arms S1 0.9999 / S2 −0.0000 | `Q5_RESULTS.json` streaming detector | PASS |
| worst streaming loss −0.7420 dualcodec_25hz_v1 | `Q5_RESULTS.json` | PASS |
| best non-causal −0.0778 bigvgan22 | `Q5_RESULTS.json` | PASS |
| 69 impostor-range markers | `Q5_RESULTS.json` recomputed | PASS |
| support counts (cells, not rows) | `Q5_CELLS.jsonl` recomputed | PASS |
| 1,512 source recordings | `PUBLICATION_MANIFEST.json` | PASS |
| device delta ≤ 2.5e-04 | `Q5_DEVICE_EQUIVALENCE.json` | PASS |

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
