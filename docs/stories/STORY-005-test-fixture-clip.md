---
id: STORY-005
title: Create tiny test fixture clip + first smoke test
phase: 0
priority: P0
srs_refs: [TST-1, NFR-PERF (verification-cost rule in WORKFLOW.md)]
status: todo
depends_on: [STORY-003]
---

## Context

The only video in the repo is the full 213 MB `sample_videos/mot20-05sample.mp4`.
Running any pipeline verification against it with YOLOv8-l on CPU takes hours — which
means no story can have a fast, honest runtime check, and the C2-class bug ("evaluation
silently ran on zero frames") stays cheap to reintroduce.

This story creates a **tiny fixture clip** (~50 frames, a few MB) and the first real
smoke test against it. Every later story's verification uses this fixture instead of
the full sequence, per the ~2-minute verification-cost rule in `docs/WORKFLOW.md`.

## Acceptance Criteria

- [ ] `tests/data/tiny_clip.mp4` exists: first ~50 frames of the MOT20-05 sample,
      same resolution, valid/reopenable, **< 10 MB**.
- [ ] `tests/smoke_test.py` runs `evaluate_pipeline` on the fixture with a cheap config
      (`img_size: 320`, `yolov8m.pt` or smaller if the operator agrees, CPU) and asserts:
      `frames_processed > 0` equivalent (no exception), `fps > 0.5`, metrics within
      [0, 1.2]. Plain script or pytest — pytest preferred but don't add test
      infrastructure beyond what's needed.
- [ ] Smoke test completes in **≤ ~2 minutes** on this machine (CPU). If YOLOv8-l/m is
      too slow even on 50 frames at 320px, reduce frame count or ask the operator about
      using `yolov8n.pt` for fixtures.
- [ ] Fixture is committed (small enough for plain git; do NOT route it through LFS —
      check `.gitattributes` `*.mp4` rule and add an exception if needed).
- [ ] Note: metrics are still the mock formula until Phase 1 (FR-EVAL-1) — the smoke
      test asserts the pipeline *runs on real frames*, not that metrics are meaningful.

## Out of Scope

- Real MOT metrics, ground-truth fixtures (Phase 1).
- CI wiring (Phase 2, DEV-1) — the test must merely be runnable locally.

## Suggested Approach

Prefer ffmpeg if installed (`ffmpeg -i sample_videos/mot20-05sample.mp4 -frames:v 50 -c:v libx264 -crf 28 tests/data/tiny_clip.mp4`);
otherwise a 10-line cv2 read/write loop in the venv. Mind the `.gitattributes` LFS rule
for `*.mp4`: add `tests/data/*.mp4 -filter -diff -merge text=auto` style exception or
an explicit unset so the fixture lands in plain git.

## Verification

```bash
ls -la tests/data/tiny_clip.mp4          # exists, < 10 MB
time .venv/bin/python tests/smoke_test.py   # passes, wall time ≤ ~2 min
git check-attr filter tests/data/tiny_clip.mp4   # NOT lfs
```
