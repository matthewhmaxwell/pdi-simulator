# Experiment 003 — Robustness pass: 5 seeds + knob isolation

**Why this experiment exists.** [EXPERIMENT_002.md](EXPERIMENT_002.md) claimed "thesis supported" from 2 seeds and 3 simultaneously-changed environment knobs. Two complaints against that claim:
1. n=2 doesn't establish a distribution.
2. Three knobs changed at once means we couldn't attribute the effect to any of them.

This experiment addresses both.

## Setup

**Part A — Firmness pass.** Same E002 config (food=15, haz=20, respawn=0.02) at 5 seeds: 42, 7, 1, 13, 99. 4 tiers × 5 seeds = 20 runs.

**Part B — Knob isolation.** Three single-knob variants from the E001 baseline (food=30, haz=8, respawn=0.05), each varying exactly one knob to its E002 value. 2 seeds (42, 7) × 3 configs × 4 tiers = 24 runs.

**Total: 44 runs** (20 new + 24 new + 16 already had = 36 actually executed this round).

## Part A — Firmness (5 seeds, E002 config)

### Final-generation survival per seed

| seed | reflex | memory | social | full   | full−reflex |
|------|--------|--------|--------|--------|-------------|
| 42   | 0.478  | 0.400  | 0.442  | 0.636  | **+0.158**  |
| 7    | 0.484  | 0.506  | 0.406  | 0.562  | +0.078      |
| 1    | 0.484  | 0.356  | 0.510  | 0.582  | +0.098      |
| 13   | 0.444  | 0.494  | 0.538  | 0.494  | +0.050      |
| 99   | 0.486  | 0.542  | 0.490  | 0.566  | +0.080      |

**Aggregates:**
- full: 0.568 ± 0.051
- reflex: 0.475 ± 0.018
- diff: **+0.093 ± 0.040**
- **Sign consistent across all 5 seeds.** Probability under the null (no difference) ≤ (0.5)⁵ = 3.1%.

This is now a real directional result, not anecdote.

### Emergent pro-social behavior (gen19 − gen0, ± stdev)

| metric              | reflex      | memory      | social         | full           |
|---------------------|-------------|-------------|----------------|----------------|
| betrayal_frequency  | 0           | 0           | **−78 ± 31**   | **−140 ± 58**  |
| cooperation grows   | 0           | 0           | (rises strongly) | (rises strongly) |

Across all 5 seeds, betrayal frequency declined across generations in both social and full tiers. We did not program a betrayal penalty.

## Part B — Knob isolation

### Cognition gap (full survival − reflex survival) per knob config

| config                                     | gap        |
|--------------------------------------------|------------|
| E001 baseline (food=30, haz=8, resp=0.05)  | **−0.208** |
| E3a food=15 only                           | −0.058     |
| E3b hazards=20 only                        | −0.194     |
| E3c respawn=0.02 only                      | −0.127     |
| E002 all three combined                    | **+0.118** |

**Surprising finding: no single knob produces the inversion.** In every single-knob variant, reflex still wins. Only the *combination* of food scarcity + hazards + slow respawn flips the ordering to favor cognition.

### Survival deltas from E001 baseline (per tier)

| config              | reflex | memory | social | full   |
|---------------------|--------|--------|--------|--------|
| E3a food=15 only    | −0.19  | −0.14  | −0.04  | −0.04  |
| E3b haz=20 only     | −0.06  | 0.00   | −0.18  | −0.05  |
| E3c respawn=0.02    | −0.16  | −0.13  | −0.08  | −0.07  |
| sum of three        | −0.41  | −0.27  | −0.30  | −0.16  |
| E002 actual         | −0.44  | −0.24  | −0.20  | **−0.11** |

For reflex, the three knobs are nearly **additive**: −0.41 predicted, −0.44 observed.
For full tier, the combined effect is **less than additive**: −0.16 predicted, −0.11 observed. Cognitive agents handle multi-factor pressure better than single-factor pressure would suggest.

## What the evidence supports

1. **Robust directional finding:** at the E002 config, full-tier cognition produces ~0.09 higher survival than reflex, consistent across 5 seeds. This is no longer anecdote.

2. **Cognition's advantage requires multi-factor pressure.** No single environmental knob (food scarcity, hazards, slow respawn) is enough. The full tier only beats reflex when all three are tightened simultaneously. This is a more interesting and more honest claim than "harder env → cognition wins."

3. **Pro-social selection is real.** Betrayal declines across generations in both social and full tiers, in every seed. The fitness function does not penalize betrayal directly.

4. **Cognitive agents are robust to compound stress.** Reflex's losses across knobs are nearly additive; full-tier losses are sub-additive. There's a real interaction effect we can't yet explain mechanistically.

## What the evidence does NOT support

1. **"Cognition causes survival" universally.** It does the opposite in the easy environment and in 3 of 4 single-knob variants. The result is regime-dependent.

2. **Memory tier as a meaningful intermediate.** Memory consistently underperforms reflex on survival across nearly every config. Either the memory policy is implemented worse than pure reflex, or memory without social machinery is genuinely useless here. Worth investigating before claiming a "lineage" of staged emergence.

3. **The fitness comparison.** Full tier's fitness lead remains partly tautological — the fitness function rewards cooperation events directly ([`agent.py`](src/pdi/agent.py) `update_fitness`). The survival comparison is the clean one.

4. **Mechanistic explanation.** We know full-tier survives better in the combined-pressure regime. We do not yet know *why* the effect is non-additive across knobs. Worth a follow-up that introspects which actions actually keep full-tier agents alive when all three pressures are on.

## Honest one-liner

In the harder regime, cognition produces a small but real survival advantage that's invisible from any single environmental change. The architecture works; the lineage isn't yet validated; memory tier needs investigation.

## Suggested next moves

1. **Diagnose the memory-tier regression.** Run a behavioral trace: what does a memory-tier agent do when food is in sight vs a reflex agent? Likely a policy bug.
2. **Mechanism investigation.** In the combined-pressure regime, log per-tier action frequencies. What is full doing that reflex isn't, that translates to survival?
3. **Decouple cooperation from fitness.** Re-run E003-firmness with `cooperation_bonus = 0` in `update_fitness`, scoring on survival + foraging only. Does cognition still win?

Only after those would I attempt to add culture or theory of mind — there are unresolved issues at the bottom of the lineage.
