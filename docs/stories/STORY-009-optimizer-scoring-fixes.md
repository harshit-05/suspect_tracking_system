---
id: STORY-009
title: Fix optimizer scoring — Pareto dominance, un-inverted FPS, memoization, seeds
phase: 1
priority: P0
srs_refs: [H4, FR-OPT-1, FR-OPT-4, FR-OPT-6, NFR-PERF-1, TST-3 (seed)]
status: todo
depends_on: [STORY-003]
---

## Context

Audit H4, all still present (re-verified 2026-07-19):

- QPSO/MOPSO compare `(mota, idf1, 1/fps)` tuples **lexicographically** with `>` —
  not Pareto — and because the third element is 1/fps under a `>` comparison, a
  **slower** config wins ties on MOTA+IDF1 (inverted).
- NSGA-II's third objective is `1/max(fps,1e-3)` with weight `-1.0` — a double
  negation that happens to point the right way but is needlessly convoluted; make it
  `fps` with weight `+1.0`.
- MOPSO re-evaluates every particle's personal best each generation — 2× the model
  cost per generation (O(2·particles) instead of O(particles)).
- No evaluation memoization despite a small discrete config space; no RNG seeding
  anywhere (`random`, `numpy`, `torch`).

## Acceptance Criteria

- [ ] New `optimization/objectives.py` (single shared module): `dominates(a, b)` for
      maximize-all vectors `(mota, idf1, fps)`; an eval memo-cache keyed by the
      quantized-config tuple; `seed_all(seed)` seeding random/numpy/torch.
- [ ] QPSO and MOPSO global/personal-best updates use dominance (document the
      tie-break for a single "best": prefer the new non-dominated point only if it
      dominates, else keep — no silent lexicographic fallback). FPS enters scoring
      **un-inverted** everywhere.
- [ ] MOPSO caches personal-best scores — zero re-evaluations of already-scored
      configs anywhere (memo cache shared across the run).
- [ ] All three optimizers take `seed` and call `seed_all`; same seed ⇒ identical
      eval sequence (assert in test).
- [ ] `tests/optimizer_test.py` with a **synthetic objective** (no model, no video):
      dominance truth-table incl. the inverted-FPS regression case (faster must beat
      slower on ties); eval-count ≤ distinct-quantized-configs (memoization); seed
      reproducibility. Runs in seconds.

## Out of Scope

- Full utils consolidation of the triplicated `load_config`/`log_to_csv` (M1/FR-OPT-3
  — Phase 2; only dominance/memo/seed live in the new shared module).
- Search-space schema (M3, Phase 3), Optuna baseline (FR-OPT-8), model caching
  (FR-OPT-7/M2 — Phase 2), hypervolume reporting (ML-3, Phase 3).

## Suggested Approach

Keep each optimizer's control flow; only swap the comparison/caching/seeding layer.
The memo cache is a dict living for one optimizer run, injected or module-level in
`objectives.py` with an explicit `reset()`. Pass `seed` from `batch_runner` (one value
recorded in the CSV log header for now — full manifests are Phase 2).

## Verification

```bash
.venv/bin/python tests/optimizer_test.py   # synthetic objective — runs in seconds
```
