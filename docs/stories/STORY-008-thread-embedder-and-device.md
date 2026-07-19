---
id: STORY-008
title: Thread embedder AND device end-to-end through the experiment matrix
phase: 1
priority: P0
srs_refs: [C3, FR-TRK-4, FR-OPT-5, FR-DET-2 (partial — device plumbing)]
status: todo
depends_on: [STORY-003]
---

## Context

Audit C3: `batch_runner.py` iterates `embedders = ["mobilenetv2", "shufflenetv2",
"resnet"]` but the value is used **only as a results-folder name** — it never reaches
the tracker. The claimed 3×3 experiment matrix is actually 1×3 with fake labels.

Two facts verified 2026-07-19:

- The installed `deep_sort_realtime==1.3.2` accepts `embedder=` with its own option
  names (`mobilenet` is the default; `torchreid` and `clip_*` need extra packages).
  The fictional labels don't map 1:1 — the matrix must be **redefined to real,
  installable options**, not renamed cosmetically.
- Related gap found during STORY-001 review: the three optimizers call
  `evaluate_pipeline(config)` without `device`, silently using the `"cuda"` default
  while `batch_runner`'s final eval passes `DEVICE`. On the future GPU box this means
  inner-loop and final evals could run on different devices. Device must be threaded
  everywhere (operator directive: everything device-modular; this box is CPU-only,
  deployment box is GPU).

## Acceptance Criteria

- [ ] `evaluate_pipeline` accepts `embedder`; `tracking/deepsort_wrapper.py` forwards
      it (plus `embedder_gpu` derived from `device`) to `DeepSort`. (The local
      package was renamed `trackers/` → `tracking/` in STORY-007 — it shadowed the
      pip `trackers` package.)
- [ ] All three optimizers accept and forward `embedder` and `device` to every
      `evaluate_pipeline` call (same pattern as `video_path` in STORY-001).
- [ ] `batch_runner.py`'s embedder list replaced with real `deep_sort_realtime`
      options. Default: `["mobilenet", "torchreid"]` — **confirm the final set with
      the operator** before implementing; add any extra packages (`torchreid`, etc.)
      to requirements.txt via uv, pinned. If an embedder's deps won't install
      cleanly on Python 3.12, drop it and report rather than fighting it.
- [ ] Plumbing proof: constructing the pipeline with `embedder=X` results in the
      underlying `DeepSort` instance actually using X (introspection assert), for
      each embedder in the final set.

## Out of Scope

- Pydantic config tree (Phase 2, NFR-REL-2). Model caching (FR-OPT-7, STORY-009 not
  it either — Phase 2). Optimizer scoring (STORY-009). Renaming results folders.

## Suggested Approach

~6 files but the optimizer edits are 2-line kwarg threading each. Mirror STORY-001's
`video_path` pattern exactly. For the plumbing proof inspect
`DeepSort` internals (`tracker.embedder` / embedder object class name) rather than
running a full eval per embedder — one real fixture run with the non-default embedder
is enough to prove it end-to-end.

## Verification

```bash
.venv/bin/python - <<'EOF'
from tracking.deepsort_wrapper import TrackByDetection
for emb in ["mobilenet", "torchreid"]:          # final set per operator decision
    t = TrackByDetection(0.3, 320, 0.5, 1, embedder=emb, device="cpu")
    print(emb, "->", type(t.tracker.embedder).__name__)
EOF
.venv/bin/python - <<'EOF'
from evaluation.evaluation import evaluate_pipeline
cfg = {"img_size": 320, "conf_thresh": 0.3, "iou_thresh": 0.5, "skip_interval": 1}
r = evaluate_pipeline(cfg, device="cpu", video_path="tests/data/tiny_clip.mp4",
                      embedder="torchreid")
print("non-default embedder end-to-end OK:", r)
EOF
```

Both together ≤ ~2 min on the fixture.
