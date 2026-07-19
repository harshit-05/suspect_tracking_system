---
id: STORY-000
title: Stabilize git state — commit drift, resolve phantom tree, stop tracking junk
phase: 0
priority: P0
srs_refs: [M6, DEV-2 (partial)]
status: review   # implemented 2026-07-19; operator decisions: untrack *.pt, commit strongsort deletion, gitignore sample_videos/
depends_on: []
---

## Context

Verified 2026-07-19: the working tree is **not** clean — `git status` shows ~18 tracked
files modified or deleted, plus large untracked areas. Specifically:

- **Phantom nested tree**: `cctv_tracking_system/.gitattributes`,
  `cctv_tracking_system/result/output_tracking.mp4`, and
  `cctv_tracking_system/sample_videos/mot20-05sample.mp4` are tracked in git but do not
  exist on disk — leftovers from a botched repo restructure where the project was moved
  up one level.
- **Tracked-but-deleted files**: `LICENSE` and `trackers/strongsort_wrapper.py` are in
  git but deleted from disk.
- **`__pycache__/*.pyc` files are tracked** (cpython-310 vintage) and show as modified.
- **The entire HPO layer is untracked**: `optimization/`, `evaluation/`,
  `batch_runner.py`, `results/`, `docs/`, `.gitignore`, `.gitattributes` at root. The
  last commit (2025-07-01) predates the optimization system entirely.
- Several tracked source files (`main.py`, both tracker wrappers, `detectors/yolo_detector.py`,
  etc.) carry uncommitted modifications — including the already-applied STORY-001 fix.

No deletion or refactor story can run safely on top of this: untracked files have **no
git history** and are unrecoverable if deleted, and the uncommitted drift makes any
story's diff impossible to review or revert cleanly.

## Acceptance Criteria

- [ ] A proper Python `.gitignore` is in place **before** any commit (`__pycache__/`,
      `*.pyc`, `results/`, `result/`, `.venv/`, `*.pt` optional — ask operator). This
      absorbs the `.gitignore` item formerly in STORY-002.
- [ ] All tracked `__pycache__/*.pyc` files removed from the index
      (`git rm -r --cached`) — files may stay on disk.
- [ ] Phantom nested `cctv_tracking_system/*` entries removed from the index
      (`git rm --cached`). They exist in history, so this is recoverable.
- [ ] `LICENSE`: restored from git (`git checkout -- LICENSE`) unless the operator says
      otherwise — deleting a license file is almost never intended.
- [ ] `trackers/strongsort_wrapper.py`: **ask the operator** — restore or commit the
      deletion. (It's in history either way; nothing referenced it in the audit.)
- [ ] All real source currently untracked (`optimization/`, `evaluation/`,
      `batch_runner.py`, `docs/`, root `.gitattributes`) is added and committed. Do NOT
      add `results/`, `result/`, `=`, or `.pyc` files — those are STORY-002 deletions
      and must not enter history now.
- [ ] Everything committed in one or a few well-messaged commits; `git status --porcelain`
      afterwards shows only the files STORY-002 is scheduled to delete (`=`, `result/`,
      `results/`) as untracked, or nothing.

## Out of Scope

- Any file deletion from disk (STORY-002).
- Git **history** rewriting / purging old LFS objects — destructive, separate
  operator-approved task (SRS DEV-2).

## Suggested Approach

This story touches git state, not code — work in this order so junk never enters
history: write `.gitignore` → `git rm --cached` the pycache + phantom entries → restore
`LICENSE` → resolve `strongsort_wrapper.py` with the operator → `git add` the real
source → commit. Stop and ask the operator before resolving anything ambiguous; never
use `git checkout`/`git restore` on a file with uncommitted modifications you haven't
diffed first.

## Verification

```bash
git status --porcelain            # only STORY-002 deletion targets (or empty)
git ls-files | grep -c "__pycache__"        # → 0
git ls-files | grep -c "^cctv_tracking_system/"   # → 0
git ls-files | grep -E "optimization/|evaluation/|batch_runner"  # all present
test -f LICENSE && echo "LICENSE restored"
```
