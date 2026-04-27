"""E008 analysis: aggregate the n=20 no-coop-fitness sweep across both envs.

Reads e7c_*_s* (cyclic) and e7g_*_s* (hard grid) for all 20 seeds (5 from
E007 + 15 from E008) and computes mean/stdev/sign-consistency for the
full vs reflex survival gap.
"""
from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"

E007_SEEDS = [42, 7, 1, 13, 99]
E008_SEEDS = [2, 3, 5, 11, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]
ALL_SEEDS = E007_SEEDS + E008_SEEDS  # n=20

TIERS = ["reflex", "memory", "social", "full"]


def load(prefix: str, tier: str, seed: int) -> list[dict]:
    p = RUNS / f"{prefix}_{tier}_s{seed}" / "metrics.csv"
    return list(csv.DictReader(p.open()))


def final(rows, k):
    return float(rows[-1][k])


def survival_at(prefix, tier, seeds=None):
    seeds = seeds or ALL_SEEDS
    return [final(load(prefix, tier, s), "avg_survival_rate") for s in seeds]


def report(label: str, prefix: str):
    print()
    print("=" * 100)
    print(f"  {label}  (n={len(ALL_SEEDS)} seeds)")
    print("=" * 100)

    print()
    print(f"{'tier':<10} {'mean':>10} {'stdev':>10} {'min':>8} {'max':>8}")
    print("-" * 60)
    for t in TIERS:
        v = survival_at(prefix, t)
        print(f"{t:<10} {statistics.mean(v):>10.3f} {statistics.stdev(v):>10.3f} {min(v):>8.3f} {max(v):>8.3f}")

    full = survival_at(prefix, "full")
    refl = survival_at(prefix, "reflex")
    diffs = [f - r for f, r in zip(full, refl)]
    n_pos = sum(1 for d in diffs if d > 0)
    n = len(diffs)
    print()
    print(f"FULL vs REFLEX survival gap:")
    print(f"  mean:   {statistics.mean(diffs):+.4f}")
    print(f"  stdev:  {statistics.stdev(diffs):.4f}")
    print(f"  min:    {min(diffs):+.4f}")
    print(f"  max:    {max(diffs):+.4f}")
    print(f"  >0 in:  {n_pos}/{n} seeds")
    if n_pos == n:
        # Two-sided binomial p under H0: p=0.5.
        p = 2 * (0.5 ** n)
        print(f"  binomial p (sign-consistency): {p:.2e}")
    elif n_pos == 0:
        p = 2 * (0.5 ** n)
        print(f"  binomial p (all negative): {p:.2e}")

    # n=5 vs n=20: did the firmer estimate change much?
    n5_diffs = [d for d, s in zip(diffs, ALL_SEEDS) if s in E007_SEEDS]
    n5_mean = statistics.mean(n5_diffs)
    print()
    print(f"  n=5 (E007 only):  mean = {n5_mean:+.4f}")
    print(f"  n=20 (E007+E008): mean = {statistics.mean(diffs):+.4f}   "
          f"(shift: {statistics.mean(diffs) - n5_mean:+.4f})")


def main():
    report("CYCLIC ENV — no-coop-fitness", "e7c")
    report("HARD GRID ENV — no-coop-fitness", "e7g")


if __name__ == "__main__":
    main()
