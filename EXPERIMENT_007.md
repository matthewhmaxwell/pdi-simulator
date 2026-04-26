# Experiment 007 — Ablate the cooperation tautology

> **Pre-stated hypothesis (before running).** "If we set `cooperation_weight = 0` in `FitnessWeights`, the full > reflex survival advantage will weaken or disappear, because part of the cognitive tiers' fitness lead came from being rewarded for cooperation events directly. The honest test of whether cognition really wins on survival."

> **Headline result: hypothesis was wrong, in an interesting direction.**
> Removing the cooperation reward made the full-vs-reflex survival gap **larger, not smaller** — by ~3× in both envs, sign-consistent across all 5 seeds. The tautology was not inflating the result; it was *masking* it.

## Setup

- **Sweep:** 4 tiers × 5 seeds × 2 envs = **40 runs.**
- **Envs:** the E005 cyclic env and the E002/E003 hard grid env, both unchanged from the original configs.
- **Sole intervention:** `--no-coop-fitness` (sets `cooperation` and `betrayal_penalty` weights to 0 in [`FitnessWeights`](src/pdi/config.py)).
- **Reproduce:** `bash scripts/run_e007_no_coop_fitness.sh`

## Results

### Survival per tier (mean ± stdev across 5 seeds)

#### Cyclic env

| tier   | with coop-fitness   | **without** coop-fitness | change       |
|--------|---------------------|--------------------------|--------------|
| reflex | 0.614 ± 0.010       | 0.614 ± 0.010            | no change    |
| memory | 0.629 ± 0.020       | 0.629 ± 0.020            | no change    |
| social | 0.694 ± 0.015       | **0.860 ± 0.036**        | **+0.166**   |
| full   | 0.700 ± 0.033       | **0.912 ± 0.036**        | **+0.212**   |

#### Hard grid env (E002/E003 config)

| tier   | with coop-fitness   | **without** coop-fitness | change       |
|--------|---------------------|--------------------------|--------------|
| reflex | 0.475 ± 0.018       | 0.475 ± 0.018            | no change    |
| memory | 0.460 ± 0.078       | 0.486 ± 0.022            | +0.026       |
| social | 0.477 ± 0.053       | **0.600 ± 0.014**        | **+0.122**   |
| full   | 0.568 ± 0.051       | **0.715 ± 0.032**        | **+0.147**   |

