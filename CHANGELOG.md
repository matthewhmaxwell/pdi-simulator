# Changelog

Notable code, config, and methodology changes. Experiments themselves live in [EXPERIMENTS.md](EXPERIMENTS.md).

## Unreleased

### Fixed
- **MemoryPolicy action-priority order matches ReflexPolicy** ([`src/pdi/cognition.py`](src/pdi/cognition.py)): food-seeking → hazard dodge → shelter → memory consult → random. Pre-fix, memory consultation could preempt food-seeking, producing high run-to-run variance (stdev 0.078 vs 0.022 post-fix). Note: a v1 attempt that put hazard-dodge before food-seeking actually tanked survival 0.21 points in scarcity regimes — only v2 (matching Reflex priority exactly) is correct. See [E004](EXPERIMENT_004.md) for the full story.

### Added
- [`tests/test_agent.py::test_memory_policy_walks_toward_visible_food_not_consults_memory`](tests/test_agent.py) — regression test that locks the MemoryPolicy fix.
- [`docs/EXPERIMENT_TEMPLATE.md`](docs/EXPERIMENT_TEMPLATE.md) — template for future experiment writeups.
- [`EXPERIMENTS.md`](EXPERIMENTS.md) — chronological index of all experiments.
- This file.

## 0.1.0 — 2026-04-24

### Added
- Initial scaffold: env / agent / memory / social / cognition / evolution / evaluation / CLI.
- 4 cognition tiers (reflex, memory, social, full) for ablation experiments.
- CLI flags `--food`, `--hazards`, `--shelters`, `--respawn` for environment knob tuning ([`src/pdi/main.py`](src/pdi/main.py)).
- 18 unit tests covering env, agent, memory, social, evolution.
- [`scripts/compare_tiers.py`](scripts/compare_tiers.py) — cross-tier metric aggregation.
- [`scripts/run_robustness_sweep.sh`](scripts/run_robustness_sweep.sh), [`scripts/analyze_robustness.py`](scripts/analyze_robustness.py) — E003 sweep + analysis.
- Experiments E001, E002, E003.
