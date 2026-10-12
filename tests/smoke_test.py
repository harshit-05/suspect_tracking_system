# Smoke test (STORY-005/006/010, SRS TST-1): proves the evaluation pipeline runs
# on real frames end-to-end and scores the official MOTChallenge metrics (MOTA,
# IDF1, HOTA via trackers.eval, TrackEval-parity) against the bundled MOT20-05
# ground-truth slice. Runs as a plain script (`python tests/smoke_test.py`) and is
# pytest-compatible for when CI lands in Phase 2.

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import evaluation.evaluation as ev  # noqa: E402

FIXTURE = str(REPO_ROOT / "tests" / "data" / "tiny_clip.mp4")
GT_FIXTURE = str(REPO_ROOT / "tests" / "data" / "tiny_clip_gt.txt")
# The fixture's path names no MOTChallenge sequence, so the rules are explicit
BENCHMARK = "MOT20"
CHEAP_CONFIG = {
    "img_size": 320,
    "conf_thresh": 0.3,
    "iou_thresh": 0.5,
    "skip_interval": 1,
}


def test_pipeline_runs_on_real_frames():
    m = ev.evaluate_pipeline_metrics(
        CHEAP_CONFIG, device="cpu", video_path=FIXTURE, gt_path=GT_FIXTURE,
        benchmark=BENCHMARK,
    )
    assert m["frames"] == 50, f"processed {m['frames']} frames, fixture has 50"
    assert m["FPS"] > 0.5, f"FPS {m['FPS']} — pipeline suspiciously slow or zero-frame sentinel"
    assert -1.0 <= m["MOTA"] <= 1.0, f"MOTA {m['MOTA']} out of valid range"
    assert 0.0 <= m["IDF1"] <= 1.0, f"IDF1 {m['IDF1']} out of valid range"
    assert 0.0 <= m["HOTA"] <= 1.0, f"HOTA {m['HOTA']} out of valid range"
    # Correctness tripwire (2026-07-20 review): IDF1 must be strictly positive.
    # Box-format-level corruption (e.g. the xyxy/ltwh bug) zeroes it exactly,
    # while the legitimate dense-crowd recall floor still yields a small
    # positive value. Bounds alone would pass a totally broken tracker.
    assert m["IDF1"] > 0.0, "IDF1 == 0: no identity ever matched GT — box corruption?"
    print(f"smoke OK: MOTA={m['MOTA']:.4f} IDF1={m['IDF1']:.4f} HOTA={m['HOTA']:.4f} "
          f"FPS={m['FPS']:.2f} ({m['benchmark']} rules)")


def test_evaluate_pipeline_keeps_the_optimizer_contract():
    # The optimizers unpack `mota, idf1, fps = evaluate_pipeline(...)`. Checked
    # model-free: the full-metrics function is stubbed with a canned result.
    canned = {"MOTA": 0.1, "IDF1": 0.2, "HOTA": 0.3, "FPS": 4.5, "frames": 50}
    real = ev.evaluate_pipeline_metrics
    ev.evaluate_pipeline_metrics = lambda *a, **kw: canned
    try:
        assert ev.evaluate_pipeline(CHEAP_CONFIG) == (0.1, 0.2, 4.5)
    finally:
        ev.evaluate_pipeline_metrics = real
    print("smoke OK: evaluate_pipeline still returns (MOTA, IDF1, FPS) for the optimizers")


def test_missing_video_raises():
    # STORY-001's deferred runtime check: bad path must fail loudly, never
    # fall through to a zero-frame result.
    try:
        ev.evaluate_pipeline(CHEAP_CONFIG, device="cpu", benchmark=BENCHMARK,
                             video_path="tests/data/does_not_exist.mp4", gt_path=GT_FIXTURE)
    except FileNotFoundError as e:
        assert "does_not_exist.mp4" in str(e)
        print("smoke OK: missing video raises FileNotFoundError with path in message")
    else:
        raise AssertionError("evaluate_pipeline did not raise on a nonexistent video")


if __name__ == "__main__":
    test_missing_video_raises()
    test_evaluate_pipeline_keeps_the_optimizer_contract()
    test_pipeline_runs_on_real_frames()
