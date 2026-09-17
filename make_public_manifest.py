r"""PUBLIC MANIFEST — the integrity record of the PUBLISHED package.

⛔ This is NOT `PUBLICATION_MANIFEST.json`, and the distinction is the whole
point of this file.

  `PUBLICATION_MANIFEST.json`  the frozen manifest of the PRIVATE canonical
                               research tree. It hashes private artifacts under
                               their private filenames. It is published as a
                               historical freeze record and is never modified.
                               It CANNOT verify the public package: the public
                               tree is a redacted derivative, so its bytes
                               differ by construction and some filenames differ
                               too. Pointed at the release it reports 26 of 32
                               artifacts as drift, which is correct behaviour
                               and useless as a public check.

  `PUBLIC_MANIFEST.json`       this file's output. It hashes the bytes that
                               actually shipped, so a reader can verify the
                               package they downloaded.

v1.0.0 advertised the first as the public verification command. That is the
defect this script exists to close.

    python make_public_manifest.py            # write PUBLIC_MANIFEST.json
    python make_public_manifest.py --verify   # re-hash, exit 1 on any drift

Verification is driven by the manifest's INVENTORY, not by what happens to be
on disk: a file that vanished is MISSING, a file that appeared is UNDECLARED,
and either one fails. Checking only what is present is the exact failure this
study hit three times before publication and once after.
"""
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "PUBLIC_MANIFEST.json"

# The manifest cannot hash itself, and nothing else is exempt.
SELF_EXCLUDE = {NAME}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# Not part of the package: version-control metadata and build caches. `.git` in
# particular is the publishing repository's own directory, not something a
# reader downloads as a file of the release.
SKIP_DIRS = {".git", ".github", "__pycache__", ".ipynb_checkpoints"}


def tree_files(d):
    out = []
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in sorted(files):
            if f in SELF_EXCLUDE:
                continue
            p = os.path.join(root, f)
            out.append((os.path.relpath(p, d).replace(os.sep, "/"), p))
    return sorted(out)


def inventory_fingerprint(files):
    """One hash over (name, sha256) pairs. Two packages agree or they do not."""
    items = sorted((n, s["sha256"]) for n, s in files.items())
    blob = json.dumps(items, separators=(",", ":")).encode()
    return {"count": len(items), "sha256": hashlib.sha256(blob).hexdigest()}


def build(d):
    files = {}
    for rel, p in tree_files(d):
        files[rel] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p)}
    return {
        "what": "Integrity record for the PUBLISHED package. Hashes the bytes "
                "that shipped.",
        "not_this": "This is NOT PUBLICATION_MANIFEST.json, which is the frozen "
                    "manifest of the PRIVATE canonical tree and cannot verify a "
                    "redacted derivative. Both are published; they answer "
                    "different questions.",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verify_command": "python make_public_manifest.py --verify",
        "n_files": len(files),
        "total_bytes": sum(v["bytes"] for v in files.values()),
        "inventory_fingerprint": inventory_fingerprint(files),
        "files": files,
    }


def verify(d):
    """Re-check the package against the manifest. EVERY recorded field is
    enforced, not merely displayed.

    An earlier version printed the recomputed fingerprint next to the recorded
    one and never compared them, and never checked the recorded byte sizes or
    counts at all. Corrupting the fingerprint or the size metadata exited 0.
    Printing a number beside another number is not a check; only a comparison
    that can fail is.
    """
    p = os.path.join(d, NAME)
    if not os.path.isfile(p):
        print("MISSING MANIFEST: %s" % p)
        return 1
    man = json.load(open(p, encoding="utf-8"))
    declared = man["files"]
    on_disk = dict(tree_files(d))

    bad = 0
    for rel in sorted(declared):
        if rel not in on_disk:
            print("MISSING     %-34s declared but not in package" % rel)
            bad += 1
            continue
        got = sha256_file(on_disk[rel])
        if got != declared[rel]["sha256"]:
            print("DRIFT       %-34s declared=%s now=%s"
                  % (rel, declared[rel]["sha256"][:16], got[:16]))
            bad += 1
        size = os.path.getsize(on_disk[rel])
        if size != declared[rel].get("bytes"):
            print("SIZE        %-34s declared=%s now=%d"
                  % (rel, declared[rel].get("bytes"), size))
            bad += 1
    for rel in sorted(on_disk):
        if rel not in declared:
            print("UNDECLARED  %-34s present but not in the manifest" % rel)
            bad += 1

    # ---- recorded totals, enforced.
    if man.get("n_files") != len(declared):
        print("COUNT       n_files=%s but the manifest lists %d file(s)"
              % (man.get("n_files"), len(declared)))
        bad += 1
    tot = sum(v.get("bytes", 0) for v in declared.values())
    if man.get("total_bytes") != tot:
        print("TOTAL       total_bytes=%s but the entries sum to %d"
              % (man.get("total_bytes"), tot))
        bad += 1

    # ---- inventory fingerprint, enforced twice: against what is on disk, and
    # against the manifest's own entries, so editing a hash and its fingerprint
    # together still fails on the first comparison.
    rec = man.get("inventory_fingerprint") or {}
    fp_disk = inventory_fingerprint({r: {"sha256": sha256_file(on_disk[r])}
                                     for r in on_disk if r in declared})
    fp_self = inventory_fingerprint(declared)
    if rec.get("sha256") != fp_disk["sha256"]:
        print("FINGERPRINT declared=%s but the package hashes to %s"
              % (str(rec.get("sha256"))[:16], fp_disk["sha256"][:16]))
        bad += 1
    if rec.get("sha256") != fp_self["sha256"]:
        print("FINGERPRINT declared=%s but its own entries hash to %s"
              % (str(rec.get("sha256"))[:16], fp_self["sha256"][:16]))
        bad += 1
    if rec.get("count") != len(declared):
        print("FINGERPRINT count=%s but the manifest lists %d file(s)"
              % (rec.get("count"), len(declared)))
        bad += 1

    print("\npublic package: %s" % d)
    print("files declared: %d   problems: %d" % (len(declared), bad))
    print("inventory fingerprint declared: %s" % str(rec.get("sha256"))[:16])
    print("inventory fingerprint now:      %s" % fp_disk["sha256"][:16])
    print("PUBLIC PACKAGE VERIFIED" if bad == 0 else "PUBLIC PACKAGE FAILED")
    return 1 if bad else 0


