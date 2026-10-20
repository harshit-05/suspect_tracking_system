"""TrackEval parity check for evaluation/mot_metrics.py (STORY-010, ADR-017).

Scores the same ground truth and tracker output twice — with our wrapper over
trackers.eval, and with TrackEval, MOTChallenge's official evaluation code —
under both MOT17 and MOT20 rules, and fails if HOTA, MOTA or IDF1 differ by
more than 1e-9. Re-run it whenever `trackers` is upgraded.

TrackEval is deliberately NOT a project dependency (unmaintained since 2022).
Run this from the repo root, in a throwaway venv whose trackers/numpy pins
equal requirements.txt:

    uv venv --python 3.12 /tmp/parity-venv
    uv pip install --python /tmp/parity-venv/bin/python \\
        "trackeval @ git+https://github.com/JonathonLuiten/TrackEval@12c8791b303e0a0b50f753af204249e622d0281a" \\
        trackers==2.5.0.post0 numpy==2.4.4
    /tmp/parity-venv/bin/python -I scripts/trackeval_parity.py \\
        [--gt tests/data/tiny_clip_gt.txt] [--tracks MOT_FILE ...]

The hypotheses are synthetic perturbations of the ground truth (each one aimed
at a different part of the metrics) plus any real tracker output passed with
--tracks. Every coordinate is an integer, so both sides read identical boxes.

Real tracker output comes from an actual pipeline run, which needs torch and
the models — the project venv, not this one. Generate it there first with
scripts/dump_tracks.py, then pass the files here:

    .venv/bin/python -W ignore scripts/dump_tracks.py --video tests/data/MOT17-04-tiny.mp4 \\
        --gt tests/data/MOT17-04-tiny_gt.txt --img-size 320 --out /tmp/t320.txt
    /tmp/parity-venv/bin/python -I scripts/trackeval_parity.py \\
        --gt tests/data/MOT17-04-tiny_gt.txt --rules MOT17 --tracks /tmp/t320.txt
"""

import argparse
import contextlib
import io
import random
import sys
import tempfile
from pathlib import Path

import numpy as np

# TrackEval (unmaintained since 2022) uses np.float / np.int / np.bool, which
# NumPy 2 removed; even its MOT loader breaks. They were plain aliases of the
# builtins (NumPy's own migration note), so restoring them here — in this
# oracle harness only, never in app code — changes no arithmetic and keeps the
# NumPy version identical on both sides of the comparison.
for _alias, _builtin in (("float", float), ("int", int), ("bool", bool)):
    if not hasattr(np, _alias):
        setattr(np, _alias, _builtin)

import trackeval  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.mot_metrics import compute_mot_metrics  # noqa: E402

TOLERANCE = 1e-9
RULES = ("MOT17", "MOT20")
DISTRACTOR_CLASSES = {2, 6, 7, 8, 12}  # the union; each rule set decides which count


def read_mot(path):
    """[(frame, id, x, y, w, h, conf, cls)] from a MOT file (conf/cls 1 if absent)."""
    rows = []
    for line in Path(path).read_text().splitlines():
        p = line.split(",")
        conf = int(float(p[6])) if len(p) > 6 else 1
        cls = int(float(p[7])) if len(p) > 7 else 1
        rows.append((int(float(p[0])), int(float(p[1])), *(round(float(v)) for v in p[2:6]),
                     conf, cls))
    return rows


