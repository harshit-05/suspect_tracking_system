"""Detector recall per sequence and image size (STORY-014, ADR-012).

Before tuning a tracker on a sequence, check the detector can see its people:
with recall near zero (MOT20-05 gives 1-4 %), MOTA and IDF1 have no dynamic
range and an optimizer just climbs noise. For a few frames per MOTChallenge
sequence, this matches person detections to the scored ground truth
(conf != 0, pedestrian) at IoU >= 0.5 and reports recall and precision.

    .venv/bin/python -I scripts/detector_recall.py \\
        --seq-dir datasets/MOT17/mot17/train/MOT17-04-FRCNN [--seq-dir ...] \\
        [--sizes 320 640 960] [--frames 3] [--conf 0.3] [--model yolov8l.pt]

Run with -I: the sequences are downloaded data.
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from detectors.yolo import YOLODetector  # noqa: E402

IOU_MATCH = 0.5
PERSON = 0  # COCO class id the pipeline keeps


def scored_gt(seq_dir):
    """{frame: (N, 4) xyxy array} of the rows MOTChallenge scores."""
    boxes = {}
    for line in (seq_dir / "gt" / "gt.txt").read_text().splitlines():
        f, _, x, y, w, h, conf, cls = line.split(",")[:8]
        if int(float(conf)) != 0 and int(float(cls)) == 1:
            x, y = float(x) - 1, float(y) - 1  # MOT files are 1-based
            boxes.setdefault(int(f), []).append([x, y, x + float(w), y + float(h)])
    return {f: np.array(b) for f, b in boxes.items()}


def iou_matrix(a, b):
    tl = np.maximum(a[:, None, :2], b[None, :, :2])
    br = np.minimum(a[:, None, 2:], b[None, :, 2:])
    inter = np.prod(np.clip(br - tl, 0, None), axis=2)
    area = lambda r: (r[:, 2] - r[:, 0]) * (r[:, 3] - r[:, 1])  # noqa: E731
    return inter / (area(a)[:, None] + area(b)[None, :] - inter)


def matched(gt, det):
    if len(gt) == 0 or len(det) == 0:
        return 0
    iou = iou_matrix(gt, det)
    rows, cols = linear_sum_assignment(-iou)
    return int((iou[rows, cols] >= IOU_MATCH).sum())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seq-dir", action="append", required=True, type=Path)
    ap.add_argument("--sizes", nargs="+", type=int, default=[320, 640, 960])
    ap.add_argument("--frames", type=int, default=3, help="evenly spaced frames per sequence")
    ap.add_argument("--conf", type=float, default=0.3)
    ap.add_argument("--model", default="yolov8l.pt")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    detectors = {s: YOLODetector(model_name=args.model, img_size=s, conf_thresh=args.conf,
                                 device=args.device) for s in args.sizes}
    print(f"model {args.model}, conf {args.conf}, IoU >= {IOU_MATCH}, "
          f"{args.frames} frames/sequence\n")
    print(f"{'sequence':18} {'GT/frame':>8}  " + "  ".join(f"{f'recall@{s}':>10} {'prec':>5}"
                                                         for s in args.sizes))
    for seq_dir in args.seq_dir:
        gt = scored_gt(seq_dir)
        frames = np.linspace(min(gt), max(gt), args.frames).round().astype(int)
        hits = {s: [0, 0] for s in args.sizes}  # matched, detections
        n_gt = 0
        for f in frames:
            image = cv2.imread(str(seq_dir / "img1" / f"{f:06d}.jpg"))
            boxes = gt.get(int(f), np.empty((0, 4)))
            n_gt += len(boxes)
            for s, det in detectors.items():
                found = np.array([d[:4] for d in det.detect(image) if d[5] == PERSON]).reshape(-1, 4)
                hits[s][0] += matched(boxes, found)
                hits[s][1] += len(found)
        cells = "  ".join(f"{m / max(n_gt, 1):10.1%} {m / max(d, 1):5.0%}"
                          for m, d in hits.values())
        print(f"{seq_dir.name:18} {n_gt / len(frames):8.0f}  {cells}")


if __name__ == "__main__":
    main()
