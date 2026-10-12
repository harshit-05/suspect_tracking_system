import os

import cv2
import time
import torch
from detectors.yolo_detectors import YOLODetector
from tracking import make_tracker
from evaluation.mot_metrics import compute_mot_metrics, infer_benchmark


def evaluate_pipeline(
    config,
    device=None,
    video_path="sample_videos/mot20-05sample.mp4",
    gt_path="datasets/MOT20/train/MOT20-05/gt/gt.txt",
    tracker="deepsort",
    embedder="mobilenet",
    benchmark=None,
):
    """(MOTA, IDF1, FPS) — the optimizers' objective vector (FR-OPT-1).
    evaluate_pipeline_metrics() returns every metric, HOTA included."""
    metrics = evaluate_pipeline_metrics(
        config, device=device, video_path=video_path, gt_path=gt_path,
        tracker=tracker, embedder=embedder, benchmark=benchmark,
    )
    return metrics["MOTA"], metrics["IDF1"], metrics["FPS"]


def evaluate_pipeline_metrics(
    config,
    device=None,
    video_path="sample_videos/mot20-05sample.mp4",
    gt_path="datasets/MOT20/train/MOT20-05/gt/gt.txt",
    tracker="deepsort",
    embedder="mobilenet",
    benchmark=None,
):
    """Run the pipeline on a video and score it with the official MOTChallenge
    rules. Returns a dict: MOTA, IDF1, HOTA, DetA, AssA, IDSW, FP, FN,
    benchmark, FPS, frames — the precursor of Phase 2's EvalResult (FR-EVAL-4).
    benchmark ('MOT17'/'MOT20') is inferred from gt_path when not given."""
    if device is None:  # device stays config-driven; auto-detect is the default
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if not os.path.exists(gt_path):
        raise FileNotFoundError(
            f"Ground-truth file not found: {gt_path} — MOT20 labels come from the "
            "TrackEval data bundle (omnomnom.vision.rwth-aachen.de/data/TrackEval/"
            "data.zip); motchallenge.net is gone (HTTP 410)"
        )
    # Fail before any model loads, not after the whole video has run
    benchmark = benchmark or infer_benchmark(gt_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    detector = YOLODetector(
        model_name="yolov8l.pt",
        img_size=int(config["img_size"]),
        conf_thresh=config["conf_thresh"],
        device=device,  # ✅ GPU-compatible
    )

    tracker_obj = make_tracker(
        tracker,
        conf_thresh=config["conf_thresh"],
        img_size=int(config["img_size"]),
        iou_thresh=config["iou_thresh"],
        skip_interval=int(config.get("skip_interval", 1)),
        appearance_weight=config.get("appearance_weight", 0.6),
        device=device,  # ✅ GPU-compatible
        embedder=embedder,
    )

    frame_count = 0
    total_time = 0.0
    tracks_by_frame = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        start = time.time()
        detections = detector.detect(frame)
        formatted_dets = [[*d[:4], d[4]] for d in detections if d[5] == 0]
        tracks = tracker_obj.update(formatted_dets, frame)
        end = time.time()

        total_time += end - start
        frame_count += 1
        tracks_by_frame[frame_count] = tracks

    cap.release()

    if frame_count == 0:
        raise RuntimeError(f"No frames read from video: {video_path}")

    avg_fps = frame_count / total_time
    metrics = compute_mot_metrics(
        gt_path, tracks_by_frame, num_frames=frame_count, benchmark=benchmark
    )
    metrics.update(FPS=round(avg_fps, 3), frames=frame_count)
    return metrics
