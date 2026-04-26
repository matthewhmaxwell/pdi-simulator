"""Metrics aggregation and export."""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Iterable

from .agent import Agent
from .evolution import EpisodeResult
from .schemas import GenerationMetrics


def _strategy_diversity(agents: Iterable[Agent]) -> float:
    """Mean per-field stdev of genome weights — higher = more diverse population."""
    agents = list(agents)
    if not agents:
        return 0.0
    fields = agents[0].state.strategy.model_dump().keys()
    stdevs = []
    for f in fields:
        vals = [getattr(a.state.strategy, f) for a in agents]
        if len(vals) > 1:
            stdevs.append(statistics.pstdev(vals))
    return statistics.mean(stdevs) if stdevs else 0.0


def _memory_usefulness(agents: Iterable[Agent]) -> float:
    usefs = []
    for a in agents:
        for ev in a.memory.events:
            usefs.append(ev.usefulness)
    return statistics.mean(usefs) if usefs else 0.0


def _social_trust_accuracy(agents: Iterable[Agent]) -> float:
    """Proxy: fraction of social beliefs where the predicted_behavior label
    matches the sign of (helpful - harmful) observations."""
    correct = 0
    total = 0
    for a in agents:
        for b in a.social.beliefs.values():
            diff = b.observed_helpful_actions - b.observed_harmful_actions
            if diff == 0 and b.observed_helpful_actions + b.observed_harmful_actions == 0:
                continue
            total += 1
            if diff > 0 and b.predicted_behavior == "cooperator":
                correct += 1
            elif diff < 0 and b.predicted_behavior in ("defector", "threat"):
                correct += 1
            elif diff == 0:
                correct += 0.5
    return (correct / total) if total else 0.0


def aggregate_generation(
    generation: int,
    episodes: list[EpisodeResult],
    agents: list[Agent],
    baseline_fitness: float,
) -> GenerationMetrics:
    pop = len(agents) or 1
    survival_rate = statistics.mean(e.survivors / pop for e in episodes) if episodes else 0.0
    avg_food = statistics.mean(e.total_food_collected for e in episodes) if episodes else 0.0
    coop_freq = statistics.mean(e.cooperation_events for e in episodes) if episodes else 0.0
    betray_freq = statistics.mean(e.betrayal_events for e in episodes) if episodes else 0.0
    pred_acc = statistics.mean(e.avg_prediction_accuracy for e in episodes) if episodes else 0.0
    avg_fit = statistics.mean(a.state.fitness_score for a in agents)
    improvement = avg_fit - baseline_fitness if baseline_fitness else 0.0

    # Decoupled per-component scores (mean across agents). Empty dict if
    # update_fitness hasn't been called yet for this generation.
    def _component_mean(name: str) -> float:
        vals = [a.score_components.get(name, 0.0) for a in agents]
        return statistics.mean(vals) if vals else 0.0

    avg_novelty = statistics.mean(len(a.novel_state_tags) for a in agents) if agents else 0.0

    return GenerationMetrics(
        generation=generation,
        avg_survival_rate=survival_rate,
        avg_fitness=avg_fit,
        avg_resource_collection=avg_food,
        cooperation_frequency=coop_freq,
        betrayal_frequency=betray_freq,
        prediction_accuracy=pred_acc,
        social_trust_accuracy=_social_trust_accuracy(agents),
        memory_usefulness=_memory_usefulness(agents),
        strategy_diversity=_strategy_diversity(agents),
        improvement_vs_baseline=improvement,
        avg_novelty=avg_novelty,
        survival_score_mean=_component_mean("survival"),
        foraging_score_mean=_component_mean("foraging"),
        cooperation_score_mean=_component_mean("cooperation"),
        prediction_score_mean=_component_mean("prediction"),
    )


def export_run_csv(path: Path, gen_metrics: list[GenerationMetrics]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not gen_metrics:
        path.write_text("")
        return
    fieldnames = list(gen_metrics[0].model_dump().keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for gm in gen_metrics:
            writer.writerow(gm.model_dump())


def export_run_json(
    path: Path,
    cfg_dict: dict,
    gen_metrics: list[GenerationMetrics],
    final_agents: list[Agent],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": cfg_dict,
        "generations": [gm.model_dump() for gm in gen_metrics],
        "final_population": [
            {
                **a.state.model_dump(),
                "memory_size": len(a.memory),
                "causal_beliefs": len(a.causal),
                "social_beliefs": len(a.social.beliefs),
            }
            for a in final_agents
        ],
    }
    path.write_text(json.dumps(payload, indent=2, default=str))
