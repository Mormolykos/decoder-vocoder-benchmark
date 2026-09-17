# What a Streaming Decoder Costs: A Five-Gate Benchmark of Twenty Neural Audio Decoders, and a Metric That Failed Its Own Validity Check

**Panagiotis Gkilis** · BedVibe Studios, Oslo
ORCID 0009-0007-3805-170X

**Version 1.0.1 — corrected.** Supersedes v1.0.0 (DOI 10.5281/zenodo.22798416),
which remains permanently available. An independent post-publication adversarial
review found reporting and public-reproducibility defects; `CORRECTIONS_v1.0.1.md`
lists every one, with the original wording beside the corrected wording.
**No measurement changed** — the corrections are to prose, to release packaging
and to claims that outran their evidence. Publication manifest `1e93e28b9adb3b1f`.
Every numeric value is generated from a frozen artifact by `make_paper_tables.py`;
the prose cites the generated tables and adds no number of its own.

---

## Abstract

Choosing a neural audio decoder for a streaming text-to-speech product requires
four separate answers — does it run, does it truly stream, how fast is it, and
what does it cost the signal — and the literature answers them with figures that
are rarely comparable. We benchmarked **twenty decoder arms** under one frozen
protocol on identical audio, with each gate's protocol pre-registered before it
was measured and each instrument attacked before it was trusted. Two later
freezes — Gate 4's analysis layer, and revisions 4–6 of the Q5 specification —
were **post-measurement repairs** rather than prospective pre-registrations;
§3 and §9 say which, why, and what changed as a result.

Three results stand out, and two of them are negative.

**First, "streaming" is a property almost nothing in the candidate set has.** Of
twenty arms, only **three** reproduce full-context output from partial input
while carrying state — all three explicitly causal FocalCodec configurations.
**Fifteen** use stateless chunking rather than load-bearing streaming state.
One streams its network but never emits audio from partial input, and its label
says so. Several of the fifteen never claimed to stream; the classification is a
measurement of what they do, not a charge against what they advertised.

**Second, our sole pre-registered cross-arm quality metric failed the validity
instrument we built to catch exactly that.** Griffin-Lim, a zero-parameter
phase-retrieval algorithm from 1984, does not merely score close to the trained
mel decoders under our mel-cepstral distance — it scores **best in six states of
six**. The pre-registration declared in advance what that would mean, so the
finding is reported as a property of the metric, not as a decoder ranking.

**Third, a second measurement with no shared code path reached the same verdict
on the same three arms.** Measuring speaker-embedding retention with three
separately calibrated speaker encoders, the three causal configurations show
**near-zero median additional change** when streamed, under the tested encoders,
supported recordings and imposed chunking regime: offline-vs-streamed cosine
**0.999866–0.999946**, and a paired retention delta of **−3.9×10⁻⁵ to
−5.3×10⁻⁶** — small, and strictly negative. The other thirteen lose between **−0.078** and
**−0.742** *on the retention delta*; that is a different quantity from the
cosine and the two are never quoted as one range. ⚠️ The two measurements are
independent in *construction* — a
spectral distance and three speaker encoders, sharing no implementation — but
**not** in *data*: both run on the same reconstructions of the same corpus, so a
corpus-level or reconstruction-level artefact would move both. What their
agreement adds is that two different representations of the signal register the
same three survivors.

We also report what we could not establish: perceptual quality was never
measured, and the identity result is a statement about speaker-encoder
representations rather than about how the audio sounds. The study went through
**six rounds of independent adversarial audit**: four before publication, which
found three defects that changed conclusions; a fifth against the published
package, which found that its advertised reproduction commands did not run and
that four claims outran their evidence; and a sixth against the correction
itself. All are reported here, and in `CORRECTIONS_v1.0.1.md`, because the
repairs changed what the paper is entitled to say.

---

## 1. Introduction

