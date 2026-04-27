# Experiment 006 — Time-aware memory retrieval

> **Pre-stated hypothesis (before running, written in [EXPERIMENT_005.md](EXPERIMENT_005.md)).** "Memory tier was bottlenecked by retrieval — `MemoryStore.retrieve_similar` looks at state-tag overlap, not timestamp pattern, so memory tier literally cannot exploit periodicity. Real test of the hypothesis requires building time-aware retrieval."
>
> **Headline.** Hypothesis confirmed. With per-tile food-observation history and a `predict_food_return` method wired into `MemoryPolicy`, memory tier survival jumps from 0.629 → 0.767 in cyclic env, lifting the memory-vs-reflex gap from +0.015 (within noise) to **+0.153 ± 0.030, sign-consistent across 5/5 seeds**.

## What changed in code

### `src/pdi/memory.py` — added per-tile food-observation history

```python
class MemoryStore:
    def __init__(self, capacity: int = 200, tile_history_capacity: int = 50):
        ...
        # Per-tile food-observation log: position → [(step, had_food), ...]
        self.tile_food_observations: dict[tuple[int, int], list[tuple[int, bool]]] = {}

    def observe_tile(self, pos, step, has_food): ...
    def observe_local_view(self, observation, step): ...
    def predict_food_return(self, pos, current_step, max_lookback=100) -> Optional[int]:
        """Median consecutive-delta between food observations, minus elapsed time."""
    def known_feeding_ground(self, pos, min_observations=2) -> bool: ...
```

`predict_food_return` is deliberately simple: take the median delta between consecutive food sightings at this tile as the period estimate, then return `max(0, period − elapsed)`. It returns `None` if we've seen food at this tile fewer than twice. This is a passable estimator for `CyclicEnvironment` (truly periodic) and produces noise on `GridWorldEnvironment` (random respawn) — that's fine, the consumer only acts on it when confidence is high.

### `src/pdi/agent.py` — record observations into the per-tile log

```python
self.memory.add(ev)
self.novel_state_tags.add(_state_tag(observation))
self.memory.observe_local_view(observation, timestamp)  # E006
```

### `src/pdi/cognition.py::MemoryPolicy.choose_action` — two new affordances

1. **Wait at known feeding grounds.** If standing on a tile we've seen food at multiple times before, and `predict_food_return` says food returns within `_wait_threshold_steps` (default 5), choose `observe` instead of moving.
2. **Walk toward predicted-food tiles.** If a known feeding ground in vision range is predicted to fruit at roughly the time we'd arrive (minimize `|steps_until − travel_distance|`), head there.

Both are gated by `genome.memory_reliance` so the population still gets to evolve how much to trust memory. Action priority above this stays the same as the E004 v2 fix (food → hazard → shelter → memory consult → random).

## Results

5 seeds (42, 7, 1, 13, 99), cyclic env, no-coop-fitness, n=50 pop, 20 gens, 10 ep/gen.

| seed | reflex | memory (old) | memory (E006) |
|------|--------|--------------|---------------|
| 42   | 0.606  | 0.634        | **0.758**     |
| 7    | 0.630  | 0.622        | **0.754**     |
| 1    | 0.614  | 0.660        | **0.776**     |
| 13   | 0.616  | 0.622        | **0.814**     |
| 99   | 0.604  | 0.608        | **0.732**     |

**Aggregates:**

|                 | reflex          | memory (old)    | memory (E006)  |
|-----------------|-----------------|-----------------|----------------|
| mean ± stdev    | 0.614 ± 0.010   | 0.629 ± 0.020   | **0.767 ± 0.031** |

**Memory − reflex gap:**

|                | mean ± stdev   | sign-positive seeds |
|----------------|----------------|---------------------|
| old retrieval  | +0.015 ± 0.022 | 4/5                 |
| E006 retrieval | **+0.153 ± 0.030** | **5/5**         |

**E006 lift (paired by seed):** +0.138 ± 0.031, positive on 5/5 seeds. Per-seed: [+0.124, +0.132, +0.116, +0.192, +0.124].

## What the evidence supports

1. **Memory tier finally outperforms reflex when given retrieval that uses timing.** This was the explicit prediction from E005 — "real test of the hypothesis requires building time-aware retrieval" — and it holds. The architecture now demonstrates that *adding the right kind of memory* improves outcomes in *the right kind of env*.
2. **Time-aware memory is a real ability, not a free win.** The ablation is paired: same env, same seeds, same population size, only the retrieval implementation differs. The +0.138 lift is the cleanest cognition-pays-off result this simulator has produced.
3. **The cognition lineage is now partially validated.** We have an env (cyclic) where memory beats reflex by +0.15 (E006), social beats memory by +0.09, full beats social by +0.05 (from E008's contaminated-but-directionally-valid table). The ordering is monotonic and the gaps are non-trivial.

## What the evidence does NOT support

1. **Memory tier helps in *all* envs.** The retrieval was added precisely because it should pay off in cyclic env. We have not yet verified this doesn't *hurt* memory tier in random-respawn grid envs, where `predict_food_return` will return noisy predictions. **Open question:** does memory tier under E006 retrieval still match reflex in `GridWorldEnvironment`? Worth a quick check (E006b).
2. **A general "memory makes agents smarter" claim.** The retrieval mechanism here is hand-coded to exploit periodicity. A truly general memory mechanism would need to learn what kind of structure to look for. We've added one specific affordance and shown it works for one specific env type.
3. **n=5 is small.** The effect is large enough that even at n=5 the binomial sign test is significant (`(0.5)^5 = 3.1%`), but real claims would want n=20.

## Caveats

- The contamination flagged in E008 (memory-tier runs in `e7c_memory_s2..s59` mixing old and new code) is not a problem here — the E006 verification ran the original 5 seeds (42, 7, 1, 13, 99) cleanly with the new code (`e6m_memory_s*`).
- `predict_food_return`'s period estimator is a median, not anything fancier (e.g., FFT, autocorrelation). It works because the env is *exactly* periodic. Real environments would need something more robust.
- The `_wait_threshold_steps = 5` and search radius `r = 5` in `MemoryPolicy.choose_action` are unsearched magic numbers. Different choices might tune this further.

## Suggested next experiments

1. **E006b — verify time-aware memory doesn't hurt in random-respawn env.** Run memory tier × cyclic env (we have it) AND grid env (we don't) at n=5 and compare to reflex. Predict: memory ≈ reflex in grid (within noise), memory > reflex in cyclic.
2. **E009 — transfer evaluation.** Train memory-tier agents in cyclic, evaluate (no learning) in grid. Do their evolved genomes generalize?
3. **Continue the queue:** E012 mandatory-cooperation tile, E010 real LLM policy.

## One-line conclusion

Building the right kind of memory affordance — per-tile food history with periodicity prediction — produces the first robustly measurable lift the memory tier has shown in this simulator: +0.138 survival paired by seed, sign-consistent across 5/5 seeds.
