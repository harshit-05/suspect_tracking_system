# Smoke test (STORY-005 + STORY-006, SRS TST-1): proves the evaluation pipeline
# runs on real frames end-to-end and scores REAL MOTA/IDF1 (motmetrics) against
# the bundled MOT20-05 ground-truth slice. Runs as a plain script
# (`python tests/smoke_test.py`) and is pytest-compatible for when CI lands in
# Phase 2.

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.evaluation import evaluate_pipeline  # noqa: E402

FIXTURE = str(REPO_ROOT / "tests" / "data" / "tiny_clip.mp4")
GT_FIXTURE = str(REPO_ROOT / "tests" / "data" / "tiny_clip_gt.txt")
CHEAP_CONFIG = {
    "img_size": 320,
    "conf_thresh": 0.3,
    "iou_thresh": 0.5,
    "skip_interval": 1,
}


def test_pipeline_runs_on_real_frames():
    mota, idf1, fps = evaluate_pipeline(
        CHEAP_CONFIG, device="cpu", video_path=FIXTURE, gt_path=GT_FIXTURE
    )
    assert fps > 0.5, f"FPS {fps} — pipeline suspiciously slow or zero-frame sentinel"
    assert -1.0 <= mota <= 1.0, f"MOTA {mota} out of valid range"
    assert 0.0 <= idf1 <= 1.0, f"IDF1 {idf1} out of valid range"
    print(f"smoke OK: real MOTA={mota:.3f} IDF1={idf1:.3f} FPS={fps:.2f}")


def test_missing_video_raises():
    # STORY-001's deferred runtime check: bad path must fail loudly, never
    # fall through to a zero-frame result.
    try:
        evaluate_pipeline(CHEAP_CONFIG, device="cpu",
                          video_path="tests/data/does_not_exist.mp4", gt_path=GT_FIXTURE)
    except FileNotFoundError as e:
        assert "does_not_exist.mp4" in str(e)
        print("smoke OK: missing video raises FileNotFoundError with path in message")
    else:
        raise AssertionError("evaluate_pipeline did not raise on a nonexistent video")


if __name__ == "__main__":
    test_missing_video_raises()
    test_pipeline_runs_on_real_frames()
