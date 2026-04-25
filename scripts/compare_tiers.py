"""Aggregate cross-tier, cross-seed metrics from completed runs.

Usage:
    python scripts/compare_tiers.py
"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"

TIERS = ["reflex", "memory", "social", "full"]
SEEDS = [42, 7]
METRICS = [
    "avg_survival_rate",
    "avg_fitness",
    "avg_resource_collection",
    "cooperation_frequency",
    "betrayal_frequency",
    "prediction_accuracy",
    "social_trust_accuracy",
    "memory_usefulness",
    "strategy_diversity",
]


def load(tier: str, seed: int) -> list[dict]:
    p = RUNS / f"exp_{tier}_s{seed}" / "metrics.csv"
    return list(csv.DictReader(p.open()))


def final_value(rows: list[dict], key: str) -> float:
    return float(rows[-1][key])


def gen0_value(rows: list[dict], key: str) -> float:
    return float(rows[0][key])


def trajectory(rows: list[dict], key: str) -> list[float]:
    return [float(r[key]) for r in rows]


def main() -> None:
    # Headline table: final-generation metrics, mean across seeds.
    print("=" * 96)
    print("FINAL-GENERATION METRICS (mean across seeds 42, 7)")
    print("=" * 96)
    header = f"{'metric':<28}" + "".join(f"{t:>15}" for t in TIERS)
    print(header)
    print("-" * 96)

    for m in METRICS:
        row = f"{m:<28}"
        for tier in TIERS:
            vals = [final_value(load(tier, s), m) for s in SEEDS]
            mean = statistics.mean(vals)
            spread = max(vals) - min(vals)
            row += f" {mean:>9.2f}±{spread/2:.2f}"
        print(row)

    # Improvement deltas: gen19 - gen0, mean across seeds.
    print()
    print("=" * 96)
    print("LEARNING DELTA (gen19 - gen0, mean across seeds)")
    print("=" * 96)
    header = f"{'metric':<28}" + "".join(f"{t:>15}" for t in TIERS)
    print(header)
    print("-" * 96)

    for m in METRICS:
        row = f"{m:<28}"
        for tier in TIERS:
            deltas = [final_value(load(tier, s), m) - gen0_value(load(tier, s), m) for s in SEEDS]
            mean = statistics.mean(deltas)
            row += f"{mean:>+15.2f}"
        print(row)

    # Per-seed final fitness, for variance gut-check.
    print()
    print("=" * 96)
    print("PER-SEED FINAL FITNESS (variance gut-check)")
    print("=" * 96)
    header = f"{'seed':<8}" + "".join(f"{t:>15}" for t in TIERS)
    print(header)
    print("-" * 60)
    for seed in SEEDS:
        row = f"s={seed:<6}"
        for tier in TIERS:
            row += f"{final_value(load(tier, seed), 'avg_fitness'):>15.1f}"
        print(row)

    # Survival trajectory hint: did anyone trend up vs down?
    print()
    print("=" * 96)
    print("SURVIVAL TRAJECTORY (gen 0 → 9 → 19, mean across seeds)")
    print("=" * 96)
    for tier in TIERS:
        trajs = [trajectory(load(tier, s), "avg_survival_rate") for s in SEEDS]
        n = len(trajs[0])
        early = statistics.mean(t[0] for t in trajs)
        mid = statistics.mean(t[n // 2] for t in trajs)
        late = statistics.mean(t[-1] for t in trajs)
        print(f"  {tier:<8}  {early:.2f}  →  {mid:.2f}  →  {late:.2f}")


if __name__ == "__main__":
    main()
