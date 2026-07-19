---
id: STORY-012
title: One detector module + demo-file hygiene
phase: 1
priority: P0
srs_refs: [H1, FR-DET-1, FR-DET-2 (partial), NFR-MNT-3 (partial), L1 (partial)]
status: todo
depends_on: [STORY-007]
---

## Context

Operator review 2026-07-20 (verified): `detectors/` holds **three** near-identical
modules — `detectors.py` (dead, nothing imports it), `yolo_detector.py` (imported by
`main.py`, default `yolov8l.pt`) and `yolo_detectors.py` (imported by
`evaluation/evaluation.py`, default `yolov8m.pt` — a file that no longer exists on
disk). Two live detector code paths with divergent defaults is audit finding H1, the
exact drift the rebuild is meant to kill. STORY-002's hygiene pass missed these.

Also from the same review, demo-file debt: dead commented-out blocks in `main.py`
(the old `formatted_dets`/`processed_tracks` experiments), and `draw_utils.py`
tab-indented comment lines plus a "color cont" typo.

## Acceptance Criteria

- [ ] Exactly one detector module remains: `detectors/yolo.py` (the Phase-2 target
      name), exposing `YOLODetector` with **no default model name** — callers must
      pass it explicitly, killing silent default divergence (FR-DET-2 spirit).
- [ ] `main.py` and `evaluation/evaluation.py` import from it; `detectors.py`,
      `yolo_detector.py`, `yolo_detectors.py` deleted via `git rm`.
- [ ] Grep-verified: no import of the deleted modules anywhere.
- [ ] `main.py` dead commented blocks removed; `draw_utils.py` tabs → spaces, typo
      fixed. No behavior change in either.
- [ ] Contract test + smoke test still pass.

## Out of Scope

- Class filtering at the detector boundary (FR-DET-3), batching (FR-DET-4),
  Detections dataclass (Phase 2), model caching (FR-OPT-7).

## Suggested Approach

Diff the three modules first (they drifted — check `detect()` return shapes match
before unifying). Base the survivor on whichever the evaluator uses today, since its
output format is what both the wrappers and metrics consume. ~6 small files.

## Verification

```bash
grep -rn "yolo_detector\b\|yolo_detectors\b\|from detectors.detectors" --include="*.py" . ; test $? -eq 1 && echo "OK: one detector"
.venv/bin/python -W ignore tests/tracker_contract_test.py
.venv/bin/python -W ignore tests/smoke_test.py
```
