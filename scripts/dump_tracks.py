"""Save the tracker output a pipeline run scored, as a MOT file (STORY-014 follow-up).

scripts/trackeval_parity.py checks our metrics against TrackEval on synthetic
hypotheses and on real tracker output. The real output has to come from an
actual pipeline run; this regenerates it, so those parity cases can be
reproduced rather than trusted. In the project venv:

    .venv/bin/python -W ignore scripts/dump_tracks.py \\
        --video tests/data/MOT17-04-tiny.mp4 --gt tests/data/MOT17-04-tiny_gt.txt \\
        --img-size 320 --out /path/to/tracks_320.txt

then, in the parity venv, pass the file to `scripts/trackeval_parity.py --tracks`.
The defaults are the smoke-test config: conf 0.3, IoU 0.5, DeepSORT + mobilenet.
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import evaluation.evaluation as ev  # noqa: E402
from evaluation.mot_metrics import _write_tracks  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--video", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--img-size", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--conf", type=float, default=0.3)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--tracker", default="deepsort")
    ap.add_argument("--embedder", default="mobilenet")
    ap.add_argument("--device", default=None)
    ap.add_argument("--benchmark", default=None, help="MOT17/MOT20; inferred from --gt if omitted")
    args = ap.parse_args()

    captured = {}
    score = ev.compute_mot_metrics

    def capture(gt_path, tracks_by_frame, **kwargs):
        captured.update(tracks_by_frame)
        return score(gt_path, tracks_by_frame, **kwargs)

    # Dev-tool seam: evaluate_pipeline_metrics scores through the module-level
    # name compute_mot_metrics, so wrapping it hands over exactly the tracks it
    # scored, without a second video loop (NFR-MNT-3).
    ev.compute_mot_metrics = capture
    try:
        config = {"img_size": args.img_size, "conf_thresh": args.conf, "iou_thresh": args.iou}
        m = ev.evaluate_pipeline_metrics(
            config, device=args.device, video_path=args.video, gt_path=args.gt,
            tracker=args.tracker, embedder=args.embedder, benchmark=args.benchmark,
        )
    finally:
        ev.compute_mot_metrics = score

    rows = sum(len(tracks) for tracks in captured.values())
    if rows == 0:
        # TrackEval can't read a file holding only the id -1 placeholder that
        # _write_tracks writes for an empty run; the parity script's "empty"
        # case already covers a run with no tracks.
        print("no tracks to dump: the run produced none", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    _write_tracks(captured, args.out)  # the same writer, and so the same rows, that were scored
    print(f"MOTA={m['MOTA']:.4f} IDF1={m['IDF1']:.4f} HOTA={m['HOTA']:.4f} FPS={m['FPS']:.2f} "
          f"({m['benchmark']} rules, img_size {args.img_size}, {args.tracker})")
    print(f"wrote {rows} rows over {len(captured)} frames -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