A team building a streaming TTS system has to choose a decoder. The published
record makes that harder than it should be. Real-time factors are quoted without
hardware; "streaming" is claimed for architectures that require the whole
utterance; quality figures come from different corpora at different sample rates
through different measurement paths. None of it composes into a decision.

This benchmark exists to make one decision inspectable rather than asserted. It
measures **representation → waveform only**. Generator and autoregressive timing
are outside its scope, and a decode-only number read as end-to-end TTS
performance would be a failed report.

The study is organised as five gates, each pre-registered before it was run:

| gate | question |
|---|---|
| **0 — candidate** | which decoders are runnable, licensed and comparable at all? |
| **1 — functionality** | does the arm produce structurally valid audio? |
| **2 — streaming** | does it *truly* stream, or is it stateless chunking? |
| **3 — performance** | latency, real-time factor, first-audio, jitter, memory |
| **4 — quality** | what does the round trip cost the signal? |
| **Q5 — identity** | does the speaker survive, and does he stay one person? |

One methodological commitment shapes everything below: **an instrument is
attacked before it is trusted, and its author does not certify it.** Two of the
three headline findings are consequences of that rule rather than of the
decoders.

## 2. Candidate set, and a reframing that changed it

The candidate gate closed with a finding that changed the population: **for a TTS
build, only the decoder needs to be causal.** The encoder runs at training time
on complete utterances; at inference the generator emits tokens directly and no
encoder sits in the serving path. NVIDIA's NanoCodec makes the point concrete —
non-causal encoder, causal HiFi-GAN decoder. "Is this codec causal?" is
therefore the wrong question, and asking it nearly excluded several candidates
for the wrong reason.

The measured population is twenty arms spanning two routes — **Route A**,
representation → waveform through a codec's own decoder, and **Route B**,
mel → waveform — at three sample-rate bands (16 kHz, 22–24 kHz, 48 kHz), because
sample rate is an architectural variable and was never normalised away.

Two arms carry declared non-results rather than numbers. `nanocodec` is
**BLOCKED — PLATFORM**: it could not be loaded here, and no timing figure is
manufactured for it. `melflow` is AGPL-3.0 and carries a label on every result
it produces: research evidence, not a shippable closed-product dependency. Its
released streaming path also **did not execute as-is** and required two
structural repairs, which an independent delta audit confirmed were inert —
touching no weight and no arithmetic operation.

## 3. Method

**Corpus.** Seven speakers, English, one studio, one recording chain, six
emotional states — Neutral, Angry, Happy, Scared, Shouting, Whisper. **1,512
distinct source recordings**, every file hashed with SHA-256 before use: Set S
(1,302 recordings, 31 texts, all six states, 2.54–13.50 s), Set L (210
recordings, 15 long texts, Neutral and Whisper, measured on a derived 14 s top
rung), and a calibration subset (126 recordings) held out by construction. The
source audio is private, rights-cleared and consented, and is **not published**.

**Environment.** NVIDIA GeForce RTX 5080, torch 2.10.0+cu128, CUDA 12.8, seed
20260911, eager mode throughout — no `torch.compile`, no CUDA graphs. Timing
used 30 warm repetitions plus 3 cold, 5 warm-ups discarded, block-randomised,
one GPU process at a time.

**Freeze discipline.** Every gate's apparatus is frozen and hashed, `--verify`
reports drift, drift was 0 at every checkpoint, and superseded revisions are
retained rather than discarded. **Not every freeze is prospective, and the
records say which are which** — this is stated here because an earlier version
of this paper claimed uniformly that each apparatus was frozen before the data
it governs existed, which the freeze records do not support.

The protocol and the gate definitions were written before any decoder ran.
`GATE4_FREEZE.json` seals the Gate 4 corpus, instrument and selection rule and
records that at that moment "no decoder has run and no quality number exists".
`GATE3_FREEZE.json` is a different kind of record: it seals Gate 3 on
completion, after its measurements existed. Gate 4's **analysis** layer was
likewise frozen once quality numbers existed, and its own record says so
without hedging — freezing "does NOT make them blind, and nothing later can".

