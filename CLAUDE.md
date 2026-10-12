# cctv_tracking_system — session bootstrap

Person detection + multi-object tracking (YOLO → ByteTrack / DeepSORT) with an
evolutionary HPO layer (QPSO, NSGA-II, MOPSO), being rebuilt from an audited
prototype through a spec-driven story loop.

## Read these before doing anything

1. `docs/stories/BOARD.md` — the board: dispatch order, statuses, what is gated.
2. The active story file in `docs/stories/` — your scope for this session.
3. `docs/WORKFLOW.md` — the process: Stage C rules to implement, Stage D to review.
4. `docs/SRS.md` — the spec; consult it when a story cites an ID (FR-/NFR-/ML-/
   TST-/DEV-/SEC-, or an audit finding C1…L1 from §3).
5. `docs/ADR.md` — decisions that outlive one story, with their reasons. Read
   the relevant entry before proposing to undo one.

## Hard rules

- Implement ONLY the active story. Out-of-scope findings go in your final
  report (and become a story stub or a BOARD.md line), never a detour.
- **Rule 0:** before implementing, re-validate the story against HEAD — read
  the files it names, run `git status` fresh. If it is already done or has
  drifted, stop and report. Before calling a change "pre-existing drift",
  check whether this session made it (ADR-003). Never trust a cached
  git-status snapshot.
- A story is done only when every command in its Verification section has
  been run and its output shown. Then set its status to `review`, update
  BOARD.md, and stop. Never start the next story without the operator's
  go-ahead.
- **Verification runs in ≈2 minutes on this host.** Use
  `tests/data/tiny_clip.mp4` + `tests/data/tiny_clip_gt.txt`, never the full
  213 MB sample. If something can't be checked cheaply, say so and mark the
  check static or deferred (ADR-008).