def hypotheses(gt, seed=0):
    rng = random.Random(seed)
    scored = [r[:6] for r in gt if r[6] != 0 and r[7] == 1]
    frames = max(r[0] for r in gt)
    next_id = iter(range(900_000, 10**7))

    ids = sorted({r[1] for r in scored})
    swap = {}
    for a, b in zip(ids[0::7], ids[3::7]):  # disjoint pairs of tracks
        swap[a], swap[b] = b, a

    return {
        "identity": scored,
        "jitter": [(f, i, round(x + rng.gauss(0, 0.2 * w)), round(y + rng.gauss(0, 0.2 * h)), w, h)
                   for f, i, x, y, w, h in scored],
        "drop_30pct": [r for r in scored if rng.random() > 0.3],
        "id_swaps": [(f, swap.get(i, i) if f > frames // 2 else i, x, y, w, h)
                     for f, i, x, y, w, h in scored],
        "extra_boxes": scored + [(f, next(next_id), rng.randrange(0, 1500), rng.randrange(0, 950),
                                  rng.randrange(20, 120), rng.randrange(40, 240))
                                 for f in range(1, frames + 1) for _ in range(5)],
        "on_distractors": scored + [(r[0], next(next_id), *r[2:6]) for r in gt
                                    if r[7] in DISTRACTOR_CLASSES],
        "empty": [],
    }


def ours(gt_path, rows, frames, rules):
    tracks = {f: [] for f in range(1, frames + 1)}
    for f, i, x, y, w, h in rows:
        tracks[f].append((i, (x - 1, y - 1, x - 1 + w, y - 1 + h)))
    m = compute_mot_metrics(gt_path, tracks, num_frames=frames, benchmark=rules)
    return {k: m[k] for k in ("HOTA", "MOTA", "IDF1")}


def official(gt_path, rows, frames, rules):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        seq_dir = tmp / "gt" / "seq"
        (seq_dir / "gt").mkdir(parents=True)
        (seq_dir / "gt" / "gt.txt").write_text(Path(gt_path).read_text())
        (seq_dir / "seqinfo.ini").write_text(f"[Sequence]\nname=seq\nseqLength={frames}\n")
        data_dir = tmp / "trackers" / "ours" / "data"
        data_dir.mkdir(parents=True)
        # A truly empty file when there are no tracks: TrackEval reads it fine
        # (and crashes on an id -1 placeholder), so the "empty" case checks that
        # our placeholder trick scores the same as genuinely no tracks.
        lines = [f"{f},{i},{x},{y},{w},{h},1,-1,-1,-1" for f, i, x, y, w, h in rows]
        (data_dir / "seq.txt").write_text("\n".join(lines) + "\n" if lines else "")

        eval_cfg = trackeval.Evaluator.get_default_eval_config()
        eval_cfg.update(USE_PARALLEL=False, PRINT_RESULTS=False, PRINT_CONFIG=False,
                        TIME_PROGRESS=False, OUTPUT_SUMMARY=False, OUTPUT_DETAILED=False,
                        PLOT_CURVES=False, BREAK_ON_ERROR=True)
        ds_cfg = trackeval.datasets.MotChallenge2DBox.get_default_dataset_config()
        ds_cfg.update(GT_FOLDER=str(tmp / "gt"), TRACKERS_FOLDER=str(tmp / "trackers"),
                      OUTPUT_FOLDER=str(tmp / "out"), TRACKERS_TO_EVAL=["ours"],
                      BENCHMARK=rules, SEQ_INFO={"seq": frames}, SKIP_SPLIT_FOL=True,
                      PRINT_CONFIG=False)
        metric_cfg = {"THRESHOLD": 0.5, "PRINT_CONFIG": False}
        with contextlib.redirect_stdout(io.StringIO()):  # TrackEval is chatty
            res, _ = trackeval.Evaluator(eval_cfg).evaluate(
                [trackeval.datasets.MotChallenge2DBox(ds_cfg)],
                [trackeval.metrics.HOTA(metric_cfg), trackeval.metrics.CLEAR(metric_cfg),
                 trackeval.metrics.Identity(metric_cfg)],
            )
    r = res["MotChallenge2DBox"]["ours"]["seq"]["pedestrian"]
    return {"HOTA": float(np.mean(r["HOTA"]["HOTA"])), "MOTA": float(r["CLEAR"]["MOTA"]),
            "IDF1": float(r["Identity"]["IDF1"])}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--gt", default=str(REPO_ROOT / "tests" / "data" / "tiny_clip_gt.txt"))
    ap.add_argument("--tracks", nargs="*", default=[], help="real tracker output (MOT files)")
    ap.add_argument("--rules", nargs="*", default=list(RULES), choices=RULES)
    args = ap.parse_args()

    gt = read_mot(args.gt)
    frames = max(r[0] for r in gt)
    hyps = hypotheses(gt)
    for path in args.tracks:
        hyps[f"real:{Path(path).name}"] = [r[:6] for r in read_mot(path)]

    print(f"GT {args.gt}: {frames} frames, {len(gt)} rows; tolerance {TOLERANCE:g}\n")
    print(f"{'rules':6} {'hypothesis':24} {'HOTA':>8} {'MOTA':>8} {'IDF1':>8}  {'max |Δ|':>9}")
    worst = 0.0
    for rules in args.rules:
        for name, rows in hyps.items():
            a, b = ours(args.gt, rows, frames, rules), official(args.gt, rows, frames, rules)
            delta = max(abs(a[k] - b[k]) for k in a)
            worst = max(worst, delta)
            flag = "ok" if delta <= TOLERANCE else "MISMATCH"
            print(f"{rules:6} {name:24} {a['HOTA']:8.4f} {a['MOTA']:8.4f} {a['IDF1']:8.4f}"
                  f"  {delta:9.1e} {flag}")
            if delta > TOLERANCE:
                print(f"{'':31} TrackEval: HOTA {b['HOTA']:.6f} MOTA {b['MOTA']:.6f} "
                      f"IDF1 {b['IDF1']:.6f}")
    verdict = "PARITY OK" if worst <= TOLERANCE else "PARITY FAILED"
    print(f"\n{verdict}: worst |Δ| = {worst:.1e} across {len(args.rules) * len(hyps)} cases")
    return 0 if worst <= TOLERANCE else 1


if __name__ == "__main__":
    sys.exit(main())
