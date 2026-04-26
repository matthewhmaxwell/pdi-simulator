# Experiment 005 — Tier ablation in `CyclicEnvironment`

> **One-line question.** Does the memory tier finally outperform reflex when the environment has *temporal structure* (fixed feeding grounds, periodic respawn) for memory to exploit?

> **Pre-stated hypothesis (before running).** "If we add an env with predictable food-respawn periods, memory tier should be able to learn the period and outperform reflex on survival. The cognitive tier ordering should become monotonic for the first time."

## Setup

- **Env:** [`CyclicEnvironment`](src/pdi/environments/cyclic.py) — 15 fixed feeding grounds, respawn period 20 steps (`--respawn 0.05`). No food on non-feeding tiles, ever. Hazards/shelters fixed at start.
- **Other config:** grid 20×20, 80 steps/episode, 50 agents, 20 generations, 10 episodes/gen, 8 hazards, 4 shelters.
- **Seeds:** 42, 7, 1, 13, 99 (5 seeds).
- **Tiers:** reflex, memory, social, full (4 tiers × 5 seeds = 20 runs).
- **Reproduce:** `bash scripts/run_e005_cyclic_sweep.sh`

## Results

### Final-generation survival, per seed

| seed  | reflex   | memory   | social   | full     | full−reflex |
|-------|----------|----------|----------|----------|-------------|
| 42    | 0.606    | 0.634    | 0.700    | 0.734    | +0.128      |
| 7     | 0.630    | 0.622    | 0.718    | 0.686    | +0.056      |
| 1     | 0.614    | 0.660    | 0.684    | 0.732    | +0.118      |
| 13    | 0.616    | 0.622    | 0.688    | 0.658    | +0.042      |
| 99    | 0.604    | 0.608    | 0.680    | 0.690    | +0.086      |

### Aggregates (mean ± stdev across 5 seeds)

| metric                     | reflex          | memory          | social          | full              |
|----------------------------|-----------------|-----------------|-----------------|-------------------|
| avg_survival_rate          | 0.614 ± 0.010   | 0.629 ± 0.020   | 0.694 ± 0.017   | **0.700 ± 0.033** |
| avg_fitness                | 235 ± 2         | 238 ± 4         | 914 ± 99        | **977 ± 85**      |
| avg_resource_collection    | **59.7 ± 0.2**  | 59.7 ± 0.2      | 53.0 ± 2.6      | 54.6 ± 1.0        |
| prediction_accuracy        | 0.96 ± 0.00     | 0.96 ± 0.01     | 0.64 ± 0.03     | 0.69 ± 0.01       |
| avg_novelty                | **6.46 ± 0.36** | 6.02 ± 0.41     | 3.06 ± 0.47     | 2.62 ± 0.40       |
| memory_usefulness          | 0.14            | 0.14            | 0.32            | 0.32              |

### Headline tests

**Memory vs Reflex** (the hypothesis-test comparison):
- mean diff = **+0.015 ± 0.022**
- per-seed signs: [+0.028, **−0.008**, +0.046, +0.006, +0.004]
- memory > reflex in **4 of 5 seeds**, not all 5. Sign-consistency does not hold.

**Full vs Reflex** (generalization check):
- mean diff = **+0.086 ± 0.037**
- per-seed signs: [+0.128, +0.056, +0.118, +0.042, +0.086]
- full > reflex on **all 5 seeds**. Sign-consistent. Binomial p ≤ 3.1%.

## What the evidence supports

1. **First monotonic tier ordering observed.** In every prior experiment memory tier was tied with reflex or worse. Here we see reflex (0.61) < memory (0.63) < social (0.69) < full (0.70). The cyclic env at minimum permits the predicted ordering, even if individual tier-to-tier gaps are small.

2. **Full-tier survival advantage generalizes to a new env type.** The +0.086 ± 0.037 gap is essentially the same magnitude as E003's +0.093 ± 0.040 in the hard grid env. The signal is **not specific to the multi-factor-pressure regime** — it shows up in a structurally different environment too. That's real generalization evidence.

3. **Cognition tradeoffs become visible with decoupled metrics.**
   - Reflex/memory forage **more** (60 food vs 54 for social/full).
   - Social/full have **higher fitness** despite less foraging (cooperation events drive it; weights still default).
   - Reflex/memory explore **more** (avg_novelty 6.5 vs 2.7) — social tiers stay near cooperation partners.
   - Prediction accuracy **drops** for social/full (0.65 vs 0.96) because their actions create more reward variance, making prediction harder. This is a **real cost** to higher cognition that wasn't visible before novelty/per-component decoupling.

## What the evidence does NOT support

1. **The hypothesis as stated.** Memory tier shows a +0.015 advantage — present in 4/5 seeds but with one negative seed and a stdev (0.022) larger than the mean diff (0.015). This is **not a robust positive result**, just a weak directional one. We predicted memory would meaningfully outperform reflex; it doesn't.

2. **That memory is exploiting the period.** The current `MemoryStore.retrieve_similar` retrieves by state-tag overlap, **not by timestamp pattern**. Memory has no path to learn "tile X had food at step 0, 10, 20." So even though the env has temporal structure, the memory tier can't leverage it without retrieval-side changes. **Real memory pay-off would require time-aware retrieval, which is a code change, not a parameter sweep.**

3. **That full > reflex is "because of cognition" in a clean sense.** The cooperation tautology is still in play (default `FitnessWeights`). E007 (`--no-coop-fitness` on this same config) is the cleaner test.

## Caveats and known issues

- **Memory tier's ceiling here is artificial.** Without time-aware retrieval in `MemoryStore`, no rule-based memory tier can exceed reflex by much in this env. Treat E005 as a **baseline measurement** of "how much memory helps when it can't directly use temporal patterns" — a proper test of the hypothesis requires building time-aware retrieval first.
- **n=5 still small.** Memory's +0.015 ± 0.022 might or might not survive n=20.
- **Prediction-accuracy drop in social/full is a feature, not a bug** — they take harder-to-predict actions on purpose. But it confirms that "prediction accuracy" alone cannot rank tiers, which is one reason we decoupled metrics.

## Suggested next experiments

In priority order:

1. **E006 — time-aware memory retrieval.** Extend `MemoryStore.retrieve_similar` to weight events by recency-relative-to-current-step (or, more directly, query "what happened ~`respawn_period` ago at this tile?"). Then re-run E005 to see if memory finally outperforms reflex by a real margin.
2. **E007 — `--no-coop-fitness` on cyclic env.** Test whether full > reflex survives the cooperation-tautology ablation.
3. **E008 — n=20 seeds on the E005 config.** Convert the +0.086 full-vs-reflex finding to robust statistical evidence.
4. **E009 — transfer evaluation.** Train in cyclic, evaluate (no learning) in grid (or vice versa). Tests whether evolved genomes generalize beyond their training env.

## Conclusion

The cyclic env did **not** confirm the memory-pays-off hypothesis as stated. It did produce the **first monotonic tier ordering** we've observed and confirmed that the **full > reflex survival advantage generalizes to a structurally different env** (sign-consistent across 5 seeds). The honest interpretation is "the foundation refit unlocked new measurement, the new measurements show the expected ordering exists but memory's individual contribution is bottlenecked by retrieval, and we should fix that before further claims."
