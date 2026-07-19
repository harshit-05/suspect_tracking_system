---
id: STORY-004
title: Fix VideoWriter fourcc + open checks in main.py
phase: 0
priority: P0
srs_refs: [H3, "FR-DEMO-3 (partial — full app-class restructure is Phase 2)"]
status: todo
depends_on: [STORY-000]
---

## Context

`main.py:75` constructs the output `VideoWriter` with
`cv2.VideoWriter_fourcc(*"mp0v")` — a typo, digit `0` for letter `4`; correct is
`"mp4v"` (re-verified present at HEAD, 2026-07-19). OpenCV doesn't raise on a bad
fourcc; it warns and produces a broken/empty file, discovered only after a full run.
`out.isOpened()` is never checked, and the loop has no cleanup on interrupt — Ctrl-C
can corrupt the partially-written output.

**Verification constraint:** `main.py` imports `trackers/bytetrack_wrapper.py`, which
imports `yolox` — deliberately not installed (see STORY-003) and API-broken anyway (C4).
So `main.py` **cannot run** until the Phase-1 ByteTrack fix lands. This story's fix is
correct by inspection; verification is **static-only** here, with the runtime check
explicitly deferred.

## Acceptance Criteria

- [ ] Fourcc fixed: `"mp0v"` → `"mp4v"`.
- [ ] `out.isOpened()` checked immediately after construction; raises a clear error
      matching the existing `cap.isOpened()` pattern (main.py:66-67).
- [ ] Tracking loop wrapped in `try:` with `cap.release()`, `out.release()`,
      `cv2.destroyAllWindows()` in a `finally:` so cleanup runs on every exit path
      including `KeyboardInterrupt`. No class restructure — that's Phase 2.
- [ ] A deferred-verification note is added to the Phase-1 ByteTrack story when it's
      sharded: "run `main.py` end-to-end and validate the output video reopens with
      frames (STORY-004 runtime check)."

## Out of Scope

- Restructuring `main.py` / removing globals (Phase 2, FR-DEMO-2 / FR-CLI-1).
- Headless `--no-display` mode (Phase 3, FR-DEMO-4).
- Making `main.py` runnable (Phase 1, C4).

## Suggested Approach

Small, fully-specified — no plan mode. Fix the fourcc, add the `isOpened()` raise, wrap
lines ~91-142 in `try:` and move the cleanup block (~144-147) into `finally:`.

## Verification (static — runtime deferred to Phase 1)

```bash
grep -n "mp4v" main.py && ! grep -n "mp0v" main.py && echo "OK: fourcc fixed"
grep -n "out.isOpened\|VideoWriter" main.py     # open-check present after construction
grep -n "finally" main.py                        # cleanup in finally block
.venv/bin/python -m py_compile main.py && echo "OK: compiles"
```

Plus operator eyeball of the diff: cleanup calls genuinely inside `finally:`, no logic
moved out of the loop by accident.
