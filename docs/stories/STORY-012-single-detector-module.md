---
id: STORY-012
title: One detector module + demo-file hygiene
phase: 1
priority: P0
srs_refs: [H1, FR-DET-1, FR-DET-2 (partial), NFR-MNT-3 (partial), L1 (partial)]
status: review   # implemented 2026-10-12: detectors/yolo.py (no defaults), 3 copies deleted; dead code removed, AST-proven behavior-neutral; smoke numbers unchanged
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

- [x] Exactly one detector module remains: `detectors/yolo.py` (the Phase-2 target
      name), exposing `YOLODetector` with **no default model name** — callers must
      pass it explicitly, killing silent default divergence (FR-DET-2 spirit).
- [x] `main.py` and `evaluation/evaluation.py` import from it; `detectors.py`,
      `yolo_detector.py`, `yolo_detectors.py` deleted via `git rm`.
- [x] Grep-verified: no import of the deleted modules anywhere.
- [x] `main.py` dead commented blocks removed; `draw_utils.py` tabs → spaces, typo
      fixed. No behavior change in either.
- [x] Contract test + smoke test still pass.

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

## Deviation from plan

- **`img_size` and `conf_thresh` are required too, not just `model_name`.** Confidence
  was the default that had actually drifted (0.5 vs 0.3), so leaving it would have kept
  half of H1. Both callers already passed all three by keyword, so behaviour is
  unchanged.
- **The deletions aren't staged by the agent.** "Deleted via `git rm`" predates the rule
  that the operator runs every state-changing git command (ADR-016). The files are gone
  from disk, and the hand-over recipe stages the deletions.
- **Three cleanups beyond the list, all in the same files:** a commented-out `putText`
  call in `draw_utils.py` (it held a tab), the "Gloabal" comment typo in `main.py`, and
  a stale comment about what `update()` used to return.
- **No behaviour change, proven:** for both files, the old syntax tree (minus the bare
  string statements) equals the new one; for `main.py`, the import rename is the only
  other change. The smoke numbers are unchanged (MOTA 0.0020, IDF1 0.0059, HOTA 0.0313),
  and `main.py` ran end to end on the fixture, writing 50 frames that reopen.

## Discovered

- **`detect()` truncates box coordinates to integers** (`map(int, box.xyxy[0])`),
  throwing away sub-pixel precision that every IoU — and so every metric — then uses.
  SRS §6.4's `Detections` contract wants float32; that's Phase 2's typed contract.
- **The model name is still written twice** — `"yolov8l.pt"` in `main.py` and in
  `evaluation/evaluation.py`. The two now agree, but neither comes from config
  (FR-DET-2 in full: Phase 2's Pydantic config).
- `detect()` filters by confidence a second time after `predict(conf=…)` has already
  done so — redundant but harmless.
- Person-class filtering still happens at each call site, not in the detector
  (FR-DET-3, already listed as out of scope).