def selftest():
    """Corrupt a throwaway package one way at a time; every case must FAIL.

    These are the cases an independent review ran against the first version of
    this verifier. Three of them exited 0 — fingerprint, byte size and count
    were recorded and printed but never compared. A verifier is only worth the
    failures it can actually produce, so they are pinned here.
    """
    import shutil
    import tempfile
    root = tempfile.mkdtemp(prefix="pubman_selftest_")
    cases, bad = [], 0
    try:
        for name, corrupt in [
            ("valid package (must PASS)", None),
            ("missing file", "missing"),
            ("content/hash mismatch", "content"),
            ("mapping deleted, file retained", "undeclared"),
            ("extra file, not in manifest", "extra"),
            ("wrong fingerprint", "fingerprint"),
            ("wrong recorded byte size", "size"),
            ("wrong recorded file count", "count"),
            ("wrong recorded total_bytes", "total"),
        ]:
            d = os.path.join(root, (corrupt or "valid"))
            os.makedirs(d)
            open(os.path.join(d, "a.txt"), "w").write("alpha")
            open(os.path.join(d, "b.txt"), "w").write("beta")
            man = build(d)
            if corrupt == "fingerprint":
                man["inventory_fingerprint"]["sha256"] = "0" * 64
            elif corrupt == "size":
                man["files"]["a.txt"]["bytes"] = 999
            elif corrupt == "count":
                man["n_files"] = 99
            elif corrupt == "total":
                man["total_bytes"] = 123456
            elif corrupt == "undeclared":
                del man["files"]["b.txt"]
            open(os.path.join(d, NAME), "w").write(json.dumps(man, indent=1))
            if corrupt == "missing":
                os.remove(os.path.join(d, "b.txt"))
            elif corrupt == "content":
                open(os.path.join(d, "a.txt"), "w").write("ALPHA")
            elif corrupt == "extra":
                open(os.path.join(d, "c.txt"), "w").write("gamma")

            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = verify(d)
            want = 0 if corrupt is None else 1
            ok = rc == want
            bad += not ok
            cases.append((ok, name, rc, want))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("PUBLIC MANIFEST VERIFIER SELF-TEST\n")
    print("%-4s %-36s %6s %6s" % ("", "case", "exit", "want"))
    for ok, name, rc, want in cases:
        print("%-4s %-36s %6d %6d" % ("ok" if ok else "FAIL", name, rc, want))
    print("\n%d case(s), %d failure(s)" % (len(cases), bad))
    return 1 if bad else 0


def main():
    d = HERE
    if "--tree" in sys.argv:
        d = os.path.abspath(sys.argv[sys.argv.index("--tree") + 1])
    if "--selftest" in sys.argv:
        return selftest()
    if "--verify" in sys.argv:
        return verify(d)
    man = build(d)
    out = os.path.join(d, NAME)
    open(out, "w", encoding="utf-8").write(json.dumps(man, indent=1) + "\n")
    print("wrote %s" % out)
    print("files: %d   bytes: %d" % (man["n_files"], man["total_bytes"]))
    print("inventory fingerprint: %s"
          % man["inventory_fingerprint"]["sha256"][:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
