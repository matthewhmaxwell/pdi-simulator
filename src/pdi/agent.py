"""Agent: integrates state, memory, social model, causal beliefs, cognition, and self-model.

An agent's `step` is: observe → decide → return action. The environment runner
then applies the action and calls `learn_from_outcome` so memory and beliefs update.
"""
from __future__ import annotations

import random
import uuid
from typing import Optional

from .config import AgentConfig, FitnessWeights
from .cognition import CognitionPolicy, build_policy
from .memory import MemoryStore, _state_tag
from .schemas import (
    Action,
    AgentState,
    CausalBelief,
    MemoryEvent,
    Position,
    SelfModel,
    StrategyGenome,
)
from .social import SocialModel


def new_agent_id() -> str:
    return f"a_{uuid.uuid4().hex[:8]}"


class Agent:
    """Live agent instance. `AgentState` is the serializable snapshot."""

    def __init__(
        self,
        state: AgentState,
        cfg: AgentConfig,
        cognition_tier: str,
        rng: random.Random,
    ):
        self.state = state
        self.cfg = cfg
        self.rng = rng
        self.memory = MemoryStore(capacity=cfg.memory_capacity)
        self.social = SocialModel()
        self.causal: dict[str, CausalBelief] = {}
        self.policy: CognitionPolicy = build_policy(cognition_tier, state.strategy, rng)

        # Per-episode counters.
        self.food_collected = 0
        self.cooperation_events = 0
        self.betrayal_events = 0
        self.predictions_made = 0
        self.predictions_correct = 0
        # Novelty: unique state-tags visited this episode. Useful as a
        # cognition-independent signal of exploration / curiosity.
        self.novel_state_tags: set[str] = set()
        # Decoupled per-component scores, populated by update_fitness so they
        # can be exported separately and the composite stays auditable.
        self.score_components: dict[str, float] = {}

    # ---------- factory ----------

    @classmethod
    def spawn(
        cls,
        generation: int,
        cfg: AgentConfig,
        cognition_tier: str,
        rng: random.Random,
        parent_id: Optional[str] = None,
        strategy: Optional[StrategyGenome] = None,
        position: Optional[Position] = None,
    ) -> "Agent":
        state = AgentState(
            id=new_agent_id(),
            generation=generation,
            parent_id=parent_id,
            energy=cfg.start_energy,
            health=cfg.start_health,
            location=position or Position(x=0, y=0),
            strategy=strategy or StrategyGenome(),
        )
        return cls(state, cfg, cognition_tier, rng)

    # ---------- per-episode reset ----------

    def reset_for_episode(self, start_pos: Position) -> None:
        self.state.energy = self.cfg.start_energy
        self.state.health = self.cfg.start_health
        self.state.location = start_pos
        self.state.alive = True
        self.food_collected = 0
        self.cooperation_events = 0
        self.betrayal_events = 0
        self.predictions_made = 0
        self.predictions_correct = 0
        self.novel_state_tags = set()
        self.score_components = {}

    # ---------- observe / decide ----------

    def decide(self, observation: dict) -> Action:
        """Pick an action. We also record a prediction of whether reward > 0 so
        we can later score prediction accuracy — a rough proxy for learning."""
        act = self.policy.choose_action(
            observation=observation,
            position=self.state.location,
            memory=self.memory,
            social=self.social,
            causal=self.causal,
            energy=self.state.energy,
            health=self.state.health,
        )
        # Predict via memory: does similar (state, action) usually pay off?
        similars = self.memory.retrieve_similar(observation, action=act, k=3)
        if similars:
            avg = sum(ev.reward_delta for ev in similars) / len(similars)
            self._pending_prediction = avg > 0
        else:
            self._pending_prediction = None
        return act

    # ---------- learn ----------

    def learn_from_outcome(
        self,
        episode_id: str,
        timestamp: int,
        observation: dict,
        action: Action,
        reward_delta: float,
        outcome: str,
        other_agents_present: list[str],
    ) -> None:
        ev = MemoryEvent(
            timestamp=timestamp,
            episode_id=episode_id,
            observed_state={
                "food": observation["food"],
                "hazards": observation["hazards"],
                "shelters": observation["shelters"],
                "others": [o[0] for o in observation["others"]],
            },
            action_taken=action,
            outcome=outcome,
            reward_delta=reward_delta,
            other_agents_present=other_agents_present,
            inferred_cause=self._infer_cause(observation, action, reward_delta),
            confidence=0.5,
            usefulness=max(0.0, reward_delta / 10.0),
        )
        self.memory.add(ev)
        # Track novelty: count this state-tag as visited.
        self.novel_state_tags.add(_state_tag(observation))
        # Reinforce retrieval of memories that matched this observation; they
        # proved useful enough to consult.
        similar = self.memory.retrieve_similar(observation, action=action, k=3)
        if similar:
            self.memory.reinforce_retrieved(similar, delta=0.05 if reward_delta > 0 else 0.01)

        # Update causal beliefs keyed on (action, context).
        ctx = _state_tag(observation)
        key = f"{action}@{ctx}"
        belief = self.causal.get(key)
        if belief is None:
            belief = CausalBelief(
                action=action,
                context=ctx,
                predicted_outcome="positive" if reward_delta > 0 else "negative",
            )
            self.causal[key] = belief
        belief.observed_count += 1
        if reward_delta > 0:
            belief.success_count += 1

        # Prediction accuracy.
        if self._pending_prediction is not None:
            self.predictions_made += 1
            actual_positive = reward_delta > 0
            if actual_positive == self._pending_prediction:
                self.predictions_correct += 1

    def _infer_cause(self, observation: dict, action: Action, reward: float) -> str:
        if action == "collect" and reward > 0:
            return "food_at_tile"
        if action.startswith("move_") and reward < 0:
            return "hazard_adjacent_or_energy_cost"
        if action == "share" and reward > 0:
            return "reciprocity_gain"
        if action == "rest" and reward > 0:
            return "shelter_restore"
        return "unknown"

    # ---------- fitness ----------

    def update_fitness(self, weights: FitnessWeights | None = None) -> None:
        """Compute and apply fitness from weighted per-component scores.

        Each component is also stored in `self.score_components` so it can be
        exported and inspected separately. To ablate the cooperation tautology
        (E008), pass a `FitnessWeights` with `cooperation=0`.
        """
        w = weights or FitnessWeights()
        prediction_accuracy = (
            self.predictions_correct / self.predictions_made if self.predictions_made else 0.0
        )
        components = {
            "survival": w.survival if self.state.alive else 0.0,
            "foraging": w.foraging * self.food_collected,
            "cooperation": w.cooperation * self.cooperation_events,
            "betrayal_penalty": -w.betrayal_penalty * self.betrayal_events,
            "prediction": w.prediction * prediction_accuracy,
            "energy": w.energy * self.state.energy,
        }
        self.score_components = components
        self.state.fitness_score += sum(components.values())

    # ---------- self-model ----------

    def update_self_model(self) -> None:
        sm = self.state.self_model
        sm.recent_successes = []
        sm.recent_failures = []
        if self.food_collected >= 3:
            sm.recent_successes.append("resource_rich_episode")
        if self.cooperation_events > 0:
            sm.recent_successes.append("cooperated_successfully")
        if not self.state.alive:
            sm.recent_failures.append("died")
        if self.state.energy < 10 and self.state.alive:
            sm.recent_failures.append("near_starvation")

        # Simple strength/weakness inference.
        sm.strengths = []
        sm.weaknesses = []
        if self.food_collected >= 3:
            sm.strengths.append("foraging")
        if self.cooperation_events >= 2:
            sm.strengths.append("cooperation")
        if self.state.health < 20:
            sm.weaknesses.append("fragile")
        if self.predictions_made > 0 and self.predictions_correct / self.predictions_made > 0.7:
            sm.strengths.append("prediction")
        elif self.predictions_made >= 5:
            sm.weaknesses.append("prediction")

        # Preferred strategy label from genome leanings.
        g = self.state.strategy
        if g.cooperation_weight > g.competition_weight + 0.15:
            sm.preferred_strategy = "cooperator"
        elif g.competition_weight > g.cooperation_weight + 0.15:
            sm.preferred_strategy = "competitor"
        elif g.exploration_weight > 0.6:
            sm.preferred_strategy = "explorer"
        else:
            sm.preferred_strategy = "balanced"

        sm.predicted_survival_chance = max(
            0.0, min(1.0, (self.state.energy / 100.0) * 0.5 + (self.state.health / 100.0) * 0.5)
        )
        accuracy = (
            self.predictions_correct / self.predictions_made if self.predictions_made else 0.5
        )
        sm.confidence_level = 0.3 + 0.7 * accuracy
