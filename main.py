# main.py
import os
import cv2
import time
from detectors.yolo_detector import YOLODetector
import numpy as np

# from trackers.deepsort_wrapper import TrackByDetection
from trackers.bytetrack_wrapper import TrackByDetection
from utils.draw_utils import draw_tracks, draw_metrics

# --- Gloabal variable  to store suspect's id and last frame's tracks
suspect_id = None
g_last_tracks = []


def select_suspect_callback(event, x, y, flags, param):
    """mouse callback fn to select or deselect a suspect"""
    global suspect_id
    # Check for left mouse button click
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_on_person = False
        # Iterate over the tracks from the last frame
        for tid, bbox in g_last_tracks:
            #            bbox = track.to_ltrb() # [x1, y1, x2, y2]
            #            track_id = track.track_id
            # Check if the click was inside this track's bounding box
            if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
                if suspect_id == tid:
                    # If clicking the same suspect again, deselect them
                    suspect_id = None
                    print(f"[INFO] Suspect ID:{tid} deselected.")
                else:
                    # Select a new suspect
                    suspect_id = tid
                    print(f"[INFO] SUSPECT SELECTED - ID: {suspect_id}")
                clicked_on_person = True
                break
        # If the background was clicked, deselect any active suspect
        if not clicked_on_person:
            suspect_id = None
            print("[INFO] Suspect deselected.")


# --- Paths ---
model_name = "yolov8l.pt"
input_path = os.path.join("sample_videos", "mot20-05sample.mp4")
output_path = os.path.join("results", "output.mp4")


# --- Config ---
conf_thresh = 0.3
img_size = 640
iou_thresh = 0.5
skip_interval = 1

# --- Init Detector + Tracker ---
detector = YOLODetector(
    model_name=model_name, img_size=img_size, conf_thresh=conf_thresh
)
tracker = TrackByDetection(conf_thresh, img_size, iou_thresh, skip_interval)

# --- Init Video Capture ---
cap = cv2.VideoCapture(input_path)
if not cap.isOpened():
    raise IOError(f"Cannot open video: {input_path}")

fps_input = cap.get(cv2.CAP_PROP_FPS) or 30
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# --- Init Video Writer ---
out = cv2.VideoWriter(
    output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps_input, (width, height)
)
if not out.isOpened():
    raise IOError(f"Cannot open video writer: {output_path}")

# --- Setting up window and Mouse Callback
window_name = "Live Tracking"
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, select_suspect_callback)
print("\n[INFO] Click on a person's box to mark them as a suspect.")

# --- Tracking Loop ---
frame_count = 0
total_time = 0

print("[INFO] Starting tracking... Press 'q' to quit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        start = time.time()

        detections = detector.detect(frame)
        # formatted_dets = [[*d[:4], d[4]] for d in detections if d[5] == 0]
        formatted_dets = np.array(
            [d[:5] for d in detections if d[5] == 0], dtype=np.float32
        )
        """
        formatted_dets = [
            ([d[0], d[1], d[2] - d[0], d[3] - d[1]], d[4], "person")
            for d in detections
            if d[5] == 0
        ]
        """
        """
        formatted_dets = []
        for d in detections:
            if d[5] == 0:
                x1, y1, x2, y2 = d[:4]
                w, h = x2 - x1, y2 - y1
                formatted_dets.append([[x1, y1, w, h], d[4]])
        """
        # tracker.update() used to return  list of track  objects
        tracks = tracker.update(formatted_dets, frame)
        end = time.time()
        """
        processed_tracks = []
        for t in track_objects:
            #t.to_ltrb() gets the bounding box in coordinate format
            processed_tracks.append((t.track_id, t.to_ltrv()))
        """
        # --- Updating global tracks for the callback
        g_last_tracks = tracks
        frame_count += 1
        total_time += end - start

        # --- Draw + Show (honest live values only — FR-DEMO-5) ---
        frame = draw_tracks(frame, tracks, suspect_id)
        fps = frame_count / total_time if total_time > 0 else 0
        frame = draw_metrics(frame, fps, len(tracks))

        out.write(frame)
        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    # --- Cleanup (runs on every exit path, including Ctrl-C) ---
    cap.release()
    out.release()
    cv2.destroyAllWindows()
print(f"[✓] Tracking complete. Output saved to: {output_path}")
print(f"[INFO] Average FPS: {frame_count / total_time:.2f}")
print(f"[INFO] Total frames processed: {frame_count}")
print(f"[INFO] Total time taken: {total_time:.2f} seconds")
print("[INFO] Done.")
