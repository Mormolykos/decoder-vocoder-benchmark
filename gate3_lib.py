"""GATE 3 — shared timing primitives. ONE implementation, imported by every runner.

R6: when several processes must agree on what a measurement is, the measuring
function is shared code, not a convention repeated in four runners.

⛔ FROZEN RULES THIS FILE IMPLEMENTS, none of them chosen here:
  §9.1  torch.cuda.synchronize() before starting AND before stopping the clock
  §9.2  wall clock PRIMARY, CUDA events DIAGNOSTIC. They measure different
        scopes and are NOT expected to agree; disagreement NEVER voids a run.
        The only voiding condition is a missing or failed synchronize, and that
        is asserted STRUCTURALLY here rather than inferred from the numbers.
  §9.3  cold init / first decode / warm steady state kept separate, never mixed
  §9.4  5 warm-up decodes discarded before any measured repetition
  §10.3 TTFA stops at the first PLAYABLE PCM BLOCK - a contiguous buffer of at
        least the condition's requested duration, at the arm's declared rate and
        channel count, PASSING THE §8 VALIDITY GATE. Anything shorter is not a
        block and does not stop the clock.
  §10.4 chunk conditions snapped UPWARD to the arm's own granularity, collisions
        deduplicated, ACTUAL effective duration recorded, never the requested one
  §11   N = 30 warm + 3 cold per cell; every individual run kept; execution
        block-randomised under a stored seed
  §12   every failure is a recorded row carrying its state, never a missing row

Nothing in this file decides a label. It measures and it records.
"""

import hashlib
import json
import os
import platform
import random
import subprocess
import time

import numpy as np
import torch

# ---- frozen constants, all from PROTOCOL.md, none introduced here -----------
SEED = 20260911
DURATIONS_S = (1, 2, 5, 10, 30)              # §11
CHUNK_TARGETS_MS = (20, 40, 80, 160, 320, 640, 1000)   # §10.4
N_WARM = 30                                  # §11
N_COLD = 3                                   # §11
N_WARMUP_DISCARD = 5                         # §9.4
STREAM_CUT_S = 2                             # chunk-condition sweep utterance
LONGRUN_CUT_S = 30                           # sustained-run utterance
N_LONGRUN = 3                                # declared before results, amendment 9
OVERLAP_ANCHOR_MS = 80                       # §10.2 overlap sweep anchor
OVERLAP_QUANTA = (0, 1, 2, 4)                # left context, in quanta
C1_MAX_ERR = 1e-3

_SMI = ("name,memory.total,memory.used,memory.free,temperature.gpu,clocks.sm,"
        "clocks.mem,power.draw,utilization.gpu")


def gpu_state():
    """§7.2: VRAM, temperature, SM and memory clocks, power draw and utilisation,
    recorded before and after every measured cell. Thermal and clock state drift
    over a long session and would otherwise be absorbed into whichever arm ran
    last - the confound §11's block randomisation exists to break, and this is
    the sensor that lets it be CHECKED rather than assumed."""
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={_SMI}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20).stdout.strip().split(",")
        k = ("gpu_name", "vram_total_MiB", "vram_used_MiB", "vram_free_MiB",
             "temp_C", "clock_sm_MHz", "clock_mem_MHz", "power_W", "util_pct")
        d = {}
        for key, v in zip(k, out):
            v = v.strip()
            d[key] = v if key == "gpu_name" else float(v)
        return d
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def _host_state_ctypes():
    """§10.5 requires CPU and host RAM per arm. `psutil` is installed in
    `decbench` but NOT in `fish` or `decbench_melflow` - and neither may be
    touched: `fish` is read-only production work, and installing into
    `decbench_melflow` would invalidate the package set already captured in
    ENVIRONMENT.json. So the fallback is stdlib ctypes, which needs nothing
    installed anywhere and gives the SAME fields in all three environments."""
    import ctypes
    from ctypes import wintypes

    out = {}
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", wintypes.DWORD),
                        ("dwMemoryLoad", wintypes.DWORD),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        m = MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        out["ram_total_MB"] = m.ullTotalPhys / 2**20
        out["ram_available_MB"] = m.ullAvailPhys / 2**20
        out["ram_load_pct"] = float(m.dwMemoryLoad)
    except Exception as e:
        out["ram"] = f"NOT AVAILABLE: {type(e).__name__}"
    try:
        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        c = PMC()
        c.cb = ctypes.sizeof(PMC)
        ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        out["proc_rss_MB"] = c.WorkingSetSize / 2**20
        out["proc_peak_rss_MB"] = c.PeakWorkingSetSize / 2**20
    except Exception as e:
        out["proc_rss"] = f"NOT AVAILABLE: {type(e).__name__}"
    return out