The Q5 specification went through six revisions. Revisions 1–3 were frozen with
no Q5 artifact of any kind on disk. **Revisions 4–6 were post-measurement
repairs**: measured artifacts already existed when each was frozen, and each
carries `OVERRIDDEN — artifacts existed at spec-freeze time` together with the
sentence "no claim of blindness is made for this revision". The guards record
`Q5_CELLS.jsonl`, `Q5_EMBEDDINGS.npz`, `Q5_CALIBRATION.json` and `Q5_FUZZ.json`
present at all three, and by revision 6 the aggregated `Q5_RESULTS.json` as
well. **No blindness is claimed for any of them.** What they changed, and what
changed in the labels as a result, is in §9. What freezing establishes throughout is that the decisions were
declared, fixed and auditable; it does not establish that the analyst was blind
to the data, and for revisions 4–6 they demonstrably were not.

**Statistics.** The experimental unit is the **recording**, never the cell.
Intervals are 95% percentile intervals from a cluster bootstrap over recordings,
4,000 resamples, seed 20260911, aggregated within (speaker × state) before
across. **No hypothesis tests are performed and no p-value is reported** —
intervals and effect sizes only.

## 4. Gate 1 — functionality

Every arm passes a structural gate before any claim: finite samples, peak in
(0, 1], duration within one frame of that arm's own rate, energy ratio 0.25–4.0,
float32, correct channel count. **Nineteen of twenty arms PASS.** The twentieth
is `nanocodec`, recorded as `NOT RUN — arm could not be loaded`.

Gate 1 is deliberately weak. It establishes that a number *may* be computed, not
that it means anything.

## 5. Gate 2 — true streaming versus stateless chunking

This is the gate we expected to be routine, and it was the most discriminating
of the five.

An arm is `TRUE_INCREMENTAL` only if **both** conjuncts hold: **C1**, stateful
chunked decode reproduces full-context output to `max|err| ≤ 1e-3`; and **C2**,
state is load-bearing — the stateless error is at least 10× the stateful error.
C2 exists because C1 alone can be satisfied by an arm that ignores state.

| classification | arms |
|---|---|
| `STATELESS_CHUNKING` | **15** |
| `TRUE_INCREMENTAL` (representation → PCM) | **3** — `focalcodec_50hz_2k_causal`, `focalcodec_50hz_4k_causal`, `focalcodec_50hz_65k_causal` |
| `TRUE_INCREMENTAL` — neural decoder only, iSTFT streaming not established | 1 — `melflow` |
| `BLOCKED — PLATFORM` | 1 — `nanocodec` |

The three causal configurations pass C2 with ratios of **3,530 to 36,740**
against a threshold of 10 — state is not marginally load-bearing, it is
decisive.

**The negative controls are what make the positives mean anything.** The
non-causal FocalCodec configurations are driven through the *identical* stateful
code path. Their C2 ratio is **exactly 1**: carrying state changes nothing. Had
a negative control passed, the experiment would have been void rather than the
arm promoted.

`melflow` is the honest boundary case. Its neural decoder is driven
frame-synchronously with carried state and passes both conjuncts, but the
inverse STFT runs once over the assembled spectrogram, so **no PCM is emitted
from partial input**. A control measured that the overlap-add stage is not free
— a naive split-and-concatenate inverse STFT departs by 134.65% — so streaming
the neural decoder does not imply streaming the chain. Its label carries the
qualification and it is never counted with the arms that emit PCM.

We also measured per-chunk length drift rather than assuming it away: four arms
accumulate a constant offset per chunk, worst case **47,360 samples ≈ 1.97 s**
for `vocos_mel24` and `griffinlim`. Part of the error attributed to boundary
damage in a naive analysis is misalignment.

## 6. Gate 3 — performance

