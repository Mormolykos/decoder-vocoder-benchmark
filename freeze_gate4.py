"""GATE 4 — freeze manifest. Hashes CODE + PREREG + CORPUS SELECTION + FUZZ together.

Minor finding from the final delta review: `fuzz_gate4_lib.py` was NEWER than
`fuzz_gate4_lib.json`, and this directory is not under version control, so the
report could not be proved by inspection to come from the shipped source. A
freeze record must bind them.

⭐ `GATE4_CORPUS.json` embeds `generated_utc`, so the CONTAINER is not
byte-reproducible even though the SELECTION is deterministic. This script
therefore hashes a CANONICAL SELECTION VIEW - the decision content with the
timestamp and other non-semantic fields removed - alongside the raw file hash.
The canonical hash is the one a re-run must reproduce.

    python freeze_gate4.py            # write GATE4_FREEZE.json
    python freeze_gate4.py --verify   # expect: drift: 0

⛔ This freezes the APPARATUS, not a result. No decoder has run.
"""

import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "GATE4_FREEZE.json")

GROUPS = {
    "preregistration": ["GATE4_PREREG.md"],
    "instrument_code": ["gate4_lib.py", "fuzz_gate4_lib.py", "gate4_corpus.py",
                        "gate4_source_gate.py", "gate4_length_policy.py",
                        "gate4_support.py",
                        "freeze_gate4.py"],
    "instrument_artifacts": ["fuzz_gate4_lib.json", "gate4_source_gate.json",
                             "gate4_support_calibration.json"],
    "corpus": ["GATE4_CORPUS.json"],
    "inherited_frozen": ["gate2_matrix.json", "gate3_matrix.json",
                         "gate_lib.py", "gate3_lib.py", "gate3_arms.py",
                         "GATE3_FREEZE.json"],
}

#: Fields that carry no decision content. Excluded from the CANONICAL hash so a
#: re-run of a deterministic producer reproduces it.
NON_SEMANTIC = ("generated_utc", "generated_by")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_corpus(path):
    """The SELECTION, with non-semantic fields stripped and keys ordered."""
    d = json.load(open(path))
    view = {
        "source": d["source"],
        "selection_rule": d["selection_rule"],
        "set_S": {k: v for k, v in d["set_S"].items() if k != "n_recordings"},
        "set_L": {k: v for k, v in d["set_L"].items() if k != "n_recordings"},
        "calibration": d["calibration"],
        "counts": d["counts"],
        "absent_files": d["absent_files"],
        # the per-file sha256 ARE the content address of the corpus
        "cell_hashes": {k: sorted(r["sha256"] for r in v)
                        for k, v in d["cells"].items()},
    }
    for f in NON_SEMANTIC:
        view.pop(f, None)
    return sha256_bytes(json.dumps(view, sort_keys=True,
                                   separators=(",", ":")).encode())


def build():
    arts, missing = {}, []
    for group, files in GROUPS.items():
        arts[group] = {}
        for f in files:
            p = os.path.join(HERE, f)
            if not os.path.isfile(p):
                missing.append(f)
                continue
            arts[group][f] = {"sha256": sha256_file(p),
                              "bytes": os.path.getsize(p)}
    fz = json.load(open(os.path.join(HERE, "fuzz_gate4_lib.json")))
    rank = [k for k, r in fz["metrics"].items()
            if r["verdict"]["verdict"] == "SEVERITY SCALE"]
    return {
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "The Gate 4 APPARATUS: pre-registration, instrument code, "
                 "instrument artifacts and corpus SELECTION. No decoder has run "
                 "and no quality number exists.",
        "not_started": ["Stage 1 decode", "Stage 2 metrics", "Q5 speaker "
                        "identity", "Q6 intelligibility", "human listening",
                        "Detectorproof"],
        "ranking_metrics": rank,
        "instrument_floors": fz.get("INSTRUMENT_FLOORS", {}),
        "canonical_corpus_selection_sha256": canonical_corpus(
            os.path.join(HERE, "GATE4_CORPUS.json")),
        "canonical_note": "GATE4_CORPUS.json embeds generated_utc and is NOT "
                          "byte-reproducible. The CANONICAL hash above covers "
                          "the selection content and every per-file sha256, and "
                          "IS what a deterministic re-run must reproduce.",
        "missing": missing,
        "n_artifacts": sum(len(v) for v in arts.values()),
        "verify_command": "python freeze_gate4.py --verify",
        "artifacts": arts,
    }


def verify():
    if not os.path.isfile(OUT):
        print("no GATE4_FREEZE.json - nothing frozen yet")
        return 1
    rec = json.load(open(OUT))
    drift, checked = [], 0
    for group, files in rec["artifacts"].items():
        for f, meta in files.items():
            p = os.path.join(HERE, f)
            checked += 1
            if not os.path.isfile(p):
                drift.append((f, "MISSING"))
            elif sha256_file(p) != meta["sha256"]:
                drift.append((f, "CHANGED"))
    cc = canonical_corpus(os.path.join(HERE, "GATE4_CORPUS.json"))
    if cc != rec["canonical_corpus_selection_sha256"]:
        drift.append(("GATE4_CORPUS.json", "SELECTION CHANGED"))
    else:
        print("canonical corpus selection reproduces: OK")
    print(f"verified {checked} artifacts against the freeze of {rec['frozen_utc']}")
    for f, why in drift:
        print(f"  DRIFT {why}: {f}")
    print(f"\ndrift: {len(drift)}")
    return 1 if drift else 0


if __name__ == "__main__":
    if "--verify" in sys.argv:
        sys.exit(verify())
    rec = build()
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=1)
    print(f"froze {rec['n_artifacts']} artifacts")
    print(f"ranking metrics: {rec['ranking_metrics']}")
    print(f"canonical corpus selection: {rec['canonical_corpus_selection_sha256'][:24]}...")
    if rec["missing"]:
        print(f"MISSING: {rec['missing']}")
    print(f"wrote {OUT}")
