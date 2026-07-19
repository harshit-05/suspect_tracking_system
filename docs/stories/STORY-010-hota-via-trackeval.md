---
id: STORY-010
title: HOTA metric via TrackEval
phase: 1
priority: P0
srs_refs: [C1 (completion), FR-EVAL-1 (completes it)]
status: todo
depends_on: [STORY-006]
---

## Context

FR-EVAL-1 requires MOTA, IDF1 **and HOTA**. STORY-006 delivers the first two via
`motmetrics`, which does not implement HOTA; the accepted implementation is
[TrackEval](https://github.com/JonathonLuiten/TrackEval). TrackEval is not a polished
PyPI citizen — it may need installation from a pinned git ref and has its own
expectations about dataset folder layout, which is why this is a separate story
rather than part of STORY-006.

## Acceptance Criteria

- [ ] TrackEval installed via uv from a **pinned source** (exact ref recorded in
      requirements.txt with a comment; if a usable PyPI release exists, pin that).
      If it will not install/run on Python 3.12, STOP and report options — do not
      hand-roll a HOTA implementation.
- [ ] `evaluation/mot_metrics.py` extended: HOTA computed for the same
      (gt, tracker-output) pair used for MOTA/IDF1 — via TrackEval's API or by
      writing the MOTChallenge-format files TrackEval expects into a temp dir.
- [ ] `evaluate_pipeline` returns/prints HOTA alongside MOTA/IDF1 on the fixture;
      smoke test asserts HOTA ∈ [0, 1].
- [ ] Comparability note added to `evaluation/mot_metrics.py` docstring: all three
      metrics computed from identical inputs (ML-2 spirit).

## Out of Scope

- EvalResult schema / manifests (Phase 2). Any change to trackers/optimizers.
- Full MOT20 benchmark runs (GPU box, later — fixture only here).

## Suggested Approach

TrackEval's `trackeval.Evaluator` with the `MotChallenge2DBox` dataset class is the
documented path: write gt + results in MOTChallenge layout to a temp dir, run the
HOTA metric only, read the summary dict. Keep the temp-dir shim inside
`mot_metrics.py` so callers see just numbers.

## Verification

```bash
.venv/bin/python - <<'EOF'
from evaluation.evaluation import evaluate_pipeline
cfg = {"img_size": 320, "conf_thresh": 0.3, "iou_thresh": 0.5, "skip_interval": 1}
res = evaluate_pipeline(cfg, device="cpu", video_path="tests/data/tiny_clip.mp4",
                        gt_path="tests/data/tiny_clip_gt.txt")
print(res)  # must include HOTA in [0, 1]
EOF
```

≤ ~2 min on the fixture.