**One environment finding governs how these numbers may be read.** A controlled
probe — byte-identical tokens, same GPU, `encodec24_q8` as a single arm in every
environment — found the incumbent's environment **50.2% faster** than the
reference (`transformers` 4.35.2 versus 4.57.3), a near-constant 3–4 ms
device-side offset at identical torch. Host overhead is 0.022 ms versus 0.024 ms
while CUDA time is 10.344 ms versus 6.328 ms: the two library versions launch
different GPU work for the same decode. Consequently **`fish_modified_dac` may
not be compared numerically against any arm measured in the reference
environment.** Its numbers stand within its own environment. This says nothing
about whether the incumbent is fast or slow; it says the comparison does not
exist.

At the ~80 ms chunk anchor, **first-audio latency (TTFA) spans 1.37 ms**
(`vocos_mel24`) **to 27.64 ms** (`bigvgan22`) across the arms that have a
numerical TTFA at all. `melflow` is not in that range: its TTFA is **NOT
ESTABLISHED**, because it emits spectrogram frames and producing PCM from a
partial stream needs an overlap-add stage this study records as not
established. Its **375.91 ms is a steady-state p50**, a different quantity, and
the two are never mixed — in eager mode and therefore an upper bound, since its
upstream recommends CUDA graphs. Real-time margin spans **64×** down to
**0.2×**. Seventeen arms show zero underrun at the anchor;
`qwen3_tts_tokenizer_12hz` shows 0.0013 with a p99 of 17.39 ms against a **max
of 208.10 ms** — a tail that a p50 hides completely.

**Speed does not imply validity, and Gate 3 refuses to let it.** **Two** arms
produce streamed output that fails the study's own §8 validity gate at every
chunk size tested: `vocos_mel24` (0/7 conditions) and `griffinlim` (0/6), both
on `duration_ok`. A third, `focalcodec_12_5hz`, fails **at the anchor** but not
everywhere: it passes **2 of 5** tested conditions, failing on `energy_ok` at
the smaller sizes, so its minimum viable configuration is **640.8 ms**, not
80 ms. Their timing numbers are real; what they timed at the anchor is not a
valid streaming configuration.
`vocos_mel24` is the sharpest illustration: the **fastest** first-audio in the
study, and no achievable streaming configuration at all.

## 7. Gate 4 — reconstruction quality, and a metric that failed

Gate 4 ranked on **one** metric, mel-cepstral distance, chosen after nine metric
variants were implemented and attacked; the other eight were demoted to
detectors, permitted to report that two signals differ but never that one
decoder is better. Ranking required three conjuncts: the cell inside a validated
support domain, a paired 95% recording-cluster interval excluding zero, and an
effect exceeding a state-aware absolute floor.

Of 108 within-route pairs: **46 SEPARATION ESTABLISHED · 42 ORDERED, SEPARATION
NOT ESTABLISHED · 20 QUALITY COMPARISON NOT ESTABLISHED.** Only **three** pairs
are ROBUST, all of them statements that `mimi_q8` is worse than another arm, and
one further pair is floor-fragile. Forty-two of the ordered pairs rest on **3 to
17 paired cells** and **all 42 contain a FocalCodec arm** — the survivors are
that arm's most favourable cells, so the direction survives its own selection
but the magnitude does not.

### 7.1 Q9 fires

The pre-registration installed Griffin-Lim as a zero-parameter floor and stated
in advance what it would mean if a 1984 phase-retrieval algorithm scored close
to a trained neural codec: *a finding about the metric*.

It did not score close. It scored **best, in six states of six** (see T-Q9
below, generated): 81.6 versus 102.6 and 127.7 at Neutral, and the same ordering
in every other state.

A proposed explanation was tested and **refuted**. The hypothesis that the
metric's low-level frame floor favours a magnitude-matching algorithm failed:
splitting each cell at its own median energy, Griffin-Lim leads in **both**
halves and by *more* in the loud half (21.4 versus 16.0).

