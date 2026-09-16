r"""FREEZE THE STAGE 2 ANALYSIS LAYER — the answer to BLOCKING finding B1.

The Gate 4 apparatus was frozen before any decoder output existed. The ~600
lines that turn measured cells into published labels never were, and four
successive audits each found new undeclared decisions in them.

Two stages:

    --freeze-spec   records GATE4_STAGE2_SPEC.md ALONE. Writes `spec_frozen_utc`.
    --freeze        records the spec plus the analysis implementation. Refuses
                    to run unless the spec was frozen first AND still hashes to
                    the recorded value.
    --verify        re-hashes everything and reports drift.

⛔ WHAT THIS DOES **NOT** ESTABLISH, corrected after audit 3 M5. An earlier
version of this file claimed the two stages PROVE the specification preceded the
implementation. THEY DO NOT, and the claim is withdrawn:

  * nothing is hashed about the implementation at --freeze-spec time, so code
    that already existed is invisible. Writing the implementation first, then a
    specification to match, then running both stages in order, passes every
    check here.
  * both timestamps are time.gmtime() on this machine, with no external anchor,
    and this tree is NOT a git repository - there is no tamper-evident record.
  * GATE4_STAGE2_FREEZE.json is a plain rewritable file; --freeze-spec refuses
    only while an `implementation` key exists, and deleting the file clears it.
  * MEASURED and decisive: the ordering claim was FALSE for one of the five
    files. gate4_determinism.py has mtime 2026-09-13T06:41:32Z, two hours and
    twenty-five minutes BEFORE the spec freeze at 09:06:54Z. It was never
    changed to match the spec.

WHAT IT DOES ESTABLISH, which is all that is claimed now: the specification did
not move between the two stages, and the declared specification and
implementation are FIXED, HASHED AND AUDITABLE. Filesystem mtimes happen to be
consistent with the claimed order for the other four files; that is an
observation, not a proof.

⛔ This freezes the ANALYSIS LAYER ONLY. gate4_lib.py, gate4_support.py, the
instrument floors, the corpus and GATE4_PREREG.md live in GATE4_FREEZE.json and
are NOT reopened, restated or shadowed here.
"""
import argparse
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "GATE4_STAGE2_FREEZE.json")

SPEC = ["GATE4_STAGE2_SPEC.md"]

IMPLEMENTATION = [
    "gate4_metrics.py",         # aggregation, verdicts, taxonomy
    "gate4_determinism.py",     # SECTION 7.2, run post-hoc
    "gate4_retro_sha.py",       # M3 retrospective reproduction
    "gate4_report.py",          # S10: the package is generated, not typed
    "freeze_gate4_stage2.py",   # this file freezes itself
]


def sha256_file(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(buf), b""):
            h.update(c)
    return h.hexdigest()


def digest(names):
    out = {}
    for n in names:
        p = os.path.join(HERE, n)
        out[n] = sha256_file(p) if os.path.isfile(p) else "MISSING"
    return out


