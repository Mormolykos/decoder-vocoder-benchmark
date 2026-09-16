"""Shared Gate Zero primitives. ONE implementation, imported by every arm.

METHODOLOGY.md R6: when two sides must agree on what a node is, the naming
function is shared code, not a convention repeated on both sides. A layout rule
copy-pasted into five gate scripts is five chances for them to drift apart, so
it lives here once.

Nothing in this file times anything.
"""

from typing import Optional, Tuple

import numpy as np

# Declared validity domain. Frozen before any arm was probed.
MIN_ENERGY_RATIO, MAX_ENERGY_RATIO = 0.25, 4.0
DURATION_TOL_FRAMES = 1.5


def rms(x) -> float:
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    return float(np.sqrt(np.mean(x**2))) if x.size else 0.0


def resolve_layout(
    shape: Tuple[int, ...],
    expected_frames: Optional[int] = None,
    expected_codebooks: Optional[int] = None,
    frame_slack: int = 2,
) -> Tuple[str, Optional[int], Optional[int]]:
    """Decide whether a 2-D code tensor is [time, codebooks] or [codebooks, time].

    FAILS CLOSED. Orientation is never guessed from axis position, because
    position is not shared across codecs: Qwen returns [time, codebooks] while
    the transformers codecs return [codebooks, time]. Reading by position turned
    a 12.5 Hz / 16-codebook codec into a fictional "16 Hz / 199-codebook"
    architecture - a number that looks entirely respectable and is inverted.

    Returns (layout, n_frames, n_codebooks), or ("NEEDS RESOLUTION", None, None)
    when the evidence does not force a single answer.
    """
    if len(shape) != 2:
        return "NEEDS RESOLUTION", None, None

    a, b = shape

    def frames_ok(v):
        return expected_frames is not None and abs(v - expected_frames) <= frame_slack

    def cb_ok(v):
        return expected_codebooks is not None and v == expected_codebooks

    # Score each orientation on BOTH axes, not one.
    time_major = frames_ok(a) + cb_ok(b)
    cb_major = frames_ok(b) + cb_ok(a)

    if time_major > cb_major and time_major > 0:
        return "[time, codebooks]", a, b
    if cb_major > time_major and cb_major > 0:
        return "[codebooks, time]", b, a

    # Square, or both orientations equally consistent, or no expectation given.
    return "NEEDS RESOLUTION", None, None


def validate(
    rec,
    src,
    out_sr: int,
    in_dur_s: float,
    frame_s: Optional[float] = None,
) -> Tuple[dict, str]:
    """Structural validity only. Never a quality judgement.

    Duration tolerance is ONE FRAME OF THE ARM UNDER TEST, not a constant. A
    12.5 Hz codec quantises to 80 ms and cannot align finer; a fixed 50 ms
    predicate failed such a codec for obeying its own architecture.
    """
    rec = np.asarray(rec, dtype=np.float64).reshape(-1)
    n = rec.size
    c = {}
    c["samples"] = int(n)
    c["finite"] = bool(np.isfinite(rec).all()) if n else False
    c["peak"] = float(np.abs(rec).max()) if n else 0.0
    c["peak_in_range"] = 0.0 < c["peak"] <= 1.0
    c["out_seconds"] = n / out_sr if out_sr else float("nan")
    tol = DURATION_TOL_FRAMES * frame_s if frame_s else 0.05
    c["duration_tol_s"] = tol
    c["duration_ok"] = abs(c["out_seconds"] - in_dur_s) <= tol
    er = rms(rec) / max(rms(src), 1e-12)
    c["energy_ratio"] = er
    # The predicate near-silence cannot satisfy. A peak check alone could not
    # tell a correct reconstruction from quiet noise.
    c["energy_ok"] = MIN_ENERGY_RATIO <= er <= MAX_ENERGY_RATIO

    ok = all(c[k] for k in ("finite", "peak_in_range", "duration_ok", "energy_ok"))
    return c, ("PASS" if ok else "FAIL")


# =====================================================================
# Added 2026-09-11 by the GATE2_AUDIT repair queue. Everything below is
# shared so that one definition serves every arm (R6). Nothing above was
# edited, so results already recorded under `validate()` remain readable.
# =====================================================================

