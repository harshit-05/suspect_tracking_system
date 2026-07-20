# Optimizer scoring tests (STORY-009, SRS TST-3). Model-free: a synthetic
# objective stands in for evaluate_pipeline, so this runs in well under a
# second and needs no video, GT, or weights. Covers the three things audit H4
# broke: Pareto dominance (incl. the inverted-FPS regression), memoization,
# and seed reproducibility.

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from optimization.objectives import (  # noqa: E402
    dominates, replaces_best, MemoizedObjective,
)
from optimization.qpso_optimizer import qpso_optimize  # noqa: E402
from optimization.mopso_optimizer import run_mopso  # noqa: E402

# Tiny discrete space: 3 × 3 = 9 distinct quantized configs.
BOUNDS = {"a": [0, 2], "b": [0, 2]}
ALLOWED = {"a": [0, 1, 2], "b": [0, 1, 2]}


def synthetic(config):
    """Deterministic (mota, idf1, fps) from a config. FPS decreases with 'a',
    so higher 'a' trades throughput — a real Pareto surface, not noise."""
    a, b = config["a"], config["b"]
    return (a / 2.0, b / 2.0, float(3 - a))


def test_dominance_truth_table():
    # All objectives maximized: (MOTA, IDF1, FPS).
    assert dominates((0.6, 0.6, 10), (0.5, 0.5, 5))       # better on all
    assert not dominates((0.5, 0.5, 5), (0.5, 0.5, 5))    # equal, not strict
    assert not dominates((0.6, 0.5, 5), (0.5, 0.6, 10))   # incomparable
    # THE regression: equal MOTA+IDF1, faster must dominate slower. The old
    # lexicographic (mota, idf1, 1/fps) compare inverted this — slower won.
    assert dominates((0.5, 0.5, 10), (0.5, 0.5, 5)), "faster must beat slower"
    assert not dominates((0.5, 0.5, 5), (0.5, 0.5, 10)), "slower must NOT win"
    # replaces_best: no incumbent -> adopt; incomparable -> keep incumbent.
    assert replaces_best((0.5, 0.5, 5), None)
    assert not replaces_best((0.6, 0.5, 5), (0.5, 0.6, 10))
    print("dominance OK: truth table incl. inverted-FPS regression")


def test_memoization_counts_only_distinct_configs():
    calls = []
    memo = MemoizedObjective(lambda c: (calls.append(config_tuple(c)), synthetic(c))[1])
    for a in (0, 1, 0, 1, 0):        # 5 calls, 2 distinct configs
        memo({"a": a, "b": 0})
    assert memo.evaluations == 2, memo.evaluations
    assert len(calls) == 2, "wrapped fn called on cache hits"
    print(f"memoization OK: 5 requests -> {memo.evaluations} real evaluations")


def config_tuple(c):
    return tuple(sorted(c.items()))


def test_qpso_memoized_far_below_visit_count():
    seen = []
    obj = lambda c: (seen.append(1), synthetic(c))[1]  # noqa: E731
    qpso_optimize(BOUNDS, ALLOWED, num_particles=6, generations=8,
                  seed=1, objective=obj)
    total_visits = 6 * 8  # 48
    assert len(seen) <= 9, f"more real evals ({len(seen)}) than distinct configs (9)"
    assert len(seen) < total_visits, "memoization did not reduce evaluations"
    print(f"qpso memo OK: {total_visits} visits -> {len(seen)} real evals (≤9 configs)")


def test_seed_reproducibility():
    def run():
        seen = []
        obj = lambda c: (seen.append(config_tuple(c)), synthetic(c))[1]  # noqa: E731
        best = run_mopso(BOUNDS, ALLOWED, num_particles=5, generations=6,
                         seed=42, objective=obj)
        return best, seen
    best1, seen1 = run()
    best2, seen2 = run()
    assert best1 == best2, f"same seed, different best: {best1} vs {best2}"
    assert seen1 == seen2, "same seed produced a different evaluation sequence"
    print("seed reproducibility OK: identical best + eval sequence across runs")


if __name__ == "__main__":
    test_dominance_truth_table()
    test_memoization_counts_only_distinct_configs()
    test_qpso_memoized_far_below_visit_count()
    test_seed_reproducibility()
    print("\nall optimizer tests passed")
