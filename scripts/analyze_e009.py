"""E009 analysis: transfer evaluation across cyclic ↔ grid envs.

For each (tier, source_seed):
  - cc: cyclic-trained genomes evaluated in cyclic (self-control)
  - cg: cyclic-trained genomes evaluated in hard grid (cross-transfer)
  - gc: grid-trained genomes evaluated in cyclic (cross-transfer)
  - gg: grid-trained genomes evaluated in hard grid (self-control)

Transfer cost = self_survival - cross_survival. If positive (cross < self),
the genomes did NOT generalize. If near zero, they did.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
SEEDS = [42, 7, 1, 13, 99]
TIERS = ["reflex", "memory", "social", "full"]


def summary(prefix_pair: str, tier: str, seed: int) -> dict:
    """Return parsed summary.json for an e9_*_<tier>_s<seed> run."""
    path = RUNS / f"e9_{prefix_pair}_{tier}_s{seed}" / "summary.json"
    return json.loads(path.read_text())


def survival(prefix_pair, tier):
    return [summary(prefix_pair, tier, s)["mean_survival_rate"] for s in SEEDS]


def report_transfer(label, self_pair, cross_pair):
    """For a given training-env pair, compare self-eval vs cross-eval."""
    print(f"\n{label}")
    print("-" * 90)
    print(f"  {'tier':<10} {'self-eval':>20} {'cross-eval':>20} {'transfer cost':>15}")
    for tier in TIERS:
        self_s = survival(self_pair, tier)
        cross_s = survival(cross_pair, tier)
        self_m = statistics.mean(self_s)
        cross_m = statistics.mean(cross_s)
        diff = self_m - cross_m
        print(f"  {tier:<10} "
              f"{self_m:>10.3f}±{statistics.stdev(self_s):.3f}     "
              f"{cross_m:>10.3f}±{statistics.stdev(cross_s):.3f}     "
              f"{diff:>+10.3f}")


def main():
    print("=" * 90)
    print("  E009 — Transfer evaluation: cyclic ↔ hard grid")
    print("  20 episodes per eval (no breeding), 5 source seeds, --no-coop-fitness")
    print("=" * 90)

    report_transfer(
        "CYCLIC-TRAINED genomes (eval in cyclic vs eval in hard grid):",
        self_pair="cc", cross_pair="cg",
    )
    report_transfer(
        "GRID-TRAINED genomes (eval in grid vs eval in cyclic):",
        self_pair="gg", cross_pair="gc",
    )

    print()
    print("=" * 90)
    print("  COGNITION-GAP PRESERVATION")
    print("  Does the full > reflex gap survive transfer to a different env?")
    print("=" * 90)

    for src_label, self_pair, cross_pair in [
        ("cyclic-trained", "cc", "cg"),
        ("grid-trained",   "gg", "gc"),
    ]:
        full_self = survival(self_pair, "full")
        refl_self = survival(self_pair, "reflex")
        full_cross = survival(cross_pair, "full")
        refl_cross = survival(cross_pair, "reflex")

        gap_self = [f - r for f, r in zip(full_self, refl_self)]
        gap_cross = [f - r for f, r in zip(full_cross, refl_cross)]

        n_pos_self = sum(1 for d in gap_self if d > 0)
        n_pos_cross = sum(1 for d in gap_cross if d > 0)

        print(f"\n{src_label} genomes:")
        print(f"  full−reflex on self-env:  {statistics.mean(gap_self):+.3f} ± "
              f"{statistics.stdev(gap_self):.3f}   sign-positive: {n_pos_self}/{len(SEEDS)}")
        print(f"  full−reflex on other-env: {statistics.mean(gap_cross):+.3f} ± "
              f"{statistics.stdev(gap_cross):.3f}   sign-positive: {n_pos_cross}/{len(SEEDS)}")

    print()
    print("=" * 90)
    print("  PER-TIER TRANSFER PENALTY (self mean - cross mean, mean across 5 seeds)")
    print("=" * 90)
    for tier in TIERS:
        cc = statistics.mean(survival("cc", tier))
        cg = statistics.mean(survival("cg", tier))
        gc = statistics.mean(survival("gc", tier))
        gg = statistics.mean(survival("gg", tier))
        print(f"  {tier:<10}  cyclic→grid penalty: {cc - cg:+.3f}    "
              f"grid→cyclic penalty: {gg - gc:+.3f}")


if __name__ == "__main__":
    main()
