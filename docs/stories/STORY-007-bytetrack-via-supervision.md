---
id: STORY-007
title: ByteTrack via supervision + tracker selection in demo and evaluator
phase: 1
priority: P0
srs_refs: [C4, H2, FR-TRK-1, FR-TRK-2, FR-TRK-3, TST-4 (seed), "H3 (STORY-004 deferred runtime check)"]
status: review   # implemented 2026-07-20: roboflow `trackers` ByteTrack (operator-approved over deprecated sv.ByteTrack); deepsort ltwh fix; local pkg renamed trackers/->tracking/ (shadowed pip pkg); main.py ran end-to-end first time (50 frames)
depends_on: [STORY-003]
---

## Context

`trackers/bytetrack_wrapper.py` imports `yolox` (deliberately not installed — see
requirements.txt) and calls `BYTETracker` with a constructor and `update()` signature
that match no stock YOLOX release (C4): it has **never worked**.

**Addendum (found by STORY-006's first real measurement, 2026-07-19):** the DeepSORT
wrapper has its own format bug — `deepsort_wrapper.py:46-48` passes detections to
`deep_sort_realtime.update_tracks` as **xyxy**, but the library expects
**[left, top, width, height]**. Confirmed empirically: an 87×188 px detection became a
927×1045 px track box. Every DeepSORT track ever produced was geometrically wrong
(real MOTA≈0/IDF1=0 on the fixture). Fix it here (1-line xyxy→ltwh conversion) as part
of the same-`Detections`-type contract this story owns, and cover it in
`tests/tracker_contract_test.py` (a track box must roughly match its input detection). Because of it,
`main.py` cannot even import, which is also why STORY-004's fourcc/cleanup fix could
only be statically verified. Meanwhile the evaluator runs DeepSORT — so the demo and
the evaluation pipeline don't even use the same tracker family (H2).

## Acceptance Criteria

- [ ] `supervision` added to `requirements.txt` (uv-installed, `==` pinned); `yolox`
      exclusion comment updated to point here.
- [ ] `trackers/bytetrack_wrapper.py` rewritten as a thin adapter over
      `supervision.ByteTrack`, exposing the **same interface** as the DeepSORT
      wrapper: constructed from (conf_thresh, img_size, iou_thresh, skip_interval),
      `update(dets, frame) -> [(track_id, [x1, y1, x2, y2]), ...]`, same dets format.
- [ ] A `tracker` parameter (`"bytetrack" | "deepsort"`) selects the wrapper via one
      shared factory used by BOTH `main.py` and `evaluate_pipeline` — no divergent
      construction logic (interim fix for H2; the full single-Pipeline unification is
      Phase 2, FR-DEMO-1).
- [ ] `tests/tracker_contract_test.py`: both wrappers consume the same detections
      fixture — including an **empty** detections array — and return well-formed
      track lists (locks the C4 interface; seeds SRS TST-4).
- [ ] **STORY-004 deferred runtime check:** `main.py` runs end-to-end on the fixture
      clip and the output video reopens with ≥ 1 frame. Allow overriding
      `input_path`/`output_path` via two `os.environ.get(...)` lookups (no CLI
      framework yet — that's Phase 2, FR-CLI-1).

## Out of Scope

- Frame skipping semantics (FR-TRK-5), single `Pipeline` object (Phase 2),
  Detections/Track dataclasses (Phase 2), removing main.py globals (Phase 2).

## Suggested Approach

`supervision.ByteTrack.update_with_detections(sv.Detections)` handles association;
build `sv.Detections(xyxy=..., confidence=..., class_id=...)` from the wrapper's
input and map `tracker_id` back to the `(tid, ltrb)` tuples the drawing code expects.
Pin the `supervision` version in requirements.txt. Keep the DeepSORT wrapper's public
surface untouched.

## Verification

```bash
.venv/bin/python tests/tracker_contract_test.py
INPUT_PATH=tests/data/tiny_clip.mp4 OUTPUT_PATH=/tmp/story007_out.mp4 \
  .venv/bin/timeout 150 .venv/bin/python main.py </dev/null || true
.venv/bin/python -c "
import cv2; cap = cv2.VideoCapture('/tmp/story007_out.mp4')
assert cap.isOpened(); n=0
while cap.read()[0]: n+=1
assert n >= 1, 'output video empty'
print('STORY-004 runtime check OK:', n, 'frames written')"
```

(Display `:1` is available; if the window blocks a headless run, `main.py` may skip
`imshow` when `DISPLAY` is unset — keep any such change to ≤3 lines.)