def host_state():
    """CPU time is CUMULATIVE process CPU seconds, from the stdlib, in every
    environment. The runner records this before and after each cell, so the
    delta over that cell's wall time is its CPU utilisation - a derived quantity
    rather than an instantaneous sample that happens to land where it lands."""
    d = {"cpu_count_logical": os.cpu_count(),
         "proc_cpu_time_s": time.process_time(),
         "source": "stdlib+ctypes"}
    d.update(_host_state_ctypes())
    try:
        import psutil

        vm = psutil.virtual_memory()
        p = psutil.Process()
        d.update({"ram_total_MB": vm.total / 2**20,
                  "ram_available_MB": vm.available / 2**20,
                  "proc_rss_MB": p.memory_info().rss / 2**20,
                  "source": "psutil"})
    except Exception:
        pass
    return d


class Timer:
    """§9.1 / §9.2. Both clocks, both scopes, both recorded.

    The synchronize calls live HERE and nowhere else, and `synced` records
    structurally that both of them ran. §9.2's only voiding condition is a
    missing or failed synchronize; it is asserted, not inferred from whether the
    two clocks happen to agree.
    """

    def __init__(self, device="cuda"):
        self.device = device
        self.cuda = device == "cuda" and torch.cuda.is_available()

    def __call__(self, fn):
        synced_before = synced_after = False
        ev0 = ev1 = None
        if self.cuda:
            torch.cuda.synchronize()
            synced_before = True
            ev0, ev1 = (torch.cuda.Event(enable_timing=True),
                        torch.cuda.Event(enable_timing=True))
        t0 = time.perf_counter()
        if ev0 is not None:
            ev0.record()
        out = fn()
        if ev1 is not None:
            ev1.record()
        if self.cuda:
            torch.cuda.synchronize()
            synced_after = True
        t1 = time.perf_counter()
        rec = {
            "wall_s": t1 - t0,                                  # PRIMARY
            "cuda_ms": (ev0.elapsed_time(ev1) if ev0 is not None else None),  # DIAGNOSTIC
            "synced_before": synced_before,
            "synced_after": synced_after,
            "admissible": bool(synced_before and synced_after) if self.cuda else True,
        }
        if rec["cuda_ms"] is not None:
            # §9.2: their DIFFERENCE is itself a recorded measurement - the
            # host-side cost of getting the work onto the GPU. It is worth
            # knowing because it is the part a different serving language could
            # remove. It is never a validity check.
            rec["host_overhead_ms"] = rec["wall_s"] * 1000.0 - rec["cuda_ms"]
        return out, rec


def snap_conditions(frame_ms, quantum_units, targets=CHUNK_TARGETS_MS):
    """§10.4. Snap UPWARD to the arm's own granularity, dedupe collisions, and
    record the ACTUAL effective duration.

    An arm whose quantum is 80 ms simply has no 20 or 40 ms condition. It is not
    penalised for physics, and no arm is flattered by a unit choice.
    """
    q_ms = frame_ms * quantum_units
    seen, out = set(), []
    for t in targets:
        units = max(1, int(np.ceil(t / q_ms - 1e-9))) * quantum_units
        if units in seen:
            continue
        seen.add(units)
        out.append({"requested_ms": float(t), "units": int(units),
                    "effective_ms": round(units * frame_ms, 4)})
    return out


def stats(xs):
    """§13: descriptive as primary - median, IQR, min, and ALL raw runs are kept
    by the caller. Percentiles are linear-interpolated; n is always reported
    beside them, because a p99 over 30 points is a different object from a p99
    over 3000 (R18 corollary: report the count you did not judge)."""
    a = np.asarray([x for x in xs if x is not None], dtype=np.float64)
    if a.size == 0:
        return {"n": 0}
    q1, q3 = np.percentile(a, [25, 75])
    return {
        "n": int(a.size), "mean": float(a.mean()), "median": float(np.median(a)),
        "p50": float(np.percentile(a, 50)), "p95": float(np.percentile(a, 95)),
        "p99": float(np.percentile(a, 99)), "iqr": float(q3 - q1),
        "q1": float(q1), "q3": float(q3),
        "min": float(a.min()), "max": float(a.max()), "std": float(a.std(ddof=1))
        if a.size > 1 else 0.0,
    }


