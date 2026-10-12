from ultralytics import YOLO
import torch


class YOLODetector:
    """The project's single detector (FR-DET-1, audit H1).

    Model, image size and confidence threshold have no defaults: the three
    copies this module replaces had drifted to different ones (yolov8m at 0.5
    vs yolov8l at 0.3), and a default is where that drift hides (FR-DET-2).
    device=None auto-detects (ADR-013).
    """

    def __init__(self, *, model_name, img_size, conf_thresh, device=None):
        self.model = YOLO(model_name)
        self.img_size = img_size
        self.conf_thresh = conf_thresh
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def detect(self, frame):
        results = self.model.predict(
            source=frame,
            imgsz=self.img_size,
            conf=self.conf_thresh,
            device=self.device,
            verbose=False,
        )

        detections = []
        for result in results:
            for box in result.boxes:
                if box.conf.item() >= self.conf_thresh:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf)
                    cls = int(box.cls)
                    detections.append([x1, y1, x2, y2, conf, cls])
        return detections
