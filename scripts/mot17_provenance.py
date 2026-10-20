"""Provenance check for the MOT17 copy from `trackers.download_dataset` (STORY-014).

That copy comes from Roboflow's storage, not motchallenge.net (gone, HTTP 410).
It uses ByteTrack's half split: each official training sequence of n frames is
cut into a train half (official frames 1..n//2+1) and a val half (the rest),
both renumbered from frame 1. This script checks that against an independent
copy of the official ground truth — the TrackEval data bundle from RWTH Aachen,
the lab behind MOTChallenge:

  - train + val lengths add up to the official sequence length;
  - image counts match each half's seqinfo.ini;
  - every ground-truth row matches the official one, after the frame offset.

It also prints the sha256 of the downloaded archives (the interim record until
DVC, NFR-REP-5) and each sequence's count of distractor rows — the regions
MOTChallenge ignores — for choosing the TrackEval parity sequence.

    .venv/bin/python -I scripts/mot17_provenance.py \\
        [--root datasets/MOT17/mot17] [--bundle datasets/_sources/trackeval/data.zip]

Run with -I: both inputs are downloaded data. Exits 1 on any mismatch.
"""

import argparse
import configparser
import hashlib
import sys
import zipfile
from pathlib import Path

DISTRACTOR_CLASSES = {2, 7, 8, 12}  # MOT17 rules (ADR-017)
BUNDLE_GT = "data/gt/mot_challenge/MOT17-train/{seq}/"


def rows(text):
    """GT rows as numeric tuples, sorted — order-independent comparison."""
    out = []
    for line in text.splitlines():
        if line.strip():
            p = [float(v) for v in line.split(",")]
            out.append((int(p[0]), int(p[1]), *p[2:]))
    return sorted(out)


def seq_length(ini_text):
    cfg = configparser.ConfigParser()
    cfg.read_string(ini_text)
    return int(cfg["Sequence"]["seqLength"])


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=Path("datasets/MOT17/mot17"))
    ap.add_argument("--bundle", type=Path, default=Path("datasets/_sources/trackeval/data.zip"))
    ap.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "trackers")
    args = ap.parse_args()

    bundle = zipfile.ZipFile(args.bundle)
    failures = 0
    print(f"{'sequence':16} {'official':>8} {'train':>6} {'val':>5} {'GT rows':>8} "
          f"{'distractor rows':>16}  result")
    for train_dir in sorted((args.root / "train").iterdir()):
        seq = train_dir.name
        val_dir = args.root / "val" / seq
        official_len = seq_length(bundle.read(BUNDLE_GT.format(seq=seq) + "seqinfo.ini").decode())
        official = rows(bundle.read(BUNDLE_GT.format(seq=seq) + "gt/gt.txt").decode())
        train_len = seq_length((train_dir / "seqinfo.ini").read_text())
        val_len = seq_length((val_dir / "seqinfo.ini").read_text())

        problems = []
        if train_len + val_len != official_len:
            problems.append(f"lengths {train_len}+{val_len} != {official_len}")
        for d, n in ((train_dir, train_len), (val_dir, val_len)):
            images = len(list((d / "img1").glob("*.jpg")))
            if images != n:
                problems.append(f"{d.parent.name}: {images} images, seqinfo says {n}")
        expected_train = [r for r in official if r[0] <= train_len]
        expected_val = sorted((r[0] - train_len, *r[1:]) for r in official if r[0] > train_len)
        if rows((train_dir / "gt" / "gt.txt").read_text()) != expected_train:
            problems.append("train GT differs from official")
        if rows((val_dir / "gt" / "gt.txt").read_text()) != expected_val:
            problems.append("val GT differs from official")

        distractors = sum(1 for r in official if int(r[7]) in DISTRACTOR_CLASSES)
        failures += bool(problems)
        print(f"{seq:16} {official_len:8} {train_len:6} {val_len:5} {len(official):8} "
              f"{distractors:16}  {'ok' if not problems else 'MISMATCH: ' + '; '.join(problems)}")

    print("\nsha256 (interim provenance record, NFR-REP-5):")
    for path in sorted(args.cache.glob("*mot17*")) + [args.bundle]:
        print(f"  {sha256(path)}  {path.name}")
    print(f"\n{'PROVENANCE OK' if not failures else f'PROVENANCE FAILED ({failures} sequences)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
