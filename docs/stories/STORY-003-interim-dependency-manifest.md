---
id: STORY-003
title: Interim dependency manifest + pinned Python environment
phase: 0
priority: P0
srs_refs: [C5, "NFR-REP-1 (partial — full uv/pyproject.toml migration is Phase 2)"]
status: review   # implemented 2026-07-19: Python 3.12.13 venv via uv, 11 deps pinned, cold-install proven, yolox excluded per C4
depends_on: [STORY-000]
---

## Context

Verified 2026-07-19: **no working Python environment for this project exists anywhere on
the machine.** System python is 3.14.6 with essentially nothing installed (only `tqdm`
of the ~11 required packages). No conda, no venv under the project tree. The committed
`.pyc` files show the code historically ran under CPython 3.10 and later 3.11 — both
environments are gone.

Consequences this story must handle:

- There is **no existing environment to freeze a manifest from** — version constraints
  must be hand-authored and then proven by a clean install.
- Python 3.14 is almost certainly too new for `torch`/`ultralytics` wheels. The
  environment must pin **Python 3.11 or 3.12** explicitly.
- `yolox` (imported by `trackers/bytetrack_wrapper.py`) is known-problematic: audit
  finding C4 says the wrapper doesn't match stock YOLOX's API anyway, and YOLOX is
  awkward to pip-install. **Do not fight this here** — the Phase-1 fix replaces it with
  the `supervision` library (SRS FR-TRK-2).

Every other story's verification command depends on this environment existing, which is
why this story runs immediately after STORY-000.

## Acceptance Criteria

- [ ] `requirements.txt` at repo root with hand-authored, tested version constraints for:
      `ultralytics`, `torch`, `torchvision`, `opencv-python`, `numpy`,
      `deep_sort_realtime`, `deap`, `matplotlib`, `tqdm`, `pyyaml`, `natsort`.
- [ ] **`yolox` deliberately excluded**, with a comment block in `requirements.txt`
      explaining: known-broken wrapper (C4), replacement by `supervision` scheduled for
      Phase 1. Consequently `trackers/bytetrack_wrapper.py` (and `main.py`, which
      imports it) will not import yet — this is accepted and documented, not hidden.
- [ ] Required Python version (3.11 or 3.12 — whichever is installable on this Arch
      system) stated at the top of `requirements.txt` and in the README setup section.
- [ ] A project venv exists (`.venv/`, gitignored by STORY-000's `.gitignore`) created
      with **uv** (`uv venv --python 3.12 .venv`), with
      `uv pip install -r requirements.txt` completing cleanly. All environment
      management goes through uv — no bare `pip`, no conda (operator directive,
      2026-07-19).
- [ ] README gains a minimal Setup section (≤10 lines): python version, uv venv
      creation, `uv pip install` command. Full README rewrite stays Phase 3 (DEV-5).

## Out of Scope

- `pyproject.toml` / `uv` migration (Phase 2, NFR-REP-1 full).
- Fixing the ByteTrack wrapper or installing yolox (Phase 1, C4).
- Running the full pipeline — import-level verification only; runtime smoke comes with
  STORY-005's fixture.

## Suggested Approach

uv is installed (`~/.local/bin/uv`, verified 2026-07-19) — use it for everything:
`uv python install 3.12` (uv manages its own Python builds; no system packages needed),
then `uv venv --python 3.12 .venv` and `uv pip install -r requirements.txt`. Start
constraints loose-but-bounded (e.g. `ultralytics>=8.2,<9`, `torch>=2.3,<3` CPU wheels),
install, and tighten to the resolved versions with `==` pins (from `uv pip freeze`)
once the import test passes.

If torch wheel resolution turns painful (CUDA vs CPU index), stop and ask the operator
which they want rather than guessing — this machine may or may not have a usable GPU.

## Verification

```bash
.venv/bin/python -c "
import ultralytics, torch, cv2, numpy, deep_sort_realtime, deap, yaml, natsort, matplotlib, tqdm
print('core deps OK:', torch.__version__, cv2.__version__)
"
# deepsort-side pipeline must import (bytetrack side is documented-broken until Phase 1)
.venv/bin/python -c "from evaluation.evaluation import evaluate_pipeline; print('evaluation imports OK')"
```
