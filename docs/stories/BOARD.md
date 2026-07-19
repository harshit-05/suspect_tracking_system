# Story Board

Status values: `todo` → `in-progress` → `review` → `done`. See [`docs/WORKFLOW.md`](../WORKFLOW.md).

**Order matters in Phase 0** — respect `depends_on` in each story's frontmatter.
Dispatch strictly top-to-bottom unless a story says otherwise.

## Phase 0 — Stop the bleeding

| # | Story | Title | Priority | SRS refs | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | [STORY-000](STORY-000-stabilize-git-state.md) | Stabilize git state — commit drift, resolve phantom tree | P0 | M6, DEV-2 (partial) | **done** (operator committed & pushed as `209c468`, 2026-07-19) |
| 2 | [STORY-003](STORY-003-interim-dependency-manifest.md) | Interim dependency manifest + pinned Python env | P0 | C5, NFR-REP-1 (partial) | **done** (committed `3cb7366`) |
| 3 | [STORY-002](STORY-002-repo-hygiene-cleanup.md) | Repo hygiene cleanup — dead files, poisoned results | P0 | M6, L1 | **done** (committed `1d4eb77`) |
| 4 | [STORY-005](STORY-005-test-fixture-clip.md) | Tiny test fixture clip + first smoke test | P0 | TST-1 | **done** (committed `5c23ca6`) |
| 5 | [STORY-004](STORY-004-fix-writer-fourcc-and-checks.md) | Fix VideoWriter fourcc + open checks (static verify) | P0 | H3, FR-DEMO-3 (partial) | **done** (committed `9a00c82`; runtime check → STORY-007) |
| — | [STORY-001](STORY-001-fix-eval-video-path.md) | Fix evaluation entry point — real path + fail-fast guards | P0 | C2, FR-EVAL-2 | **done** (implemented by agent session 2026-07-19; verified by inspection, runtime check deferred to STORY-005) |

## Phase 1 — Make the numbers real

Sharded 2026-07-19 (Stage B; operator waived a separate Stage-A pass — SRS §13 Phase 1
followed directly). Phase-0 carry-overs are embedded: STORY-007 contains STORY-004's
deferred runtime check; STORY-006 supersedes STORY-005's mock-metrics caveat.

| # | Story | Title | Priority | SRS refs | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | [STORY-006](STORY-006-real-mot-metrics.md) | Real MOTA/IDF1 via motmetrics — delete mock formula | P0 | C1, FR-EVAL-1 (partial), ML-1 | **done** (committed `4ba5231`) |
| 2 | [STORY-007](STORY-007-bytetrack-via-supervision.md) | ByteTrack via roboflow trackers + tracker selection | P0 | C4, H2, FR-TRK-1..3, TST-4 | review |
| 3 | [STORY-008](STORY-008-thread-embedder-and-device.md) | Thread embedder AND device end-to-end | P0 | C3, FR-TRK-4, FR-OPT-5 | todo |
| 4 | [STORY-009](STORY-009-optimizer-scoring-fixes.md) | Pareto dominance, un-inverted FPS, memoization, seeds | P0 | H4, FR-OPT-1/4/6, NFR-PERF-1 | todo |
| 5 | [STORY-010](STORY-010-hota-via-trackeval.md) | HOTA via TrackEval | P0 | FR-EVAL-1 (completes) | todo |
| 6 | [STORY-011](STORY-011-sanity-combo-run.md) | Sanity end-to-end combo run (small budget, fixture) | P0 | Phase 1.9, ML-1, TST-5 | todo |

## Phase 2 — Restructure to target architecture

Not yet sharded.

## Phase 3 — Research quality & polish

Not yet sharded.
