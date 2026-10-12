"""Official MOTChallenge metrics — MOTA, IDF1 and HOTA — via ``trackers.eval``.

``trackers.eval`` ports TrackEval (MOTChallenge's official evaluation code) for
numerical parity, and ``evaluate_mot_sequence`` applies MOTChallenge
preprocessing: ground truth is ``conf != 0`` pedestrians only, and a tracker box
matched to a distractor ground-truth box is dropped instead of being counted as
a false positive. ``scripts/trackeval_parity.py`` checks the parity against
TrackEval itself (STORY-010, ADR-017).

All three metrics are computed from identical inputs — the same ground-truth
slice and the same tracker rows, one IoU threshold for CLEAR and Identity (HOTA
sweeps its own) — so they can be compared with each other (ML-2).
"""

import re
import tempfile
from pathlib import Path

from trackers.eval import evaluate_mot_sequence

BENCHMARKS = ("MOT17", "MOT20")

# MOT20 also ignores non_mot_vehicle (class 6): TrackEval does so for its MOT20
# benchmark, but trackers.eval doesn't yet (a TODO in trackers/io/mot.py).
# Relabelling those rows as class 8 (distractor) gets the same suppression
# through the public API.
_MOT20_NON_MOT_VEHICLE = 6
_DISTRACTOR = 8
_SEQUENCE_NAME = re.compile(r"(MOT17|MOT20)-\d{2}")

# A row with a negative ID is an unconfirmed track, ignored by both trackers.eval
# and TrackEval. It stands in for "no tracks at all", which trackers.eval cannot
# read as an empty file — and an all-empty run is a valid (terrible) result for
# a bad HPO config, so it must score 0, not crash.
_PLACEHOLDER_ROW = "1,-1,0,0,1,1,1,-1,-1,-1"


def infer_benchmark(gt_path):
    """'MOT17' or 'MOT20', from the sequence folder in a MOTChallenge GT path
    (``.../MOT20-05/gt/gt.txt``). Raises ValueError when there is none."""
    for part in reversed(Path(gt_path).parts):
        match = _SEQUENCE_NAME.match(part)
        if match:
            return match.group(1)
    raise ValueError(
        f"Can't infer the benchmark (MOT17 or MOT20) from GT path {gt_path}; "
        "pass benchmark= explicitly"
    )


def _write_gt_slice(gt_path, num_frames, benchmark, out_path):
    """Copy the GT rows for frames 1..num_frames. trackers.eval scores every
    frame up to the highest one in either file, so an unsliced full-sequence GT
    would count every unprocessed frame as misses. Returns the row count."""
    rows = []
    with open(gt_path) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 8 or int(float(parts[0])) > num_frames:
                continue
            if benchmark == "MOT20" and int(float(parts[7])) == _MOT20_NON_MOT_VEHICLE:
                parts[7] = str(_DISTRACTOR)
            rows.append(",".join(parts))
    Path(out_path).write_text("\n".join(rows) + "\n")
    return len(rows)


def _write_tracks(tracks_by_frame, out_path):
    """Tracker output as MOTChallenge rows. Tracker boxes are 0-based ltrb;
    MOT files are 1-based xywh."""
    rows = [
        f"{frame},{tid},{x1 + 1},{y1 + 1},{x2 - x1},{y2 - y1},1,-1,-1,-1"
        for frame, tracks in sorted(tracks_by_frame.items())
        for tid, (x1, y1, x2, y2) in tracks
    ]
    Path(out_path).write_text("\n".join(rows or [_PLACEHOLDER_ROW]) + "\n")


def compute_mot_metrics(gt_path, tracks_by_frame, num_frames=None, benchmark=None,
                        iou_threshold=0.5):
    """Score tracker output against MOTChallenge ground truth.

    tracks_by_frame: {frame (1-based): [(track_id, (x1, y1, x2, y2)), ...]}
    num_frames: frames processed (default: the highest key in tracks_by_frame).
    benchmark: 'MOT17' or 'MOT20' preprocessing rules (default: inferred from
        gt_path).

    Returns a dict with MOTA, IDF1, HOTA, DetA, AssA (fractions) and the IDSW,
    FP, FN counts, plus the benchmark whose rules were applied.
    """
    benchmark = benchmark or infer_benchmark(gt_path)
    if benchmark not in BENCHMARKS:
        raise ValueError(f"Unknown benchmark {benchmark!r}; choose from {BENCHMARKS}")
    if num_frames is None:
        num_frames = max(tracks_by_frame, default=0)

    with tempfile.TemporaryDirectory() as tmp:
        gt_file, tracks_file = Path(tmp) / "gt.txt", Path(tmp) / "tracks.txt"
        if _write_gt_slice(gt_path, num_frames, benchmark, gt_file) == 0:
            raise ValueError(f"No ground truth in frames 1..{num_frames} of {gt_path}")
        _write_tracks(tracks_by_frame, tracks_file)
        result = evaluate_mot_sequence(
            gt_file, tracks_file, metrics=["CLEAR", "HOTA", "Identity"],
            threshold=iou_threshold,
        )

    return {
        "MOTA": float(result.CLEAR.MOTA),
        "IDF1": float(result.Identity.IDF1),
        "HOTA": float(result.HOTA.HOTA),
        "DetA": float(result.HOTA.DetA),
        "AssA": float(result.HOTA.AssA),
        "IDSW": int(result.CLEAR.IDSW),
        "FP": int(result.CLEAR.CLR_FP),
        "FN": int(result.CLEAR.CLR_FN),
        "benchmark": benchmark,
    }
