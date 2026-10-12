# Architecture Decision Records — cctv_tracking_system

This file records the significant decisions made while rebuilding an audited
CCTV tracking + HPO prototype (`docs/SRS.md` §3: mocked metrics, zero-frame
evaluations, a tracker wrapper that never ran) into a system whose numbers can
be trusted. It is written for two readers: **future sessions** (human or
Claude) who need to know *why* something is the way it is before touching it,
and **the operator**, as a record of reasoning that generalizes past this
project.

Each entry has the same shape:

- **Context** — the situation that forced a choice.
- **Decision** — what was chosen, precisely.
- **Consequences** — what was gained, and what is now owed in exchange.
- **Alternatives considered** — the other options, and why each lost.
- **Lesson** — the general principle this instance teaches.

Entries are numbered in the order the decisions were made. Status is
`Accepted`, `Accepted (provisional)` — right for now, with a named trigger to
revisit — or `Superseded by ADR-0NN`. The format, and several of the process
decisions, mirror the maintainer's sibling project RAG_System
(`docs/ADR.md` there); where an entry here repeats a lesson learned there, it
says so.

## Index

| ADR | Title | Status | Phase |
| --- | --- | --- | --- |
| [001](#adr-001-a-spec-driven-story-loop-with-an-operator-checkpoint-per-story) | A spec-driven story loop with an operator checkpoint per story | Accepted | Process |
| [002](#adr-002-sequence-phase-0-by-recoverability) | Sequence Phase 0 by recoverability | Accepted | 0 |
| [003](#adr-003-re-validate-every-story-against-head-before-implementing) | Re-validate every story against HEAD before implementing | Accepted | Process |
| [004](#adr-004-large-artifacts-live-outside-git-weights-download-on-first-use) | Large artifacts live outside git; weights download on first use | Accepted | 0 |
| [005](#adr-005-the-operator-owns-git-history) | The operator owns git history | Accepted (tightened by ADR-016) | Process |
| [006](#adr-006-squash-unpushed-commits-to-keep-oversized-blobs-out-of-a-push) | Squash unpushed commits to keep oversized blobs out of a push | Accepted | 0 |
| [007](#adr-007-uv-only-with-an-interim-exact-pinned-requirementstxt) | uv only, with an interim exact-pinned `requirements.txt` | Accepted (provisional) | 0 → 2 |
| [008](#adr-008-a-50-frame-fixture-in-plain-git-and-a-two-minute-verification-rule) | A 50-frame fixture in plain git, and a two-minute verification rule | Accepted | 0 |
| [009](#adr-009-real-motaidf1-via-motmetrics-proven-against-an-identity-oracle) | Real MOTA/IDF1 via motmetrics, proven against an identity oracle | Accepted (provisional) | 1 |
| [010](#adr-010-bytetrack-from-roboflows-trackers-package-local-package-renamed-to-tracking) | ByteTrack from roboflow's `trackers` package; local package renamed to `tracking/` | Accepted | 1 |
| [011](#adr-011-assert-properties-a-broken-system-cannot-satisfy-not-ranges) | Assert properties a broken system cannot satisfy, not ranges | Accepted | 1 |
| [012](#adr-012-dont-optimize-a-metric-that-has-no-dynamic-range) | Don't optimize a metric that has no dynamic range | Accepted (provisional) | 1 |
| [013](#adr-013-device-is-configuration-never-code) | Device is configuration, never code | Accepted | 1 |
| [014](#adr-014-the-embedder-matrix-holds-only-embedders-that-install) | The embedder matrix holds only embedders that install | Accepted (provisional) | 1 |
| [015](#adr-015-pareto-dominance-with-a-single-leader-rule-memoized-and-seeded) | Pareto dominance with a single-leader rule, memoized and seeded | Accepted (provisional) | 1 → 3 |
| [016](#adr-016-one-rulebook-across-the-maintainers-projects) | One rulebook across the maintainer's projects | Accepted | Process |

---

## ADR-001: A spec-driven story loop with an operator checkpoint per story

**Status:** Accepted · **Date:** 2026-07-19 · **Refs:** H5, `docs/WORKFLOW.md`

**Context.** The audit (SRS §3) found that every optimizer result on record was
fabricated: MOTA/IDF1 came from a modulo formula over the track count (C1), and
every evaluation had run on zero frames of a video that didn't exist (C2). No
test or review caught either. The prototype had grown by accretion — three
detector copies, three copies of the optimizer helpers — with no record of why
anything was the way it was.

**Decision.** A fixed chain of durable artifacts: `SRS.md` → stories sharded
per phase (`docs/stories/STORY-0NN-*.md`, ≤ ~5 files, one verification command
each) → one story per agent turn → an operator review (WORKFLOW Stage D) →
commit. Session state lives in files: `BOARD.md` and each story's frontmatter.

**Consequences.**

- *Pros:* any session can resume from three files instead of a chat
  transcript. "Done" is defined before code is written, so review asks "did
  the listed commands pass and show their output", not "re-read every line".
- *Cons:* overhead per story, worth it only for multi-session work. And a
  story is a snapshot: written from an audit, it goes stale as the tree moves
  (ADR-002, ADR-003).

**Alternatives considered.**

- *Conversational development, no artifacts* — the process that produced C1
  and C2. Rejected as the problem, not an option.
- *Full BMAD-style agent ceremony* — disproportionate for a one-maintainer
  project.

**Lesson.** Same as RAG_System's ADR-001: the artifact is what lets work be
resumed by someone — including future-you — who wasn't there when the
decision was made. The tell that you need it is rewriting something because
you don't trust your own past reasoning.

---

## ADR-002: Sequence Phase 0 by recoverability

**Status:** Accepted · **Date:** 2026-07-19 · **Refs:** STORY-000…005, M6, DEV-2

**Context.** Phase 0 was first sharded from the audit snapshot as: fix the
eval path → hygiene deletions → dependency manifest → fourcc fix. A cross-check
against the real tree found it unsafe as ordered. About 18 tracked files had
uncommitted changes or deletions. The entire HPO layer (`optimization/`,
`evaluation/`, `batch_runner.py`) was **untracked**, the index held phantom
`cctv_tracking_system/*` paths from a botched restructure, and `.pyc` files
were tracked. No Python environment existed, so every verification command
would fail at import. The hygiene story would have run `rm` on untracked files
(`run_plot_pareto.py`, `optimization/config.py`): no git history, no undo.

**Decision.** Re-sequence: STORY-000 (commit the drift, untrack junk, track
the real source) → STORY-003 (environment) → STORY-002 (deletions) → STORY-005
(test fixture) → STORY-004 (fourcc fix, verified statically; its runtime check
deferred to the Phase-1 story that made `main.py` importable, STORY-007).

**Consequences.**

- *Pros:* every deletion ran on a committed baseline. The three dead modules
  went via `git rm`, recoverable, because STORY-000 had tracked them first.
  Each later story's verification had an environment to run in.
- *Cons:* one extra story, and files committed only to be deleted a story
  later now sit in history.

**Alternatives considered.**

- *Run the stories as written* — irreversible deletions, on top of drift that
  made any diff unreviewable.
- *Delete the untracked junk first, commit after* — the same irreversibility,
  one step earlier.

**Lesson.** Order destructive work by reversibility: make a thing recoverable
before you make it gone. An untracked file plus `rm` has no undo — the same
reason a backup is taken before a migration, not after.

---

## ADR-003: Re-validate every story against HEAD before implementing

**Status:** Accepted · **Date:** 2026-07-19 · **Refs:** WORKFLOW Stage C Rule 0

**Context.** Two failures on the same day. Stories written from the audit
described a tree that had moved (ADR-002). And a reviewer session read the
STORY-001 fix — made minutes earlier by the implementing session, still
uncommitted — as "pre-implemented drift", nearly recording real work as work
nobody did. The session-start "git status: clean" snapshot was also wrong: the
tree had about 18 changed files.

**Decision.** Stage C Rule 0: before implementing, read every file the story
names, run `git status` fresh, and confirm the problem still exists at HEAD; if
the story is done or has drifted, stop and report. Reviewers check whether the
current session made a change before calling it drift. A cached git snapshot is
never evidence.

**Consequences.**

- *Pros:* a few read-only commands per story. It has caught real drift since —
  a fix committed in one commit and refined in the next, a story's stale
  verification block.
- *Cons:* none worth naming; the cost is seconds.

**Alternatives considered.**

- *Trust the story text* — it is a snapshot of the tree on the day it was
  written.
- *Rewrite stories at dispatch time* — heavier, and still a snapshot.

**Lesson.** A plan describes the world as it was when the plan was written.
Check that the bug still reproduces before fixing it, and remember that "it
was already like this" may mean "I did this an hour ago".

---

## ADR-004: Large artifacts live outside git; weights download on first use

**Status:** Accepted · **Date:** 2026-07-19 · **Refs:** STORY-000, M6, NFR-REP-4/5, SEC-1

**Context.** `yolov8m.pt` (52 MB) was tracked as a raw blob; `yolov8l.pt`
(84 MB), a 212 MB sample video and a 296 MB output video sat untracked. A
`.gitattributes` routed `*.mp4`/`*.pt` to Git LFS. GitHub rejects any blob over
100 MB, LFS storage is billed, and the SRS wants weights fetched rather than
committed (NFR-REP-4) and large data outside git (NFR-REP-5).

**Decision** (operator, 2026-07-19). Untrack `yolov8m.pt`. Gitignore `*.pt`,
`sample_videos/`, `datasets/`, `results/` and `result/`. Ultralytics downloads
weights on first use; datasets stay local (DVC or documented storage later,
NFR-REP-5). Old blobs stay in history; purging them (`git filter-repo`, DEV-2)
is a separate, operator-approved task. One exception: tiny fixtures in
`tests/data/` go to plain git (ADR-008).

**Consequences.**

- *Pros:* a small clone, and no LFS bill. `.gitignore` now documents what the
  project treats as not-source.
- *Cons:* a fresh clone can't run the full sequence without fetching data.
  Weight checksums aren't recorded yet (that's the Phase-2 run manifest,
  NFR-REP-2/4).

**Alternatives considered.**

- *Keep everything in LFS* — about 350 MB of billed storage for files that
  either download themselves (weights) or belong in a data store (video). The
  SRS names DVC over LFS for multi-hundred-MB outputs.
- *Commit raw* — GitHub rejects the 212 MB and 296 MB files outright.

**Lesson.** Decide where each class of artifact lives — source, fixture, data,
weights, outputs — before the first commit, and let `.gitignore` say it.
RAG_System's ADR-002 adds the trap: `.gitignore` never untracks a file that is
already tracked; only `git rm --cached` does.

---

## ADR-005: The operator owns git history

**Status:** Accepted, tightened by ADR-016 · **Date:** 2026-07-19 · **Refs:** STORY-000

**Context.** While implementing STORY-000, the agent made three local commits.
The operator stopped it ("don't commit please, I will do it"), soft-reset them,
and committed the work themselves.

**Decision.** The agent never commits or pushes. From 2026-07-19 to 2026-10-11
it staged changes and handed over a commit message; ADR-016 tightened that to
"the operator runs every state-changing git command, staging included".

**Consequences.**

- *Pros:* every byte that enters history passes the operator, who is
  accountable for it — this is what made the push problem in ADR-006 visible
  before it shipped.
- *Cons:* the agent can't checkpoint its own work, and every handover must name
  its paths exactly, because the operator often has unrelated work in progress
  in the same tree.

**Alternatives considered.**

- *The agent commits after approval* — faster, but history then records what
  the agent decided to group, under the operator's name.

**Lesson.** Whoever is accountable for a history should be the one who writes
it.

---

## ADR-006: Squash unpushed commits to keep oversized blobs out of a push

**Status:** Accepted · **Date:** 2026-07-19 · **Refs:** STORY-000, `209c468`

**Context.** After the operator rebased, local `main` was three commits ahead of
`origin/main` (`a6a109e`). Two of those commits still carried junk that HEAD
had deleted. The rebased initial commit (`5bba31b`) held a raw 295 MB video, a
raw 212 MB video and the 50 MB weight in the phantom nested tree. The next
(`382de88`) turned the videos into LFS pointers. GitHub rejects any pushed blob
over 100 MB (GH001) whatever HEAD contains, and pushing the LFS commit would
have uploaded about 507 MB of billed storage for files deleted one commit
later.

**Decision.** `git reset --soft a6a109e`, then a single commit whose tree is
the clean HEAD, pushed as a fast-forward. No force-push, and nothing already
published was rewritten. The result is `209c468`.

**Consequences.**

- *Pros:* the oversized blobs never left the machine, and GitHub accepted the
  push.
- *Cons:* the three-commit split was lost — but two of the three were the junk
  commits DEV-2 wants out of history anyway.

**Alternatives considered.**

- *Push as-is* — rejected by GitHub.
- *`git filter-repo` over the unpushed range* — works, but is heavier than
  needed when the range is local-only.
- *Rewrite and force-push published history* — a separate, operator-approved
  task (DEV-2), never part of a routine story.

**Lesson.** A push ships history, not a snapshot: a file deleted at HEAD still
travels inside every commit that contains it. After any cleanup, look at the
blobs in `origin/main..HEAD` before pushing.

---

## ADR-007: uv only, with an interim exact-pinned `requirements.txt`

**Status:** Accepted (provisional — until Phase 2's `pyproject.toml` + `uv.lock`)
· **Date:** 2026-07-19 · **Refs:** STORY-003, C5, NFR-REP-1

**Context.** No dependency manifest existed (C5), and no environment either:
the tracked `.pyc` files showed CPython 3.10, then 3.11, both gone. System
Python was 3.14, newer than the ML wheels then supported. The operator
directive was uv, never conda or bare pip. The SRS puts the full
`pyproject.toml` + `uv.lock` migration in Phase 2.

**Decision.** `uv venv --python 3.12 .venv` plus `requirements.txt` with an
`==` pin for every direct dependency, each pin proven by a cold install into a
scratch venv. Torch is pinned without the `+cpu` tag, so the same file resolves
CUDA wheels on the GPU box (ADR-013); CPU hosts add
`--extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match`.
Two packages with no usable PyPI release are pinned to git commits:
motmetrics (ADR-009) and OpenAI CLIP (ADR-014). `yolox` is excluded, with the
reason in the file (C4, ADR-010).

**Consequences.**

- *Pros:* a fresh machine reaches a working environment with two documented
  commands, and every Phase-0 verification had something to run in.
- *Cons:* there is no lockfile, so transitive dependencies float. The CPU
  install also makes the PyTorch index a *general* index searched by
  best-match — exactly the setup RAG_System's ADR-005 shows can silently
  resolve non-torch packages from that index. The risk is bounded here,
  because every direct dependency is `==`-pinned and versions can't drift,
  but a package's *source* index still can. The fix comes with Phase 2's
  `pyproject.toml`: `[[tool.uv.index]] explicit = true` plus
  `[tool.uv.sources] torch = { index = "pytorch-cpu" }`.
- *Cons (noted 2026-10-11):* "resolves CUDA wheels on the GPU box" assumed a
  fresh environment. The GPU box is a hosted notebook (ADR-013) that ships its
  own CUDA torch, so the GPU recipe will likely keep the platform's torch and
  install everything else — to be settled by that recipe's story.

**Alternatives considered.**

- *`pyproject.toml` + `uv.lock` now* — Phase-2 work that would have blocked
  every Phase-0 verification on a restructure.
- *Freeze an existing environment* — none existed.
- *conda* — ruled out by the operator.

**Lesson.** An interim solution is fine when its weakness is named, bounded,
and scheduled for removal. And a custom package index is a question about
*which packages* it serves; the resolver's default answer — all of them — is
usually wrong.

---

## ADR-008: A 50-frame fixture in plain git, and a two-minute verification rule

**Status:** Accepted · **Date:** 2026-07-19 · **Refs:** STORY-005, STORY-006, TST-1

**Context.** STORY-001's verification as first written ran the full 3,315-frame,
213 MB MOT20-05 clip through YOLOv8-l on CPU — hours. A verification nobody
runs is not a verification.

**Decision.** `tests/data/tiny_clip.mp4` is the first 50 frames, re-encoded to
955 KB (ffmpeg, libx264, CRF 28). It is exempted from the `*.mp4` LFS rule by
`tests/data/*.mp4 -filter -diff -merge text=auto` in `.gitattributes`, and the
staged blob was checked to be the real 978 KB, not an LFS pointer.
`tests/data/tiny_clip_gt.txt` (396 KB) is the matching ground-truth slice,
frames 1–50 (STORY-006). WORKFLOW's rule: every verification command finishes
in about two minutes, against the fixture.

**Consequences.**

- *Pros:* the smoke test takes about 15 s, the tracker contract test seconds,
  the optimizer test about 2 s — cheap enough to run every story.
- *Cons:* the fixture is the densest crowd in MOT20, so it inherits the recall
  floor (ADR-012). It proves the mechanics work, not that quality is good.

**Alternatives considered.**

- *The full clip* — hours per check.
- *A synthetic video* — no real ground truth to score against.
- *The fixture in LFS* — a fetch step at clone time, billing, and CI friction,
  all for under 1 MB.

**Lesson.** Verification cost is a design parameter. Build the cheap check
before you need it — every later story inherits it.

---

## ADR-009: Real MOTA/IDF1 via motmetrics, proven against an identity oracle

**Status:** Accepted (provisional — the git pin goes when motmetrics releases a
NumPy-2 build) · **Date:** 2026-07-19 · **Refs:** STORY-006, C1, FR-EVAL-1, ML-1

**Context.** C1: the mock formula. FR-EVAL-1 names motmetrics or TrackEval.
PyPI's `motmetrics==1.4.0` calls `np.asfarray`, which NumPy 2 removed (we run
2.4.4). Ground truth had to come from somewhere: motchallenge.net timed out on
2026-07-19 and answered HTTP 410 Gone on 2026-10-11. The TrackEval data bundle
from RWTH Aachen, the lab behind MOTChallenge, carries MOT20-05's `gt.txt`.

**Decision.** `evaluation/mot_metrics.py` scores pedestrian rows only (conf 1,
class 1) at IoU 0.5, and accumulates only frames present in the tracker output,
so a prefix clip scores correctly against the full `gt.txt`.
`compute_mock_metrics` is deleted from the codebase. motmetrics is pinned to
upstream commit `e5ae766`, with a comment saying why. The ground truth was
checked twice: `seqinfo.ini` matches the video exactly (3,315 frames,
1654×1080, 25 fps), and the frame-1 GT boxes, drawn on fixture frame 1, sit on
the people. The metric code was checked once more: GT scored against itself
returns MOTA 1.0 and IDF1 1.0.

**Consequences.**

- *Pros:* the first honest numbers. They were damning — MOTA −0.004, IDF1
  0.000 on the fixture — and within the hour they exposed the DeepSORT box bug
  (ADR-011).
- *Cons:* a dependency pinned to a git commit rather than a release; revisit
  when a NumPy-2-compatible release ships.

**Alternatives considered.**

- *Pin NumPy below 2* — drags the whole stack backwards for one function.
- *Shim `np.asfarray` in application code* — a monkeypatch that outlives its
  reason.
- *TrackEval only* — its packaging is fragile, which is why HOTA got its own
  story (STORY-010).

**Lesson.** Test a metric implementation on an input whose answer you know —
ground truth scored against itself must be perfect. And the first real
measurement doubles as a bug detector: the mock hadn't only faked the numbers,
it had hidden a broken tracker.

---

## ADR-010: ByteTrack from roboflow's `trackers` package; local package renamed to `tracking/`

**Status:** Accepted · **Date:** 2026-07-20 · **Refs:** STORY-007, C4, H2, FR-TRK-1..3

**Context.** The yolox-based ByteTrack wrapper had never worked: its
constructor and `update()` signature match no YOLOX release (C4). FR-TRK-2
names supervision's ByteTrack, but supervision 0.29.1 deprecates it ("deprecated
since v0.28.0. It will be removed in v0.30.0"); Roboflow moved tracking into the
dedicated `trackers` package, by the same maintainers. And the repo's own
top-level `trackers/` directory shadowed that pip package. Separately, the demo
ran ByteTrack while the evaluator ran DeepSORT (H2).

**Decision** (operator-approved, 2026-07-20). A ByteTrack adapter over
`trackers.ByteTrackTracker`, keeping `supervision` for its `Detections` type.
Mapping: `conf_thresh` → `track_activation_threshold` and
`high_conf_det_threshold`; `iou_thresh` → `minimum_iou_threshold`. The local
package was renamed `trackers/` → `tracking/` with `git mv`. One factory,
`make_tracker(name, **kwargs)`, builds the tracker for both `main.py` and
`evaluate_pipeline` — the interim fix for H2; the single `Pipeline` object is
Phase 2.

**Consequences.**

- *Pros:* a maintained API, and `main.py` ran end to end for the first time
  ever (STORY-004's deferred runtime check: 50 frames written and re-read).
  BoT-SORT, OC-SORT and SORT sit behind the same API, future experiment
  dimensions at almost no cost.
- *Cons:* one more dependency, and a deviation from the SRS's wording. It
  keeps the SRS's intent — "a maintained implementation instead of vendoring
  YOLOX". This was the first use of the "incumbent stack isn't sacred, propose
  then switch" rule (CLAUDE.md).

**Alternatives considered.**

- *Pin `supervision<0.30`* — a migration guaranteed at the next minor release.
- *Vendor YOLOX* — how C4 happened.
- *Keep `trackers/` and juggle `sys.path`* — fragile, and it breaks whenever
  import order changes.

**Lesson.** A top-level package name claims a global namespace; a collision
with a PyPI name stays invisible until someone installs that package. And when
a spec names a library that is being deprecated, follow the spec's intent and
record the deviation.

---

## ADR-011: Assert properties a broken system cannot satisfy, not ranges

**Status:** Accepted · **Date:** 2026-07-20 · **Refs:** STORY-007, `406adbe`, TST-1, TST-4

**Context.** STORY-006's first real scores showed IDF1 = 0.000. The cause:
`deepsort_wrapper.py` passed boxes to `deep_sort_realtime` as xyxy, but the
library expects `[left, top, width, height]`. An 87×188 px detection came back
as a 927×1045 px track. Every DeepSORT result the project had ever produced was
geometrically wrong; the mock metrics had hidden it, and the smoke test's range
checks (MOTA ∈ [−1, 1], IDF1 ∈ [0, 1]) passed anyway. The 2026-07-20 review put
it plainly: a totally broken tracker would still pass.

**Decision.** Two checks that a broken system cannot satisfy:

1. **Contract test** (`tests/tracker_contract_test.py`): fed the same
   detection for a few frames, each tracker must return a confirmed track whose
   box has IoU > 0.5 with that detection. Both must return `[]` for empty input,
   given as a list or as an array. After the fix: ByteTrack 1.00, DeepSORT 0.99.
2. **Smoke tripwire:** IDF1 > 0. Box-format corruption zeroes it exactly; the
   genuine recall floor still leaves a small positive value.

**Consequences.**

- *Pros:* this class of bug now fails in seconds.
- *Cons:* IDF1 > 0 only catches total corruption. Real quality gates need a
  sequence where the metrics have range (ADR-012) and, later, golden numbers
  (TST-7).

**Alternatives considered.**

- *Shape checks* (four finite numbers per box) — the corrupted boxes pass.
- *Golden-number tests now* — brittle while data and detector are still
  changing; that is TST-7's job, later.

**Lesson.** A range describes a type, not correctness. Ask what property a
broken system cannot have, then assert that.

---

## ADR-012: Don't optimize a metric that has no dynamic range

**Status:** Accepted (provisional — until a sparser sequence is in place) ·
**Date:** 2026-07-20 · **Refs:** `406adbe`, STORY-011, STORY-013, M5, ML-4

**Context.** The operator measured stock YOLOv8-l's recall on MOT20-05 frame 1
(about 214 people in ground truth): 0.9 % at 320 px, 1.4 % at 640, 4.2 % at
960. With recall that low, MOTA and IDF1 sit near zero whatever the tracker or
config, so HPO would hill-climb noise. On top of that, `skip_interval` made
trackers return no tracks on skipped frames (M5), so the search space explored
configs that tank MOTA by construction.

**Decision** (operator, 2026-07-20: "assertions now, sparser sequence later").
The smoke test asserts IDF1 > 0 (ADR-011). `skip_interval` leaves the search
space until STORY-013 implements coasting. STORY-011, and any HPO run whose
metrics matter, waits for a sparser MOTChallenge sequence (MOT17-04 or -09).
MOT20-05 is re-checked at full resolution on the GPU box. A CrowdHuman-trained
detector was considered and deferred.

**Consequences.**

- *Pros:* no optimizer budget spent on noise.
- *Cons:* Phase 1's sanity run is blocked on data. motchallenge.net is gone
  (HTTP 410, 2026-10-11); the TrackEval bundle has MOT17's ground truth but no
  images, so the images need another source.

**Alternatives considered.**

- *Tune on MOT20-05 anyway* — the optimizer would "improve" noise.
- *A crowd-trained detector now* — weight provenance and validation work
  before any HPO story could run.

**Lesson.** Before optimizing a metric, measure its dynamic range on your data.
An optimizer has no idea whether it is climbing signal or noise.

---

## ADR-013: Device is configuration, never code

**Status:** Accepted · **Date:** 2026-07-20 · **Refs:** STORY-008, FR-DET-2, FR-CLI-2

**Context.** The development host is CPU-only; deployment and full-scale
experiments run on a GPU (operator, 2026-07-19) — specifically a hosted
notebook GPU on Colab, Kaggle or SageMaker (clarified 2026-10-11; "the GPU box"
elsewhere in these docs means one of those). The code assumed one or the other. `evaluate_pipeline` defaulted to `"cuda"`, and the optimizers never
passed a device, so any standalone optimizer run crashed on CPU. The DeepSORT
wrapper stored `device` but never passed it to its embedder. `batch_runner.py`
chose a device by commenting one of two assignments in or out.

**Decision.** Device threads from `batch_runner` through the optimizers and
`evaluate_pipeline` to the tracker and its embedder. `None` means auto-detect
(`"cuda"` if available, else `"cpu"`); `DEVICE` in the environment overrides
it. DeepSORT derives `embedder_gpu` and `half` from it. The dependency pins
resolve on both kinds of host (ADR-007).

**Consequences.**

- *Pros:* the same code runs on both hosts, and standalone optimizer runs work
  on CPU.
- *Cons:* GPU-only behaviour, such as half-precision embeddings, has never run
  here; its first real test is the first GPU run.

**Alternatives considered.**

- *A per-host constant* — that was the bug.
- *A CLI flag only* — Phase 2's Typer CLI; the environment variable is the
  interim.

**Lesson.** A fact about one environment baked into a default is a bug that
fires only in the other environment — usually the one you can't easily debug.

---

## ADR-014: The embedder matrix holds only embedders that install

**Status:** Accepted (provisional — revisit torchreid on the GPU box) ·
**Date:** 2026-07-20 · **Refs:** STORY-008, C3, FR-TRK-4, FR-OPT-5

**Context.** C3: `batch_runner.py` looped over
`["mobilenetv2", "shufflenetv2", "resnet"]`, but those values only named result
folders — they never reached the tracker. The "3×3 matrix" was 1×3 with fake
labels. `deep_sort_realtime` 1.3.2 actually accepts `mobilenet`, `torchreid`
and `clip_*`. PyPI's `torchreid` 0.2.5 lacks the `torchreid.utils` import path
that `deep_sort_realtime` uses, even after chasing `gdown` and `tensorboard`;
building upstream from git needed build-time NumPy, then Cython, with no end in
sight. OpenAI's CLIP installs from git and builds a working `Clip_Embedder`.

**Decision** (operator-approved). The matrix is `["mobilenet", "clip_ViT-B/32"]`
crossed with the three optimizers. torchreid is dropped, to be revisited on the
GPU box. CLIP is pinned to commit `d05afc4`; its weights download on first use
and are gitignored. Embedder names map to filesystem-safe slugs for result
paths (`embedder_slug()`), because `clip_ViT-B/32` contains a `/`.

**Consequences.**

- *Pros:* the matrix is real — 2×3 instead of a fictional 3×3 — and the
  plumbing is checked by introspecting the embedder object's class, not by
  trusting the label.
- *Cons:* fewer embedder families, and CLIP is a heavy first-use download.

**Alternatives considered.**

- *Keep the old labels* — that is C3.
- *Fight torchreid's build chain* — no end in sight on Python 3.12.
- *Vendor torchreid* — a new maintenance burden to keep one option.

**Lesson.** An experiment dimension that never reaches the system under test
is a label, not a variable. Verify the plumbing by inspecting the object the
system actually built, not the name in the log.

---

## ADR-015: Pareto dominance with a single-leader rule, memoized and seeded

**Status:** Accepted (provisional — a Pareto archive with hypervolume, ML-3,
replaces the single-leader rule in Phase 3) · **Date:** 2026-07-20 ·
**Refs:** STORY-009, `7116171`, H4, FR-OPT-1/4/6, NFR-PERF-1

**Context.** H4. QPSO and MOPSO compared `(mota, idf1, 1/fps)` tuples with `>`:
lexicographic rather than Pareto, and inverted on FPS, so the *slower* config
won ties. NSGA-II used `1/fps` with weight −1.0 — the right direction through a
double negation. MOPSO re-evaluated every personal best every generation,
doubling the model cost. Nothing was memoized or seeded. And because
`flatten_config_space` collapses continuous ranges to their endpoints (M3), the
whole quantized space is only 24 configs, so repeat evaluations were the norm.

**Decision.** `optimization/objectives.py` is the one home for scoring:
`dominates()` (maximize all of MOTA, IDF1 and FPS); `replaces_best()` (a leader
is replaced only by a point that dominates it, and an incomparable point keeps
the incumbent — documented, not lexicographic); `MemoizedObjective`, keyed by
the sorted quantized config, which logs only real evaluations; and `seed_all()`
for `random`, NumPy and torch. NSGA-II's weights become `(1, 1, 1)` on raw FPS.
MOPSO caches personal-best scores. Each optimizer accepts an injectable
objective, so `tests/optimizer_test.py` runs in about 2 s with no model.

**Consequences.**

- *Pros:* scoring points the right way and costs O(particles) per generation;
  runs are reproducible (same seed, same evaluation sequence — tested); 48
  particle visits made 6 real evaluations in the test.
- *Cons:* the single-leader rule is order-dependent — the first incomparable
  point to arrive stays leader. And with only 24 distinct configs the swarms
  converge almost at once; widening the space is M3's schema fix (Phase 3).

**Alternatives considered.**

- *Scalarize with a weighted sum* — FPS (about 5) and MOTA (≤ 1) live on
  different scales; without normalization the weights would be arbitrary.
- *A full Pareto archive now* — Phase 3 scope (ML-3).
- *Keep lexicographic order, just un-invert FPS* — still not Pareto, still
  violating FR-OPT-1.

**Lesson.** A comparison operator is a policy decision. `>` on tuples quietly
means "lexicographic", and nobody chose that. When you compare compound values,
name the order you mean and test it — including the case that once went wrong
(here, faster must beat slower on a tie).

---

## ADR-016: One rulebook across the maintainer's projects

**Status:** Accepted · **Date:** 2026-10-11 · **Refs:** `CLAUDE.md`, ADR-005

**Context.** The maintainer runs two projects through the same spec-driven loop.
RAG_System had grown a `CLAUDE.md` that every session loads, Conventional
Commits and Conventional Branch (since 2026-10-01), a no-AI-attribution rule,
one PR per story, phase-exit tags, model routing, and an ADR log. Here, the
equivalent rules were scattered across `WORKFLOW.md`, story files and an
agent's per-session memory — and that memory isn't in the repo, so a fresh
session or a different model never saw it.

**Decision.** Adopt RAG_System's rules here, adapted to this project, in a
root `CLAUDE.md` plus this file:

- Conventional Commits and Conventional Branch, with story IDs as trailers
  (`Refs: STORY-0NN, …`). Commits before 2026-10-11 predate this and stay as
  they are.
- The operator runs every state-changing git command, staging included — this
  tightens ADR-005. Claude hands over an exact recipe that names its paths.
- No AI attribution, in commits or PR bodies.
- One PR per story.
- A git tag at each phase exit, starting with `v0.1` for Phase 0.
- Model routing per story.

RAG-only rules — LangChain, Ollama, the `corpus/` directory — were left out.

**Consequences.**

- *Pros:* one set of habits across both projects, kept in files every session
  loads rather than in anyone's memory.
- *Cons:* until CI lands (Phase 2, DEV-1), a PR is a review surface only — no
  gate runs on it. Phase 0's exit commit (`9a00c82`) predates the tagging rule
  and is untagged; a retroactive `v0.1` is the operator's call.
- *Lifetime (operator, 2026-10-11):* `CLAUDE.md` is published while the project
  is in progress and removed from the remote at completion. A deleting commit
  only hides it from the current tree, so to remove it from history too, strip
  it in the same `git filter-repo` rewrite that DEV-2 plans for the old
  weight and video blobs (one force-push for both). At that point, update the
  references to it in `docs/WORKFLOW.md` and this file.

**Alternatives considered.**

- *Keep project-local rules* — the two projects' habits drift, and each
  session relearns which rules apply where.
- *Copy RAG_System's CLAUDE.md verbatim* — its stack-specific rules don't
  apply here, and a rule that doesn't apply teaches readers to skim the ones
  that do.

**Lesson.** A process rule that lives in a chat transcript or an agent's memory
is invisible to the next session. Put it where every session loads it.

---

## How to extend this file

When a decision of this weight is made — choosing a technology, reversing an
earlier decision, accepting a tradeoff a future session should know was
deliberate — add a new `ADR-0NN` entry at the end (never renumber) and add it to
the index. If a later decision replaces an earlier one, mark the old entry
`Superseded by ADR-0NN` instead of deleting it: a decision that looks wrong in
hindsight, with its original reasoning intact, is worth more to future-you than
a clean history with no trace of it.
