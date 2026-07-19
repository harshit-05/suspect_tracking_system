# trackers/bytetrack_wrapper.py

from yolox.tracker.byte_tracker import BYTETracker
from yolox.tracking_utils.timer import Timer

class TrackByDetection:
    def __init__(self, conf_thresh=0.5, img_size=640, iou_thresh=0.5, skip_interval=1):
        self.conf_thresh = conf_thresh
        self.img_size = img_size
        self.iou_thresh = iou_thresh
        self.skip_interval = skip_interval
        self.frame_id = 0
        self.timer = Timer()

        self.tracker = BYTETracker(
            track_thresh=conf_thresh,
            match_thresh=iou_thresh,
            frame_rate=30  # default FPS
        )

    def update(self, detections, frame):
        self.frame_id += 1
        if self.frame_id % self.skip_interval != 0:
            return []

        self.timer.tic()
        online_targets = self.tracker.update(detections, frame)
        self.timer.toc()

        tracks = []
        for target in online_targets:
            tlwh = target.tlwh
            tid = target.track_id
            bbox = [int(tlwh[0]), int(tlwh[1]), int(tlwh[0] + tlwh[2]), int(tlwh[1] + tlwh[3])]
            tracks.append((tid, bbox))
        return tracks

    def get_fps(self):
        return self.timer.average_time
