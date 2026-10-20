---
id: STORY-011
title: Sanity end-to-end combo run with real metrics (small budget, fixture)
phase: 1
priority: P0
srs_refs: [Phase 1.9 roadmap item, ML-1, TST-5 (seed), NFR-PERF-1 (observable)]
status: todo
depends_on: [STORY-006, STORY-008, STORY-009]
---

## Context

**Gate lifted by STORY-014 (2026-10-20, ADR-018).** MOT20-05 is too dense for stock
YOLO at CPU sizes (1–4 % recall, ADR-012), so this story runs on the **MOT17-04
fixture**: `tests/data/MOT17-04-tiny.mp4` + `tests/data/MOT17-04-tiny_gt.txt` (first
50 frames of the tuning sequence; MOT17 rules are inferred from the filename). There
the metrics have range — MOTA 0.153 → 0.347, IDF1 0.296 → 0.535 from 320 to 960 px —
and trade off against speed (2.36 → 0.53 FPS). The full sequences live in
`datasets/MOT17/` (tuning: MOT17-04 train half; held out: MOT17-04 and MOT17-13 val
halves). MOT20-05 full-resolution behaviour gets re-checked on the GPU box later.

SRS §13 Phase 1 step 9: "Re-run one full combo and sanity-check outputs by eye before
re-running the matrix." This is the first time detector→tracker→**real metrics**→
optimizer→logs runs as one system since the audit. Two standing constraints
(operator directives): all heavy/full-matrix runs happen later on the **GPU box** —
this story uses the fixture and a tiny budget on CPU; and the operator makes all
commits.

## Acceptance Criteria

- [ ] One combo runs end-to-end on CPU: DeepSORT + one real embedder + QPSO,
      **4 particles × 2 generations**, fixture video + fixture GT, fixed seed.
- [ ] Outputs land in `results/` (old layout is fine — per-run manifest dirs are
      Phase 2): eval log CSV with one row per evaluation including real
      MOTA/IDF1/HOTA/FPS, and a best-config metrics JSON.
- [ ] Log inspection confirms, and the report shows: (a) number of distinct
      evaluations ≤ distinct quantized configs (memoization observable in the wild),
      (b) no `0.001` FPS or mock-formula values (no MOTA that equals
      `0.80 + 0.05·(n%5)` pattern), (c) same seed twice ⇒ identical log.
- [ ] Operator eyeballs the numbers (that's the point of the story) — agent presents
      the log table and flags anything suspicious rather than declaring victory.
- [ ] A short `docs/PHASE1-RESULTS.md` note: what was run, seed, wall time, and the
      explicit statement that full-matrix numbers await the GPU box.

## Out of Scope

- The full 3×3 matrix or any full-sequence MOT20-05 run (GPU box, later).
- Pareto front plotting fixes (`plot_pareto.py` untouched unless it crashes the run —
  if it does, disable the call and report, don't fix plotting here).

## Suggested Approach

Drive through `batch_runner.run_combo` if its coupling allows a small-budget
override; otherwise a 20-line script calling `qpso_optimize` directly with the
fixture paths and tiny budget. Expected wall time, re-estimated for the full-HD MOT17
fixture (STORY-014 measured ~21 s per evaluation at 320 px, ~95 s at 960): 8 particle
visits, fewer real evaluations after memoization, ≈ 3–8 min depending on how many land
on 960 px. Over the 2-minute rule — accepted for this one integration story; say so
in the report, with the actual time.

## Verification

```bash
time .venv/bin/python scripts/sanity_combo.py   # or the batch_runner invocation used
head -20 results/<combo>/log.csv                # real metrics, no sentinels
```
