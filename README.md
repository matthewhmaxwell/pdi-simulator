# Primate Developmental Intelligence Simulator

A small evolutionary sandbox with **pluggable environments**, **swappable cognition tiers** (reflex / memory / social / full / LLM), **decoupled fitness components**, and an honest experimental record. Designed so each cognitive layer can be turned on, off, or compared in isolation.

The aspirational name precedes the science by a wide margin — see [ROADMAP.md](ROADMAP.md) for an honest discussion of what we have versus what we'd need to earn the bigger labels. This is currently a defensible foundation for additional intelligence-research work, **not** yet a model of primate cognition or general intelligence.

## The thesis

The staged developmental lineage we are probing:

```
environment awareness
    → causal learning
    → social awareness
    → cooperation / competition
    → theory of mind
    → shared intentionality
    → culture
    → self-modeling
```

The simulator is structured so each of these can be turned on, off, or swapped as an experimental variable.

## What we've found so far

See [EXPERIMENTS.md](EXPERIMENTS.md) for the full chronological log. Top-line:

- **The architecture works** ([E001](EXPERIMENT_001.md)). Genomes evolve, populations converge under selection, metrics differ across cognition tiers.
- **Cognition is regime-dependent** ([E002](EXPERIMENT_002.md)). It costs survival in easy environments and pays off in hard ones.
- **The pay-off requires multi-factor pressure** ([E003](EXPERIMENT_003.md)). No single environmental knob (food scarcity, hazards, slow respawn) produces the inversion — only the combined three-knob regime does.
- **Memory tier had a policy bug** ([E004](EXPERIMENT_004.md)) that made it skip food-seeking. Diagnosed, fixed, verified.
- **Cognition advantage is real and ~3× larger than originally measured** ([E007](EXPERIMENT_007.md), [E008](EXPERIMENT_008.md)). After ablating the cooperation tautology in fitness, full > reflex survival is **+0.290 ± 0.038** (cyclic env) and **+0.243 ± 0.046** (hard grid env), **sign-consistent across all 20 seeds**, binomial p ≤ 1.91e-06.
- **The "pro-social selection" claim was wrong.** With cooperation no longer rewarded in fitness, evolved cognitive agents stop sharing (1500/episode → ~10/episode) and survive *more*. The fitness function was misdirecting them.
- **Time-aware memory delivers a real lift** ([E006](EXPERIMENT_006.md)). Per-tile food-observation history + period prediction lifts memory-tier survival 0.629 → 0.767 in cyclic env. First robust memory-tier-beats-reflex result. Doesn't hurt in non-periodic envs ([E006b](EXPERIMENT_006b.md)).
- **Cognition transfers between envs** ([E009](EXPERIMENT_009.md)). Frozen genomes evaluated in an env they weren't trained in still beat reflex by ≈ the same margin. Cyclic-trained: gap +0.300 home → +0.293 abroad (5/5 seeds). Grid-trained: +0.352 home → +0.308 abroad (5/5 seeds). First evidence of a generalizable cognitive trait, not just env-specific overfitting.

The lineage is not yet validated. We have one regime where full-tier cognition beats reflex on survival, with the effect requiring compound environmental pressure. The honest framing is "suggestive directional evidence" not "thesis confirmed."

See also: [CHANGELOG.md](CHANGELOG.md), [docs/EXPERIMENT_TEMPLATE.md](docs/EXPERIMENT_TEMPLATE.md).

## What the simulator does

- Runs a 2D grid world with food, hazards, shelters, and other agents.
- Populates it with agents carrying a mutable **StrategyGenome** (exploration, cooperation, memory reliance, risk tolerance, etc.).
- Each agent accumulates **memory events**, **causal beliefs**, **social beliefs about peers**, and a **self-model** across an episode.
- After every generation, fitness is computed, elites are selected, offspring inherit mutated genomes (but not lifetime memory — learning is the phenotype, not the genotype).
- Metrics are exported so you can **measure** whether added cognition actually improves survival and adaptation.

## Repo layout

```
pdi-simulator/
├── pyproject.toml
├── README.md
├── src/pdi/
│   ├── config.py          # knobs (env / agent / evolution)
│   ├── schemas.py         # Pydantic models for every persisted object
│   ├── environment.py     # grid world
│   ├── memory.py          # structured, bounded, usefulness-ranked memory
│   ├── social.py          # per-peer SocialBelief model
│   ├── cognition.py       # reflex / memory / social / full policy tiers
│   ├── agent.py           # Agent: state + cognition + learning
│   ├── evolution.py       # episodes, selection, mutation, crossover
│   ├── evaluation.py      # metrics + CSV/JSON export
│   ├── logging_utils.py
│   └── main.py            # CLI
├── tests/
│   ├── test_environment.py
│   ├── test_agent.py
│   └── test_evolution.py
└── data/
    ├── runs/              # one subdirectory per run
    └── agents/
```

