import cv2
import time
from detectors.yolo_detectors import YOLODetector
from trackers.deepsort_wrapper import TrackByDetection  # if using Deep SORT


def compute_mock_metrics(tracks):
    # You should implement true MOTA and IDF1 calculation if ground truth exists
    num_tracks = len(tracks)
    mota = 0.80 + 0.05 * (num_tracks % 5)  # mock value
    idf1 = 0.75 + 0.03 * (num_tracks % 3)  # mock value
    return mota, idf1


def evaluate_pipeline(config, device="cuda", video_path="sample_videos/mot20-05sample.mp4"):
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
    all_tracks = []

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
        all_tracks.extend(tracks)

    cap.release()

    if frame_count == 0:
        raise RuntimeError(f"No frames read from video: {video_path}")

    avg_fps = frame_count / total_time
    mota, idf1 = compute_mock_metrics(all_tracks)

    return mota, idf1, round(avg_fps, 3)