**Reflex and memory tiers are unaffected** (they don't share or withhold), as expected. Social and full tiers — the only ones with access to cooperation actions — gain massively when not rewarded for cooperation.

### Full vs reflex survival gap

| env       | with coop-fitness        | **without** coop-fitness   | change |
|-----------|--------------------------|----------------------------|--------|
| cyclic    | +0.086 ± 0.037           | **+0.298 ± 0.045**         | +0.212 |
| hard grid | +0.093 ± 0.040           | **+0.240 ± 0.018**         | +0.147 |

Sign-consistent across all 5 seeds in both envs. Per-seed gaps in the without-coop conditions: cyclic [+0.33, +0.23, +0.33, +0.28, +0.32], hard grid [+0.24, +0.25, +0.23, +0.22, +0.27]. Binomial p ≤ 3.1% in each env independently.

### What happened to cooperation behavior?

| env       | tier   | coop events with reward | coop events without reward | ratio |
|-----------|--------|-------------------------|----------------------------|-------|
| cyclic    | social | 1681 ± 217              | 6 ± 7                      | 0.00× |
| cyclic    | full   | 1807 ± 200              | 17 ± 15                    | 0.01× |
| hard grid | social | 1066 ± 171              | 14 ± 15                    | 0.01× |
| hard grid | full   | 1296 ± 173              | 16 ± 12                    | 0.01× |

When cooperation is not rewarded, agents almost completely stop cooperating (≤1% of prior rate). And they survive much longer.

### Foraging is essentially unchanged

| env       | tier   | food w/ reward | food w/o reward | delta |
|-----------|--------|----------------|-----------------|-------|
| cyclic    | social | 53.0           | 51.6            | −1.4  |
| cyclic    | full   | 54.6           | 55.4            | +0.7  |

Foraging efficiency barely moves. The survival gain isn't from collecting more food.

## Mechanistic explanation

The original fitness function rewarded each `share` action with `+2.0` fitness. Each `share` action also costs `2.0` energy ([`config.py`](src/pdi/config.py) `share_cost`). Cognitive agents were converging on a strategy where they shared ~1500 times per episode — burning ~3000 energy for ~3000 fitness points. The fitness was real but the survival cost was real too. When food is scarce and respawn is slow, that energy budget difference matters: agents who didn't share could afford to keep moving and foraging.

When we removed the cooperation reward, selection pressure became purely survival-oriented. Agents kept the *capability* to share (genome still has `cooperation_weight`, `reciprocity_weight`, etc.), but the policy effectively stopped firing it. They retained the rest of social cognition — threat avoidance, peer following, social-trust prediction — and used it to live longer.

**Without the tautology, the social/full tiers learned that "almost-never cooperate, but track peers" is a better survival strategy than "cooperate constantly."** This matches actual primate behavior more than the original "pro-social agents" we celebrated in E003.

## What the evidence supports

1. **Full > reflex on survival is REAL, and ~3× larger than previously measured.**
   - Cyclic: +0.298 ± 0.045 (was +0.086).
   - Hard grid: +0.240 ± 0.018 (was +0.093).
   - Sign-consistent across all 5 seeds in both envs.

2. **The fitness function in E001-E006 was actively misdirecting cognitive tiers.** The cooperation bonus was rewarding agents for burning energy on share events that didn't help survival. The "cognition advantage" was not inflated by the tautology — it was *suppressed* by the tautology.

3. **The "pro-social selection" finding from E003 is now reframed.** Betrayal-frequency declines were not emergent altruism; they were selection chasing the cooperation reward. With the reward removed, agents converge on near-zero cooperation. Whatever pro-sociality this simulator demonstrates, it is contingent on the fitness function paying for it.

4. **The cognitive advantage is robust across env types.** The +0.24-0.30 gap appears in both cyclic (temporal structure) and hard grid (multi-factor scarcity) configs. Not specific to either regime.

## What the evidence does NOT support

1. **"Cognitive agents are inherently more cooperative"** — the opposite was found. Without external reward for cooperation, evolved cognitive agents nearly stop cooperating altogether.

2. **The original E003 framing of "pro-social selection emerges unprompted"** — it doesn't. It's an artifact of the cooperation fitness term. The honest version: in this simulator, agents cooperate when the fitness function rewards it; they don't when it doesn't.

3. **Memory tier as a meaningful intermediate** — even in this cleaner setup, memory's improvement over reflex remains within noise (cyclic: 0.629 vs 0.614; hard grid: 0.486 vs 0.475). Confirms the E005 finding that memory's contribution is bottlenecked by retrieval.

## Caveats

- **n=5 still small.** The full > reflex effect size in cyclic env (+0.298) is so large relative to its stdev (0.045) that even at n=5 the binomial test is overwhelmingly significant, but real claims would still want n=20.
- **The genome still has cooperation-related weights** (`cooperation_weight`, `reciprocity_weight`, `social_learning_weight`, etc.). These didn't drift to zero — they drifted to whatever values happen to support the new survival-focused strategy. We haven't analyzed which weights changed.
- **This may be specific to the exact cost-benefit structure** (`share_cost = 2.0`, `food_energy = 12.0`). In a different cost regime cooperation might be net positive for survival. Worth varying.

## Implications for the project

This experiment substantially **strengthens** the architectural foundation:
- The headline finding (full > reflex on survival) is now ~3× larger and more robust than before.
- We caught a real misalignment in the fitness function. Without E007 we'd have continued claiming "pro-social selection emerges" when in fact our reward function was prompting it.
- The decoupled-fitness infrastructure built in the foundation refit paid for itself on its first test.

It also sharpens what's left to verify:
- The "lineage of staged emergence" claim now needs a different mechanism for cooperation than the fitness reward. Suggested follow-up: introduce environmental conditions where cooperation directly helps survival (E012's mandatory-cache-tile mechanic) and re-test whether cooperation re-emerges without a fitness bonus.

## Suggested next experiments

1. **E008 — n=20 seeds on the no-coop-fitness condition** (highest priority). Convert the spectacular +0.298 finding to robust statistical evidence.
2. **E012 — mandatory-cooperation tile** (food cache that requires ≥2 adjacent agents to harvest). Tests whether cooperation re-emerges when the *environment*, not the fitness function, makes it survival-relevant.
3. **E006 — time-aware memory retrieval** (still queued from E005). Now that we know the survival metric is clean, memory's true contribution can be tested honestly.
4. **E009 — transfer evaluation.** Train in cyclic without-coop, evaluate in grid without-coop. Tests generalization of the genuinely-survival-selected genomes.

## One-line conclusion

The fitness function was masking the cognition advantage by paying agents to do something costly. With that bookkeeping fixed, full > reflex on pure survival is ~3× larger and more robust than the original headline claimed — and the "pro-social selection" we celebrated turned out to be a fitness-function artifact, not an emergent property.
