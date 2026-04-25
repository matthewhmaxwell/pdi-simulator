"""Analyze the robustness sweep:

  Part A: 5-seed firmness pass at E002 config (seeds 42,7,1,13,99).
          → Compute mean ± stdev for survival/fitness across 5 seeds, per tier.

  Part B: knob isolation. Three single-knob configs:
            e3a: food alone (15 instead of 30)
            e3b: hazards alone (20 instead of 8)
            e3c: respawn alone (0.02 instead of 0.05)
          → Compare survival across knobs to attribute the E001→E002 effect.
"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
TIERS = ["reflex", "memory", "social", "full"]


def load(prefix: str, tier: str, seed: int) -> list[dict]:
    p = RUNS / f"{prefix}_{tier}_s{seed}" / "metrics.csv"
    return list(csv.DictReader(p.open()))


def final(rows: list[dict], k: str) -> float:
    return float(rows[-1][k])


def gen0(rows: list[dict], k: str) -> float:
    return float(rows[0][k])


# ---------- Part A: firmness ----------

def firmness_pass():
    seeds = [42, 7, 1, 13, 99]
    print("=" * 96)
    print(f"PART A — 5-SEED FIRMNESS PASS @ E002 config (food=15, haz=20, respawn=0.02)")
    print(f"        seeds: {seeds}")
    print("=" * 96)

    metrics = ["avg_survival_rate", "avg_fitness", "cooperation_frequency", "betrayal_frequency"]
    print(f"{'metric':<28}" + "".join(f"{t:>16}" for t in TIERS))
    print("-" * 96)
    for m in metrics:
        row = f"{m:<28}"
        for tier in TIERS:
            vals = [final(load("e2", tier, s), m) for s in seeds]
            mean = statistics.mean(vals)
            sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            row += f" {mean:>9.2f}±{sd:>4.2f}"
        print(row)

    # Survival deltas (gen19 - gen0).
    print()
    print("LEARNING DELTA (gen19 - gen0, mean±stdev across 5 seeds)")
    print("-" * 96)
    for m in ["avg_survival_rate", "avg_fitness", "betrayal_frequency"]:
        row = f"{m:<28}"
        for tier in TIERS:
            deltas = [final(load("e2", tier, s), m) - gen0(load("e2", tier, s), m) for s in seeds]
            mean = statistics.mean(deltas)
            sd = statistics.stdev(deltas) if len(deltas) > 1 else 0.0
            row += f" {mean:>+9.2f}±{sd:>4.2f}"
        print(row)

    # Per-seed survival, for transparency.
    print()
    print("PER-SEED FINAL SURVIVAL (transparency)")
    print(f"{'seed':<8}" + "".join(f"{t:>14}" for t in TIERS))
    print("-" * 70)
    for s in seeds:
        row = f"s={s:<6}"
        for tier in TIERS:
            row += f"{final(load('e2', tier, s), 'avg_survival_rate'):>14.3f}"
        print(row)

    # Headline: is full > reflex on survival? Statistical-ish answer.
    print()
    print("HEADLINE: full vs reflex survival across 5 seeds")
    full_vals = [final(load("e2", "full", s), "avg_survival_rate") for s in seeds]
    refl_vals = [final(load("e2", "reflex", s), "avg_survival_rate") for s in seeds]
    diffs = [f - r for f, r in zip(full_vals, refl_vals)]
    print(f"  full  : {statistics.mean(full_vals):.3f} ± {statistics.stdev(full_vals):.3f}")
    print(f"  reflex: {statistics.mean(refl_vals):.3f} ± {statistics.stdev(refl_vals):.3f}")
    print(f"  diff  : {statistics.mean(diffs):+.3f} ± {statistics.stdev(diffs):.3f}  "
          f"(per-seed sign: {[round(d, 3) for d in diffs]})")
    sign_consistent = all(d > 0 for d in diffs) or all(d < 0 for d in diffs)
    print(f"  sign consistent across all 5 seeds? {sign_consistent}")


# ---------- Part B: knob isolation ----------

def knob_isolation():
    seeds = [42, 7]
    configs = {
        "E001 baseline (food=30, haz=8, respawn=0.05)": "exp",
        "E3a food=15 only":                              "e3a",
        "E3b hazards=20 only":                           "e3b",
        "E3c respawn=0.02 only":                         "e3c",
        "E002 all three (food=15, haz=20, respawn=0.02)": "e2",
    }

    print()
    print("=" * 96)
    print("PART B — KNOB ISOLATION (mean across seeds 42, 7)")
    print("=" * 96)

    print("\nFinal-generation SURVIVAL by tier × knob config:")
    print(f"{'config':<55}" + "".join(f"{t:>10}" for t in TIERS))
    print("-" * 100)
    for label, prefix in configs.items():
        row = f"{label:<55}"
        for tier in TIERS:
            try:
                vals = [final(load(prefix, tier, s), "avg_survival_rate") for s in seeds]
                row += f"{statistics.mean(vals):>10.3f}"
            except FileNotFoundError:
                row += f"{'--':>10}"
        print(row)

    print("\nFinal-generation FITNESS by tier × knob config:")
    print(f"{'config':<55}" + "".join(f"{t:>10}" for t in TIERS))
    print("-" * 100)
    for label, prefix in configs.items():
        row = f"{label:<55}"
        for tier in TIERS:
            try:
                vals = [final(load(prefix, tier, s), "avg_fitness") for s in seeds]
                row += f"{statistics.mean(vals):>10.1f}"
            except FileNotFoundError:
                row += f"{'--':>10}"
        print(row)

    # Attribution: for each tier, how much survival was lost going from baseline to each single-knob config?
    print("\nSURVIVAL DELTA from E001 baseline (mean across 2 seeds):")
    print(f"{'config (single knob change)':<55}" + "".join(f"{t:>10}" for t in TIERS))
    print("-" * 100)
    base = {tier: statistics.mean([final(load("exp", tier, s), "avg_survival_rate") for s in seeds]) for tier in TIERS}
    for label, prefix in configs.items():
        if prefix == "exp":
            continue
        row = f"{label:<55}"
        for tier in TIERS:
            try:
                vals = [final(load(prefix, tier, s), "avg_survival_rate") for s in seeds]
                delta = statistics.mean(vals) - base[tier]
                row += f"{delta:>+10.3f}"
            except FileNotFoundError:
                row += f"{'--':>10}"
        print(row)

    # Cognition gap: full minus reflex per config. The thesis predicts the gap is
    # positive (cognition helps) and grows with environmental difficulty.
    print("\nCOGNITION GAP (full survival − reflex survival) per knob config:")
    print(f"{'config':<55} {'gap':>10}")
    print("-" * 70)
    for label, prefix in configs.items():
        try:
            full_vals = [final(load(prefix, "full", s), "avg_survival_rate") for s in seeds]
            refl_vals = [final(load(prefix, "reflex", s), "avg_survival_rate") for s in seeds]
            gap = statistics.mean(full_vals) - statistics.mean(refl_vals)
            print(f"{label:<55} {gap:>+10.3f}")
        except FileNotFoundError:
            print(f"{label:<55} {'--':>10}")


if __name__ == "__main__":
    firmness_pass()
    knob_isolation()