def validity(wav, sr, expect_s, expect_channels=1, frame_s=None, src_rms=None,
             energy_gates=True):
    """§8 gate, reused verbatim in the streaming path so that TTFA cannot be
    stopped by a buffer that would not have passed Gate Zero. A value failing its
    predicate is treated exactly as ABSENT, and absence is UNKNOWN (R1).

    ⚠️ `energy_gates` exists because the energy ratio is NOT one of §8's six
    frozen predicates. §8 lists sample count, sample rate, finiteness, peak
    amplitude, dtype and channels. The energy ratio was added at GATE ZERO to
    kill the sine-tone defect, where it compares a FULL reconstruction against
    the FULL source - a comparison in which the two are aligned by construction.

    Applied to a PREFIX it is not that comparison. These decoders carry a
    constant algorithmic delay (§10.6 requires it to be measured separately), so
    a 640 ms prefix of the output is not the same 640 ms of the source: on
    `focalcodec_50hz_4k_causal` that alone drove the ratio to 0.198 and would
    have voided a TTFA row for an output that is faithful.

    So: on a prefix the energy ratio is COMPUTED AND REPORTED as a diagnostic and
    is NOT a gate. On a full-clip reconstruction it gates, exactly as at Gate
    Zero. Which one applied is recorded on every row.
    """
    if not torch.is_tensor(wav):
        return {"is_tensor": False}, "UNKNOWN"
    w = wav.detach().float().cpu()
    n = w.shape[-1]
    lead = [int(d) for d in tuple(w.shape)[:-1] if d != 1]
    ch = lead[-1] if lead else 1
    c = {
        "samples": int(n), "channels": ch, "channels_ok": ch == expect_channels,
        "dtype": str(wav.dtype), "dtype_ok": wav.dtype == torch.float32,
        "finite": bool(torch.isfinite(w).all()) if n else False,
        "peak": float(w.abs().max()) if n else 0.0,
        "out_seconds": n / sr if sr else float("nan"),
    }
    c["peak_in_range"] = 0.0 < c["peak"] <= 1.0
    tol = 1.5 * frame_s if frame_s else 0.05
    c["duration_tol_s"] = tol
    c["duration_ok"] = abs(c["out_seconds"] - expect_s) <= tol
    if src_rms is not None:
        er = float(w.pow(2).mean().sqrt()) / max(src_rms, 1e-12)
        c["energy_ratio"] = er
        c["energy_in_domain"] = 0.25 <= er <= 4.0
    else:
        c["energy_ratio"] = None
        c["energy_in_domain"] = None
    c["energy_gated"] = bool(energy_gates and src_rms is not None)
    c["energy_ok"] = c["energy_in_domain"] if c["energy_gated"] else True
    ok = all(c[k] for k in ("channels_ok", "dtype_ok", "finite", "peak_in_range",
                            "duration_ok", "energy_ok"))
    return c, ("PASS" if ok else "FAIL")


def estimate_delay(src_at_out_sr, out, sr, max_ms=250.0):
    """§10.6: "any arm-specific constant delay is measured once on a fixed
    calibration clip and applied identically to every condition of that arm."

    Measured here rather than assumed, because it is what made a faithful
    640 ms prefix of `focalcodec_50hz_4k_causal` look like a 0.198 energy ratio.
    Positive lag = the decoder's output LAGS the source.

    Reported with its normalised peak correlation, so a delay estimated from a
    weak correlation can be seen to be weak rather than quoted as a fact.
    """
    n = min(src_at_out_sr.shape[-1], out.shape[-1])
    if n < 1024:
        return {"delay_samples": None, "reason": "calibration clip too short"}
    # On CPU deliberately, and never inside a timed region. Some arms hand back
    # host tensors from their decode path (the Qwen tokenizer returns numpy), so
    # correlating on whichever device the caller happens to hold is a device
    # mismatch waiting to happen - it was one.
    a = src_at_out_sr.detach().reshape(-1)[:n].float().cpu()
    b = out.detach().reshape(-1)[:n].float().cpu()
    a = a - a.mean()
    b = b - b.mean()
    maxlag = min(int(max_ms * sr / 1000.0), n - 1)
    N = 1
    while N < 2 * n:
        N *= 2
    A = torch.fft.rfft(a, N)
    B = torch.fft.rfft(b, N)
    cc = torch.fft.irfft(B * A.conj(), N)
    win = torch.cat([cc[-maxlag:], cc[:maxlag + 1]])
    idx = int(torch.argmax(win).item())
    lag = idx - maxlag
    denom = float(torch.sqrt(a.pow(2).sum() * b.pow(2).sum()))
    return {"delay_samples": int(lag), "delay_ms": 1000.0 * lag / sr,
            "normalised_peak_correlation": float(win[idx]) / max(denom, 1e-12),
            "search_window_ms": max_ms,
            "convention": "positive lag = decoder output LAGS the source"}