## Install

```bash
cd pdi-simulator
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the baseline experiment

```bash
pdi run --generations 20 --agents 50 --episodes 10
```

### Comparison experiments (the whole point)

The `--tier` flag toggles how much cognition agents get. Run each with the same seed and population to compare.

```bash
# Tier 0 — pure reflex, no memory, no social
pdi run --tier reflex --label t0_reflex --seed 42

# Tier 1 — reflex + memory
pdi run --tier memory --label t1_memory --seed 42

# Tier 2 — + social beliefs (trust / reciprocity / threat)
pdi run --tier social --label t2_social --seed 42

# Tier 3 — + causal beliefs + curiosity + exploitation
pdi run --tier full --label t3_full --seed 42

# Tier 4 — LLM policy (currently a stub that falls through to full; see ROADMAP)
pdi run --tier llm --label t4_llm --seed 42
```

Compare `data/runs/<run_id>/metrics.csv` across tiers. If adding cognition actually helps, you'll see survival, fitness, and prediction accuracy climb as you go up tiers.

### Switching environments

```bash
# Default: random-respawn grid world (no temporal structure for memory to exploit)
pdi run --env grid --tier full

# Cyclic env: fixed feeding grounds with periodic respawn (memory should pay off)
pdi run --env cyclic --tier full --respawn 0.05  # respawn period = 1/0.05 = 20 steps
```

### Ablating tautologies

```bash
# Zero out the cooperation fitness bonus to test whether the cognition-tier
# survival win holds without the direct fitness reward for cooperation events.
pdi run --tier full --no-coop-fitness --label e7_decoupled
```

### Other commands

```bash
pdi summarize-run <run_id>
pdi inspect-agent <agent_id> --run-id <run_id>
pdi export-metrics <run_id> --out /tmp/out.csv
```

## Metrics tracked per generation

| Metric                     | What it tells you                                          |
| -------------------------- | ---------------------------------------------------------- |
| `avg_survival_rate`        | Fraction of agents alive at the end of an episode          |
| `avg_fitness`              | Composite score (survival + food + coop + prediction)      |
| `avg_resource_collection`  | Foraging efficiency                                        |
| `cooperation_frequency`    | Share actions per episode                                  |
| `betrayal_frequency`       | Withhold actions per episode                               |
| `prediction_accuracy`      | Did memory-based predictions match observed outcomes?      |
| `social_trust_accuracy`    | Do predicted behaviors match observed helpful/harmful acts |
| `memory_usefulness`        | Mean usefulness of retained memories                       |
| `strategy_diversity`       | Genome variation across the population                     |
| `improvement_vs_baseline`  | Fitness delta vs generation 0                              |

Exported to `data/runs/<run_id>/metrics.csv` and `.../run.json`.

## Architecture notes

- **Every module is replaceable.** The cognition tier is picked at runtime — an LLM policy can be dropped in by adding a new `CognitionPolicy` subclass in `cognition.py` with the same `choose_action` signature.
- **Memory is structured, not a transcript.** Events carry `observed_state`, `action_taken`, `outcome`, `reward_delta`, `inferred_cause`, and `usefulness`. Forgetting is biased toward low-usefulness events so useful memories accumulate.
- **Causal beliefs are explicit.** `CausalBelief(action, context, predicted_outcome, observed_count, success_count)` — so when an agent learns "collect when food is near → positive outcome," you can inspect the belief directly.
- **Social beliefs are explicit.** `SocialBelief(other_agent_id, trust, threat, reciprocity, observed_helpful, observed_harmful, predicted_behavior)` — per-peer, updated on every interaction.
- **The self-model updates after each episode.** Strengths, weaknesses, preferred strategy, predicted survival.
- **Memory does not cross generations.** Genomes do. This matches the "learning is the phenotype" framing.

## Design principles

- Inspectable by default. No intelligence hidden inside a prompt you can't read.
- Every improvement must be measurable against a lower-tier baseline.
- Simple mechanisms that can be tested — the module boundaries are where experiments swap in and out.
- Built for experimentation, not demo theater.

## Running tests

```bash
pytest
```

## What to try next

See [ROADMAP.md](ROADMAP.md) for the phased plan. Current Phase-2 priorities:
1. **E007** — `--no-coop-fitness` on hard-env: does cognition still win without the tautological reward?
2. **E008** — n=20 seeds on the headline finding to convert "suggestive" → "robust."
3. **E009** — transfer evaluation: train in env A, test (no learning) in env B.

Longer-horizon Phase 3 (only after Phase 2 verifies):
- Add **shared intentionality** (two agents collaborating on a goal that requires both).
- Add **culture**: let offspring inherit a summary of a parent's useful memories.
- Plug in an **LLM policy** as a new `CognitionPolicy` subclass and compare against the rule-based full tier.
- Add **theory of mind**: let agents maintain a model of other agents' self-models.
