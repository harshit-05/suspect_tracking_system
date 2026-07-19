# Smoke test (STORY-005, SRS TST-1): proves the evaluation pipeline runs on real
# frames end-to-end. Runs as a plain script (`python tests/smoke_test.py`) and is
# pytest-compatible for when CI lands in Phase 2.
#
# NOTE: MOTA/IDF1 are still the mock formula until Phase 1 (SRS FR-EVAL-1) — the
# [0, 1.2] bounds check only guards against sentinel/garbage values, it does not
# validate tracking quality.

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.evaluation import evaluate_pipeline  # noqa: E402

FIXTURE = str(REPO_ROOT / "tests" / "data" / "tiny_clip.mp4")
CHEAP_CONFIG = {
    "img_size": 320,
    "conf_thresh": 0.3,
    "iou_thresh": 0.5,
    "skip_interval": 1,
}


def test_pipeline_runs_on_real_frames():
    mota, idf1, fps = evaluate_pipeline(CHEAP_CONFIG, device="cpu", video_path=FIXTURE)
    assert fps > 0.5, f"FPS {fps} — pipeline suspiciously slow or zero-frame sentinel"
    assert 0.0 <= mota <= 1.2, f"MOTA {mota} out of sane bounds"
    assert 0.0 <= idf1 <= 1.2, f"IDF1 {idf1} out of sane bounds"
    print(f"smoke OK: MOTA={mota:.3f} IDF1={idf1:.3f} FPS={fps:.2f} (metrics are mock until Phase 1)")


def test_missing_video_raises():
    # STORY-001's deferred runtime check: bad path must fail loudly, never
    # fall through to a zero-frame result.
    try:
        evaluate_pipeline(CHEAP_CONFIG, device="cpu", video_path="tests/data/does_not_exist.mp4")
    except FileNotFoundError as e:
        assert "does_not_exist.mp4" in str(e)
        print("smoke OK: missing video raises FileNotFoundError with path in message")
    else:
        raise AssertionError("evaluate_pipeline did not raise on a nonexistent video")


if __name__ == "__main__":
    test_missing_video_raises()
    test_pipeline_runs_on_real_frames()
