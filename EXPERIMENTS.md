# Experiment Index

Chronological log of all simulation experiments. Each entry links to a writeup, names the question being asked, and gives a one-line headline.

When adding a new experiment, follow the [`docs/EXPERIMENT_TEMPLATE.md`](docs/EXPERIMENT_TEMPLATE.md) and add an entry here.

| #     | Date       | Question                                                                              | Headline                                                                                            | Writeup                                  |
|-------|------------|---------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| E001  | 2026-04-24 | Does climbing the cognition lineage (reflex→memory→social→full) improve outcomes?     | Mixed. Reflex wins survival in the easy env (0.92); cognitive tiers win fitness but lose survival. | [EXPERIMENT_001.md](EXPERIMENT_001.md)   |
| E002  | 2026-04-24 | Does cognition pay off in a harder environment (food=15, haz=20, respawn=0.02)?       | Survival ranking flips: full=0.60 > reflex=0.48. Pro-social selection emerges. (n=2 seeds — see E003.) | [EXPERIMENT_002.md](EXPERIMENT_002.md)   |
| E003  | 2026-04-25 | Is the E002 result robust across seeds, and which environmental knob caused it?       | Sign-consistent across 5 seeds (full−reflex = +0.093 ± 0.040). **No single knob produces the inversion**; only the combined three-knob regime does. | [EXPERIMENT_003.md](EXPERIMENT_003.md)   |
| E004  | 2026-04-26 | Why does memory tier consistently underperform reflex? (E003 anomaly)                 | The "underperformance" was variance, not a mean gap. v1 fix tanked survival 0.21; v2 fix matched reflex priority order and cut variance 3.5×. | [EXPERIMENT_004.md](EXPERIMENT_004.md)   |

## What we've established so far

Read in this order:
1. **The architecture works.** Genomes evolve, populations converge, metrics differ across tiers ([E001](EXPERIMENT_001.md)).
2. **Cognition is regime-dependent.** It costs survival in easy environments and pays off in hard ones ([E002](EXPERIMENT_002.md)).
3. **The pay-off requires multi-factor pressure.** No single knob (food scarcity, hazards, slow respawn) produces the inversion. Only the combination does ([E003](EXPERIMENT_003.md)).
4. **Pro-social selection is real.** Across all seeds in cognitive tiers, betrayal frequency drops over generations without being penalized in the fitness function ([E003](EXPERIMENT_003.md)).
5. **The "memory underperforms reflex" anomaly was variance, not a real mean gap.** Pre-fix memory was 0.460 ± 0.078 vs reflex's 0.475 ± 0.018. After a (failed) v1 fix and a (correct) v2 fix matching reflex's priority order, memory is now 0.486 ± 0.022 — same mean, **3.5× tighter variance**. Details in [E004](EXPERIMENT_004.md).

## What's still load-bearing but unverified

- Fitness comparison is partly tautological — `update_fitness` rewards cooperation events directly ([`agent.py`](src/pdi/agent.py)). Survival is the clean comparison; fitness should be reported with an asterisk until decoupled.
- Mechanism: we don't yet know *why* cognition's losses across knobs are sub-additive when reflex's are additive.
- Strategy diversity collapses to ~0.10 in every config. We haven't tested whether selection is finding genuinely different optima or just collapsing to the same one across runs.

## Open questions ranked

1. Does SocialMemoryPolicy have the same hazard-before-food bug as MemoryPolicy v1? Apply the same priority fix and re-measure (E005).
2. Re-run knob isolation with v2 memory — does the E003 attribution story hold? (E006)
3. Design an env where memory should genuinely help (cyclic respawn). Does memory tier finally beat reflex? (E007)
4. Decouple cooperation from fitness (zero out `cooperation_bonus`). Does full > reflex hold without the tautological reward? (E008)
5. Can we add **culture** (memory inheritance) without re-introducing the same kind of policy bugs? (E009)
6. What does shared intentionality look like as an environment mechanic — a tile only harvestable by ≥2 agents acting in concert? (E010)
