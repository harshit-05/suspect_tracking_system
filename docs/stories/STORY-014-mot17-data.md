---
id: STORY-014
title: Acquire MOT17 via trackers.download_dataset — provenance check, train/held-out pick, fixture
phase: 1
priority: P0
srs_refs: [ML-4, NFR-REP-5, SEC-4, "STORY-011 gate (ADR-012)"]
status: todo
depends_on: [STORY-010]
---

## Context

STORY-011, and any HPO run whose metrics matter, is gated on a sequence where stock
YOLO has real recall (ADR-012: MOT20-05 gives 1–4 %). motchallenge.net answered
**HTTP 410 Gone** on 2026-10-11. The roboflow `trackers` package, already pinned, ships
`download_dataset(dataset="mot17", split=..., asset=[...])`, which pulls from
Roboflow's storage (`storage.googleapis.com/com-roboflow-marketing/trackers/datasets/mot17-v2`).
Sizes from HEAD requests on 2026-10-11: train frames 427 MB, val frames 406 MB,
annotations under 1 MB per split. It is already split into train and val, which
gives SRS ML-4 (tune on one sequence, report on a held-out one) for free.

Because this is a third-party copy rather than the official source, its labels must be
checked against an independent copy before anything is trusted: the RWTH TrackEval
bundle (STORY-006's ground-truth source) carries MOT17 ground truth.

## Acceptance Criteria

- [ ] MOT17 train and val (frames + annotations) downloaded to `datasets/MOT17/`
      (gitignored). Record which sequences are in each split, the zip URLs and their
      sha256 in this story.
- [ ] Provenance: for at least one sequence, the Roboflow ground truth matches the
      TrackEval bundle's MOT17 ground truth row for row (after sorting), and frame
      counts match `seqinfo.ini`. A mismatch stops the story.
- [ ] Pick a **tuning** sequence and a **held-out** sequence (ML-4) from the measured
      recall of the stock detector on frame 1 (the ADR-012 table, repeated here). The
      tuning sequence must show real dynamic range. Record the pick and the reason.
- [ ] Fixture: the first ~50 frames of the tuning sequence as an mp4 (ffmpeg from the
      frames) plus its ground-truth slice in `tests/data/`, in plain git, under 10 MB.
- [ ] `scripts/trackeval_parity.py` re-run on the MOT17 fixture's ground truth (MOT17
      rules) — still within 1e-9.
- [ ] STORY-011 updated to use the MOT17 data; the gate note on BOARD.md removed.

## Out of Scope

- Frames in git (only the ~50-frame fixture goes in).
- The HPO sanity run itself (STORY-011).
- A DVC setup (NFR-REP-5's full form, Phase 2+); the sha256 record is the interim.

## Verification

The download is a one-time setup step (minutes on this connection), not part of each
story's two-minute check. The checks themselves are cheap:

```bash
ls datasets/MOT17/ && sha256sum ~/.cache/trackers/*mot17*   # recorded in this story
.venv/bin/python scripts/mot17_provenance.py                 # written in this story
ls -la tests/data/mot17_*                                     # < 10 MB
<parity-venv>/bin/python -I scripts/trackeval_parity.py --gt tests/data/mot17_tiny_gt.txt --benchmark MOT17
```
