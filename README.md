# decoder-vocoder-benchmark

**What a Streaming Decoder Costs: A Five-Gate Benchmark of Twenty Neural Audio
Decoders, and a Metric That Failed Its Own Validity Check**

Panagiotis Gkilis · [ORCID 0009-0007-3805-170X](https://orcid.org/0009-0007-3805-170X)

Twenty neural audio decoders measured under one frozen protocol on identical
audio, with each gate's protocol pre-registered before it was measured and each
instrument attacked before it was trusted. Two later freezes — Gate 4's analysis
layer and Q5 specification revisions 4–6 — were post-measurement repairs rather
than prospective pre-registrations, and the paper says which.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22811349.svg)](https://doi.org/10.5281/zenodo.22811349)

Read the paper: [`PAPER.pdf`](PAPER.pdf) · source [`PAPER.md`](PAPER.md) · article [ai.bedvibe.studio/decoder-benchmark](https://ai.bedvibe.studio/decoder-benchmark/)

**Cite this version:** [10.5281/zenodo.22811349](https://doi.org/10.5281/zenodo.22811349) · **all versions:** [10.5281/zenodo.22798415](https://doi.org/10.5281/zenodo.22798415)

> **Version 1.0.1 — corrected, and this is the current release.** An
> independent review after publication found reporting and reproducibility
> defects in v1.0.0: the advertised public commands did not run, a first-audio
> range borrowed a steady-state number for its upper end, and several sentences
> claimed more than the measurements support. A further round then found five
> more in the correction itself. All are corrected here and itemised in
> [`CORRECTIONS_v1.0.1.md`](CORRECTIONS_v1.0.1.md). **No measurement changed.**
> v1.0.0 remains permanently available at tag
> [`v1.0.0`](https://github.com/Mormolykos/decoder-vocoder-benchmark/releases/tag/v1.0.0)
> and at [10.5281/zenodo.22798416](https://doi.org/10.5281/zenodo.22798416).

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
encoders. Two distinct quantities, never quoted as one range: **S1**, the
offline↔streamed cosine, and **S2**, the paired retention delta. For the three
causal configurations S1 is **0.999866–0.999946** and S2 is **−3.9×10⁻⁵ to
−5.3×10⁻⁶** — a near-zero median additional change under the tested encoders,
supported recordings and imposed chunking regime. The other thirteen lose
**−0.078 to −0.742 on S2**. ⚠️ No minimum detectable streaming change and no
equivalence threshold were established, so this is not a claim that the change
falls below the instrument's resolution. ⚠️ The two measurements are independent
in construction but **not in data** — both run on the same reconstructions.

**Not measured: perceptual quality.** No listening test was run. Nothing here
says which decoder sounds best.

## What is in this repository

| path | contents |
|---|---|
| `PAPER.pdf` · `PAPER.md` | the paper |
| `CORRECTIONS_v1.0.1.md` | every correction made after v1.0.0, with the original wording beside the corrected wording |
| `TABLES_GENERATED.md` | every numeric table, machine-generated from the frozen artifacts |
| `CLAIM_AUDIT.md` | claim audit: numeric claims traced to artifacts, plus an independent two-model review of title, abstract and conclusions |
| `GATE*.md` · `Q5_SPEC.md` · `PROTOCOL.md` | pre-registrations and frozen specifications |
| `*_FREEZE.json` | freeze records and hashes |
| `PUBLIC_MANIFEST.json` | integrity record for **this** package — hashes the bytes that shipped |
| `PUBLICATION_MANIFEST.json` | the frozen manifest of the **private canonical tree**, published as a historical record; it does not describe this package |
| `GATE2_MATRIX.md` · `GATE3_MATRIX.md` · `GATE4_STAGE2_TABLES.md` · `Q5_TABLES.md` | generated result tables |
| `*_RESULTS*.json` · `*_matrix.json` · `Q5_CALIBRATION.json` | machine-readable results |
| `AUDIT.md` · `GATE2_AUDIT.md` · `GATE3_AUDIT.md` · `STAGE*_STATE.md` | the audit trail, including defects that changed conclusions |
| `*.py` | the measurement and analysis code |
| `REDACTION_REPORT.md` | exactly how this public tree differs from the private one |

## Reproducing

These three run from this package with no private input, on a clean copy:

```
python make_paper_tables.py            # regenerate every table in the paper
python claim_audit.py                  # re-trace every headline claim (exit 1 on failure)
python make_public_manifest.py --verify   # re-hash the bytes that shipped
```

**What that establishes, and what it does not.** Every table and every headline
number is recomputed from the published aggregate artifacts and re-traced to the
artifact it came from. That is a *consistency check*. It is not independent
reconstruction: the aggregates and their confidence intervals cannot be rebuilt
from this package, because that needs the withheld per-recording rows and
embeddings. One claim — the support-domain cell counts — is computed from those
rows, and the public claim audit reports it `WITHHELD` rather than `PASS`.

**Two manifests, two questions.** `PUBLIC_MANIFEST.json` hashes the bytes in
this package; `make_public_manifest.py --verify` checks them, and reports both
missing and undeclared files. `PUBLICATION_MANIFEST.json` is the frozen manifest
of the **private canonical research tree**, published as a historical freeze
record. It hashes private artifacts under their private filenames and will
report drift against this redacted package — that is correct behaviour, not a
fault. v1.0.0 advertised it as the public check; that was the defect.

⚠️ `PAPER.pdf` is **not byte-reproducible**: it is rendered through headless
Chrome, which embeds a build timestamp, so rebuilding it yields a different
SHA-256 from the same Markdown. `PUBLIC_MANIFEST.json` hashes the PDF that
shipped, which is the thing a reader downloads; it does not claim that a
rebuild reproduces those bytes. Every *table* and every *number* is
byte-reproducible, and `make_paper_tables.py` is what proves it.

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

Speaker names are pseudonymised throughout (`Speaker_01`…`Speaker_07`), private
corpus roots are masked, and the operator's local account name is masked to
`<PRIVATE_HOME>` — v1.0.0 retained eight such paths in `ENVIRONMENT.json`
despite this sentence, which is corrected in v1.0.1. Conda environment names
below that point are preserved because the paper refers to them and they are
not private. `REDACTION_REPORT.md` records every substitution with the source
hash. Aggregate counts, selection rules, duration statistics and the ladder
derivation are preserved in full.

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