What remains is an explanation **consistent with** the result rather than a
demonstrated mechanism, and it is worth stating the difference. Mel-cepstral
distance as implemented here is derived from the magnitude spectrum — mel
filtering of the power spectrum, a logarithm, a cepstral transform, and removal
of coefficient zero — and it is blind to phase by construction. Griffin-Lim
iterates toward consistency of the **linear STFT magnitude** and optimises
nothing else, accepting whatever phase error that leaves. The two objectives
are aligned in domain but are **not the same quantity**, and this package does
not demonstrate that Griffin-Lim minimises the released cepstral distance
exactly. That alignment is the most plausible account of a zero-parameter
algorithm winning six states of six; it is not established here, and no claim
in this paper rests on it.

**What is established is narrower and does not depend on the mechanism: a
metric whose ranking puts an untrained phase-retrieval algorithm first is not,
on its own, a sufficient authority for cross-decoder quality.** That is the
pre-registered consequence, and it fired on the evidence rather than on the
explanation. It does not follow that optimising a related quantity
automatically disqualifies a metric — the disqualifying observation here is the
ranking itself.
Two scope limits travel with this finding: the instrument exists only in Route B,
so the same check is `NOT ESTABLISHED` — not "passed" — in Route A; and no new
metric was introduced after seeing the data, because choosing a ruler once you
know who won under the old one is precisely the failure Q9 exists to catch.

### 7.2 What the support domain removed

Coverage varies by more than two orders of magnitude: `griffinlim` 99.3% of
cells rankable, `mimi_q32` 79.4%, and every FocalCodec arm between **1.0% and
0.2%**. A FocalCodec quality comparison is therefore drawn from the few percent
of cells where that arm retained broadband energy. This is stated rather than
smoothed, and it is why 20 of the 20 refused pairs involve FocalCodec.

## 8. Q5 — speaker identity

Gate 4 pre-registered speaker-identity retention as **Q5** and marked it *metric
not built, not fuzzed*. It was built afterwards as a separate layer, consuming
the frozen reconstructions without reopening any Gate 4 verdict.

Q5 measures two quantities that a single similarity score conflates, and refuses
to merge them:

- **Retention (R)** — cosine between a source recording and its own
  reconstruction.
- **Dispersion (D)** — cosine between *different* reconstructions of the same
  speaker, so a decoder that moves a voice consistently can be told apart from
  one that makes the speaker wander.

Both are read against two references measured on **source audio alone, before
any reconstruction was opened**: the human within-speaker ceiling (how far apart
two genuine recordings of one speaker sit) and the between-speaker floor.

**The panel is three independently calibrated encoders** (T1), chosen
mechanically from a previously frozen fourteen-encoder study before any Q5
number existed. Cosine values are **encoder-specific and never averaged**; the
panel's role is agreement, not a pooled score.

**The instrument was calibrated and gated before use** (T2, T3). Each encoder's
usable range G — the distance between "same person again" and "a different
person" on this corpus — is 0.2663 to 0.4056, and each encoder's response to a
one-sample shift is 100× smaller than the bound that would demote it. All 24
separability gates pass.

### 8.1 Retention

Retention (T4) runs from **0.9952** (`griffinlim`, `ecapa`) down to **0.4316**
(`focalcodec_12_5hz`). **The three encoders show broadly similar ordering, with
some pairwise reversals** — `encodec24_q8` sits above `dualcodec_12hz_v1` under
`ecapa` (0.8781 versus 0.8621) and below it under both ReDimNet encoders, and
`encodec_vocos` leads `mimi_q32` under `ecapa` and `redimnet_M_vb2_ptn` but
trails it under `redimnet_b6_lm` (0.8546 versus 0.8581). Per-encoder spread
reaches 0.1193, which is why a bare cosine without its encoder name is not a
result, and why neighbouring arms should not be read as ranked against each
other at all.

