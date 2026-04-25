# Primate Developmental Intelligence Simulator

Primate Developmental Intelligence Simulator is a research sandbox for studying whether increasingly general agent behavior can emerge from staged environmental interaction, causal learning, social pressure, memory evolution, and selection across generations.

This is **not** "LLM agents in a chatroom." It is a developmental-evolutionary simulation where intelligence is hypothesized to emerge from pressures, not prompts.

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
```

Compare `data/runs/<run_id>/metrics.csv` across tiers. If adding cognition actually helps, you'll see survival, fitness, and prediction accuracy climb as you go up tiers.

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

- Add **shared intentionality** (two agents collaborating on a goal that requires both).
- Add **culture**: let offspring inherit a summary of a parent's useful memories.
- Plug in an **LLM policy** as a new `CognitionPolicy` subclass and compare against the rule-based full tier.
- Add **theory of mind**: let agents maintain a model of other agents' self-models.
