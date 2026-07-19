# Tracker contract test (STORY-007, seeds SRS TST-4): both adapters must
# consume the same detections format — rows of [x1, y1, x2, y2, conf] — and
# return [(track_id, [x1, y1, x2, y2]), ...]. Includes the regression check
# for the xyxy/ltwh confusion that corrupted every DeepSORT box (STORY-006).

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tracking import make_tracker  # noqa: E402

FRAME = np.full((480, 640, 3), 127, dtype=np.uint8)
DET = [50.0, 80.0, 150.0, 300.0, 0.9]  # one clear synthetic person-sized box
TRACKER_NAMES = ("bytetrack", "deepsort")


def _make(name):
    return make_tracker(
        name, conf_thresh=0.3, img_size=640, iou_thresh=0.5,
        skip_interval=1, device="cpu",
    )


def _iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


def test_empty_input():
    for name in TRACKER_NAMES:
        trk = _make(name)
        for dets in ([], np.zeros((0, 5), dtype=np.float32)):
            result = trk.update(dets, FRAME)
            assert result == [], f"{name}: empty input must yield [], got {result}"
        print(f"contract OK [{name}]: empty input (list and array) -> []")


def test_confirmed_track_matches_its_detection():
    for name in TRACKER_NAMES:
        trk = _make(name)
        final = []
        for _ in range(6):  # enough frames to pass both confirmation windows
            final = trk.update([DET], FRAME)
        assert len(final) == 1, f"{name}: expected 1 confirmed track, got {final}"
        tid, box = final[0]
        assert len(box) == 4 and all(np.isfinite(box)), f"{name}: bad box {box}"
        iou = _iou(box, DET[:4])
        assert iou > 0.5, (
            f"{name}: track box {box} does not match its own input detection "
            f"{DET[:4]} (IoU={iou:.2f}) — box-format bug?"
        )
        print(f"contract OK [{name}]: confirmed track id={tid}, IoU vs input={iou:.2f}")


if __name__ == "__main__":
    test_empty_input()
    test_confirmed_track_matches_its_detection()