**Griffin-Lim has the highest speaker-embedding retention of the eighteen arms.**
That sentence is the whole claim. It is not a statement that Griffin-Lim is the
best decoder, and it is not a perceptual claim — it is a measurement of how well
one representation survives a round trip. Read together with Q9 it says
something sharper: **two instruments, a spectral distance and three speaker
encoders, both rank a phase-blind algorithm first.** Both are blind to the same
thing, and only a listening test can settle what that costs.

### 8.2 Dispersion

Of 540 labelled strata (T5), the dominant outcome is `NOT ESTABLISHED` (314) —
which here means dispersion **statistically indistinguishable from the human
ceiling**, not absence of information. `INCONSISTENT / DRIFTING` accounts for
152, concentrated in the FocalCodec family; `PRESERVED + CONSISTENT` for 19; and
`STABLE OFFSET` — voice moved but internally coherent — for 8, almost all of
them FocalCodec at 25–65 Hz under `redimnet_M_vb2_ptn`. That last category is
the one a single retention score cannot express.

**One dispersion result survives its own confound and one does not.** `mimi_q8`
disperses *inside* the validated support domain (180 of 217 cells in support,
D 0.6237 against a ceiling lower bound of 0.6440), so its drift is not a
band-limiting artefact. Every FocalCodec drift verdict, by contrast, rests on
out-of-support cells — **0 to 6 in-support cells per stratum, and 50 strata with
zero** — so for that family identity dispersion and band-limiting **cannot be
separated in this design**, and no causal claim is made.

A caveat measured on human speech alone: for `ecapa` and `redimnet_b6_lm` the
*human* cross-state ceiling already sits near their own impostor floor. Every one
of the 69 `APPROACHES IMPOSTOR RANGE` markers fell on those two encoders and on
cross-state strata only. **That is an encoder baseline limitation, not decoder
drift.**

### 8.3 Streaming identity

The streaming detector (T6) compares each arm against **its own offline decode**
on the same recording, so no ceiling or floor enters and no cross-arm ranking is
implied.

**The three explicitly causal FocalCodec configurations show near-zero median
additional change under the tested encoders, supported recordings and imposed
chunking regime.** Across all three arms and all three encoders, S1 runs from
**0.999866 to 0.999946** and the S2 median additional change runs from
**−3.9×10⁻⁵ to −5.3×10⁻⁶** — small, and consistently negative. That is the
whole claim. ⚠️ **This study establishes no minimum detectable streaming change
and no equivalence threshold**, so "near-zero median" must not be read as
"below the instrument's resolution": the calibrated quantity G, the separation
between the same-speaker and different-speaker reference distributions, is not
a detection limit for a paired within-arm change and is not used as one here.
Nothing is claimed to be lost, and nothing is claimed to be preserved.

Every other arm degrades by an amount orders of magnitude larger,
from **−0.078** (`bigvgan22`, `ecapa`) to **−0.742** (`dualcodec_25hz_v1`,
`ecapa`); S2 is a paired retention delta, not a cosine, and the two are reported
separately in T6. For `focalcodec_25hz` under `redimnet_b6_lm` the
offline-versus-streamed cosine itself reaches **−0.013**: the streamed output is
essentially orthogonal to that arm's own offline decode *in this embedding
space*. That is a statement about speaker-embedding similarity only — it does
not establish the absence of waveform, linguistic or spectral relationships,
which were not measured here.

This agrees with Gate 4's Q1 detector, an aligned maximum-error detector on the
waveform, which found streamed-versus-offline error at 105–225% of peak for
every arm **except** the same three causal configurations at **0.69–0.74%**. Two
measurements sharing no implementation, the same three survivors. ⚠️ They also
share their input: the same reconstructions of the same corpus. The agreement is
**corroborating evidence** — it makes an independent implementation error in
both less likely — but agreement between two implementations cannot rule out an
error in either, and it says nothing about an artefact of the material both were
computed on.

**The claim is about streamed behaviour, not defect.** Thirteen of these arms
were driven with chunked context they were never designed for. What the result
establishes is the cost of streaming a decoder that was not built to stream.

