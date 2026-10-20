---
id: STORY-014
title: Acquire MOT17 via trackers.download_dataset — provenance check, train/held-out pick, fixture
phase: 1
priority: P0
srs_refs: [ML-4, NFR-REP-5, SEC-4, "STORY-011 gate (ADR-012)"]
status: review   # implemented 2026-10-20: MOT17 (Roboflow half split) verified row-for-row vs TrackEval bundle; tune MOT17-04, hold out 04+13 val halves; fixture + exact parity; STORY-011 gate lifted
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

- [x] MOT17 train and val (frames + annotations) downloaded to `datasets/MOT17/`
      (gitignored). Record which sequences are in each split, the zip URLs and their
      sha256 in this story.
- [x] Provenance: for at least one sequence, the Roboflow ground truth matches the
      TrackEval bundle's MOT17 ground truth row for row (after sorting), and frame
      counts match `seqinfo.ini`. A mismatch stops the story.
- [x] Pick a **tuning** sequence and a **held-out** sequence (ML-4) from the measured
      recall of the stock detector on frame 1 (the ADR-012 table, repeated here). The
      tuning sequence must show real dynamic range. Record the pick and the reason.
- [x] Fixture: the first ~50 frames of the tuning sequence as an mp4 (ffmpeg from the
      frames) plus its ground-truth slice in `tests/data/`, in plain git, under 10 MB.
- [x] `scripts/trackeval_parity.py` re-run on the MOT17 fixture's ground truth (MOT17
      rules) — still within 1e-9.
- [x] STORY-011 updated to use the MOT17 data; the gate note on BOARD.md removed.

## Out of Scope

