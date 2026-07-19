import numpy as np
import motmetrics as mm


def load_mot_gt(gt_path):
    """Parse a MOTChallenge gt.txt into {frame: (ids, xywh boxes)}.

    Keeps only entries evaluated by the benchmark: conf == 1 and class == 1
    (pedestrian). Coordinates stay in the file's 1-based pixel convention.
    """
    per_frame = {}
    with open(gt_path) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 8:
                continue
            frame, tid = int(parts[0]), int(parts[1])
            x, y, w, h = (float(v) for v in parts[2:6])
            conf, cls = int(float(parts[6])), int(float(parts[7]))
            if conf != 1 or cls != 1:
                continue
            per_frame.setdefault(frame, []).append((tid, x, y, w, h))
    return {
        frame: (
            np.array([r[0] for r in rows], dtype=int),
            np.array([r[1:] for r in rows], dtype=float),
        )
        for frame, rows in per_frame.items()
    }


def compute_mot_metrics(gt_path, tracks_by_frame, iou_max=0.5):
    """Real MOTA and IDF1 for tracker output against MOTChallenge ground truth.

    tracks_by_frame: {frame (1-based): [(track_id, (x1, y1, x2, y2)), ...]}

    Only frames present in tracks_by_frame enter the accumulator, so a clip
    that is a prefix of the full sequence scores correctly against the full
    gt.txt as well as against a sliced one.
    """
    gt = load_mot_gt(gt_path)
    if not gt:
        raise ValueError(f"No evaluated GT entries parsed from: {gt_path}")

    acc = mm.MOTAccumulator(auto_id=False)
    empty = (np.empty(0, dtype=int), np.empty((0, 4)))
    for frame, tracks in sorted(tracks_by_frame.items()):
        gt_ids, gt_boxes = gt.get(frame, empty)
        hyp_ids = [tid for tid, _ in tracks]
        # tracker ltrb (0-based) -> MOT xywh (1-based)
        hyp_boxes = np.array(
            [[b[0] + 1, b[1] + 1, b[2] - b[0], b[3] - b[1]] for _, b in tracks],
            dtype=float,
        ).reshape(-1, 4)
        dist = mm.distances.iou_matrix(gt_boxes, hyp_boxes, max_iou=iou_max)
        acc.update(gt_ids.tolist(), hyp_ids, dist, frameid=frame)

    summary = mm.metrics.create().compute(acc, metrics=["mota", "idf1"], name="eval")
    return float(summary.loc["eval", "mota"]), float(summary.loc["eval", "idf1"])
