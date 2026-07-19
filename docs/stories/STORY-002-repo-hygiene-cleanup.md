---
id: STORY-002
title: Repo hygiene cleanup — dead files, poisoned results
phase: 0
priority: P0
srs_refs: [M6, L1]
status: done   # implemented + Stage-D reviewed 2026-07-19: all targets grep-verified dead, deleted; 3 modules via git rm (recoverable); compiles clean
depends_on: [STORY-000, STORY-003]
---

## Context

The audit found junk in the repo: a stray file named `=` (a redirected conda log), a
296 MB `result/` directory (distinct from `results/`), dead modules, and poisoned
result files produced by the zero-frame evaluation bug (C2, fixed pre-STORY-001).

**Recoverability check (verified against `git ls-files`, 2026-07-19):**

| Target | Tracked? | If deleted… |
| --- | --- | --- |
| `=` | untracked | gone forever — it's a junk log, that's fine |
| `result/output_tracking.mp4` | untracked (only the phantom nested copy was tracked) | gone forever |
| `results/` (summary_table.csv, mobilenetv2/) | untracked | gone forever — but provably garbage (zero-frame runs) |
| `run_plot_pareto.py` | **untracked** | **gone forever** |
| `optimization/config.py` | **untracked** | **gone forever** |
| `utils/video_io.py` | tracked | recoverable from history |

STORY-000 must be `done` first (clean committed baseline) and STORY-003 provides the
env for the compile check. If STORY-000 committed `run_plot_pareto.py` /
`optimization/config.py` as part of adding the source tree, they become recoverable and
this story just deletes them; if it excluded them, this deletion is permanent — either
way, confirm with the operator before removing anything marked *gone forever* above.

## Acceptance Criteria

- [ ] Grep-confirm zero live references before each deletion (commands below); if any
      real caller appears, stop and report instead of deleting.
- [ ] Deleted: `=`, `result/`, `results/summary_table.csv`, `results/mobilenetv2/`,
      `run_plot_pareto.py`, `optimization/config.py`, `utils/video_io.py` (this one via
      `git rm`).
- [ ] Everything still compiles afterwards.
- [ ] Changes committed with a message listing what was removed and why.

## Out of Scope

- Git history purging / LFS cleanup (destructive; separate operator-approved task, DEV-2).
- Deleting `yolov8l.pt` / `yolov8m.pt` weights (Phase 2, NFR-REP-4).
- `.gitignore` — already handled by STORY-000.

## Suggested Approach

```bash
grep -rn "run_plot_pareto\|nsga_optimization\b" --include="*.py" .
grep -rn "from optimization.config\|from optimization import config\|import optimization.config" --include="*.py" .
grep -rn "video_io\|draw_particles\|draw_tracking" --include="*.py" .
```

Expected: matches only inside the files being deleted themselves. Then delete, compile-
check, commit. No plan mode needed.

## Verification

```bash
test ! -e "=" && test ! -d result && test ! -e run_plot_pareto.py \
  && test ! -e optimization/config.py && test ! -e utils/video_io.py \
  && test ! -e results/summary_table.csv && echo "OK: junk removed"

.venv/bin/python -m compileall -q detectors evaluation optimization trackers utils batch_runner.py \
  && echo "OK: compiles"
git status --porcelain   # should show only this story's staged deletions or be clean post-commit
```
