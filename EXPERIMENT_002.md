# Experiment 002 — Tier Ablation in a Harder Environment

**Question:** When the environment makes survival genuinely costly, does climbing the cognition lineage finally pay off?

**Setup:** Same as E001 (20 gen × 50 agents × 10 ep, grid 20×20, 80 steps, seeds 42 + 7), with environment knobs tightened:

| knob               | E001 | E002  |
|--------------------|------|-------|
| food count         | 30   | **15** |
| hazards            | 8    | **20** |
| food_respawn_rate  | 0.05 | **0.02** |
| shelters           | 4    | 4     |

**Configs:** [`data/runs/e2_<tier>_s<seed>/`](data/runs/)

## Headline numbers (mean across both seeds, ± half-spread)

| metric                      | reflex          | memory          | social          | full              |
|-----------------------------|-----------------|-----------------|-----------------|-------------------|
| **avg_survival_rate**       | 0.48 ± 0.00     | 0.45 ± 0.05     | 0.42 ± 0.02     | **0.60 ± 0.04**   |
| avg_fitness                 | 183 ± 0         | 158 ± 11        | 555 ± 45        | **679 ± 83**      |
| avg_resource_collection     | **38 ± 0**      | 26 ± 2          | 24 ± 2          | 30 ± 2            |
| cooperation_frequency       | 0               | 0               | 1016 ± 104      | **1211 ± 180**    |
| betrayal_frequency          | 0               | 0               | 62 ± 7          | 70 ± 2            |
| prediction_accuracy         | **0.97**        | 0.78            | 0.79            | 0.75              |
| social_trust_accuracy       | n/a             | n/a             | 0.99            | 0.98              |
| memory_usefulness           | 0.13            | 0.12            | 0.27            | **0.28**          |

## Learning over generations (gen19 − gen0)

| metric                | reflex | memory     | social    | full      |
|-----------------------|--------|------------|-----------|-----------|
| survival              | 0.00   | +0.07      | +0.02     | **+0.03** |
| fitness               | +3     | +16        | +279      | **+308**  |
| food                  | +2     | +2         | −1        | 0         |
| cooperation           | 0      | 0          | +635      | **+681**  |
| betrayal              | 0      | 0          | **−93**   | **−130**  |
| prediction accuracy   | +0.01  | −0.04      | −0.06     | −0.05     |

## Survival trajectory

```
reflex   0.48 → 0.49 → 0.48
memory   0.38 → 0.59 → 0.45
social   0.40 → 0.53 → 0.42
full     0.57 → 0.52 → 0.60   ← only tier that survives at >50% with positive trend
```

## Headline survival comparison: E001 vs E002

```
                E001 (easy env)    E002 (hard env)    delta
  reflex            0.92               0.48           -0.44
  memory            0.69               0.45           -0.24
  social            0.62               0.42           -0.20
  full              0.71               0.60           -0.11
```

The harder environment hurt **everyone**, but it hurt reflex agents the most (-0.44) and full-tier agents the least (-0.11). **Cognition is a hedge against environmental difficulty.**

## Verdict

**Thesis supported in the harder regime.**

1. **Full tier wins survival, 0.60 vs reflex's 0.48** — consistent across both seeds, spread ±0.04. The 12-point margin is real signal.
2. **The ranking from E001 inverted on survival.** In an easy environment, reflex foraging suffices and cognitive overhead is wasted energy. In a harder environment, the cognitive agents' ability to share, follow trusted peers, and avoid threats actually keeps them alive.
3. **Pro-social selection emerged.** Betrayal frequency dropped −93 (social) and −130 (full) across generations. Agents evolved away from defection without us telling them to.
4. **Reflex still has the best foraging efficiency** (38 food vs full's 30) — but full agents trade some foraging time for cooperation, and net out ahead on survival. The trade is rational under scarcity.
5. **Memory tier alone is not enough.** Memory without social machinery (0.45) underperforms reflex on survival in this environment too. The lift comes from *combining* memory + social + causal beliefs in the full tier.

## Caveats

- Prediction accuracy actually *fell* in cognitive tiers (-0.04 to -0.06). Harder environments have more variance, which makes any prediction harder. Worth understanding before adding more cognition.
- Reflex's 0.97 prediction accuracy looks impressive but is partly a ceiling artifact: reflex agents log the same kind of memory but their predictions are mostly "no food → reward will be negative" which is reliably true.
- Two seeds only. Worth running a 5-seed variance pass before publishing any chart.

## What this unlocks

The architecture's core claim — that staged cognition produces measurably better outcomes under pressure — now has empirical support. Next legitimate moves:

- **E003 (cooperation-mandatory tile):** make a single agent unable to harvest a "large cache" tile, requiring ≥2 adjacent agents acting together. Tests whether shared intentionality is selected for when it's structurally required.
- **Add culture:** offspring inherit a digest of parent's high-usefulness memories. Tests whether cumulative learning beats per-life learning.
- **Add theory of mind:** agents maintain models of *other agents'* self-models. The next rung up the lineage.