def load():
    return json.load(open(OUT, encoding="utf-8")) if os.path.isfile(OUT) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze-spec", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--revise", action="store_true",
                    help="open a new revision, RETAINING every previous hash "
                         "under `superseded` rather than overwriting it")
    ap.add_argument("--note", default="", help="why this revision exists")
    a = ap.parse_args()

    if a.revise:
        d = load()
        if not d:
            print("REFUSED: nothing is frozen, so there is nothing to revise.")
            return 2
        hist = d.pop("superseded", [])
        hist.append({k: d.get(k) for k in
                     ("spec_frozen_utc", "implementation_frozen_utc",
                      "spec", "implementation", "revision_note")})
        nd = {"what": d["what"], "superseded": hist,
              "revision_note": a.note or "(no note given)",
              "revisions": len(hist) + 1}
        json.dump(nd, open(OUT, "w"), indent=1)
        print("REVISION OPENED. %d previous freeze(s) retained under "
              "`superseded`." % len(hist))
        print("Previous spec hash: %s" % list(hist[-1]["spec"].values())[0][:16])
        print("\nNow run --freeze-spec, then --freeze.")
        return 0

    if a.freeze_spec:
        d = load() or {}
        if d.get("implementation"):
            print("REFUSED: an implementation is already frozen against the "
                  "current spec. Use --revise (with --note) to open a new "
                  "revision; the previous hashes are retained, not discarded.")
            return 2
        d.update({
            "what": "Gate 4 STAGE 2 ANALYSIS LAYER. NOT the frozen apparatus.",
            "spec_frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "spec": digest(SPEC),
            "what_this_establishes":
                "The specification did not move between --freeze-spec and "
                "--freeze, and the declared spec and implementation are fixed, "
                "hashed and auditable.",
            "⛔ what_this_does_NOT_establish":
                "IT IS NOT A PROOF THAT THE SPECIFICATION PRECEDED THE "
                "IMPLEMENTATION, and the earlier claim to that effect is "
                "WITHDRAWN (audit 3, M5). No implementation hash is taken at "
                "spec-freeze time, so pre-existing code is invisible; both "
                "timestamps are local and unanchored; this tree is not a git "
                "repository; and the claim was measurably FALSE for "
                "gate4_determinism.py, whose mtime precedes the spec freeze by "
                "2h25m and which was never changed to match the spec.",
            "not_a_preregistration":
                "SPEC section 0. This layer was specified AFTER four audits of "
                "the results. Freezing makes its decisions declared, fixed and "
                "auditable. It does NOT make them blind, and nothing later can.",
        })
        json.dump(d, open(OUT, "w"), indent=1)
        print("SPEC FROZEN at %s" % d["spec_frozen_utc"])
        for k, v in d["spec"].items():
            print("  %-28s %s" % (k, v[:16]))
        print("\nThis fixes and hashes the spec. It does NOT prove the spec "
              "preceded the implementation - see the module docstring.")
        return 0

    if a.freeze:
        d = load()
        if not d or not d.get("spec"):
            print("REFUSED: run --freeze-spec FIRST. The specification must be "
                  "frozen before the code it governs.")
            return 2
        now = digest(SPEC)
        if now != d["spec"]:
            print("REFUSED: GATE4_STAGE2_SPEC.md has changed since it was "
                  "frozen. A specification edited to match the code is not a "
                  "specification.")
            for k in SPEC:
                print("  frozen %s\n  now    %s" % (d["spec"][k], now[k]))
            return 2
        d["implementation_frozen_utc"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        d["implementation"] = digest(IMPLEMENTATION)
        json.dump(d, open(OUT, "w"), indent=1)
        print("STAGE 2 ANALYSIS LAYER FROZEN")
        print("  spec frozen           %s" % d["spec_frozen_utc"])
        print("  implementation frozen %s" % d["implementation_frozen_utc"])
        for k, v in d["implementation"].items():
            print("  %-28s %s" % (k, v[:16]))
        return 0

    if a.verify:
        d = load()
        if not d:
            print("NOT FROZEN: %s does not exist" % os.path.basename(OUT))
            return 1
        drift = 0
        for label, names in (("spec", SPEC), ("implementation", IMPLEMENTATION)):
            rec = d.get(label)
            if not rec:
                print("%s: NOT FROZEN" % label)
                continue
            now = digest(names)
            for k in rec:
                if rec[k] != now.get(k):
                    drift += 1
                    print("DRIFT %-28s frozen=%s now=%s"
                          % (k, rec[k][:16], str(now.get(k))[:16]))
        n = len(d.get("spec", {})) + len(d.get("implementation", {}))
        print("verified %d artifacts against the spec freeze of %s"
              % (n, d.get("spec_frozen_utc")))
        print("\ndrift: %d" % drift)
        return 1 if drift else 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
