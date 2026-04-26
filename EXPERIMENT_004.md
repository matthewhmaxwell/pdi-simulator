# Experiment 004 — Diagnosing the memory-tier "underperformance"

> **One-line question.** [E003](EXPERIMENT_003.md) flagged that memory tier consistently underperforms reflex on survival. Why, and can we fix it?

## Setup

- **Configs run:**
  - `data/runs/e2_*` — pre-fix runs (5 seeds at E002 hard-env config), reused from E003.
  - `data/runs/e4_*` — v1 fix attempt (4 tiers × 5 seeds). All 20 runs.
  - `data/runs/e4v2_memory_s*` — v2 fix (memory tier only × 5 seeds). 5 runs.
- **Seeds:** 42, 7, 1, 13, 99 throughout.
- **Hard-env config:** food=15, hazards=20, shelters=4, respawn=0.02, grid 20×20, 80 steps, 50 agents, 20 generations, 10 episodes/gen.

## What changed since E003

Two code edits to [`src/pdi/cognition.py::MemoryPolicy`](src/pdi/cognition.py).

**v1 fix (incorrect).** I noticed `MemoryPolicy.choose_action` collected food underfoot but did *not* walk toward visible food before consulting memory — instead it fell through to a memory consult, which often returned an unrelated action. I "fixed" this by adding food-seeking explicitly. But I also reordered the action priorities so hazard dodging came *before* food-seeking. ReflexPolicy puts food first.

**v2 fix (correct).** Reverted the priority order to match Reflex exactly (food → hazard → shelter), keeping the memory consult only as the no-urgent-action fallback. The only behavioral delta vs. Reflex is what happens in the otherwise-random fallback slot: memory consult instead of coin flip.

Also added [`tests/test_agent.py::test_memory_policy_walks_toward_visible_food_not_consults_memory`](tests/test_agent.py) — a regression test that locks the food-seeking-before-memory invariant.

## Results

### Memory tier survival, per seed, across all three versions

| seed  | pre-fix  | v1 (hazard-first)  | v2 (food-first)   |
|-------|----------|--------------------|-------------------|
| 42    | 0.400    | 0.266              | 0.474             |
| 7     | 0.506    | 0.256              | 0.480             |
| 1     | 0.356    | 0.230              | 0.514             |
| 13    | 0.494    | 0.258              | 0.460             |
| 99    | 0.542    | 0.240              | 0.502             |
| **mean ± stdev** | **0.460 ± 0.078** | **0.250 ± 0.015** | **0.486 ± 0.022** |

### Memory minus Reflex (reflex baseline = 0.475 ± 0.018)

| version          | memory − reflex   | seeds where memory > reflex |
|------------------|-------------------|-----------------------------|
| pre-fix          | −0.016 ± 0.083    | 3/5                         |
| v1 hazard-first  | −0.225 ± 0.027    | 0/5                         |
| v2 food-first    | **+0.011 ± 0.015** | 3/5                         |

### What actually changed

1. **The "memory underperforms reflex" claim from E003 was driven by variance, not a real mean gap.** Pre-fix mean diff was −0.016 ± 0.083 — well within noise, and 3 of 5 seeds actually had memory winning. The high stdev (0.078) made it look anomalous on average.

2. **v1 fix tanked survival by 0.21.** Putting hazard-dodging *before* food-seeking made agents over-cautious in a scarcity regime: they avoid damage but starve before reaching food. Net survival 0.250 — worst of all three versions.

3. **v2 fix eliminates the variance problem.** Memory survival is now 0.486 ± 0.022 — basically tied with reflex (0.475 ± 0.018) but with **3.5× tighter stdev**. The pre-fix flakiness came from stochastic memory consultation interfering with food-seeking 50% of the time; with memory relegated to no-urgent-action contexts, that interference is gone.

## What the evidence supports

1. **The original "anomaly" was a false alarm in the mean and a real signal in the variance.** Memory ≈ reflex on average, but pre-fix memory had wildly inconsistent runs because the policy occasionally derailed food-seeking in random episodes.

2. **Action-priority order in this env strongly favors aggressive food-seeking over cautious hazard-avoidance.** Both for memory tier (v1 vs v2) and for reflex itself. This is regime-dependent — different envs would prefer different priorities.

3. **Code changes confined to MemoryPolicy don't affect other tiers.** Reflex/social/full survival was *byte-identical* between pre-fix and v1 (delta = 0.000). SocialMemoryPolicy and FullPolicy override `choose_action` and don't fall through to MemoryPolicy. This was a useful sanity check on the diff blast radius.

## What the evidence does NOT support

1. **The fix doesn't make memory tier *beat* reflex.** It makes memory ≈ reflex with lower variance. To make memory genuinely outperform reflex, we'd need an environment where past observations carry predictive signal — e.g., cyclic food respawn, tile types that correlate with future events, or repeated agent-encounter patterns. The current env is mostly memoryless.

2. **No claim about the broader cognition lineage was changed.** Full > reflex (+0.093 ± 0.040) is unchanged because FullPolicy doesn't fall through to MemoryPolicy. The headline E003 finding still holds.

3. **The "memory tier consistently underperforms reflex in 4 of 5 single-knob configs"** statement from [E003](EXPERIMENT_003.md) was technically true but the gaps were within plausible variance for n=2 seeds. With v2 fix and 5 seeds, that gap is now negligible and we should re-run the knob-isolation pass to confirm.

## Caveats and known issues

- **n=5 still small.** A real publication would want n=20+ per cell. We're using n=5 here because each cell costs ~25 min wall.
- **Fix scoped to MemoryPolicy only.** SocialMemoryPolicy still has hazard-dodge before food-seeking ([`cognition.py:130`](src/pdi/cognition.py)). That's potentially the same bug pattern — worth checking whether reordering helps social/full survival in scarcity. **Open question, not addressed here.**
- **Failed-fix workflow caught a real regression.** Without the per-seed comparison, I'd have shipped v1 thinking it was an improvement. Lesson: always compare pre/post fix per-seed, not just on means.

## Suggested next experiments

1. **E005 — apply the same "food-first" priority fix to SocialMemoryPolicy.** Predict: similar variance reduction, similar near-zero mean change. If we see a *survival lift*, that's evidence the bug pattern matters in higher tiers too.
2. **E006 — re-run knob isolation with v2 memory.** Tightens the E003 attribution claims with the corrected memory tier.
3. **E007 — design an env where memory should genuinely help.** Cyclic food respawn (e.g., food returns to same tile after 20 steps). Test whether memory tier now beats reflex.
4. **E008 — decouple cooperation from fitness.** Re-run E003 firmness with `cooperation_bonus = 0` in [`agent.py::update_fitness`](src/pdi/agent.py). Does the full > reflex survival result hold without the tautological fitness reward?

---

**Reproduce:**
- v1 sweep: `bash scripts/run_e004_verify_fix.sh` (20 runs)
- v2 sweep: 5 inline `pdi run --tier memory --run-id e4v2_memory_s<seed>` calls
- Analysis: `python scripts/analyze_e004.py`
