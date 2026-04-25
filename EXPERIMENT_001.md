# Experiment 001 — Tier Ablation

**Question:** Does climbing the cognition lineage (reflex → memory → social → full) actually improve agent outcomes?

**Setup:** 20 generations, 50 agents/pop, 10 episodes/gen, grid 20×20, max 80 steps. Two seeds (42, 7). All other config defaults.

**Configs:** [`data/runs/exp_<tier>_s<seed>/`](data/runs/)

## Headline numbers (mean across both seeds, ± half-spread)

| metric                      | reflex          | memory          | social          | full              |
|-----------------------------|-----------------|-----------------|-----------------|-------------------|
| avg_survival_rate           | **0.92** ± 0.01 | 0.69 ± 0.02     | 0.62 ± 0.00     | 0.71 ± 0.02       |
| avg_fitness                 | 395 ± 1         | 302 ± 9         | 632 ± 13        | **778** ± 43      |
| avg_resource_collection     | **143** ± 1     | 108 ± 4         | 109 ± 2         | 125 ± 2           |
| cooperation_frequency       | 0               | 0               | 827 ± 23        | **1122** ± 98     |
| betrayal_frequency          | 0               | 0               | 10 ± 9          | 74 ± 22           |
| prediction_accuracy         | **0.94**        | 0.86            | 0.87            | 0.85              |
| social_trust_accuracy       | n/a             | n/a             | **1.00**        | 0.98              |
| memory_usefulness           | 0.19            | 0.17            | 0.30            | **0.34**          |

## Learning over generations (gen19 − gen0)

| metric                | reflex | memory     | social    | full      |
|-----------------------|--------|------------|-----------|-----------|
| survival              | +0.03  | **−0.10**  | −0.05     | **−0.10** |
| fitness               | +12    | −19        | +207      | **+214**  |
| food                  | +5     | 0          | −2        | −3        |
| cooperation           | 0      | 0          | +477      | **+543**  |
| betrayal              | 0      | 0          | −113      | −90       |
| prediction accuracy   | 0      | **+0.17**  | 0         | −0.01     |

## Survival trajectory

```
reflex   0.89 → 0.91 → 0.92    ← only tier that improves over generations
memory   0.79 → 0.70 → 0.69
social   0.67 → 0.61 → 0.62
full     0.81 → 0.74 → 0.71
```

## Verdict

**Mixed.** Different metrics tell opposite stories.

1. **Survival: cognition loses.** Reflex agents survive at 0.92, and reflex is the *only* tier where survival improves across generations. Memory/social/full all regress 5–10 points. In this environment, cognitive overhead (energy spent on share/withhold/follow/avoid) costs more than it earns in survival terms.

2. **Fitness: cognition wins.** Full tier ends at fitness 778, double reflex's 395, with cooperation_frequency up +543 across generations. But this is partly tautological — fitness rewards cooperation events directly, so the higher tiers self-feed.

3. **Memory tier shows the cleanest emergent learning signal.** Prediction accuracy improves +0.17 (0.66 → 0.86) across generations — agents are demonstrably learning to predict outcomes from past observations. No other tier shows this delta because they start near ceiling.

4. **Social trust accuracy hits 1.0** — the social model's `predicted_behavior` labels are robustly correct. Social cognition machinery works as designed.

## What this means

The simulator works. The thesis is **not yet validated** because the environment doesn't make cognition pay where it counts (survival).

The likely root cause is environmental: with 30 food on a 400-cell grid and easy respawn, reflex foraging suffices. Cooperation costs energy without producing proportional survival return.

## Next experiments

Two changes worth running before adding more cognition tiers:

- **E002 (harder environment):** food=15, hazards=20, food_respawn_rate=0.02. Target: a regime where reflex agents starve and cooperators outlast them.
- **E003 (cooperation-mandatory):** introduce a "large food cache" tile that requires ≥2 adjacent agents sharing within 1 step to unlock — make group action survival-relevant, not just bonus-relevant.

Only once cognition demonstrably helps survival should we layer in theory of mind, shared intentionality, and culture.
