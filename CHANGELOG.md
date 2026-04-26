# Changelog

Notable code, config, and methodology changes. Experiments themselves live in [EXPERIMENTS.md](EXPERIMENTS.md).

## Unreleased

### Foundation refit (Phase 1)

Major restructuring to convert the toy ablation testbed into a defensible foundation for additional intelligence-research work. See [ROADMAP.md](ROADMAP.md) for the phased plan.

#### Added — pluggable environments
- `src/pdi/environments/` package with abstract `BaseEnvironment`, concrete `GridWorldEnvironment` (existing behavior), and new `CyclicEnvironment` (fixed feeding grounds with periodic respawn). Each env subclass declares `_populate` and `tick_respawn` and inherits all queries.
- `ENV_REGISTRY` and `make_environment(name, cfg, rng)` factory.
- `src/pdi/environment.py` retained as a backward-compat shim re-exporting `GridWorldEnvironment` as `Environment`.
- `tests/test_environments.py` — 8 tests covering registry, both env types, and the cyclic respawn schedule.

#### Added — decoupled fitness
- `FitnessWeights` dataclass in [`config.py`](src/pdi/config.py) — every fitness component (survival, foraging, cooperation, betrayal, prediction, energy) has an independently configurable weight.
- `Agent.update_fitness(weights=...)` now writes per-component scores to `agent.score_components` so each contribution is auditable, not just summed.
- `GenerationMetrics` extended with `survival_score_mean`, `foraging_score_mean`, `cooperation_score_mean`, `prediction_score_mean`, `avg_novelty`.

#### Added — novelty tracking
- Each agent tracks `novel_state_tags: set[str]` populated by `learn_from_outcome`. Reported as `avg_novelty` in metrics. Cognition-independent signal of exploration.

#### Added — LLM tier (interface-only stub)
- `LLMPolicy(FullPolicy)` in [`cognition.py`](src/pdi/cognition.py) — same interface as other tiers, falls through to `FullPolicy` for now. Wired into `build_policy("llm", ...)` and CLI `--tier llm`. Real Claude API call deferred to E010.

#### Added — CLI flags
- `--env {grid,cyclic}` — pick environment type.
- `--no-coop-fitness` — zero out `cooperation` and `betrayal_penalty` weights to ablate the tautology flagged in E003.
- `--tier llm` — pick LLM stub tier.

#### Added — docs
- [`ROADMAP.md`](ROADMAP.md) — phased plan from "small testbed" to "intelligence-research sandbox," with explicit honesty about what we've not earned yet.

### Fixed (carried from earlier in unreleased)
- **MemoryPolicy action-priority order matches ReflexPolicy** ([`src/pdi/cognition.py`](src/pdi/cognition.py)): food-seeking → hazard dodge → shelter → memory consult → random. Pre-fix, memory consultation could preempt food-seeking, producing high run-to-run variance (stdev 0.078 vs 0.022 post-fix). Note: a v1 attempt that put hazard-dodge before food-seeking actually tanked survival 0.21 points in scarcity regimes — only v2 (matching Reflex priority exactly) is correct. See [E004](EXPERIMENT_004.md) for the full story.

### Tests
- 32 tests pass (was 19). Added: 8 environment tests, 5 fitness/LLM tests.

## 0.1.0 — 2026-04-24

### Added
- Initial scaffold: env / agent / memory / social / cognition / evolution / evaluation / CLI.
- 4 cognition tiers (reflex, memory, social, full) for ablation experiments.
- CLI flags `--food`, `--hazards`, `--shelters`, `--respawn` for environment knob tuning ([`src/pdi/main.py`](src/pdi/main.py)).
- 18 unit tests covering env, agent, memory, social, evolution.
- [`scripts/compare_tiers.py`](scripts/compare_tiers.py) — cross-tier metric aggregation.
- [`scripts/run_robustness_sweep.sh`](scripts/run_robustness_sweep.sh), [`scripts/analyze_robustness.py`](scripts/analyze_robustness.py) — E003 sweep + analysis.
- Experiments E001, E002, E003.
