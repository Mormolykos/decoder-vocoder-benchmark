"""FREEZE GATE 3 — by content hash, not by assertion.

Records the sha256 of every authoritative Gate 1/2/3 artifact at the moment of
freeze, so that any later claim of "unchanged" is CHECKABLE rather than trusted.
Re-running this file in `--verify` mode re-hashes and reports any drift.

It writes a NEW file (`GATE3_FREEZE.json`) and touches none of the artifacts it
hashes, so the state an independent spot-check cleared stays byte-identical.

  python freeze_gate3.py            write the freeze record
  python freeze_gate3.py --verify   re-hash and report drift
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "GATE3_FREEZE.json")

ARTIFACTS = {
    "gate3_authoritative": [
        "GATE3_MATRIX.md", "gate3_matrix.json",
        "results/raw_runs.csv", "results/summary.csv",
    ],
    "gate3_raw": [
        "results/gate3_raw_a.jsonl", "results/gate3_raw_b.jsonl",
        "results/gate3_raw_fish.jsonl", "results/gate3_raw_melflow.jsonl",
        "results/gate3_cells_a.jsonl", "results/gate3_cells_b.jsonl",
        "results/gate3_cells_fish.jsonl", "results/gate3_cells_melflow.jsonl",
        "results/gate3_header_a.json", "results/gate3_header_b.json",
        "results/gate3_header_fish.json", "results/gate3_header_melflow.json",
    ],
    "gate3_e6_environment_control": [
        "results/gate3_cells_e6_decbench.jsonl",
        "results/gate3_cells_e6_fish.jsonl",
        "results/gate3_cells_e6_decbench_melflow.jsonl",
        "results/gate3_raw_e6_decbench.jsonl",
        "results/gate3_raw_e6_fish.jsonl",
        "results/gate3_raw_e6_decbench_melflow.jsonl",
        "results/gate3_header_e6_decbench.json",
        "results/gate3_header_e6_fish.json",
        "results/gate3_header_e6_decbench_melflow.json",
    ],
    "gate2_authoritative_CLOSED": [
        "GATE2_MATRIX.md", "gate2_matrix.json", "GATE2_AUDIT.md",
        "gate2_repaired_a.json", "gate2_repaired_b.json",
        "gate2_repaired_fish.json", "gate2_repaired_melflow.json",
        "fuzz_gate_lib.json",
    ],
    "gate1_gate0_and_protocol": [
        "PROTOCOL.md", "MANIFEST.md", "AUDIT.md", "GATE.md", "FIELD_SURVEY.md",
        "ENVIRONMENT.json", "GATE3_AUDIT.md", "GATE4_HANDOFF.md",
    ],
    "harness": [
        "gate_lib.py", "gate3_lib.py", "gate3_arms.py", "gate3_arms_b.py",
        "gate3_arms_fish.py", "gate3_run.py", "gate3_run_melflow.py",
        "make_gate3_matrix.py", "render_gate3_md.py", "check_gate3.py",
        "export_gate3_csv.py", "correct_artifacts.py", "make_matrix.py",
        "check_consistency.py", "fuzz_gate_lib.py",
    ],
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def scan():
    out, missing = {}, []
    for group, files in ARTIFACTS.items():
        out[group] = {}
        for rel in files:
            p = os.path.join(HERE, rel.replace("/", os.sep))
            if not os.path.exists(p):
                missing.append(rel)
                continue
            out[group][rel] = {"sha256": sha256(p), "bytes": os.path.getsize(p)}
    return out, missing


if "--verify" in sys.argv:
    old = json.load(open(OUT, encoding="utf-8"))
    new, missing = scan()
    drift, checked = [], 0
    for group, files in old["artifacts"].items():
        for rel, rec in files.items():
            checked += 1
            cur = new.get(group, {}).get(rel)
            if cur is None:
                drift.append(f"MISSING  {rel}")
            elif cur["sha256"] != rec["sha256"]:
                drift.append(f"CHANGED  {rel}")
    print(f"verified {checked} artifacts against the freeze of "
          f"{old['frozen_utc']}")
    for d in drift:
        print(f"  ⛔ {d}")
    print(f"\ndrift: {len(drift)}")
    sys.exit(1 if drift else 0)

artifacts, missing = scan()
n = sum(len(v) for v in artifacts.values())
doc = {
    "frozen_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "declaration": "GATE 3 — COMPLETE / FROZEN / CLEARED",
    "scope": ("Gate Zero (validity), Gate 2 (streaming classification) and Gate 3 "
              "(GPU timing) are FROZEN. Their measurements are not to be modified "
              "again unless a later audit finds a CONCRETE DEFECT, in which case "
              "the defect is named, the repair is scoped to it, and this freeze "
              "record is regenerated."),
    "cleared_by": ("independent adversarial review across three rounds: the Gate 2 "
                   "audit, the Gate 2 delta audit and spot-check, and the Gate 3 "
                   "audit and final E1 spot-check. The final Gate 3 spot-check "
                   "returned GATE 3 FINALLY CLEARED: YES."),
    "not_started": ["Gate 4 - reconstruction / audio quality",
                    "human listening / perceptual realism", "Detectorproof"],
    "n_artifacts": n, "missing": missing,
    "verify_command": "python freeze_gate3.py --verify",
    "artifacts": artifacts,
}
json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=2)
print(f"GATE 3 FROZEN — {n} artifacts hashed")
for g, v in artifacts.items():
    print(f"  {g:<34} {len(v):>3} files")
if missing:
    print(f"\n⛔ MISSING: {missing}")
print(f"\nwritten: {OUT}")
print("verify at any time with:  python freeze_gate3.py --verify")
