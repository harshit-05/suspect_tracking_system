# tracking/bytetrack_wrapper.py

import numpy as np
import supervision as sv
from trackers import ByteTrackTracker


class TrackByDetection:
    """ByteTrack adapter over the maintained roboflow `trackers` package
    (successor of supervision's deprecated ByteTrack — see requirements.txt).

    Interface-compatible with the DeepSORT wrapper:
    update(dets, frame) -> [(track_id, [x1, y1, x2, y2]), ...] where dets is a
    list/array of rows [x1, y1, x2, y2, conf].

    Config mapping: conf_thresh -> track_activation_threshold and
    high_conf_det_threshold (classic ByteTrack uses one det_thresh for both);
    iou_thresh -> minimum_iou_threshold (association gate). ByteTrack has no
    appearance embedder, so `appearance_weight` / `embedder` / `device` are
    accepted and ignored to keep both trackers constructible from the same
    config (per-tracker validation arrives with the Phase-2 config models).
    """

    def __init__(
        self,
        conf_thresh=0.5,
        img_size=640,
        iou_thresh=0.5,
        skip_interval=1,
        **_ignored,
    ):
        self.conf_thresh = conf_thresh
        self.img_size = img_size
        self.iou_thresh = iou_thresh
        self.skip_interval = skip_interval
        self.frame_id = 0

        self.tracker = ByteTrackTracker(
            track_activation_threshold=conf_thresh,
            high_conf_det_threshold=conf_thresh,
            minimum_iou_threshold=iou_thresh,
            lost_track_buffer=30,
            frame_rate=25,
            minimum_consecutive_frames=2,
        )

    def update(self, detections, frame):
        self.frame_id += 1
        if self.frame_id % self.skip_interval != 0:
            return []

        arr = np.asarray(detections, dtype=np.float32).reshape(-1, 5)
        dets = sv.Detections(
            xyxy=arr[:, :4],
            confidence=arr[:, 4],
            class_id=np.zeros(len(arr), dtype=int),
        )
        tracked = self.tracker.update(dets, frame=frame)

        output = []
        for (x1, y1, x2, y2), tid in zip(tracked.xyxy, tracked.tracker_id):
            if tid == -1:  # not yet confirmed
                continue
            output.append((int(tid), [int(x1), int(y1), int(x2), int(y2)]))
        return output
