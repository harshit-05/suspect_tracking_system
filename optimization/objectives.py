"""Shared optimizer objective machinery (STORY-009, closes audit H4).

Objectives are the vector (MOTA, IDF1, FPS) — **all maximized**. This module is
the single home for:
  - genuine Pareto `dominates()` (replaces the lexicographic tuple `>` compares
    that also inverted FPS, so slower configs won ties);
  - a memoized objective wrapper (never evaluate a quantized config twice in a
    run — FR-OPT-4, NFR-PERF-1);
  - `seed_all()` for reproducible runs (FR-OPT-6).

A full Pareto archive + hypervolume leader selection is Phase 3 (ML-3); the
single-leader rule here is `replaces_best()`.
"""

import random

import numpy as np


def dominates(a, b):
    """True iff objective vector `a` Pareto-dominates `b` (maximize every
    component): `a` is >= `b` in all components and strictly > in at least one.
    """
    a, b = tuple(a), tuple(b)
    return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))


def replaces_best(new_score, best_score):
    """Single-leader update rule for the swarm optimizers: adopt `new_score`
    only if there is no incumbent yet or it strictly dominates the incumbent.
    Incomparable points keep the incumbent — a deterministic, documented
    tie-break, explicitly NOT a lexicographic fallback.
    """
    return best_score is None or dominates(new_score, best_score)


def config_key(config):
    """Order-independent hashable key for a quantized config dict."""
    return tuple(sorted(config.items()))


class MemoizedObjective:
    """Wraps an objective `fn(config) -> (mota, idf1, fps)` and caches results
    by quantized-config key, so a config scored once in a run is never scored
    again (FR-OPT-4). `.evaluations` counts real (cache-miss) calls only.
    """

    def __init__(self, fn):
        self._fn = fn
        self._cache = {}
        self.evaluations = 0

    def __call__(self, config):
        key = config_key(config)
        if key not in self._cache:
            self.evaluations += 1
            self._cache[key] = tuple(self._fn(config))
        return self._cache[key]

    def reset(self):
        self._cache.clear()
        self.evaluations = 0


def seed_all(seed):
    """Seed `random`, `numpy`, and `torch` (if importable) from one value so a
    run is reproducible on the same hardware (FR-OPT-6).
    """
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
