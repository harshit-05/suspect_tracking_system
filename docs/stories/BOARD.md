# Story Board

Status values: `todo` → `in-progress` → `review` → `done`. See [`docs/WORKFLOW.md`](../WORKFLOW.md).

**Order matters in Phase 0** — respect `depends_on` in each story's frontmatter.
Dispatch strictly top-to-bottom unless a story says otherwise.

## Phase 0 — Stop the bleeding

| # | Story | Title | Priority | SRS refs | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | [STORY-000](STORY-000-stabilize-git-state.md) | Stabilize git state — commit drift, resolve phantom tree | P0 | M6, DEV-2 (partial) | review |
| 2 | [STORY-003](STORY-003-interim-dependency-manifest.md) | Interim dependency manifest + pinned Python env | P0 | C5, NFR-REP-1 (partial) | todo |
| 3 | [STORY-002](STORY-002-repo-hygiene-cleanup.md) | Repo hygiene cleanup — dead files, poisoned results | P0 | M6, L1 | todo |
| 4 | [STORY-005](STORY-005-test-fixture-clip.md) | Tiny test fixture clip + first smoke test | P0 | TST-1 | todo |
| 5 | [STORY-004](STORY-004-fix-writer-fourcc-and-checks.md) | Fix VideoWriter fourcc + open checks (static verify) | P0 | H3, FR-DEMO-3 (partial) | todo |
| — | [STORY-001](STORY-001-fix-eval-video-path.md) | Fix evaluation entry point — real path + fail-fast guards | P0 | C2, FR-EVAL-2 | **done** (implemented by agent session 2026-07-19; verified by inspection, runtime check deferred to STORY-005) |

## Phase 1 — Make the numbers real

Not yet sharded. Run Stage B of `docs/WORKFLOW.md` against SRS §13 Phase 1 once Phase 0
is `done`. Carry-over items already known:

- ByteTrack fix story must include STORY-004's deferred runtime verification
  (run `main.py` end-to-end, validate output video).
- Real-metrics story supersedes the mock-formula caveat noted in STORY-005.

## Phase 2 — Restructure to target architecture

Not yet sharded.

## Phase 3 — Research quality & polish

Not yet sharded.
