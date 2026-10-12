# Metrics tests (STORY-010, SRS TST-1/TST-3 spirit). Model-free: tracker output is
# built from the fixture ground truth itself, so this runs in seconds and pins
# down each rule of the official MOTChallenge scoring that evaluation/mot_metrics.py
# relies on. scripts/trackeval_parity.py separately checks these numbers against
# TrackEval.

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.mot_metrics import compute_mot_metrics, infer_benchmark  # noqa: E402

GT = REPO_ROOT / "tests" / "data" / "tiny_clip_gt.txt"  # MOT20-05, frames 1-50


def gt_rows():
    for line in GT.read_text().splitlines():
        f, tid, x, y, w, h, conf, cls = line.split(",")[:8]
        yield int(f), int(tid), float(x), float(y), float(w), float(h), int(conf), int(cls)


def as_track(x, y, w, h):
    """MOT xywh (1-based) -> tracker ltrb (0-based), the inverse of mot_metrics."""
    return (x - 1, y - 1, x - 1 + w, y - 1 + h)


def identity_tracks(last_frame=50):
    """The scored GT itself (conf != 0 pedestrians) as tracker output."""
    tracks = {f: [] for f in range(1, last_frame + 1)}
    for f, tid, x, y, w, h, conf, cls in gt_rows():
        if f <= last_frame and conf != 0 and cls == 1:
            tracks[f].append((tid, as_track(x, y, w, h)))
    return tracks


def first_row_of_class(wanted):
    return next(r for r in gt_rows() if r[7] == wanted)


def test_identity_oracle_is_perfect():
    for benchmark in ("MOT17", "MOT20"):
        m = compute_mot_metrics(GT, identity_tracks(), benchmark=benchmark)
        assert (m["MOTA"], m["IDF1"], m["HOTA"]) == (1.0, 1.0, 1.0), m
    print("metrics OK: GT scored against itself = 1.0 MOTA/IDF1/HOTA (MOT17 + MOT20 rules)")


def test_zero_tracks_scores_zero_without_crashing():
    empty = {f: [] for f in range(1, 51)}
    m = compute_mot_metrics(GT, empty, benchmark="MOT20")
    assert (m["MOTA"], m["IDF1"], m["HOTA"], m["FP"]) == (0.0, 0.0, 0.0, 0), m
    print("metrics OK: an all-empty run scores 0/0/0 with no false positives")


def test_box_on_distractor_is_not_a_false_positive():
    # class 7 (static person) is a distractor under both rule sets
    f, _, x, y, w, h, _, _ = first_row_of_class(7)
    tracks = identity_tracks()
    tracks[f].append((99_999, as_track(x, y, w, h)))
    for benchmark in ("MOT17", "MOT20"):
        m = compute_mot_metrics(GT, tracks, benchmark=benchmark)
        assert m["FP"] == 0 and m["MOTA"] == 1.0, (benchmark, m)
    # class 6 (non_mot_vehicle) is a distractor only under MOT20 rules: the
    # relabel in mot_metrics is what makes MOT20 scoring match TrackEval's
    f, _, x, y, w, h, _, _ = first_row_of_class(6)
    tracks = identity_tracks()
    tracks[f].append((99_998, as_track(x, y, w, h)))
    assert compute_mot_metrics(GT, tracks, benchmark="MOT20")["FP"] == 0
    assert compute_mot_metrics(GT, tracks, benchmark="MOT17")["FP"] == 1
    print("metrics OK: distractor boxes ignored (class 7 both rules; class 6 MOT20 only)")


def test_prefix_clip_is_scored_on_its_own_frames():
    # 20 processed frames against the 50-frame GT: if the GT weren't cut to
    # frames 1-20, frames 21-50 would count as misses and MOTA would drop
    m = compute_mot_metrics(GT, identity_tracks(last_frame=20), num_frames=20,
                            benchmark="MOT20")
    assert (m["MOTA"], m["IDF1"], m["HOTA"]) == (1.0, 1.0, 1.0), m
    print("metrics OK: a 20-frame prefix scores only against frames 1-20")


def test_benchmark_inference():
    assert infer_benchmark("datasets/MOT20/train/MOT20-05/gt/gt.txt") == "MOT20"
    assert infer_benchmark("datasets/MOT17/train/MOT17-04-FRCNN/gt/gt.txt") == "MOT17"
    for bad_call in (
        lambda: infer_benchmark(GT),  # the fixture's path names no sequence
        lambda: compute_mot_metrics(GT, identity_tracks(), benchmark="MOT99"),
    ):
        try:
            bad_call()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")
    print("metrics OK: benchmark inferred from the sequence folder; unknown -> ValueError")


if __name__ == "__main__":
    test_identity_oracle_is_perfect()
    test_zero_tracks_scores_zero_without_crashing()
    test_box_on_distractor_is_not_a_false_positive()
    test_prefix_clip_is_scored_on_its_own_frames()
    test_benchmark_inference()
    print("\nall metrics tests passed")