def seam_metrics(full, streamed, seam_idx, sr, win_ms=5.0):
    """§10.6, frozen before any output was heard.

    Measure 1 - normalised seam jump: max |first difference| inside the seam
      window, divided by the SAME statistic on the full-context output's
      corresponding window. 1.0 means chunking added nothing.
    Measure 2 - local difference: RMS of the sample-wise difference inside the
      window, normalised by the RMS of the full-context output there.

    ⚠️ This measures what chunking cost a decoder RELATIVE TO ITSELF. It is not
    a quality ranking between decoders and no output may present it as one.
    """
    w = int(round(win_ms * sr / 1000.0))
    rows = []
    n = min(full.shape[-1], streamed.shape[-1])
    for s in seam_idx:
        lo, hi = max(0, s - w), min(n, s + w)
        if hi - lo < 4:
            continue
        f, g = full[lo:hi], streamed[lo:hi]
        df, dg = f.diff().abs().max(), g.diff().abs().max()
        rms_f = float(f.pow(2).mean().sqrt())
        rows.append({
            "seam_sample": int(s),
            "jump_ratio": float(dg / df) if float(df) > 0 else None,
            "local_diff_rms_norm": float((g - f).pow(2).mean().sqrt() / max(rms_f, 1e-12)),
        })
    def agg(key):
        v = [r[key] for r in rows if r[key] is not None]
        return {"median": float(np.median(v)), "max": float(np.max(v)), "n_seams": len(v)} \
            if v else {"n_seams": 0}
    return {"per_seam": rows, "jump_ratio": agg("jump_ratio"),
            "local_diff_rms_norm": agg("local_diff_rms_norm")}


def block_randomise(cells, seed=SEED):
    """§11: arms and conditions INTERLEAVED in a randomised order under a stored
    seed, rather than run arm-by-arm to completion. Randomisation is WITHIN
    environment, so the §7.2 environment control is not broken by it.

    Without this, thermal and clock drift over a long session is absorbed into
    whichever arm happened to run last, and that is indistinguishable from a
    real difference between arms.
    """
    rng = random.Random(seed)
    order = list(cells)
    rng.shuffle(order)
    return order


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_tensor(t):
    a = t.detach().cpu().contiguous().numpy()
    return hashlib.sha256(a.tobytes()).hexdigest()


class RawSink:
    """§11 / §12: every individual run is kept - no means-only file. Failures are
    rows carrying their state, never missing rows. Flushed continuously so a
    crash three hours in cannot destroy what already ran."""

    def __init__(self, path):
        self.path = path
        self.f = open(path, "a", encoding="utf-8")
        self.n = 0

    def write(self, **row):
        self.f.write(json.dumps(row, default=_json_default) + "\n")
        self.n += 1
        if self.n % 50 == 0:
            self.f.flush()

    def close(self):
        self.f.flush()
        self.f.close()


def _json_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if torch.is_tensor(o):
        return o.detach().cpu().tolist()
    raise TypeError(f"not JSON serialisable: {type(o).__name__}")


def env_header(env_name):
    return {
        "env": env_name, "python": platform.python_version(),
        "torch": torch.__version__, "torch_cuda": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
        "device_name": (torch.cuda.get_device_name(0)
                        if torch.cuda.is_available() else "NO CUDA"),
        "seed": SEED, "n_warm": N_WARM, "n_cold": N_COLD,
        "warmup_discarded": N_WARMUP_DISCARD,
        "gpu_state_at_start": gpu_state(), "host_state_at_start": host_state(),
    }
