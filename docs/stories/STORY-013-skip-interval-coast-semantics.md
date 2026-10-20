---
id: STORY-013
title: skip_interval skips detection, not tracks (coast semantics)
phase: 1
priority: P1
srs_refs: [M5, FR-TRK-5]
status: todo
depends_on: [STORY-007]
---

## Context

Both tracker wrappers `return []` on skipped frames, so every skipped frame records
zero tracks and every GT box on it becomes a miss — `skip_interval > 1` tanks MOTA
**by construction** while saving little (the tracker update is cheap; detection is
the expensive stage, and it still runs). Audit M5.

Interim mitigation already applied (operator review, 2026-07-20): `skip_interval`
was removed from `optimization/config.yaml`'s search space and defaulted to 1, so
HPO no longer explores self-sabotage. This story implements the real semantics and
restores the parameter.

## Acceptance Criteria

- [ ] Skipping moves out of the wrappers into the pipeline loop: on skipped frames
      the **detector** is not run; the tracker still advances and reports its
      predicted/coasting tracks (DeepSORT: Kalman predict; ByteTrack: update with
      empty detections and keep unexpired tracks reported).
- [ ] Test: on the **MOT17-04 fixture** (`tests/data/MOT17-04-tiny.*`, STORY-014 —
      the MOT20 fixture's MOTA has no range to degrade, ADR-012) with
      `skip_interval=2`, every frame still has tracks
      once established (no empty-track frames after warm-up), and MOTA degrades
      gracefully vs `skip_interval=1` instead of collapsing.
- [ ] `skip_interval` restored to the search space (as an integer range) with the
      config.yaml comment removed.
- [ ] Measured: eval wall-time at skip=2 is genuinely lower than skip=1 (that's the
      entire point of the parameter — record both numbers in the report).

## Out of Scope

- The full Pipeline object (Phase 2, FR-DEMO-1) — this stays within the current
  evaluate_pipeline loop + wrapper API (an `advance(frame)` / coast method on the
  wrappers is acceptable).

## Verification

```bash
.venv/bin/python tests/skip_interval_test.py   # written in this story, fixture-based
.venv/bin/python -W ignore tests/smoke_test.py # regression
```
