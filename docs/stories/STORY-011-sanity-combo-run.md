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
      MOTA/IDF1/(HOTA if STORY-010 landed)/FPS, and a best-config metrics JSON.
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
fixture paths and tiny budget. Expected wall time: 8–16 evals × ~16 s ≈ 2–4 min on
this CPU — slightly over the 2-minute rule, accepted for this one integration story
(note it in the report).

## Verification

```bash
time .venv/bin/python scripts/sanity_combo.py   # or the batch_runner invocation used
head -20 results/<combo>/log.csv                # real metrics, no sentinels
```
