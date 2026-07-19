---
id: STORY-006
title: Real MOTA/IDF1 via motmetrics — delete the mock formula
phase: 1
priority: P0
srs_refs: [C1, FR-EVAL-1 (partial — HOTA is STORY-010), FR-EVAL-2, ML-1, TST-1]
status: todo
depends_on: [STORY-005]
---

## Context

`evaluation/evaluation.py` still computes `compute_mock_metrics(tracks)` — MOTA/IDF1 as
a modulo function of track count (audit C1, the project's core integrity defect).
`main.py` also imports it and draws the fake numbers on the video overlay.

**Verified 2026-07-19: no MOT ground truth exists on this machine.** The sample video
was generated (on a previous machine) from `MOT20Det/train/MOT20-05/img1` frames in
natsorted order, so video frame N corresponds to dataset frame N. The fixture
`tests/data/tiny_clip.mp4` is frames 1–50 of that video.

## Acceptance Criteria

- [ ] `motmetrics` added to `requirements.txt` (uv-installed, `==` pinned).
- [ ] MOT20 **tracking** labels for MOT20-05 obtained (labels-only zip from
      motchallenge.net is a few MB — do NOT download the 5 GB image set). Full
      `gt.txt` stays out of git (`datasets/` is ignored); a **first-50-frames slice**
      is committed as `tests/data/tiny_clip_gt.txt` (plain git, a few KB).
- [ ] Frame alignment sanity-checked: overlay GT boxes for frame 1 on the fixture's
      first frame and confirm visually (save the overlay PNG for the report).
- [ ] New `evaluation/mot_metrics.py`: builds a `motmetrics` accumulator from
      (gt rows, track outputs) per frame, returns real MOTA and IDF1.
- [ ] `evaluate_pipeline` gains a `gt_path` parameter; when given, it returns real
      metrics; `compute_mock_metrics` is **deleted from the codebase** (grep-verified).
- [ ] `main.py` overlay stops showing MOTA/IDF1 (honest live values only: FPS, track
      count — FR-DEMO-5); it must still import and compile.
- [ ] `tests/smoke_test.py` updated: passes `gt_path=tests/data/tiny_clip_gt.txt`,
      asserts real MOTA ∈ [-1, 1] and IDF1 ∈ [0, 1], and drops its "metrics are mock"
      caveat (supersedes the STORY-005 note).

## Out of Scope

- HOTA / TrackEval (STORY-010). EvalResult/manifest schema (Phase 2, FR-EVAL-4).
- Per-stage FPS breakdown (Phase 2, FR-EVAL-3). Tuning/held-out split (ML-4, later).

## Suggested Approach

Roughly 7 files but every edit is small; still one reviewable unit. Get the labels
first (ask the operator if the motchallenge download needs credentials). Parse gt.txt
per MOTChallenge format (frame,id,x,y,w,h,conf,class,vis — keep conf==1/class∈{1}
pedestrian rows only). Feed `motmetrics.MOTAccumulator` per frame with IoU distances
(`motmetrics.distances.iou_matrix`, max_iou 0.5); compute `mota`, `idf1` via
`mm.metrics.create()`. If motchallenge.net is unreachable, STOP and report — do not
fabricate a GT file.

## Verification

```bash
.venv/bin/python -m pytest tests/smoke_test.py -q 2>/dev/null || .venv/bin/python tests/smoke_test.py
grep -rn "compute_mock_metrics" --include="*.py" . ; test $? -eq 1 && echo "OK: mock gone"
```

Expected: smoke test prints **real** MOTA/IDF1 (will be far below the fake 0.85 —
likely 0.2–0.6 with this untuned config; that drop is the proof), wall ≤ ~2 min.
