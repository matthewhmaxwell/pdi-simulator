# Experiment Index

Chronological log of all simulation experiments. Each entry links to a writeup, names the question being asked, and gives a one-line headline.

When adding a new experiment, follow the [`docs/EXPERIMENT_TEMPLATE.md`](docs/EXPERIMENT_TEMPLATE.md) and add an entry here.

| #     | Date       | Question                                                                              | Headline                                                                                            | Writeup                                  |
|-------|------------|---------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| E001  | 2026-04-24 | Does climbing the cognition lineage (reflex→memory→social→full) improve outcomes?     | Mixed. Reflex wins survival in the easy env (0.92); cognitive tiers win fitness but lose survival. | [EXPERIMENT_001.md](EXPERIMENT_001.md)   |
| E002  | 2026-04-24 | Does cognition pay off in a harder environment (food=15, haz=20, respawn=0.02)?       | Survival ranking flips: full=0.60 > reflex=0.48. Pro-social selection emerges. (n=2 seeds — see E003.) | [EXPERIMENT_002.md](EXPERIMENT_002.md)   |
| E003  | 2026-04-25 | Is the E002 result robust across seeds, and which environmental knob caused it?       | Sign-consistent across 5 seeds (full−reflex = +0.093 ± 0.040). **No single knob produces the inversion**; only the combined three-knob regime does. | [EXPERIMENT_003.md](EXPERIMENT_003.md)   |
| E004  | 2026-04-26 | Why does memory tier consistently underperform reflex? (E003 anomaly)                 | The "underperformance" was variance, not a mean gap. v1 fix tanked survival 0.21; v2 fix matched reflex priority order and cut variance 3.5×. | [EXPERIMENT_004.md](EXPERIMENT_004.md)   |
| Refit | 2026-04-26 | Convert toy testbed → defensible foundation: pluggable envs, decoupled fitness, LLM-tier stub, novelty metric. | Phase-1 foundation refit. New `environments/` package, `CyclicEnvironment` for temporal structure, `FitnessWeights` for tautology ablation, `LLMPolicy` stub. 32 tests pass. See [ROADMAP.md](ROADMAP.md). | [ROADMAP.md](ROADMAP.md)                  |
| E005  | 2026-04-26 | Does memory tier outperform reflex when the env has temporal structure to learn?      | First monotonic tier ordering observed (reflex<memory<social<full). Full > reflex by +0.086, sign-consistent on 5 seeds — generalizes E003 to a new env. Memory's individual lift is weak (+0.015, not sign-consistent) — bottlenecked by retrieval, hypothesis not confirmed as stated. | [EXPERIMENT_005.md](EXPERIMENT_005.md)   |
| E007  | 2026-04-26 | Does full > reflex hold when we ablate the cooperation tautology in fitness?          | **Bigger, not smaller.** Without coop-reward, gap is +0.298 cyclic / +0.240 grid — ~3× larger than before, sign-consistent in both envs. Tautology was *masking* the advantage. Cognitive agents stopped cooperating (1500/ep → 10/ep) and survived more. "Pro-social selection" from E003 was a fitness-function artifact. | [EXPERIMENT_007.md](EXPERIMENT_007.md)   |
| E008  | 2026-04-27 | Does the E007 finding survive at n=20 seeds?                                          | **Yes.** Cyclic: +0.290 ± 0.038, **20/20 seeds positive**, p=1.91e-06. Hard grid: +0.243 ± 0.046, **20/20 seeds positive**, p=1.91e-06. n=20 means within ±0.008 of n=5 estimates. | [EXPERIMENT_008.md](EXPERIMENT_008.md)   |
| E006  | 2026-04-27 | Does memory tier finally outperform reflex once retrieval is time-aware?              | **Yes.** Built per-tile food-observation history + `predict_food_return`. Memory tier in cyclic env: 0.629 → 0.767 (+0.138 paired-seed lift). Memory − reflex gap: +0.015 → +0.153, sign-positive 5/5 seeds. The E005 prediction was correct. | [EXPERIMENT_006.md](EXPERIMENT_006.md)   |
| E006b | 2026-04-27 | Does the E006 retrieval hurt memory tier in random-respawn (no periodicity) env?      | **No.** Memory ≈ reflex (+0.016 ± 0.023), within noise, 4/5 seeds positive. Time-aware retrieval is well-gated; safe to keep on by default. | [EXPERIMENT_006b.md](EXPERIMENT_006b.md) |
| E009  | 2026-04-27 | Does the cognition advantage transfer between cyclic and hard-grid envs?              | **Yes.** Full−reflex gap survives transfer with sub-stdev shrinkage. cyclic-trained: +0.300 home → +0.293 abroad (5/5 seeds). grid-trained: +0.352 home → +0.308 abroad (5/5 seeds). Cognition is a property of the genome, not the training env. New CLI: `pdi transfer-eval`. | [EXPERIMENT_009.md](EXPERIMENT_009.md)   |

## What we've established so far

