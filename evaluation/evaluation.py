import os

import cv2
import time
from detectors.yolo_detectors import YOLODetector
from trackers.deepsort_wrapper import TrackByDetection  # if using Deep SORT
from evaluation.mot_metrics import compute_mot_metrics


def evaluate_pipeline(
    config,
    device="cuda",
    video_path="sample_videos/mot20-05sample.mp4",
    gt_path="datasets/MOT20/train/MOT20-05/gt/gt.txt",
):
    if not os.path.exists(gt_path):
        raise FileNotFoundError(
            f"Ground-truth file not found: {gt_path} — MOT20 labels come from "
            "https://motchallenge.net/data/MOT20Labels.zip (mirror: TrackEval "
            "data.zip at omnomnom.vision.rwth-aachen.de)"
        )
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    detector = YOLODetector(
        model_name="yolov8l.pt",
        img_size=int(config["img_size"]),
        conf_thresh=config["conf_thresh"],
        device=device,  # ✅ GPU-compatible
    )

    tracker = TrackByDetection(
        conf_thresh=config["conf_thresh"],
        img_size=int(config["img_size"]),
        iou_thresh=config["iou_thresh"],
        skip_interval=int(config["skip_interval"]),
        appearance_weight=config.get("appearance_weight", 0.6),
        device=device,  # ✅ GPU-compatible
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
        tracks = tracker.update(formatted_dets, frame)
        end = time.time()

        total_time += end - start
        frame_count += 1
        tracks_by_frame[frame_count] = tracks

    cap.release()

    if frame_count == 0:
        raise RuntimeError(f"No frames read from video: {video_path}")

    avg_fps = frame_count / total_time
    mota, idf1 = compute_mot_metrics(gt_path, tracks_by_frame)

    return mota, idf1, round(avg_fps, 3)