- Frames in git (only the ~50-frame fixture goes in).
- The HPO sanity run itself (STORY-011).
- A DVC setup (NFR-REP-5's full form, Phase 2+); the sha256 record is the interim.

## Verification

The download is a one-time setup step (minutes on this connection), not part of each
story's two-minute check. The checks themselves are cheap:

```bash
.venv/bin/python -I scripts/mot17_provenance.py               # lengths, images, every GT row; sha256
ls -la tests/data/MOT17-04-tiny*                              # < 10 MB
<parity-venv>/bin/python -I scripts/trackeval_parity.py --gt tests/data/MOT17-04-tiny_gt.txt --rules MOT17
```

## Record (2026-10-20)

**Source.** `trackers.download_dataset(dataset="mot17", split=["train", "val"],
asset=["frames", "annotations"], output="datasets/MOT17")`, from
`https://storage.googleapis.com/com-roboflow-marketing/trackers/datasets/mot17-v2/`
(`mot17-{train,val}-{frames,annotations}.zip`). The official ground truth used for the
check is the TrackEval bundle, kept at `datasets/_sources/trackeval/data.zip`. sha256:

```text
f1f4d30dba23946694ebd4dabe6970622f51c354e433c77daf1b4b50b70dbc62  mot17-train-annotations.zip
cdc97724e577677deba01e67ae874b0f19e23540bef6fa8a0fa8e8cf208f4713  mot17-train-frames.zip
682d6b68b3548b80b1a9194cace4575fcd3476406e0062c9190f103e014b34a9  mot17-val-annotations.zip
b2a38d16c51da7bd9b2c10f666c507624978f64e159f7739b0e3842fe3bbcf45  mot17-val-frames.zip
148a4bdf56f8cb32f9bde4b3d70717242cbb2e61900ef0101abc4652e268f2a5  data.zip (TrackEval bundle)
```

**Splits.** Both splits hold the same seven official training sequences (FRCNN copies:
02, 04, 05, 09, 10, 11, 13), cut with ByteTrack's half split. Train is official
frames 1..n//2+1 and val is the rest, each renumbered from 1. `scripts/mot17_provenance.py`:
for all seven, train + val lengths equal the official length, image counts match, and
every ground-truth row matches the official one after the offset — PROVENANCE OK.

**Detector recall** (`scripts/detector_recall.py`, yolov8l, conf 0.3, 3 frames per
train half):

| sequence | GT/frame | 320 px | 640 px | 960 px |
| --- | --- | --- | --- | --- |
| MOT17-02 | 28 | 16.5 % | 32.9 % | 36.5 % |
| MOT17-04 | 45 | 21.5 % | 35.6 % | 44.4 % |
| MOT17-05 | 6 | 66.7 % | 66.7 % | 72.2 % |
| MOT17-09 | 9 | 69.2 % | 69.2 % | 69.2 % |
| MOT17-10 | 21 | 38.1 % | 54.0 % | 66.7 % |
| MOT17-11 | 12 | 66.7 % | 69.4 % | 69.4 % |
| MOT17-13 | 20 | 24.6 % | 41.0 % | 50.8 % |

(MOT20-05, for comparison: 0.9–4.2 %, ADR-012.)

**Pick (ML-4).**

- **Tune on MOT17-04, train half.** Recall roughly doubles with image size, so
  `img_size` matters to the optimizer. It is dense (45 people per frame), so identity
  metrics matter, and it is the most widely reported MOT17 sequence. MOT17-05, 09 and
  11 were ruled out because their recall barely moves with size.
- **Hold out two val halves, never used for tuning:**
  - **MOT17-04 val half** — the standard "half-val" protocol, comparable with the
    literature.
  - **MOT17-13 val half** — an unseen scene, with the recall profile closest to 04's.

**Fixture.** `tests/data/MOT17-04-tiny.mp4` (344 KB: 50 frames, 1920×1080, 30 fps, plain
git) and `tests/data/MOT17-04-tiny_gt.txt` (151 KB: 4,975 rows). The ground-truth boxes
for frame 1 sit on the people: 42 scored boxes, checked by eye. The filename names the
sequence, so the MOT17 rules are inferred. On it, the metrics move with configuration:
MOTA 0.153 / IDF1 0.296 / HOTA 0.357 at 320 px (2.36 FPS), and 0.347 / 0.535 / 0.520 at
960 px (0.53 FPS).

**Parity** (TrackEval, MOT17 rules), exact (|Δ| = 0.0) in every case:

- MOT17-02 train half — 7 synthetic cases. Picked for having the most distractor rows
  (8,020); this was the operator's refinement.
- The MOT17-04 fixture — 7 synthetic cases plus the two real tracker outputs above.

## Deviation from plan

- **Roboflow's "val" is not other sequences** — it is the second half of the same
  seven. The held-out pick therefore uses val halves: 04 (the half-val protocol) and 13
  (an unseen scene). Both are reported, so ML-4 gets a split and a sequence.
- **Parity ran twice, not once:** also on MOT17-02's full train half, chosen by
  distractor count (operator's refinement), on top of the fixture.
- **The recall measurement became a committed script** (`scripts/detector_recall.py`)
  instead of a one-off, because it will be wanted again on the GPU box and for any
  detector swap.
- **The fixture is named `MOT17-04-tiny*`, not `mot17_tiny*`,** so the benchmark rules
  are inferred from the filename. The parity flag is `--rules`, not `--benchmark`.
- **The download went to `datasets/_sources/`.** Last session's TrackEval bundle sat in
  the scratchpad on `/tmp`, a RAM tmpfs that a reboot had wiped.

## Discovered

- **The detector is now the bottleneck:** 44 % recall at best on MOT17-04. A stronger
  detector (YOLO11, or weights trained on CrowdHuman) is a candidate stack upgrade, to
  propose with numbers from `scripts/detector_recall.py`.
- **The smoke test still runs on the MOT20 fixture,** whose only quality check is
  IDF1 > 0. The MOT17 fixture would support a real floor (for example IDF1 > 0.2 at
  320 px) — a candidate small story.
- **Roboflow's frames can't be checked pixel by pixel** — no official image source is
  reachable. Ground truth was verified row by row, and frame-to-label alignment was
  checked by eye on frame 1.
