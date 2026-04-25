"""Simulation configuration. All knobs in one place so experiments stay reproducible."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class EnvironmentConfig:
    grid_size: int = 20
    num_food: int = 30
    num_hazards: int = 8
    num_shelters: int = 4
    food_energy: float = 12.0
    hazard_damage: float = 15.0
    shelter_rest: float = 5.0
    food_respawn_rate: float = 0.05  # per step probability
    vision_radius: int = 3
    max_steps: int = 80


@dataclass
class AgentConfig:
    start_energy: float = 50.0
    start_health: float = 50.0
    energy_decay: float = 0.5  # per step
    move_cost: float = 0.3
    signal_cost: float = 0.2
    share_cost: float = 2.0
    memory_capacity: int = 200
    memory_retrieval_k: int = 5


@dataclass
class EvolutionConfig:
    population_size: int = 50
    generations: int = 20
    episodes_per_generation: int = 10
    elite_fraction: float = 0.2
    mutation_rate: float = 0.15
    mutation_sigma: float = 0.1
    # Which cognition tier to run: "reflex", "memory", "social", "full"
    cognition_tier: str = "full"
    random_seed: int = 42


@dataclass
class SimConfig:
    env: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    evo: EvolutionConfig = field(default_factory=EvolutionConfig)
    run_label: str = "baseline"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