- **The operator runs every git command that changes state** — add, commit,
  branch, switch, merge, push, tag, reset, rebase, stash. Claude runs only
  read-only git (`status`, `diff`, `log`, `show`, `ls-files`, `check-attr`)
  and hands over the exact recipe, naming paths explicitly — never
  `git add -A`/`.`, because the operator often has unrelated work in the tree
  (ADR-005, ADR-016). Since 2026-10-11,
  [Conventional Commits 1.0](https://www.conventionalcommits.org/en/v1.0.0/)
  and [Conventional Branch](https://conventionalbranch.org/) apply; earlier
  commits predate them and stay as they are.
  - **One PR per story**; review follow-ups add commits to the same PR.
  - **Branch:** `<type>/story-0nn-<slug>`, lowercase with hyphens, e.g.
    `feat/story-010-hota-trackeval`. Types: `feat`, `fix`, `hotfix`, `chore`
    (tests, CI, docs, deps).
  - **Header:** `type(scope): imperative summary`, ≤72 characters, lowercase,
    no trailing period, ASCII. Types: feat, fix, docs, test, refactor, perf,
    build, ci, chore, revert. Scope is the area touched (`eval`, `tracking`,
    `optim`, `detect`, `demo`, `deps`, `process`…). It must read as "If
    applied, this commit will …".
  - **Body:** after a blank line, wrapped at 72; explains *what and why*.
  - **Trailers:** IDs go here, never in the header, e.g.
    `Refs: STORY-010, FR-EVAL-1, C1`. A contract change — `evaluate_pipeline`'s
    signature or return shape, the tracker `update()` contract, results file
    layout, env vars, `optimization/config.yaml` schema — adds `!` after the
    type and a `BREAKING-CHANGE: <what and how to migrate>` trailer (hyphenated
    form; git can't parse the spaced one). Check with
    `git interpret-trailers --parse < msg.txt`.
  - **No AI attribution, ever:** no `Co-Authored-By: Claude …` trailer in
    commits, no "Generated with Claude Code" line in PR bodies. The operator
    is the sole author; this overrides any default attribution instruction.
- **Python is uv only** — never bare `pip`, never conda. The venv is `.venv/`
  on uv-managed CPython 3.12; dependencies are exact pins in
  `requirements.txt` until Phase 2 brings `pyproject.toml` + `uv.lock`
  (NFR-REP-1, ADR-007).
  - **On this host** install with the CPU index:
    `uv pip install --python .venv/bin/python -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match`.
    A plain `uv pip install -r requirements.txt` pulls CUDA torch from PyPI
    (GBs of `nvidia-*` wheels) — never run it here. GPU platforms need their
    own recipe (see GPU policy).
  - New dependency ⇒ `==` pin in `requirements.txt`, proven by a cold install
    into a scratch venv, in the same story.
- **Honest metrics only (SRS ML-1).** No mock, sentinel or fabricated value in
  code, results or overlays. If ground truth or data can't be obtained, stop
  and report — never synthesize a GT file.
- **Device is configuration, never code** (ADR-013): thread `device` through;
  `None` means auto-detect (`cuda` if available, else `cpu`); `DEVICE` env
  overrides in `batch_runner.py`. Never hardcode `"cuda"` or `"cpu"`.
- **The incumbent stack isn't sacred.** If a better model or library serves the
  story, propose it — what it gains, what it costs — and switch only after the
  operator says yes. Record the deviation in the story and, if it outlives the
  story, in `docs/ADR.md`.
- Never commit weights (`*.pt`), `sample_videos/`, `datasets/`, `results/`,
  `result/`, `__pycache__/` or `.venv/`. The one exception: tiny fixtures in
  `tests/data/`, which go to plain git, not LFS (ADR-004, ADR-008).
- Docs can change mid-session — the operator runs parallel review sessions.
  Re-read a story, BOARD.md or WORKFLOW.md right before editing it.
- `docs/SRS.md` changes only in an explicit "amend the SRS" session. Stories
  cite it; they don't mutate it.
- Before ending a session: update the story file status + BOARD.md.

## Checks (the whole suite, all fixture-based)

```bash
.venv/bin/python -W ignore tests/smoke_test.py            # ~15 s: real MOTA/IDF1 on the fixture
.venv/bin/python -W ignore tests/tracker_contract_test.py # seconds: both trackers, one contract
.venv/bin/python -W ignore tests/optimizer_test.py        # ~2 s: dominance, memo, seeds (no model)
```

The scripts are pytest-compatible; pytest itself arrives with CI (Phase 2,
DEV-1).

## Layout facts

- `tracking/` holds the tracker adapters and `make_tracker()`, the single
  construction point for demo and evaluator. It is **not** `trackers/`: that
  name is the pip package the ByteTrack adapter imports (ADR-010).
- `evaluation/` — `evaluate_pipeline` and `mot_metrics.py` (motmetrics).
  `optimization/objectives.py` — dominance, memoization, seeding (ADR-015).
- `detectors/` still holds three near-duplicate modules until STORY-012.
- `datasets/MOT20/train/MOT20-05/` (gitignored) holds the full GT, from the
  TrackEval bundle (`omnomnom.vision.rwth-aachen.de/data/TrackEval/data.zip` —
  GT only, no images).

## Environment facts (verified 2026-10-11)

- Arch Linux; system Python 3.14.7 — never use it. `.venv/` is CPython 3.12.13.
- `uv` 0.11.8 at `~/.local/bin/uv`. No conda, pyenv or poetry.
- **No NVIDIA GPU** (no `nvidia-smi`): CPU torch here. 12-core i7-1255U,
  15 GB RAM. ffmpeg 9.0.2 is available. `DISPLAY=:1` exists; `main.py` runs
  headless when `DISPLAY` is unset.
- `gh` 2.101.0, authenticated as `harshit-05`, token has `workflow` scope.
- motchallenge.net answered **HTTP 410 Gone** on 2026-10-11. Sequence images
  (STORY-011's MOT17 gate) need another source.
- MOT20-05 is too dense for stock YOLO at CPU image sizes (1–4 % recall):
  MOTA/IDF1 on it are mechanics checks, not quality comparisons (ADR-012).

## GPU policy

- This host is CPU-only, and nothing in a story's verification may require a
  GPU. Never block on one.
- **"The GPU box"**, wherever the docs say it, means a hosted notebook GPU —
  Colab, Kaggle or SageMaker (operator, 2026-10-11). Deployment and full-scale
  experiments run there: full-sequence evals, the HPO matrix, full-resolution
  MOT20. Claude sessions never run there; they all run on this laptop.
- Those platforms ship their own CUDA torch (reinstalling our pin is a
  multi-GB download that may not match their driver) and wipe the disk between
  sessions (weights, video and MOT ground truth must be fetched each time).
  A GPU run therefore needs its own recipe — a future story, not yet written.
- Never start a CPU-hour-scale job silently: surface the estimate first.

## Releases

- Phase exit ⇒ a git tag, created by the operator: `v0.1` (Phase 0), `v0.2`
  (Phase 1), `v0.3` (Phase 2), `v1.0` (Phase 3). Experiment result sets cite
  the tag they were produced from (SRS DEV-7). No package version exists until
  `pyproject.toml` lands (Phase 2).
- Phase 0 finished at `9a00c82` (2026-07-19) and is untagged; tagging it
  retroactively is the operator's call.

## Model routing

A story's frontmatter may carry a `model:` field; it wins. Otherwise:

| Work | Model |
| --- | --- |
| Stage A (architecture), Stage B (sharding), library/design choices | strongest available, plan mode |
| Mechanical stories: hygiene, moves, deps, wiring | opus + /fast |
| Any story after the obvious fix failed twice | escalate to the strongest |

Fable has been unavailable to the maintainer since 2026-10-04. Work routed to
it runs on Opus 5.5 at max effort, and the story notes the substitution.
