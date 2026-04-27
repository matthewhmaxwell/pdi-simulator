"""E006 analysis: did the time-aware memory retrieval finally make memory tier
outperform reflex in the cyclic env?

Compares:
  - e6m_memory_s*  : memory tier with E006 time-aware retrieval, no-coop-fitness
  - e7c_reflex_s*  : reflex baseline, no-coop-fitness (same env, same condition)
  - e7c_memory_s*  : memory tier WITHOUT time-aware retrieval (E007 baseline)
                     [n=5 only, the original E007 runs; later E008 runs may be
                     contaminated by my mid-run code change]
"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
SEEDS = [42, 7, 1, 13, 99]


def load_final(prefix: str, tier: str, seed: int) -> dict:
    p = RUNS / f"{prefix}_{tier}_s{seed}" / "metrics.csv"
    return list(csv.DictReader(p.open()))[-1]


def survival(prefix, tier):
    return [float(load_final(prefix, tier, s)["avg_survival_rate"]) for s in SEEDS]


def main():
    print("=" * 100)
    print("  E006 — time-aware memory retrieval in CyclicEnvironment (no-coop-fitness)")
    print("=" * 100)

    refl = survival("e7c", "reflex")
    mem_old = survival("e7c", "memory")
    mem_new = survival("e6m", "memory")

    print()
    print("Final-generation survival per seed:")
    print(f"{'seed':>6} {'reflex':>10} {'memory (old)':>15} {'memory (new, E006)':>20}")
    for s, r, mo, mn in zip(SEEDS, refl, mem_old, mem_new):
        print(f"{s:>6} {r:>10.3f} {mo:>15.3f} {mn:>20.3f}")

    print()
    print("Aggregates (mean ± stdev across 5 seeds):")
    print(f"  reflex:           {statistics.mean(refl):.3f} ± {statistics.stdev(refl):.3f}")
    print(f"  memory (old):     {statistics.mean(mem_old):.3f} ± {statistics.stdev(mem_old):.3f}")
    print(f"  memory (E006):    {statistics.mean(mem_new):.3f} ± {statistics.stdev(mem_new):.3f}")

    diff_old = [m - r for m, r in zip(mem_old, refl)]
    diff_new = [m - r for m, r in zip(mem_new, refl)]
    diff_e006 = [n - o for n, o in zip(mem_new, mem_old)]

    print()
    print("Memory − Reflex survival gap:")
    print(f"  old (no time-aware):   {statistics.mean(diff_old):+.4f} ± {statistics.stdev(diff_old):.4f}   "
          f"sign-positive: {sum(1 for d in diff_old if d > 0)}/5")
    print(f"  new (E006 time-aware): {statistics.mean(diff_new):+.4f} ± {statistics.stdev(diff_new):.4f}   "
          f"sign-positive: {sum(1 for d in diff_new if d > 0)}/5")

    print()
    print("E006 lift (memory_new − memory_old, paired by seed):")
    print(f"  mean:   {statistics.mean(diff_e006):+.4f}")
    print(f"  stdev:  {statistics.stdev(diff_e006):.4f}")
    print(f"  per-seed: {[round(d, 3) for d in diff_e006]}")
    print(f"  positive in: {sum(1 for d in diff_e006 if d > 0)}/5 seeds")

    # Verdict.
    print()
    print("VERDICT:")
    if statistics.mean(diff_new) > 0 and all(d > 0 for d in diff_new):
        print("  ✓ Memory tier with time-aware retrieval beats reflex on every seed.")
        print("    The hypothesis from E005 (memory should help when env has temporal structure)")
        print("    is confirmed once retrieval is no longer the bottleneck.")
    elif statistics.mean(diff_new) > statistics.mean(diff_old):
        print("  ~ Memory tier improved with time-aware retrieval but doesn't yet beat reflex robustly.")
    else:
        print("  ✗ Time-aware retrieval did not produce a meaningful lift over old memory tier.")


if __name__ == "__main__":
    main()