Read in this order:
1. **The architecture works.** Genomes evolve, populations converge, metrics differ across tiers ([E001](EXPERIMENT_001.md)).
2. **Cognition is regime-dependent.** It costs survival in easy environments and pays off in hard ones ([E002](EXPERIMENT_002.md)).
3. **The pay-off requires multi-factor pressure.** No single knob (food scarcity, hazards, slow respawn) produces the inversion. Only the combination does ([E003](EXPERIMENT_003.md)).
4. **Pro-social selection is real.** Across all seeds in cognitive tiers, betrayal frequency drops over generations without being penalized in the fitness function ([E003](EXPERIMENT_003.md)).
5. **The "memory underperforms reflex" anomaly was variance, not a real mean gap.** Pre-fix memory was 0.460 ± 0.078 vs reflex's 0.475 ± 0.018. After a (failed) v1 fix and a (correct) v2 fix matching reflex's priority order, memory is now 0.486 ± 0.022 — same mean, **3.5× tighter variance**. Details in [E004](EXPERIMENT_004.md).
6. **The full-tier survival advantage generalizes to a structurally different env** ([E005](EXPERIMENT_005.md)). The +0.086 ± 0.037 in cyclic env is essentially the same magnitude as +0.093 ± 0.040 in the E003 hard grid env. Sign-consistent across 5 seeds. Plus: first monotonic tier ordering observed.
7. **Memory tier's lift is bottlenecked by retrieval, not by env design** ([E005](EXPERIMENT_005.md)). Even with explicit temporal structure, current `MemoryStore` retrieves by state-tag overlap not timestamp pattern, so memory tier can't exploit periodicity. Real test of the hypothesis requires building time-aware retrieval.
8. **The fitness function in E001-E006 was masking the cognition advantage, not inflating it** ([E007](EXPERIMENT_007.md)). With `--no-coop-fitness`, full > reflex jumps from +0.086/+0.093 to +0.298/+0.240 in the two envs (~3× bigger). The cooperation reward was paying cognitive agents to burn energy on share events that hurt survival.
9. **"Pro-social selection emerges unprompted" from E003 was wrong** ([E007](EXPERIMENT_007.md)). With the cooperation reward removed, cognitive agents nearly stop cooperating (1500/episode → 10/episode). The pro-sociality was selection chasing the fitness term, not emergent altruism.
10. **The headline survives n=20 robustness** ([E008](EXPERIMENT_008.md)). Full > reflex on survival in the no-coop-fitness condition: cyclic +0.290 ± 0.038, hard grid +0.243 ± 0.046, both **20/20 seeds positive**, binomial p ≤ 1.91e-06. n=5 estimate was within ±0.008 of the n=20 mean.
11. **Time-aware memory delivers the first real memory-tier lift** ([E006](EXPERIMENT_006.md)). Per-tile food-observation history + `predict_food_return` lifts memory tier cyclic survival 0.629 → 0.767. Memory−reflex gap goes from +0.015 (within noise) to +0.153, sign-consistent 5/5. Confirms the E005 prediction that memory was bottlenecked by retrieval, not by env design.
12. **The cognition advantage transfers between envs** ([E009](EXPERIMENT_009.md)). Frozen genomes evaluated in an env they weren't trained in still beat reflex by approximately the same margin. Cyclic-trained gap: +0.300 home → +0.293 abroad. Grid-trained gap: +0.352 home → +0.308 abroad. Both 5/5 sign-consistent. **First evidence the simulator produces a generalizable cognitive trait, not just env-specific overfitting.**
13. **Time-aware memory is well-gated, safe in non-periodic envs** ([E006b](EXPERIMENT_006b.md)). In random-respawn grid env where periodicity isn't there, memory ≈ reflex (+0.016 ± 0.023, within noise). The retrieval pays off when its predicate holds and goes silent otherwise.

## What's still load-bearing but unverified

- Fitness comparison is partly tautological — `update_fitness` rewards cooperation events directly ([`agent.py`](src/pdi/agent.py)). Survival is the clean comparison; fitness should be reported with an asterisk until decoupled.
- Mechanism: we don't yet know *why* cognition's losses across knobs are sub-additive when reflex's are additive.
- Strategy diversity collapses to ~0.10 in every config. We haven't tested whether selection is finding genuinely different optima or just collapsing to the same one across runs.

## Open questions ranked

(See [ROADMAP.md](ROADMAP.md) for the phased plan. Phase 1 + Phase 2 done.)

1. **E012 — Mandatory-cooperation tile.** Now that we know cognitive agents won't cooperate without a fitness reward, test whether they will when the *environment* requires cooperation for survival.
2. **E010 — Real `LLMPolicy` implementation.** Wire the Anthropic SDK with prompt caching; compare LLM tier against rule-based on transfer envs.
3. **E011+ — Add cognitive layers** (theory of mind, shared intentionality, culture) — Phase 3 work.
4. **E006c — re-run E006b in scarcity grid env** (food=15 instead of 30). Confirms E006 retrieval is also benign when stakes are higher (E006b ran at near-survival ceiling).
