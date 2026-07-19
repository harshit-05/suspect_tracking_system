---
id: STORY-001
title: Fix evaluation entry point — real video path + fail-fast guards
phase: 0
priority: P0
srs_refs: [C2, FR-EVAL-2, NFR-REL-1, TST-1]
status: done   # implemented 2026-07-19 by the dispatched STORY-001 agent session; verified by inspection
---

## Resolution — implemented as dispatched

Implemented on 2026-07-19 by the STORY-001 agent session, per this story's Suggested
Approach. (A same-day cross-check reported it as "pre-implemented drift" — in fact the
reviewer was seeing this session's fresh, uncommitted edits. The story was accurate at
dispatch.) The changes are uncommitted until STORY-000 commits the working tree:

- `evaluation/evaluation.py:15` — `video_path` is a parameter defaulting to the real
  file `sample_videos/mot20-05sample.mp4`.
- `evaluation/evaluation.py:17-18` — `cap.isOpened()` guard raises `FileNotFoundError`
  with the path in the message.
- `evaluation/evaluation.py:57-58` — `frame_count == 0` guard raises `RuntimeError`;
  the `1e-3` sentinel is gone.
- All three optimizers (`qpso_optimizer.py:40`, `nsga_optimizer.py:30`,
  `mopso_optimizer.py:37`) accept and forward `video_path`; `batch_runner.py:14`
  defines it and passes it at every call site (lines 110/119/124/136). No `NameError`
  gaps found.

Every acceptance criterion below is satisfied by inspection. Runtime verification was
**not** possible (no Python environment exists yet — see STORY-003) and is deferred to
STORY-005's fixture-based smoke test.

## Original Acceptance Criteria (all met)

- [x] `evaluate_pipeline` accepts `video_path` as a parameter pointing at a real file.
- [x] All call sites pass or forward the real path.
- [x] `isOpened()` failure raises with the path in the message.
- [x] `frame_count == 0` raises before FPS computation; sentinel removed.
- [x] Error style matches `main.py`'s existing `cap.isOpened()` pattern.

## Lesson captured

Runtime verification was blocked because the story's verification command assumed an
environment (none exists — STORY-003) and would have run the full 213 MB clip on CPU
(hours — hence the WORKFLOW.md verification-cost rule and STORY-005's fixture). The
workflow also now requires re-validating every story against HEAD before implementing
(`docs/WORKFLOW.md`, Stage C Rule 0) — several other Phase-0 stories *had* genuinely
drifted; reviewers must also account for in-flight session work before calling
something pre-existing drift.
