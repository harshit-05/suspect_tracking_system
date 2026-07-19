# utils/draw_utils.py

import cv2

# --- color cont ---
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)

def draw_tracks(frame, tracks, suspect_id=None):
    for tid, bbox in tracks:
        x1, y1, x2, y2 = map(int, bbox)
	#suspect
        if tid == suspect_id:
            color = RED
            thickness = 3
            label = f"SUSPECT ID: {tid}"
            font_scale = 0.7
	#regular person
        else:
            color = GREEN
            thickness = 2
            label = f"ID: {tid}"
            font_scale = 0.6
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        (label_width, label_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        cv2.rectangle(frame, (x1, y1 - label_height -baseline), (x1 + label_width, y1), color, -1)
#	cv2.putText(frame, f"ID {tid}", (x1, y1 - 10),
#                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.putText(frame, label, (x1, y1 - baseline), cv2.FONT_HERSHEY_SIMPLEX, font_scale, WHITE, thickness)
    return frame

def draw_metrics(frame, mota, idf1, fps):
    text = f"MOTA: {mota:.3f}  IDF1: {idf1:.3f}  FPS: {fps:.2f}"
    cv2.putText(frame, text, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)
    return frame
