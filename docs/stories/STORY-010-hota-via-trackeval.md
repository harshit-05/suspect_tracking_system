---
id: STORY-010
title: Official MOT metrics (HOTA, MOTA, IDF1) via trackers.eval, with TrackEval as the parity oracle
phase: 1
priority: P0
srs_refs: [C1 (completion), FR-EVAL-1 (completes it), ML-1, TST-1, "TST-7 (seed)"]
status: done   # implemented 2026-10-11 (trackers.eval + official preprocessing; parity exact, |Δ|=0; motmetrics removed; setuptools pinned); reviewed 2026-10-12, committed f9f0c65
depends_on: [STORY-006]
---

## Context

**Rescoped 2026-10-11** (operator: "go with what's best for the bigger picture"). The
original story added HOTA via TrackEval. Checking both libraries before implementing
found:

- **TrackEval** is MOTChallenge's official evaluation code (its README says so), but it
  has been unmaintained since 2022-11-29 (`12c8791`), works only on a folder layout on
  disk, and would be a second git-pinned dependency next to motmetrics.
- **`trackers.eval`** (roboflow `trackers`, pinned since STORY-007) ports TrackEval's
  CLEAR, HOTA and Identity code "for numerical parity", line by line.
  `evaluate_mot_sequence` also applies MOTChallenge preprocessing: ground truth is
  `conf != 0` pedestrians only, and tracker boxes that match a distractor (classes 2, 7,
  8, 12) are dropped instead of counted as false positives.
- **Our STORY-006 motmetrics path skips that distractor step**, so our MOTA/IDF1 are not
  comparable with published numbers.
- **trackers.eval lacks MOT20's extra distractor**, class 6 (`non_mot_vehicle`); it's a
  TODO in its `io/mot.py`. All our data today is MOT20.
- **Traps:** it scores frames up to the highest frame in either file, so the ground
  truth must be cut to the processed frames. An empty tracker file raises, while a
  single `id = -1` row (ignored by convention) yields 0/0/0 with no false positives.

## Acceptance Criteria

- [x] `evaluation/mot_metrics.py` computes MOTA, IDF1 and HOTA through
      `trackers.eval.evaluate_mot_sequence`, writing temporary MOT files: ground truth
      cut to the processed frames, class 6 marked as a distractor under MOT20 rules,
      and a placeholder row when there are no tracks.
- [x] The benchmark rules (`MOT17` | `MOT20`) are inferred from the sequence folder in
      the GT path (`…/MOT20-05/gt/gt.txt`), with an explicit override. If they can't be
      inferred, raise `ValueError` (fail fast).
- [x] `evaluate_pipeline` keeps its `(mota, idf1, fps)` return for the optimizers. A new
      `evaluate_pipeline_metrics(...)` returns a dict with every metric plus FPS and
      frame count. No optimizer file changes (the operator has work in progress there).
- [x] **Parity:** `scripts/trackeval_parity.py` scores the same inputs with our wrapper
      and with TrackEval (pinned `12c8791`, throwaway venv only, never in
      `requirements.txt`), under both MOT17 and MOT20 rules. The inputs are the fixture
      ground truth plus synthetic hypotheses (identity, jitter, dropped boxes, ID swaps,
      extra boxes, boxes on distractors) and the real tracker output.
      HOTA, MOTA and IDF1 agree within 1e-9.
- [x] `tests/metrics_test.py` (model-free, a few seconds): identity oracle gives 1.0
      on all three; a zero-track run gives 0/0/0 without crashing; a box on a
      distractor is not a false positive; scoring a prefix against the full ground
      truth equals scoring it against the matching slice; benchmark inference and its
      `ValueError` work.
- [x] The smoke test reports HOTA, asserts HOTA ∈ [0, 1] and keeps the IDF1 > 0
      tripwire.
- [x] motmetrics is removed from `requirements.txt`, from the code (grep-verified) and
      from `.venv`; a cold install from `requirements.txt` still works.
- [x] The report gives old (motmetrics) vs new (official rules) numbers on the fixture,
      so the protocol fix is quantified.
- [x] `docs/ADR.md`: a new ADR supersedes ADR-009; `CLAUDE.md`'s layout line is updated.

## Out of Scope

- The `EvalResult` Pydantic model and run manifests (Phase 2, FR-EVAL-4); the dict is
  its precursor.
- Changing the optimizer objective: HOTA is reported, not optimized. The vector stays
  MOTA/IDF1/FPS (FR-OPT-1).
- MOT17 data, and parity on a MOT17 sequence: STORY-014.
- Sending the MOT20 distractor fix upstream to roboflow/trackers.

## Verification

```bash
.venv/bin/python -W ignore tests/metrics_test.py     # seconds, no model
.venv/bin/python -W ignore tests/smoke_test.py       # ~15 s
# one-time oracle check; the throwaway-venv setup is in the script's header
<parity-venv>/bin/python -I scripts/trackeval_parity.py
grep -rn "motmetrics" --include="*.py" . ; grep -c "motmetrics" requirements.txt
```

## Deviation from plan

- **`setuptools==78.1.0` pinned — not planned.** The cold install found that
  setuptools had floated to 84.0.0 (torch asks only for `>=77.0.3`), and 81+
  removed the `pkg_resources` that `deep_sort_realtime` imports. Every fresh
  install crashed DeepSORT on first use. The pin was needed for this story's own
  cold-install criterion. Recorded in ADR-007.
- **The parity harness restores `np.float`/`np.int`/`np.bool` before importing
  TrackEval**, which otherwise can't even load a GT file on NumPy 2. This is in
  the script only, never in app code.
- **TrackEval crashes on a tracker file whose only row has `id = -1`.** In the
  "no tracks" case the harness gives TrackEval a truly empty file, so that case
  checks our placeholder trick against genuinely empty output.

## Discovered

- An earlier claim in session — that TrackEval's removed NumPy aliases sat
  outside the MOT path — was wrong; the MOT loader uses `np.float` (81 alias
  uses in total).
- Results, old (motmetrics) → new (official rules) on the fixture, same tracks:
  320 px MOTA 0.0017 → 0.0020, IDF1 0.0059 → 0.0059, HOTA 0.0313; 960 px MOTA
  0.0324 → 0.0429, IDF1 0.0930 → 0.0937, HOTA 0.1480. The recall floor
  (ADR-012) still dominates.
- STORY-008's Verification block still names `torchreid`, which was dropped
  (stale; not fixed here).
- trackers.eval's MOT20 distractor TODO could be fixed upstream in
  roboflow/trackers; our class-6 relabel would then be redundant but harmless.
