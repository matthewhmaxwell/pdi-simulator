"""Compare pre-fix (e2_*) and post-fix (e4_*) runs at the E002 hard-env config.

The fix: MemoryPolicy now seeks visible food before consulting memory.
We expect the memory tier's survival to rise; reflex/social/full should be
roughly unchanged (their policies are unaffected by the fix, modulo their
own fall-throughs to MemoryPolicy.choose_action via super().choose_action).
"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
TIERS = ["reflex", "memory", "social", "full"]
SEEDS = [42, 7, 1, 13, 99]


def final(prefix: str, tier: str, seed: int, k: str) -> float:
    p = RUNS / f"{prefix}_{tier}_s{seed}" / "metrics.csv"
    rows = list(csv.DictReader(p.open()))
    return float(rows[-1][k])


def gen0(prefix: str, tier: str, seed: int, k: str) -> float:
    p = RUNS / f"{prefix}_{tier}_s{seed}" / "metrics.csv"
    rows = list(csv.DictReader(p.open()))
    return float(rows[0][k])


def main() -> None:
    print("=" * 92)
    print("E004 — POST-FIX vs PRE-FIX at E002 hard-env config (5 seeds)")
    print("=" * 92)

    for metric in ["avg_survival_rate", "avg_fitness", "cooperation_frequency",
                   "betrayal_frequency", "prediction_accuracy"]:
        print(f"\n{metric}")
        print(f"  {'tier':<10}{'pre-fix (e2)':>20}{'post-fix (e4)':>20}{'delta':>15}{'sign?':>10}")
        print("  " + "-" * 75)
        for tier in TIERS:
            pre = [final("e2", tier, s, metric) for s in SEEDS]
            post = [final("e4", tier, s, metric) for s in SEEDS]
            deltas = [a - b for a, b in zip(post, pre)]
            pre_mean = statistics.mean(pre)
            post_mean = statistics.mean(post)
            pre_sd = statistics.stdev(pre)
            post_sd = statistics.stdev(post)
            delta_mean = statistics.mean(deltas)
            consistent = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)
            sign = "→ all+" if all(d > 0 for d in deltas) else "→ all-" if all(d < 0 for d in deltas) else "mixed"
            print(f"  {tier:<10}{pre_mean:>9.3f}±{pre_sd:>4.2f}     "
                  f"{post_mean:>9.3f}±{post_sd:>4.2f}     "
                  f"{delta_mean:>+10.3f}    {sign:>10}")

    # Headline: did memory tier close the gap with reflex?
    print()
    print("=" * 92)
    print("HEADLINE — MEMORY vs REFLEX SURVIVAL (does the fix close the gap?)")
    print("=" * 92)
    for label, prefix in [("PRE-FIX  (e2)", "e2"), ("POST-FIX (e4)", "e4")]:
        mem = [final(prefix, "memory", s, "avg_survival_rate") for s in SEEDS]
        ref = [final(prefix, "reflex", s, "avg_survival_rate") for s in SEEDS]
        diffs = [m - r for m, r in zip(mem, ref)]
        sign_consistent = all(d > 0 for d in diffs) or all(d < 0 for d in diffs)
        print(f"\n  {label}")
        print(f"    memory: {statistics.mean(mem):.3f} ± {statistics.stdev(mem):.3f}")
        print(f"    reflex: {statistics.mean(ref):.3f} ± {statistics.stdev(ref):.3f}")
        print(f"    diff (memory - reflex): {statistics.mean(diffs):+.3f} ± {statistics.stdev(diffs):.3f}")
        print(f"    per-seed signs: {[f'{d:+.3f}' for d in diffs]}")
        print(f"    sign consistent: {sign_consistent}")

    # And: did the firmness pass headline (full > reflex) survive the fix?
    print()
    print("=" * 92)
    print("HEADLINE — FULL vs REFLEX SURVIVAL (does the E003 directional finding hold?)")
    print("=" * 92)
    for label, prefix in [("PRE-FIX  (e2)", "e2"), ("POST-FIX (e4)", "e4")]:
        full = [final(prefix, "full", s, "avg_survival_rate") for s in SEEDS]
        ref = [final(prefix, "reflex", s, "avg_survival_rate") for s in SEEDS]
        diffs = [f - r for f, r in zip(full, ref)]
        sign_consistent = all(d > 0 for d in diffs)
        print(f"\n  {label}")
        print(f"    full  : {statistics.mean(full):.3f} ± {statistics.stdev(full):.3f}")
        print(f"    reflex: {statistics.mean(ref):.3f} ± {statistics.stdev(ref):.3f}")
        print(f"    diff (full - reflex): {statistics.mean(diffs):+.3f} ± {statistics.stdev(diffs):.3f}")
        print(f"    per-seed: {[f'{d:+.3f}' for d in diffs]}")
        print(f"    full > reflex on every seed? {sign_consistent}")


if __name__ == "__main__":
    main()