C1_MAX_ERR = 1e-3   # stateful chunked decode reproduces full context
C2_MIN_RATIO = 10.0  # state is load-bearing


def gate_zero_record(wav, src, out_sr, in_dur_s, frame_s, expect_channels=1):
    """The FULL frozen PROTOCOL.md §8 gate, COMPUTED for every field.

    `close_gate2.py` wrote the literal string `"PASS (this run)"` into four
    rows. A gate that cannot fail is not a gate (R1: a zero is a claim, and so
    is a pass). This function computes every §8 predicate, including the two
    `validate()` does not cover - dtype and channel count - and returns FAIL
    when any of them is unmet.

    `wav` is the raw decoder output tensor BEFORE any reshape, because the
    shape is itself one of the things under test.
    """
    import torch

    c = {}
    c["is_tensor"] = bool(torch.is_tensor(wav))
    if not c["is_tensor"]:
        return c, "UNKNOWN"
    c["shape"] = tuple(int(d) for d in wav.shape)
    c["dtype"] = str(wav.dtype)
    c["dtype_ok"] = wav.dtype == torch.float32
    lead = [int(d) for d in c["shape"][:-1] if d != 1]
    c["channels"] = lead[-1] if lead else 1
    c["channels_ok"] = c["channels"] == expect_channels
    c["sample_rate"] = int(out_sr)

    sub, verdict = validate(wav.detach().cpu().numpy(), src, out_sr, in_dur_s, frame_s)
    c.update(sub)
    ok = (verdict == "PASS") and c["dtype_ok"] and c["channels_ok"]
    return c, ("PASS" if ok else "FAIL")


def _flat(t):
    return t.detach().float().reshape(-1)


def err(full, chunked):
    """max|full - chunked| over the common prefix, and the same divided by the
    reference's own peak. IDENTICAL definition for every arm.

    ⛔ The normalised figure is a DETECTOR, not a severity scale. A one-sample
    misalignment on encodec24_q8 produces 34.07%, inside the band this metric
    reported for genuine chunking damage. It supports "chunking departs from
    full context" and NOT "arm X departs more than arm Y".
    """
    n = min(full.shape[-1], chunked.shape[-1])
    raw = float((full[:n] - chunked[:n]).abs().max())
    pk = max(float(full[:n].abs().max()), 1e-12)
    return raw, raw / pk


def pcm_valid(w):
    import numpy as _np

    w = _np.asarray(w.detach().cpu().numpy() if hasattr(w, "detach") else w,
                    dtype=_np.float64).reshape(-1)
    if w.size == 0:
        return False
    pk = float(_np.abs(w).max())
    return bool(_np.isfinite(w).all()) and 0.0 < pk <= 1.0


def measure_condition(full, chunked, cf, unit_ms, samples_per_unit, n_chunks,
                      stateful=None):
    """One chunk condition, with LENGTH DRIFT recorded rather than hidden.

    `n = min(lengths)` conceals a decoder that emits fewer samples per chunk
    than the grid implies: vocos_mel24 and griffinlim lose one hop (256
    samples) per chunk, which at 8-frame chunks accumulates to ~2 s of
    misalignment, and DualCodec loses 4 samples per chunk. Reported error is
    then substantially drift rather than boundary damage, so drift is now a
    recorded column on every row.
    """
    full, chunked = _flat(full), _flat(chunked)
    row = {
        "chunk_units": int(cf),
        "chunk_ms": round(unit_ms * cf, 3),
        "n_chunks": int(n_chunks),
        "chunked_samples": int(chunked.shape[-1]),
        "expected_samples": int(round(n_chunks * cf * samples_per_unit)),
    }
    row["drift_total_samples"] = row["chunked_samples"] - row["expected_samples"]
    row["drift_per_chunk_samples"] = round(
        row["drift_total_samples"] / max(n_chunks, 1), 4)
    raw, rel = err(full, chunked)
    row["compared_samples"] = int(min(full.shape[-1], chunked.shape[-1]))
    row["stateless_raw"] = raw
    row["stateless_rel_pct"] = round(100 * rel, 4)
    row["valid_pcm"] = bool(pcm_valid(chunked))

    if stateful is None:
        row["stateful_raw"] = None
        row["stateful_rel_pct"] = None
        row["c2_ratio"] = None
        row["C1"] = False
        row["C2"] = None
    else:
        stateful = _flat(stateful)
        sraw, srel = err(full, stateful)
        row["stateful_raw"] = sraw
        row["stateful_rel_pct"] = round(100 * srel, 4)
        row["stateful_samples"] = int(stateful.shape[-1])
        ratio = raw / max(sraw, 1e-12)
        row["c2_ratio"] = ratio
        row["C1"] = bool(sraw <= C1_MAX_ERR)
        row["C2"] = bool(ratio >= C2_MIN_RATIO)
    return row


