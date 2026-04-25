"""Pydantic schemas for all persisted objects.

Every stateful concept in the simulator has a schema here so agents, memories,
beliefs, and run artifacts stay inspectable across episodes and generations.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


Action = Literal[
    "move_n", "move_s", "move_e", "move_w",
    "observe", "collect", "share", "withhold",
    "signal", "follow", "avoid", "rest",
]

ALL_ACTIONS: tuple[Action, ...] = (
    "move_n", "move_s", "move_e", "move_w",
    "observe", "collect", "share", "withhold",
    "signal", "follow", "avoid", "rest",
)


class Position(BaseModel):
    x: int
    y: int

    def as_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)


class StrategyGenome(BaseModel):
    """Mutable weights that parameterize decision-making. One genome per agent."""
    exploration_weight: float = 0.5
    exploitation_weight: float = 0.5
    cooperation_weight: float = 0.5
    competition_weight: float = 0.3
    risk_tolerance: float = 0.4
    memory_reliance: float = 0.5
    social_learning_weight: float = 0.4
    curiosity_weight: float = 0.4
    deception_tolerance: float = 0.2
    reciprocity_weight: float = 0.6


class MemoryEvent(BaseModel):
    timestamp: int
    episode_id: str
    observed_state: dict = Field(default_factory=dict)
    action_taken: Action
    outcome: str
    reward_delta: float
    other_agents_present: list[str] = Field(default_factory=list)
    inferred_cause: Optional[str] = None
    confidence: float = 0.5
    usefulness: float = 0.0  # updated over time based on retrieval utility


class CausalBelief(BaseModel):
    action: Action
    context: str  # compressed state tag, e.g. "food_near" or "hazard_adj"
    predicted_outcome: str
    observed_count: int = 0
    success_count: int = 0

    @property
    def confidence(self) -> float:
        if self.observed_count == 0:
            return 0.0
        return self.success_count / self.observed_count


class SocialBelief(BaseModel):
    other_agent_id: str
    trust_score: float = 0.5
    threat_score: float = 0.0
    reciprocity_score: float = 0.5
    observed_helpful_actions: int = 0
    observed_harmful_actions: int = 0
    predicted_behavior: str = "unknown"


class SelfModel(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    preferred_strategy: str = "balanced"
    recent_failures: list[str] = Field(default_factory=list)
    recent_successes: list[str] = Field(default_factory=list)
    predicted_survival_chance: float = 0.5
    confidence_level: float = 0.5


class AgentState(BaseModel):
    """Serializable snapshot of an agent. Used for persistence & offspring creation."""
    id: str
    generation: int
    parent_id: Optional[str] = None
    energy: float
    health: float
    location: Position
    strategy: StrategyGenome
    self_model: SelfModel = Field(default_factory=SelfModel)
    fitness_score: float = 0.0
    alive: bool = True
    episodes_survived: int = 0


class EpisodeMetrics(BaseModel):
    episode_id: str
    generation: int
    steps: int
    survivors: int
    total_food_collected: int
    cooperation_events: int
    betrayal_events: int
    avg_fitness: float
    avg_prediction_accuracy: float


class GenerationMetrics(BaseModel):
    generation: int
    avg_survival_rate: float
    avg_fitness: float
    avg_resource_collection: float
    cooperation_frequency: float
    betrayal_frequency: float
    prediction_accuracy: float
    social_trust_accuracy: float
    memory_usefulness: float
    strategy_diversity: float
    improvement_vs_baseline: float
