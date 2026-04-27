# Roadmap

This file tracks the project's evolution from "small ablation testbed" toward a more defensible intelligence-research sandbox. It complements [EXPERIMENTS.md](EXPERIMENTS.md) (chronological log) and [CHANGELOG.md](CHANGELOG.md) (code/methodology log) by stating where we're going and what would have to be true for us to claim the bigger labels.

## Honest framing

What we have now is a small evolutionary sandbox with pluggable cognition tiers, decoupled metrics, and an honest experimental record. It is **not** yet a model of primate cognition or a general-intelligence research platform. The aspirational name precedes the science by a wide margin. We're trying to close that gap.

## Phase 1 — Foundation refit (in progress)

**Goal:** convert the toy MDP testbed into something that can support multiple environments, multiple cognitive policies (including LLM-driven), and metrics that are not tautologically tied to fitness.

| Item | Status | Notes |
|------|--------|-------|
| Pluggable env interface (`environments/base.py`) | ✅ done | Abstract `BaseEnvironment`; subclasses declare `_populate` and `tick_respawn`. |
| `GridWorldEnvironment` (existing behavior) | ✅ done | E001-E004 reproducible. |
| `CyclicEnvironment` (fixed feeding grounds, periodic respawn) | ✅ done | Tests temporal structure; memory tier should now have a path to outperform reflex. |
| Decoupled fitness components (`FitnessWeights`) | ✅ done | `--no-coop-fitness` ablates the cooperation tautology flagged in E003. |
| Per-component score export (`survival_score_mean`, etc.) | ✅ done | Each fitness contribution is independently auditable in `metrics.csv`. |
| Novelty tracking (`avg_novelty`) | ✅ done | Unique state-tags visited per agent per episode — cognition-independent exploration signal. |
| `LLMPolicy` interface stub | ✅ done | Wired through CLI/build_policy; falls through to `FullPolicy` for now. Real call deferred to E010+. |
| E005: tier ablation in CyclicEnvironment | ✅ done | First monotonic tier ordering; full > reflex generalizes (+0.086, sign-consistent 5/5). Memory needed time-aware retrieval (E006). |

## Phase 2 — Verify the foundation actually works  ✅ DONE

**Goal:** before piling new mechanics on, confirm the foundation does what we built it to do.

| Item | Status | Result |
|------|--------|--------|
| **E005** — tier ablation in CyclicEnvironment | ✅ done | First monotonic tier ordering; memory bottlenecked by retrieval (→ E006). |
| **E006** — time-aware memory retrieval | ✅ done | Memory tier cyclic survival 0.629 → 0.767 (+0.138 paired-seed lift, 5/5). |
| **E006b** — verify E006 doesn't hurt non-periodic env | ✅ done | Memory ≈ reflex (+0.016 ± 0.023, within noise). Safe by default. |
| **E007** — `--no-coop-fitness` on hard-env | ✅ done | Bigger, not smaller: full−reflex jumped from +0.086 → +0.298 (cyclic) and +0.093 → +0.240 (grid). The tautology was *masking* the advantage. |
| **E008** — n=20 seeds on the headline | ✅ done | Cyclic +0.290 ± 0.038 (20/20, p=1.91e-06). Grid +0.243 ± 0.046 (20/20, p=1.91e-06). Robust. |
| **E009** — transfer evaluation | ✅ done | Cognition transfers cleanly. Cyclic-trained: gap +0.300 home → +0.293 abroad. Grid-trained: +0.352 → +0.308. 5/5 each direction. |

## Phase 3 — Add cognitive layers with real grounding

Phase 2 validated the foundation. We now have empirical evidence that:
- The cognition advantage is real, robust, and ~3× larger than originally measured.
- It's a property of the genome, not the training env (transferable).
- Memory tier finally outperforms reflex with the right retrieval mechanism.

This is enough foundation to add new layers. Each rung gets its own experiment with a pre-stated prediction:

| Rung | Experiment | Prediction (must state before running) |
|------|------------|----------------------------------------|
| Shared intentionality | **E012**: large-cache tile requires ≥2 adjacent agents to harvest | Cooperation should re-emerge in cognitive tiers when the env requires it (without fitness reward). |
| LLM cognition | **E010**: real `LLMPolicy` implementation with prompt caching | LLM tier should beat hand-rolled cognition on novel transfer envs. |
| Theory of mind | E011: agents track other agents' inferred self-models | Cognitive tiers should predict peer behavior more accurately than reflex baselines. |
| Culture | E013: offspring inherit a digest of parent's high-usefulness memories | Cumulative learning across generations should beat per-life learning in cyclic envs. |

## Phase 4 — What would let us drop "primate" and "intelligence"

The current name is aspirational. To earn it we'd need:

- **Multiple env types** (≥5) with structurally different challenges, not just parameter tweaks.
- **Demonstrated transfer**: agents trained in env A perform above chance in env B.
- **A real LLM tier** with prompt caching, evaluated against rule-based tiers.
- **Metrics that are not summable into a single fitness number** — survival, novelty, prediction, transfer all reported separately.
- **Pre-registered hypotheses** for each new mechanic before running the experiment.
- **n=20+ seeds** for headline claims.

We are nowhere near all of these. The roadmap above is the path to getting closer.

## What we're NOT going to do

- Ship "look how smart the agents are" demos. The point is to measure whether they're smart, not to perform smartness.
- Add new mechanics on top of unverified mechanics. Phase 2 must clear before Phase 3 starts.
- Claim biological grounding the simulator does not have. The mechanisms are computationally suggestive, not biologically faithful.

## Reproducibility expectations

Every experiment should produce, under `data/runs/<run_id>/`:
- `config.json` — full config snapshot
- `metrics.csv` — per-generation metrics
- `run.json` — config + metrics + final population summary
- `final_agents.jsonl` — per-agent state at end of run

And every experiment writeup (`EXPERIMENT_NNN.md`) should include:
- The exact run-id pattern used
- The pre-stated hypothesis (where applicable)
- The script path that reproduces the runs
- Honest "what evidence supports / does NOT support" sections
