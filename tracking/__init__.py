# tracking/ — local tracker adapters. (Renamed from trackers/ in STORY-007:
# the old name shadowed the pip `trackers` package the ByteTrack adapter uses.)

from tracking.bytetrack_wrapper import TrackByDetection as ByteTrackWrapper
from tracking.deepsort_wrapper import TrackByDetection as DeepSortWrapper

TRACKERS = {"bytetrack": ByteTrackWrapper, "deepsort": DeepSortWrapper}


def make_tracker(name, **kwargs):
    """Single construction point for every driver (demo, evaluator) — FR-TRK-3."""
    try:
        cls = TRACKERS[name]
    except KeyError:
        raise ValueError(
            f"Unknown tracker '{name}' — choose from {sorted(TRACKERS)}"
        ) from None
    return cls(**kwargs)