## 9. Audit history, and why it is in the paper

Six rounds of independent adversarial audit ran against this study — four
before publication, one against the published package, and one against the
correction itself. They are
reported because **three of the defects they found changed conclusions**, and a
methods section that hides them would misrepresent how the numbers were
obtained.

- **The cross-state reference used pairs the measurement forbade.** Dispersion
  compared different texts; its human ceiling did not, admitting the *same
  sentence spoken in two emotions* — in a parallel corpus, the most similar
  cross-state pair that exists. Excess: 3,255 pairs in Set S. **Eight of 108
  cross-state labels changed** when it was repaired.
- **The Set L ceiling was measured on the wrong duration.** Calibration used
  full-length recordings where the measurement compares 14-second prefixes,
  inflating the ceiling by 0.020–0.055 cosine against interval widths of
  0.02–0.03. Counterfactual: **73 of 108 Set L strata would have carried a
  different label, 67 of them false drift verdicts.**
- **A pair-grouping convention was order-dependent.** Permuting row order moved
  cross-state estimates by up to 0.089 — enough to flip a label. Replaced with a
  symmetric rule and verified invariant to machine precision.

A fourth class of defect was archival rather than scientific: evidence
verification hashed the instrument but not the evidence, and the archive
validated what it listed rather than what it required. Both are repaired and
negative-tested. One superseded snapshot was nonetheless **permanently lost**,
and that is recorded as unrecoverable rather than described as retained; the 540
labels were instead reconstructed independently from the unchanged measurement
rows, with 0 mismatches.

The pattern is worth naming because it recurred three times in different
disguises: **verification that checks what is present rather than what is
required.** The estimator without its reference; the instrument without its
evidence; the manifest without its inventory.

**A fifth round ran after v1.0.0 was published**, against the published package
rather than the private tree, and it found the same pattern a fourth time — in
the release itself. The advertised public reproduction commands did not run:
the scripts resolved artifacts relative to their location in the *private* tree,
where they sat one directory above the data, and the release ships them flat.
The claim audit additionally required a withheld file unconditionally, and the
verifier being advertised was the manifest of the private tree, which cannot
verify a sanitised package and reported 26 of 32 artifacts as drift. Alongside
that, four claims outran their evidence — a first-audio range that borrowed a
steady-state number for its upper end, a chunk-failure count of three where two
arms fail everywhere and a third fails only at the anchor, a mechanism asserted
for Griffin-Lim that this package does not demonstrate, and three sentences
claiming more than their evidence could carry — that the causal arms lost
*nothing*, when their medians are small but non-zero; that one arm's streamed
output bore *no relation* to its own offline decode, when what was measured was
a single embedding distance; and that agreement between two instruments
*excluded* an implementation error in either, which agreement cannot do. Every
one is corrected in v1.0.1 and itemised in
`CORRECTIONS_v1.0.1.md`. **No measurement changed.**

**A sixth round then attacked the correction itself**, before any of it was
published, and found five more defects — including two claims in the repair that
outran their evidence, a privacy scanner that still listed roots instead of
declaring its domain, and a package verifier that printed its own integrity
fingerprint without ever comparing it. Those are corrected too, and recorded in
place rather than rewritten. The lesson generalises the one above three times
over: a package that verifies its own private origin has not verified what it
shipped; a verifier that prints a value has not compared it; and a correction
is not exempt from the discipline that produced it.

## 10. Limitations

1. **Perceptual quality is not measured.** No listening test was run. Which
   decoder *sounds* best is not established and no sentence here implies it.
2. **The sole ranking metric failed its own validity instrument in Route B**
   (§7.1), and the check has **not been run** in Route A, which is not the same
   as passing it.
3. Mel-cepstral distance is gain-invariant by construction and blind to a pure
   level error; these values are not literature-scale MCD and must never be
   quoted against published figures.
