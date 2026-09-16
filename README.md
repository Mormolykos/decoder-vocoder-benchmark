# decoder-vocoder-benchmark

**What a Streaming Decoder Costs: A Five-Gate Benchmark of Twenty Neural Audio
Decoders, and a Metric That Failed Its Own Validity Check**

Panagiotis Gkilis · [ORCID 0009-0007-3805-170X](https://orcid.org/0009-0007-3805-170X)

Twenty neural audio decoders measured under one frozen protocol on identical
audio, with each gate pre-registered before it was measured and each instrument
attacked before it was trusted.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22798416.svg)](https://doi.org/10.5281/zenodo.22798416)

Read the paper: [`PAPER.pdf`](PAPER.pdf) · source [`PAPER.md`](PAPER.md) · archived at [10.5281/zenodo.22798416](https://doi.org/10.5281/zenodo.22798416)

---

## Three results

**Only three of twenty arms truly stream.** An arm counts as incremental only if
stateful chunked decode reproduces full-context output (`max|err| ≤ 1e-3`) *and*
state is load-bearing (stateless error ≥ 10× stateful). Three explicitly causal
FocalCodec configurations pass, with C2 ratios of 3,530–36,740 against a
threshold of 10. Fifteen arms use stateless chunking. Non-causal configurations
driven through the identical stateful code path give a C2 ratio of exactly 1 —
the negative control that makes the positives mean something.

**The sole pre-registered ranking metric failed its own validity instrument.**
Griffin-Lim, a zero-parameter phase-retrieval algorithm, scores *best* on the
mel-cepstral distance in six states of six. The pre-registration declared in
advance what that would mean, so it is reported as a property of the metric. A
proposed explanation was tested and refuted.

**A second measurement, sharing no implementation, found the same three
survivors.** Speaker-embedding retention with three separately calibrated
encoders: the causal configurations show no measured loss when streamed
(offline-vs-streamed cosine 0.9999), while thirteen others lose −0.078 to
−0.742. ⚠️ The two measurements are independent in construction but **not in
data** — both run on the same reconstructions.

**Not measured: perceptual quality.** No listening test was run. Nothing here
says which decoder sounds best.

## What is in this repository

| path | contents |
|---|---|
| `PAPER.pdf` · `PAPER.md` | the paper |
| `TABLES_GENERATED.md` | every numeric table, machine-generated from the frozen artifacts |
| `CLAIM_AUDIT.md` | claim audit: 36 numeric claims traced to artifacts, plus an independent two-model review of title, abstract and conclusions |
| `GATE*.md` · `Q5_SPEC.md` · `PROTOCOL.md` | pre-registrations and frozen specifications |
| `*_FREEZE.json` · `PUBLICATION_MANIFEST.json` | freeze records and hashes |
| `GATE2_MATRIX.md` · `GATE3_MATRIX.md` · `GATE4_STAGE2_TABLES.md` · `Q5_TABLES.md` | generated result tables |
| `*_RESULTS*.json` · `*_matrix.json` · `Q5_CALIBRATION.json` | machine-readable results |
| `AUDIT.md` · `GATE2_AUDIT.md` · `GATE3_AUDIT.md` · `STAGE*_STATE.md` | the audit trail, including defects that changed conclusions |
| `*.py` | the measurement and analysis code |
| `REDACTION_REPORT.md` | exactly how this public tree differs from the private one |

## Reproducing

Results regenerate from the released artifacts:

```
python make_paper_tables.py     # regenerate every table in the paper
python claim_audit.py           # re-trace every headline claim (exit 1 on failure)
python make_publication_manifest.py --verify   # re-hash all 32 artifacts
```

Re-running the *measurement* additionally needs the private corpus, four conda
environments and third-party decoder checkpoints; see `STAGE1_STATE.md`.

## What is NOT released, and why

- **The source audio.** 1,512 private, rights-cleared recordings of seven
  consented speakers.
- **Speaker embeddings** (`Q5_EMBEDDINGS.npz`) and **per-recording rows**
  (`Q5_CELLS.jsonl`). An embedding of a named human is biometric data;
  publishing it is a different act from the research use the consent covers.
- **The reconstructed audio** (35.65 GB), retained for the later perceptual and
  detectability phases.

Speaker names are pseudonymised throughout (`Speaker_01`…`Speaker_07`) and
private paths are masked. `REDACTION_REPORT.md` records every substitution with
the source hash. Aggregate counts, selection rules, duration statistics and the
ladder derivation are preserved in full.

## Licence

**Paper, documentation, tables and data files: [CC BY 4.0](LICENSE).**

⚠️ **The source code carries no separate licence designation.** No distinct code
licence existed in the private tree, and none has been added here, because
applying one silently would be a relicensing decision the author has not made.
Until a code licence is designated, **no grant beyond CC BY 4.0 is made for the
`.py` files**, and CC BY is not a software licence. If you want to reuse the
code, open an issue and ask.

Third-party decoder implementations are **not** included. One benchmarked arm
(`melflow`) is AGPL-3.0 upstream and was evaluated in isolation; its results
carry that label in the paper.
