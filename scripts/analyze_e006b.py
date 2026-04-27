"""E006b: does the time-aware memory retrieval added in E006 hurt memory tier
in random-respawn grid env (where periodicity isn't there to exploit)?"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
SEEDS = [42, 7, 1, 13, 99]


def final(prefix, tier, seed, key):
    p = RUNS / f"{prefix}_{tier}_s{seed}" / "metrics.csv"
    rows = list(csv.DictReader(p.open()))
    return float(rows[-1][key])


def main():
    print("=" * 100)
    print("  E006b — time-aware memory tier in RANDOM-RESPAWN grid env")
    print("=" * 100)

    refl = [final("e6b", "reflex", s, "avg_survival_rate") for s in SEEDS]
    mem = [final("e6b", "memory", s, "avg_survival_rate") for s in SEEDS]

    print()
    print("Final-generation survival per seed:")
    print(f"{'seed':>6} {'reflex':>10} {'memory (E006)':>15}")
    for s, r, m in zip(SEEDS, refl, mem):
        print(f"{s:>6} {r:>10.3f} {m:>15.3f}")

    print()
    print(f"Aggregates (n={len(SEEDS)}):")
    print(f"  reflex:        {statistics.mean(refl):.3f} ± {statistics.stdev(refl):.3f}")
    print(f"  memory (E006): {statistics.mean(mem):.3f} ± {statistics.stdev(mem):.3f}")

    diffs = [m - r for m, r in zip(mem, refl)]
    n_pos = sum(1 for d in diffs if d > 0)
    print()
    print(f"Memory − Reflex gap:")
    print(f"  mean:   {statistics.mean(diffs):+.4f}")
    print(f"  stdev:  {statistics.stdev(diffs):.4f}")
    print(f"  per-seed: {[round(d, 3) for d in diffs]}")
    print(f"  positive in: {n_pos}/{len(SEEDS)} seeds")

    print()
    print("VERDICT:")
    if abs(statistics.mean(diffs)) < 2 * statistics.stdev(diffs):
        print("  ✓ memory ≈ reflex in grid env (within noise) — E006 doesn't hurt.")
    elif statistics.mean(diffs) > 0:
        print("  + memory > reflex in grid env — unexpected positive transfer.")
    else:
        print("  ✗ memory underperforms reflex in grid env — E006 retrieval is harmful here.")


if __name__ == "__main__":
    main()