def classify(rows, state_constructible, state_note):
    """THE label, computed from BOTH criteria.

    `close_gate2.py:134` read `if codec.causal and raws and max(raws) <= C1`.
    C2 appeared only inside a print statement, so both TRUE_INCREMENTAL labels
    in that batch were awarded on C1 alone - contradicting the file's own
    docstring. C2 is a conjunct here, at every condition.
    """
    if not rows:
        return ("STREAMING SUPPORT NOT ESTABLISHED",
                "no chunk condition produced a comparable output")
    if not state_constructible:
        if all(r["valid_pcm"] for r in rows):
            return ("STATELESS_CHUNKING",
                    f"C2 not constructible: {state_note}. Chunked output is valid "
                    f"PCM at every condition but departs from full context.")
        return ("FULL_CONTEXT_ONLY",
                f"C2 not constructible: {state_note}. Chunked output is not valid "
                f"PCM at one or more conditions.")

    c1_all = all(r["C1"] for r in rows)
    c2_all = all(bool(r["C2"]) for r in rows)
    if c1_all and c2_all:
        return ("TRUE_INCREMENTAL",
                "C1 and C2 both pass at every chunk condition on the arm's own grid")
    if all(r["valid_pcm"] for r in rows):
        failed = "C1" if not c1_all else "C2"
        return ("STATELESS_CHUNKING",
                f"state is constructible but {failed} fails; chunked output stays "
                f"valid PCM and departs from full context")
    return ("FULL_CONTEXT_ONLY",
            "chunked output is not valid PCM at one or more conditions")


def json_default(o):
    """numpy scalars leak out of the predicates and are not JSON serialisable
    under every interpreter in this estate. Coerce rather than lose an artifact
    after the measurement has already run."""
    import numpy as _np

    if isinstance(o, _np.bool_):
        return bool(o)
    if isinstance(o, _np.integer):
        return int(o)
    if isinstance(o, _np.floating):
        return float(o)
    if isinstance(o, _np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serialisable: {type(o).__name__}")


def native_grid(frame_ms, quantum_units=1, targets=(80.0, 160.0, 400.0, 800.0)):
    """Chunk conditions on the ARM'S OWN grid (PROTOCOL.md amendment 1).

    Targets are wall-time durations so conditions are comparable across arms;
    each is snapped to an integer number of the arm's atomic streaming blocks.
    Feeding a streaming model off-grid fragments and concluding it cannot
    stream is an instrument defect, and it has already happened twice here.
    """
    q_ms = frame_ms * quantum_units
    out = []
    for t in targets:
        # round HALF UP, not Python's banker's rounding: round(0.5) is 0 and
        # round(2.5) is 2, so a quantum coarser than a target silently collapsed
        # two conditions into one. Found by fuzz_gate_lib.py, 2026-09-11. No arm
        # in this study had a grid affected - verified condition by condition -
        # but a latent defect in a shared grid function is not left in place.
        n = max(1, int(t / q_ms + 0.5)) * quantum_units
        if n not in out:
            out.append(n)
    return out


def band(rows, key):
    """min-max band with enough significant figures to survive rounding.

    `rel: "0.0-0.0%"` on both causal FocalCodec rows was a `.1f` format
    destroying 0.0072% and 0.0358%.
    """
    vals = [r[key] for r in rows if r.get(key) is not None]
    if not vals:
        return None
    lo, hi = min(vals), max(vals)
    return f"{lo:.4g}" if lo == hi else f"{lo:.4g}-{hi:.4g}"
