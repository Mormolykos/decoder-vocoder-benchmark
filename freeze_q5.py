r"""FREEZE THE Q5 SPEAKER-IDENTITY LAYER — spec first, implementation second.

Q5 is declared in GATE4_PREREG.md (line 127, SECTION 5.4.1, SECTION 11.2.3) and was never
built: the frozen text says `NOT YET ADMISSIBLE - METRIC NOT BUILT, NOT FUZZED
(D10)`. Q5_SPEC.md supplies only what that text left open. This script fixes and
hashes it.

    --freeze-spec   records Q5_SPEC.md ALONE, and REFUSES if any Q5 result
                    artifact already exists on disk (see GUARD below).
    --freeze        records the spec plus the implementation. Refuses unless the
                    spec was frozen first AND still hashes to the recorded value.
    --verify        re-hashes everything and reports drift.
    --revise        opens a new revision, RETAINING every previous hash under
                    `superseded`.

GUARD, and it is the only thing here stronger than the Stage 2 freezer: at
--freeze-spec time this script checks that NONE of the Q5 result artifacts exist.
A specification frozen after its own results exist is a description, not a
declaration. The check and its outcome are recorded in the JSON.

WHAT THIS DOES NOT ESTABLISH, withdrawn in advance rather than after an audit:
it is NOT a proof that the specification preceded the implementation. No
implementation hash is taken at spec-freeze time, both timestamps are local
time.gmtime() with no external anchor, this tree is NOT a git repository, and
Q5_SPEC_FREEZE.json is a plain rewritable file. The identical claim was found
FALSE for one file in GATE4_STAGE2_FREEZE.json (audit 3, M5) and is not made here.

It is also NOT BLIND. The author has read Stage 2's results and EXP_SPK's ECAPA
figures. Freezing buys `declared, fixed and auditable before any Q5 number
exists` - nothing more. R19: the author is not the certifier.

This freezes the Q5 LAYER ONLY. GATE4_FREEZE.json, GATE3_FREEZE.json and
GATE4_STAGE2_FREEZE.json are not reopened, restated or shadowed.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Q5_SPEC_FREEZE.json")
#: Superseded evidence sets are copied here, in full, before a new set is
#: recorded. Metadata retention is not preservation.
ARCHIVE_DIR = "Q5_EVIDENCE_ARCHIVE"

SPEC = ["Q5_SPEC.md"]

# Implementation files, hashed at --freeze. Absent ones record as MISSING, which
# is a reportable state and not an error: the spec is frozen before they exist.
IMPLEMENTATION = [
    "q5_lib.py",          # encoders, resampling, embedding, admissibility states
    "q5_calibration.py",  # SECTION 3: ceiling and floor, SOURCE ONLY, runs first
    "q5_fuzz.py",         # SECTION 9: the domain probes, run before any real cell
    "q5_run.py",          # SECTION 1/4: per-cell embeddings and R, cache-keyed by sha256
    "q5_analyze.py",      # SECTION 5/8: aggregation, intervals, labels
    "q5_report.py",       # SECTION 10: tables are generated, never typed
    "freeze_q5.py",       # this file freezes itself
]

# ⭐ THE EVIDENCE SET. Hashing the instrument proves the RULER did not move; it
# says nothing about the MEASUREMENTS. SECTION 10 makes "--verify drift 0" the
# precondition for deleting 35.65 GB of WAVs, so the check gating an
# irreversible deletion must be able to see the thing it protects. Found by
# independent audit 2026-09-15 (MINOR 2).
EVIDENCE = [
    "Q5_CELLS.jsonl",        # the measurement: one row per cell x encoder
    "Q5_EMBEDDINGS.npz",     # the embeddings the WAVs can be deleted against
    "Q5_CALIBRATION.json",   # ceiling, floor, G(e), separability verdicts
    "Q5_FUZZ.json",          # F1 mechanics + F2 calibrated gates
    "Q5_RESULTS.json",       # aggregates, intervals, labels, refusals
    "Q5_TABLES.md",          # the generated report the conclusions are read from
]

# The guard: none of these may exist when the spec is frozen.
RESULT_ARTIFACTS = [
    "Q5_CELLS.jsonl",
    "Q5_RESULTS.json",
    "Q5_CALIBRATION.json",
    "Q5_EMBEDDINGS.npz",
    "Q5_FUZZ.json",
    os.path.join("results", "q5_cells.jsonl"),
    os.path.join("results", "q5_embeddings"),
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


def existing_results():
    return [n for n in RESULT_ARTIFACTS if os.path.exists(os.path.join(HERE, n))]


def _count_meta(name, p):
    """Row/array/label counts, so a truncated artifact is visible as more than
    a changed hash."""
    try:
        if name.endswith(".jsonl"):
            n = sum(1 for line in open(p, encoding="utf-8") if line.strip())
            return {"rows": n}
        if name.endswith(".npz"):
            import numpy as np
            with np.load(p) as z:
                return {"arrays": len(z.files)}
        if name == "Q5_RESULTS.json":
            d = json.load(open(p, encoding="utf-8"))
            labels = sum(1 for _a, per in d.get("arms", {}).items()
                         for _e, blk in per.items()
                         for _s, sb in blk["sets"].items() for _st in sb)
            return {"arms": len(d.get("arms", {})), "labels": labels}
        if name == "Q5_CALIBRATION.json":
            d = json.load(open(p, encoding="utf-8"))
            return {"encoders": len(d.get("calibration", {}))}
        if name == "Q5_FUZZ.json":
            d = json.load(open(p, encoding="utf-8"))
            return {"sections": sorted(k for k in d if k in ("F1", "F2"))}
        if name.endswith(".md"):
            return {"lines": sum(1 for _ in open(p, encoding="utf-8"))}
    except Exception as ex:                      # recorded, never swallowed
        return {"meta_error": "%s: %s" % (type(ex).__name__, ex)}
    return {}


def inventory_fingerprint(evidence):
    """Canonical fingerprint of an evidence inventory.

    Protects the INVENTORY itself. Without it, deleting an entry from a
    snapshot's `evidence` mapping shrinks the set of things verification
    demands - i.e. tampering makes verification EASIER. The fingerprint is
    computed over the (name, sha256) pairs, so a removed, added or altered
    entry changes it.
    """
    items = sorted((k, v.get("sha256", "")) for k, v in evidence.items())
    blob = json.dumps(items, separators=(",", ":")).encode()
    return {"count": len(items),
            "names": [k for k, _ in items],
            "sha256": hashlib.sha256(blob).hexdigest()}


def verify_archived(d, base=None):
    """⛔ Validate EVERY superseded snapshot that claims `recoverable: true`.

    Added after an independent audit, 2026-09-15: the previous --verify checked
    only the CURRENT instrument and evidence files. `recoverable: true` was
    written once, at archive time, and never revalidated - so a deleted or
    corrupted archive still reported success. A recovery claim that is never
    re-tested is not a recovery claim.

    Per archived artifact: the path must exist, the file must open, the sha256
    and byte size must match what was recorded, the count metadata must match,
    and an .npz must survive a real read of every array (which forces the zip
    CRC check - a hash match alone does not prove the archive is loadable).
    """
    base = base or HERE
    drift = 0
    checked = 0
    for h in d.get("evidence_superseded", []):
        stamp = h.get("evidence_frozen_utc", "?")
        if not h.get("recoverable"):
            print("  archive %-24s recoverable=false, %d artifact(s) recorded "
                  "as unrecoverable - nothing to validate"
                  % (stamp, len(h.get("NOT_ARCHIVED", {}))))
            continue
        arch = h.get("archived_files") or {}
        inv = h.get("evidence") or {}

        # ⛔ COMPLETENESS, added after the third audit finding, 2026-09-15.
        # Iterating `archived_files` validates only what the manifest chose to
        # list, so a snapshot could claim recoverable=true while archiving one
        # artifact of six and still pass. Verification must be driven by what is
        # REQUIRED, never by what is LISTED - the same failure class as
        # validating an estimator without its reference.
        fp = h.get("inventory_fingerprint")
        if not fp:
            drift += 1
            print("  ARCHIVE DRIFT %-20s recoverable=true with NO inventory "
                  "fingerprint - its inventory cannot be protected from "
                  "tampering and the recovery claim is not verifiable" % stamp)
        else:
            now_fp = inventory_fingerprint(inv)
            if now_fp != fp:
                drift += 1
                print("  ARCHIVE DRIFT %-20s INVENTORY TAMPERED: recorded "
                      "%d artifact(s) fp=%s, now %d fp=%s; removed=%s added=%s"
                      % (stamp, fp.get("count"), str(fp.get("sha256"))[:16],
                         now_fp["count"], now_fp["sha256"][:16],
                         sorted(set(fp.get("names", [])) - set(now_fp["names"])),
                         sorted(set(now_fp["names"]) - set(fp.get("names", [])))))

        missing_from_inv = [n for n in EVIDENCE if n not in inv]
        if missing_from_inv:
            drift += len(missing_from_inv)
            print("  ARCHIVE DRIFT %-20s recoverable=true but its evidence "
                  "INVENTORY omits required artifact(s): %s"
                  % (stamp, ", ".join(missing_from_inv)))
        # Required = the snapshot's own canonical inventory (by fingerprint where
        # available) union the module's required set. Verification is driven by
        # what is REQUIRED, never by what the mapping happens to list.
        required = sorted(set(inv) | set(EVIDENCE) | set(fp.get("names", []) if fp else []))
        unmapped = [n for n in required if n not in arch]
        extra = [n for n in arch if n not in required]
        if extra:
            drift += len(extra)
            print("  ARCHIVE DRIFT %-20s %d UNEXPECTED archive mapping(s) not "
                  "in the required inventory: %s"
                  % (stamp, len(extra), ", ".join(sorted(extra))))
        if unmapped:
            drift += len(unmapped)
            print("  ARCHIVE DRIFT %-20s recoverable=true but %d required "
                  "artifact(s) have NO archive mapping: %s"
                  % (stamp, len(unmapped), ", ".join(unmapped)))
        if not arch:
            print("  ARCHIVE DRIFT %-20s claims recoverable=true but records NO "
                  "archived files at all" % stamp)
            continue
        for name, rel in sorted(arch.items()):
            checked += 1
            p = os.path.join(base, rel)
            rec = inv.get(name, {})
            if not rec:
                drift += 1
                print("  ARCHIVE DRIFT %-20s %-22s archived but NOT in the "
                      "evidence inventory" % (stamp, name))
                continue
            if not os.path.isfile(p):
                drift += 1
                print("  ARCHIVE DRIFT %-20s %-22s MISSING at %s"
                      % (stamp, name, rel))
                continue
            try:
                size = os.path.getsize(p)
                sha = sha256_file(p)
            except Exception as ex:
                drift += 1
                print("  ARCHIVE DRIFT %-20s %-22s UNREADABLE: %s"
                      % (stamp, name, type(ex).__name__))
                continue
            if sha != rec.get("sha256"):
                drift += 1
                print("  ARCHIVE DRIFT %-20s %-22s SHA MISMATCH archived=%s "
                      "recorded=%s" % (stamp, name, sha[:16],
                                       str(rec.get("sha256"))[:16]))
                continue
            if size != rec.get("bytes"):
                drift += 1
                print("  ARCHIVE DRIFT %-20s %-22s SIZE MISMATCH archived=%d "
                      "recorded=%s" % (stamp, name, size, rec.get("bytes")))
                continue
            meta = _count_meta(name, p)
            bad = {k: (rec.get(k), v) for k, v in meta.items()
                   if k in rec and rec.get(k) != v}
            if bad or "meta_error" in meta:
                drift += 1
                print("  ARCHIVE DRIFT %-20s %-22s COUNT MISMATCH %s"
                      % (stamp, name, bad or meta))
                continue
            if name.endswith(".npz"):
                try:
                    import numpy as np
                    with np.load(p) as z:          # forces the zip CRC check
                        for k in z.files:
                            _ = z[k]
                except Exception as ex:
                    drift += 1
                    print("  ARCHIVE DRIFT %-20s %-22s CORRUPT NPZ: %s: %s"
                          % (stamp, name, type(ex).__name__, ex))
                    continue
        if not drift:
            print("  archive %-24s %d artifact(s) validated: present, readable, "
                  "hash + size + counts match" % (stamp, len(arch)))
    return drift, checked


def selftest_archive():
    """In-memory regression suite for archive verification.

    Builds synthetic snapshots in a temp directory and asserts that each
    defective shape produces archived-evidence drift > 0 and that a valid
    complete archive produces 0. Touches no Q5 artifact.
    """
    import tempfile

    passed = failed = 0

    def run(title, mutate, expect_drift):
        nonlocal passed, failed
        with tempfile.TemporaryDirectory() as base:
            adir = os.path.join(base, ARCHIVE_DIR, "TESTSTAMP")
            os.makedirs(adir)
            ev, arch = {}, {}
            # Fixtures must be PARSEABLE by _count_meta, or the baseline case
            # fails for a reason that has nothing to do with archiving.
            fixtures = {
                "Q5_CELLS.jsonl": b'{"a":1}\n{"a":2}\n',
                "Q5_CALIBRATION.json": b'{"calibration":{"e1":{},"e2":{},"e3":{}}}',
                "Q5_FUZZ.json": b'{"F1":{},"F2":{}}',
                "Q5_RESULTS.json": b'{"arms":{"arm":{"enc":{"sets":{"S":{"Neutral":{}}}}}}}',
                "Q5_TABLES.md": b"# t\nline\n",
            }
            for n in EVIDENCE:
                p = os.path.join(adir, n)
                if n.endswith(".npz"):
                    import numpy as np
                    np.savez(p, a=np.arange(4))
                else:
                    with open(p, "wb") as f:
                        f.write(fixtures.get(n, b"payload\n"))
                with open(p, "rb") as f:
                    body = f.read()
                rec = {"sha256": hashlib.sha256(body).hexdigest(),
                       "bytes": os.path.getsize(p)}
                rec.update(_count_meta(n, p))
                ev[n] = rec
                arch[n] = os.path.join(ARCHIVE_DIR, "TESTSTAMP", n)
            snap = {"evidence_frozen_utc": "TESTSTAMP", "evidence": ev,
                    "inventory_fingerprint": inventory_fingerprint(ev),
                    "archived_files": arch, "NOT_ARCHIVED": {},
                    "recoverable": True}
            mutate(snap, base, adir)
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                drift, _n = verify_archived({"evidence_superseded": [snap]}, base=base)
            ok = (drift > 0) if expect_drift else (drift == 0)
            print("  %-4s %-44s drift=%d %s"
                  % ("PASS" if ok else "FAIL", title, drift,
                     "" if ok else "<-- UNEXPECTED"))
            if not ok:
                print("        " + buf.getvalue().strip().replace("\n", "\n        "))
            if ok:
                passed += 1
            else:
                failed += 1

    print("ARCHIVE VERIFICATION REGRESSION SUITE")
    run("valid complete archive", lambda s, b, a: None, False)
    run("one missing archive mapping",
        lambda s, b, a: s["archived_files"].pop(EVIDENCE[0]), True)
    run("multiple missing archive mappings",
        lambda s, b, a: [s["archived_files"].pop(n) for n in EVIDENCE[:3]], True)
    run("empty archive mapping",
        lambda s, b, a: s.update(archived_files={}), True)
    run("extra/unexpected archive mapping",
        lambda s, b, a: s["archived_files"].update({"NOT_EVIDENCE.txt": "x/y.txt"}),
        True)
    run("missing archived FILE",
        lambda s, b, a: os.remove(os.path.join(a, EVIDENCE[0])), True)
    run("corrupt / hash-mismatched archived file",
        lambda s, b, a: open(os.path.join(a, EVIDENCE[2]), "ab").write(b" "), True)
    run("truncated NPZ (CRC / load failure)",
        lambda s, b, a: open(os.path.join(a, "Q5_EMBEDDINGS.npz"), "r+b").truncate(40),
        True)
    run("inventory entry deleted (tamper to weaken checks)",
        lambda s, b, a: s["evidence"].pop(EVIDENCE[1]), True)
    run("recoverable=true with no fingerprint",
        lambda s, b, a: s.pop("inventory_fingerprint"), True)
    print("\n%d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


def evidence_digest():
    out = {}
    for n in EVIDENCE:
        p = os.path.join(HERE, n)
        if not os.path.isfile(p):
            out[n] = {"sha256": "MISSING"}
            continue
        rec = {"sha256": sha256_file(p), "bytes": os.path.getsize(p)}
        rec.update(_count_meta(n, p))
        out[n] = rec
    return out


def load():
    return json.load(open(OUT, encoding="utf-8")) if os.path.isfile(OUT) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze-spec", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest-archive", action="store_true",
                    help="run the in-memory archive-verification regression "
                         "suite. Touches no Q5 artifact.")
    ap.add_argument("--freeze-evidence", action="store_true",
                    help="record the sha256, byte size and row/array/label "
                         "counts of the EVIDENCE set as canonical. Hashing the "
                         "instrument proves the ruler did not move; this proves "
                         "the measurements did not.")
    ap.add_argument("--revise", action="store_true")
    ap.add_argument("--note", default="", help="why this revision exists")
    ap.add_argument("--allow-existing-results", default="",
                    metavar="REASON",
                    help="freeze the spec even though Q5 result artifacts "
                         "exist. The REASON is RECORDED in the freeze file and "
                         "never discarded. Legitimate only for a defect "
                         "correction made BEFORE any label was computed; a "
                         "spec written to fit results it has already seen is "
                         "not a specification.")
    a = ap.parse_args()

    if a.revise:
        d = load()
        if not d:
            print("REFUSED: nothing is frozen, so there is nothing to revise.")
            return 2
        hist = d.pop("superseded", [])
        hist.append({k: d.get(k) for k in
                     ("spec_frozen_utc", "implementation_frozen_utc",
                      "spec", "implementation", "revision_note",
                      "guard_no_results_present")})
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
                  "current spec. Use --revise (with --note); previous hashes "
                  "are retained, not discarded.")
            return 2
        found = existing_results()
        if found and not a.allow_existing_results:
            print("REFUSED: Q5 result artifacts already exist, so this would be "
                  "a description of results rather than a declaration:")
            for f in found:
                print("   %s" % f)
            print("\nIf this is a defect correction made before any label was "
                  "computed, re-run with --allow-existing-results \"reason\". "
                  "The reason is recorded permanently.")
            return 2
        guard = {"checked": RESULT_ARTIFACTS, "found": found,
                 "result": "PASS - no Q5 result artifact existed at spec-freeze time"}
        if found:
            guard["result"] = "OVERRIDDEN - artifacts existed at spec-freeze time"
            guard["override_reason"] = a.allow_existing_results
            guard["what_this_costs"] = (
                "This spec was frozen while measured artifacts existed. It is "
                "therefore NOT blind to them, and no claim of blindness is made "
                "for this revision. The artifacts present are listed in `found`.")
        d.update({
            "what": "Gate 4 Q5 SPEAKER-IDENTITY LAYER (retention + dispersion). "
                    "NOT the frozen Gate 4 apparatus, NOT Stage 2, NOT Q8.",
            "spec_frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "spec": digest(SPEC),
            "guard_no_results_present": guard,
            "what_this_establishes":
                "The specification is fixed, hashed and auditable; it did not "
                "move between --freeze-spec and --freeze; and no Q5 result "
                "artifact existed on disk when it was frozen.",
            "what_this_does_NOT_establish":
                "IT IS NOT A PROOF THAT THE SPEC PRECEDED THE IMPLEMENTATION, "
                "and no such claim is made: no implementation hash is taken "
                "here, both timestamps are local and unanchored, this tree is "
                "not a git repository, and this file is plainly rewritable. The "
                "same claim was measurably FALSE for one file in "
                "GATE4_STAGE2_FREEZE.json (audit 3, M5).",
            "not_blind":
                "The author has read Stage 2's results and EXP_SPK's ECAPA "
                "figures. Freezing makes the decisions declared, fixed and "
                "auditable before any Q5 number exists. It does not make them "
                "blind, and nothing later can. R19: the author is not the "
                "certifier.",
            "authority":
                "GATE4_PREREG.md wins on every point it already fixes. Where "
                "Q5_SPEC.md differs, the prereg is right and the spec is "
                "defective.",
        })
        json.dump(d, open(OUT, "w"), indent=1)
        print("Q5 SPEC FROZEN at %s" % d["spec_frozen_utc"])
        for k, v in d["spec"].items():
            print("  %-24s %s" % (k, v))
        print("  guard                    %s" % guard["result"])
        if found:
            print("  artifacts present        %s" % ", ".join(found))
            print("  reason recorded          %s" % a.allow_existing_results[:160])
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
            print("REFUSED: Q5_SPEC.md has changed since it was frozen. A "
                  "specification edited to match the code is not a "
                  "specification. Use --revise --note '...' if the change is "
                  "intended; every previous hash is retained.")
            for k in SPEC:
                print("  frozen %s\n  now    %s" % (d["spec"][k], now[k]))
            return 2
        d["implementation_frozen_utc"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        d["implementation"] = digest(IMPLEMENTATION)
        json.dump(d, open(OUT, "w"), indent=1)
        print("Q5 LAYER FROZEN")
        print("  spec frozen           %s" % d["spec_frozen_utc"])
        print("  implementation frozen %s" % d["implementation_frozen_utc"])
        for k, v in d["implementation"].items():
            print("  %-24s %s" % (k, v[:16]))
        return 0

    if a.selftest_archive:
        return selftest_archive()

    if a.freeze_evidence:
        d = load()
        if not d or not d.get("spec"):
            print("REFUSED: freeze the spec and implementation first.")
            return 2
        ev = evidence_digest()
        missing = [k for k, v in ev.items() if v["sha256"] == "MISSING"]
        if missing:
            print("REFUSED: evidence artifact(s) missing: %s" % ", ".join(missing))
            return 2
        # ⛔ REPAIRED after an independent audit, 2026-09-15. The previous
        # version retained only HASHES AND COUNTS of a superseded evidence set
        # and the author described that as "recoverable". IT WAS NOT: a hash
        # proves identity, never recovery. The offline-only Q5_RESULTS.json and
        # Q5_TABLES.md of 2026-09-15T06:57:57Z are GONE and cannot be restored.
        # From here on, the FILES THEMSELVES are copied into ARCHIVE_DIR before
        # a new set is recorded, and the archive path is stored beside the hash.
        if d.get("evidence"):
            stamp = (d.get("evidence_frozen_utc") or "unknown").replace(":", "")
            dest = os.path.join(HERE, ARCHIVE_DIR, stamp)
            copied, failed = {}, {}
            for name, rec in d["evidence"].items():
                src = os.path.join(HERE, name)
                if not os.path.isfile(src):
                    failed[name] = "NOT ON DISK - cannot be archived"
                    continue
                cur_sha = sha256_file(src)
                if cur_sha != rec.get("sha256"):
                    failed[name] = ("CONTENT ALREADY CHANGED - on-disk sha %s "
                                    "!= recorded %s; the superseded bytes are "
                                    "gone" % (cur_sha[:16], str(rec.get("sha256"))[:16]))
                    continue
                os.makedirs(dest, exist_ok=True)
                shutil.copy2(src, os.path.join(dest, name))
                copied[name] = os.path.join(ARCHIVE_DIR, stamp, name)
            hist = d.pop("evidence_superseded", [])
            hist.append({"evidence_frozen_utc": d.get("evidence_frozen_utc"),
                         "note": a.allow_existing_results or d.get("evidence_label",
                                                                   "(no label)"),
                         "evidence": d["evidence"],
                         "inventory_fingerprint": inventory_fingerprint(d["evidence"]),
                         "archived_files": copied,
                         "NOT_ARCHIVED": failed,
                         "recoverable": not failed})
            d["evidence_superseded"] = hist
            if failed:
                print("⚠️  %d superseded artifact(s) could NOT be archived - "
                      "their bytes no longer exist:" % len(failed))
                for k, v in failed.items():
                    print("      %-22s %s" % (k, v))
            if copied:
                print("archived %d superseded artifact(s) to %s"
                      % (len(copied), os.path.join(ARCHIVE_DIR, stamp)))
        d["evidence_label"] = a.allow_existing_results or "(no label)"
        d["evidence_frozen_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        d["evidence"] = ev
        d["evidence_note"] = (
            "The canonical offline-Q5 evidence set. --verify reports INSTRUMENT "
            "drift and EVIDENCE drift separately and fails closed on either. "
            "SECTION 10 makes drift 0 a precondition for deleting the WAVs; "
            "before this block existed, that check could not see the evidence "
            "it was protecting (independent audit, 2026-09-15).")
        json.dump(d, open(OUT, "w"), indent=1)
        print("EVIDENCE FROZEN at %s" % d["evidence_frozen_utc"])
        for k, v in ev.items():
            extra = " ".join("%s=%s" % (a2, b2) for a2, b2 in v.items()
                             if a2 not in ("sha256", "bytes"))
            print("  %-22s %s  %10d bytes  %s"
                  % (k, v["sha256"][:16], v["bytes"], extra))
        return 0

    if a.verify:
        d = load()
        if not d:
            print("NOT FROZEN: %s does not exist" % os.path.basename(OUT))
            return 1
        inst_drift = 0
        for label, names in (("spec", SPEC), ("implementation", IMPLEMENTATION)):
            rec = d.get(label)
            if not rec:
                print("%s: NOT FROZEN" % label)
                continue
            now = digest(names)
            for k in rec:
                if rec[k] != now.get(k):
                    inst_drift += 1
                    print("INSTRUMENT DRIFT %-24s frozen=%s now=%s"
                          % (k, rec[k][:16], str(now.get(k))[:16]))
        n = len(d.get("spec", {})) + len(d.get("implementation", {}))
        print("INSTRUMENT: verified %d artifact(s) against the spec freeze of %s"
              % (n, d.get("spec_frozen_utc")))
        print("instrument drift: %d" % inst_drift)

        ev_rec = d.get("evidence")
        if not ev_rec:
            print("\nEVIDENCE: NOT FROZEN - run --freeze-evidence. Until then "
                  "nothing verifies the measurements, and SECTION 10's deletion "
                  "precondition is NOT met.")
            return 1
        ev_drift = 0
        now = evidence_digest()
        for k, v in ev_rec.items():
            cur = now.get(k, {"sha256": "MISSING"})
            if cur.get("sha256") != v.get("sha256"):
                ev_drift += 1
                print("EVIDENCE DRIFT %-22s frozen=%s now=%s"
                      % (k, v["sha256"][:16], str(cur.get("sha256"))[:16]))
                for m in set(v) | set(cur):
                    if m not in ("sha256",) and v.get(m) != cur.get(m):
                        print("      %-16s frozen=%s now=%s" % (m, v.get(m), cur.get(m)))
        print("\nEVIDENCE: verified %d artifact(s) against the evidence freeze of %s"
              % (len(ev_rec), d.get("evidence_frozen_utc")))
        print("evidence drift: %d" % ev_drift)

        print("\nARCHIVED EVIDENCE: every superseded snapshot claiming "
              "recoverable=true is opened and re-checked")
        arch_drift, n_arch = verify_archived(d)
        print("archived-evidence drift: %d  (%d artifact(s) validated)"
              % (arch_drift, n_arch))

        print("\ntotal drift: %d (instrument %d + current evidence %d + "
              "archived evidence %d)"
              % (inst_drift + ev_drift + arch_drift, inst_drift, ev_drift,
                 arch_drift))
        return 1 if (inst_drift or ev_drift or arch_drift) else 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
