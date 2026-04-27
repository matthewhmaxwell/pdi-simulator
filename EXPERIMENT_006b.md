# Experiment 006b — Does time-aware memory retrieval hurt in random-respawn grid env?

> **Pre-stated hypothesis (in [E006](EXPERIMENT_006.md)).** "The time-aware retrieval was tuned for periodic respawn. Confirm it doesn't degrade memory tier in `GridWorldEnvironment` where periodicity isn't there to exploit."

> **Headline.** Confirmed. Memory tier (E006 retrieval) ≈ reflex in random-respawn grid env: +0.016 ± 0.023 survival, within noise. The new affordance neither hurts nor helps when its predicate (predictable periodicity) isn't satisfied.

## Setup

- 5 seeds (42, 7, 1, 13, 99), `--no-coop-fitness`, n=50 pop, 20 generations, 10 episodes/gen, 80 steps.
- **Env: random-respawn grid** (food=30, hazards=8, shelters=4, respawn_rate=0.05) — the original E001 baseline config. Food respawns probabilistically on empty tiles, no fixed feeding grounds, no period.
- 4 tiers × 5 seeds = 10 runs (just memory + reflex; the others were tested in E007/E008).
- **Reproduce:** `bash scripts/run_e006b_grid.sh`

## Results

| seed | reflex | memory (E006) |
|------|--------|---------------|
| 42   | 0.924  | 0.908         |
| 7    | 0.914  | 0.924         |
| 1    | 0.896  | 0.906         |
| 13   | 0.898  | 0.938         |
| 99   | 0.890  | 0.926         |

**Aggregates (n=5):**
- reflex: 0.904 ± 0.014
- memory (E006 retrieval): 0.920 ± 0.013
- **Memory − reflex gap: +0.016 ± 0.023, sign-positive 4/5 seeds.**

## What the evidence supports

1. **The E006 retrieval doesn't hurt in random-respawn envs.** The +0.016 ± 0.023 gap is within noise — about ⅔ of one stdev. We can layer the time-aware retrieval into the default `MemoryPolicy` without worrying about regressions in non-periodic envs.

2. **The retrieval is well-gated.** When `predict_food_return` returns noise (because periodicity isn't there), the policy mostly falls through to its non-temporal fallbacks. The "act on prediction" code paths are gated by `genome.memory_reliance` AND by tile-history minima, so they don't fire on garbage data.

## What the evidence does NOT support

1. **A general claim about robustness across all env types.** We tested random-respawn grid here and cyclic in [E006](EXPERIMENT_006.md). Other envs (e.g., predator/prey, multi-resource) might still surface failure modes.

2. **n=5 paired test.** Same caveat as the rest of the program — this is a small sample. The difference is small enough that even at n=20 it might or might not move.

## Caveats

- This config has **abundant food** (30 tiles vs E007's 15). Survival is near ceiling in both tiers (~90%), which makes the test less discriminating than scarcity regimes. A more aggressive test would re-run at food=15 in grid env to see if memory still ≈ reflex when stakes are higher. **Open follow-up: E006c at food=15 grid env.**
- One run (`e6b_reflex_s13`) was killed mid-execution by an unrelated systemd service restart and had to be re-run separately. Final data is clean.

## Implication

The E006 retrieval can stay enabled by default. It pays off in periodic envs (cyclic: +0.138 survival lift) and is silent in non-periodic envs (grid: +0.016, within noise). No regression cost.

## One-line conclusion

Time-aware memory retrieval doesn't help and doesn't hurt in random-respawn grid env. Safe to keep on by default.
