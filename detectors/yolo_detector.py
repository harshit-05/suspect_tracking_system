from ultralytics import YOLO
import torch


class YOLODetector:
    def __init__(
        self, model_name="yolov8l.pt", img_size=640, conf_thresh=0.3, device=None
    ):
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