4. **Q5 measures speaker-encoder representations**, not perceptual identity and
   not cloning quality.
5. **17,020 of 31,248 offline cells and 26,147 of 27,776 streamed cells fall
   outside the validated support domain** (14,083 and 781 inside, respectively).
   Support is carried as a covariate, never as an exclusion, and every aggregate
   is reported both pooled and stratified.
6. FocalCodec dispersion and band-limiting **cannot be separated** in this
   design (§8.2).
7. Cross-state markers on two of three encoders are **encoder baseline
   limitations** (§8.2).
8. Seven speakers, one studio, one chain, English. Absolute values are not
   comparable to VoxCeleb-scale benchmarks.
9. The incumbent's environment is **not numerically comparable** to the
   reference environment (§6).
10. `melflow` results rest on **locally repaired upstream code**, and its
    latency is an eager-mode upper bound.
11. One encoder runs on CPU because it failed an exact-zero cross-process
    determinism probe on CUDA. The measured CPU-versus-GPU cosine difference is
    ≤ 2.5e-04, roughly 100× below the smallest decision bound.

## 11. Conclusions

**For a product decision.** If the requirement is genuine streaming, the
candidate set is far smaller than the literature suggests: three arms in twenty
reproduce full-context output from partial input with load-bearing state, and
the same three are the only ones showing **near-zero median additional change
under our speaker-embedding metric** when streamed — under the tested encoders,
supported recordings and imposed chunking regime. That is a representation-level
result measured with three encoders, not a claim that those decoders preserve
identity as a listener would judge it, and not a claim that the change is below
any established detection threshold, because this study establishes none.
Everything else is a chunking strategy whose cost we have now measured rather
than assumed.

**For measurement practice.** Two measurements ranked a zero-parameter
phase-blind algorithm first. Neither was wrong about what it measured — a
spectral distance and a speaker-embedding similarity, each computed correctly.
**Neither establishes perceptual quality**, and this study cannot say what
either costs a listener, because no listening test was run. The
pre-registration that named this outcome in advance is the only reason it reads
as a finding rather than an embarrassment — and the reason no metric was swapped
in afterwards to produce a tidier table.

**What comes next, and is not claimed here.** Human listening and adversarial
detectability are declared later phases, neither started. The reconstructions
are retained for exactly that reason.

## Data and code availability

The analysis code, frozen specifications, machine-readable results, generated
tables and the publication manifest are released. **The source audio is not
released**: it is private, rights-cleared recordings of seven consented
speakers. Derived **speaker embeddings are also withheld** — an embedding of a
named human is biometric data, and publishing it is a different act from the
research use the consent covers.

**What the public package can and cannot do is worth stating exactly**, because
v1.0.0 of this paper claimed more than it delivered.

*Regenerates from the released artifacts.* Every table in §§5–8 and every
headline number in the prose is recomputed from the published aggregate
artifacts by `make_paper_tables.py`, and re-traced to its source artifact by
`claim_audit.py`. `make_public_manifest.py --verify` re-hashes the released
bytes. All three run from the release package with no private input.

*Does not.* One claim — the support-domain cell counts, **17,020 of 31,248
offline and 26,147 of 27,776 streamed** — is computed from `Q5_CELLS.jsonl`,
the per-recording rows, which are withheld. The public claim audit reports it
`WITHHELD`, not `PASS`. More generally, the published aggregates and their
confidence intervals **cannot be independently reconstructed from the public
package**: that needs the withheld per-recording rows and embeddings.
Recomputing a table from a published aggregate is a consistency check, and this
paper does not represent it as more than one.

`PUBLICATION_MANIFEST.json` is the frozen manifest of the **private canonical
tree** and is published as a historical record; it does not describe the
sanitised public package and will report drift against it. `PUBLIC_MANIFEST.json`
is the integrity record for the released bytes. The frozen records carry SHA-256
for each artifact, and the private verification tool reports instrument,
evidence and archive drift separately, failing closed on any of them.
