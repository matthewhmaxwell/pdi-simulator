"""E007 analysis: compare full > reflex survival with vs without
the cooperation tautology, in both cyclic env (vs E005) and hard grid env
(vs E002/E003)."""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
TIERS = ["reflex", "memory", "social", "full"]
SEEDS = [42, 7, 1, 13, 99]


def load(prefix: str, tier: str, seed: int) -> list[dict]:
    p = RUNS / f"{prefix}_{tier}_s{seed}" / "metrics.csv"
    return list(csv.DictReader(p.open()))


def final(rows, k):
    return float(rows[-1][k])


def survival_at(prefix, tier):
    return [final(load(prefix, tier, s), "avg_survival_rate") for s in SEEDS]


def report(label: str, with_coop_prefix: str, without_coop_prefix: str):
    print()
    print("=" * 100)
    print(f"  {label}")
    print(f"    with-coop-fitness runs: {with_coop_prefix}_*")
    print(f"    without-coop-fitness:   {without_coop_prefix}_*")
    print("=" * 100)

    print()
    print(f"{'tier':<10} {'with-coop':>20} {'without-coop':>20} {'change':>15}")
    print("-" * 80)
    for t in TIERS:
        with_v = survival_at(with_coop_prefix, t)
        without_v = survival_at(without_coop_prefix, t)
        with_m = statistics.mean(with_v)
        without_m = statistics.mean(without_v)
        delta = without_m - with_m
        print(
            f"{t:<10} "
            f"{with_m:>10.3f}±{statistics.stdev(with_v):.3f}     "
            f"{without_m:>10.3f}±{statistics.stdev(without_v):.3f}     "
            f"{delta:>+9.3f}"
        )

    print()
    # Critical: full vs reflex survival, before and after.
    full_with = survival_at(with_coop_prefix, "full")
    refl_with = survival_at(with_coop_prefix, "reflex")
    full_without = survival_at(without_coop_prefix, "full")
    refl_without = survival_at(without_coop_prefix, "reflex")

    diffs_with = [f - r for f, r in zip(full_with, refl_with)]
    diffs_without = [f - r for f, r in zip(full_without, refl_without)]

    print("HEADLINE — full vs reflex SURVIVAL gap, with and without coop-fitness:")
    print(
        f"  with    coop fitness: {statistics.mean(diffs_with):+.3f} ± "
        f"{statistics.stdev(diffs_with):.3f}   per-seed: {[round(d, 3) for d in diffs_with]}   "
        f"sign-consistent: {all(d > 0 for d in diffs_with) or all(d < 0 for d in diffs_with)}"
    )
    print(
        f"  WITHOUT coop fitness: {statistics.mean(diffs_without):+.3f} ± "
        f"{statistics.stdev(diffs_without):.3f}   per-seed: {[round(d, 3) for d in diffs_without]}   "
        f"sign-consistent: {all(d > 0 for d in diffs_without) or all(d < 0 for d in diffs_without)}"
    )

    # Verdict.
    print()
    print("VERDICT:")
    if statistics.mean(diffs_without) > 0 and all(d > 0 for d in diffs_without):
        print("  ✓ Full > reflex survival HOLDS without the cooperation tautology.")
        print("    The cognition advantage is REAL on survival, not a fitness-bookkeeping artifact.")
    elif statistics.mean(diffs_without) > 0:
        print("  ~ Full > reflex survival weakens but persists (mean+, not sign-consistent).")
    elif statistics.mean(diffs_without) <= 0:
        print("  ✗ Full > reflex survival COLLAPSES without the cooperation tautology.")
        print("    The headline finding was partly mechanical — selection rewarded coop events directly.")


def main():
    # Cyclic env: with-coop = E005 (e5_*), without-coop = e7c_*
    report("CYCLIC ENV (vs E005)", "e5", "e7c")
    # Hard grid env: with-coop = E002/E003 (e2_*), without-coop = e7g_*
    report("HARD GRID ENV (vs E002/E003)", "e2", "e7g")


if __name__ == "__main__":
    main()
