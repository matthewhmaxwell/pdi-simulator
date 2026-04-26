"""Cognition loop.

Rule-based action policy parameterized by the agent's StrategyGenome. Designed
as a pluggable policy so an LLM-driven version can slot in later without
changing the surrounding simulation machinery.

The loop is:
    observe -> retrieve memories -> predict -> act -> (env resolves) -> update

This module owns observe → predict → act. Memory/belief updates happen after
the environment resolves the action (see agent.py::Agent.learn_from_outcome).
"""
from __future__ import annotations

import random
from typing import Optional

from .memory import MemoryStore, _state_tag
from .schemas import (
    ALL_ACTIONS,
    Action,
    CausalBelief,
    Position,
    StrategyGenome,
)
from .social import SocialModel


# ---------- scoring helpers ----------

def _distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _best_direction_toward(src: tuple[int, int], dst: tuple[int, int]) -> Action:
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    if abs(dx) >= abs(dy):
        return "move_e" if dx > 0 else "move_w"
    return "move_s" if dy > 0 else "move_n"


def _best_direction_away(src: tuple[int, int], dst: tuple[int, int]) -> Action:
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    if abs(dx) >= abs(dy):
        return "move_w" if dx > 0 else "move_e"
    return "move_n" if dy > 0 else "move_s"


# ---------- cognition tiers ----------

class CognitionPolicy:
    """Base policy. Tiers override `choose_action` to layer capabilities in."""

    def __init__(self, genome: StrategyGenome, rng: random.Random):
        self.genome = genome
        self.rng = rng

    def choose_action(
        self,
        observation: dict,
        position: Position,
        memory: MemoryStore,
        social: SocialModel,
        causal: dict[str, CausalBelief],
        energy: float,
        health: float,
    ) -> Action:
        raise NotImplementedError


class ReflexPolicy(CognitionPolicy):
    """Tier 0: no memory, no social. Direct response to local view."""

    def choose_action(self, observation, position, memory, social, causal, energy, health) -> Action:
        pos = (position.x, position.y)

        # Low energy → seek shelter/food aggressively.
        if observation["food"]:
            nearest = min(observation["food"], key=lambda f: _distance(pos, f))
            if nearest == pos:
                return "collect"
            return _best_direction_toward(pos, nearest)

        # Avoid adjacent hazards.
        for hz in observation["hazards"]:
            if _distance(pos, hz) <= 1:
                return _best_direction_away(pos, hz)

        if health < 20 and observation["shelters"]:
            nearest = min(observation["shelters"], key=lambda s: _distance(pos, s))
            if nearest == pos:
                return "rest"
            return _best_direction_toward(pos, nearest)

        return self.rng.choice(["move_n", "move_s", "move_e", "move_w", "observe"])


class MemoryPolicy(ReflexPolicy):
    """Tier 1: reflex + consult memory for state-action values.

    Memory is a *fallback* for ambiguous situations, not a replacement for
    goal-directed behavior. The action-priority order matches ReflexPolicy
    exactly (food-seeking → hazard dodge → shelter when hurt) so the only
    behavioral delta vs. reflex is what happens in the otherwise-random
    fallback slot: a memory consult instead of a coin flip.

    Why "food first" before hazard: in scarcity regimes, agents that defer
    food-seeking to dodge nearby hazards starve before they reach food.
    The fitness function already penalizes hazard damage; the priority
    order is empirically tuned. (See E004 writeup for the failed v1 fix
    that put hazard before food and tanked survival 0.21 points.)
    """

    def choose_action(self, observation, position, memory, social, causal, energy, health) -> Action:
        pos = (position.x, position.y)

        # Visible food → walk toward it (or collect underfoot). Matches reflex.
        if observation["food"]:
            nearest = min(observation["food"], key=lambda f: _distance(pos, f))
            if nearest == pos:
                return "collect"
            return _best_direction_toward(pos, nearest)

        # Avoid adjacent hazards (only after food check, matching reflex).
        for hz in observation["hazards"]:
            if _distance(pos, hz) <= 1:
                return _best_direction_away(pos, hz)

        # Hurt and shelter visible → rest there.
        if health < 20 and observation["shelters"]:
            nearest = min(observation["shelters"], key=lambda s: _distance(pos, s))
            if nearest == pos:
                return "rest"
            return _best_direction_toward(pos, nearest)

        # No urgent action → consult memory if we trust it. This is the only
        # slot where MemoryPolicy diverges from ReflexPolicy.
        if self.rng.random() < self.genome.memory_reliance:
            suggested = memory.most_common_successful_action(observation)
            if suggested is not None:
                return suggested

        return self.rng.choice(["move_n", "move_s", "move_e", "move_w", "observe"])


class SocialMemoryPolicy(MemoryPolicy):
    """Tier 2: adds social beliefs (follow trusted, avoid threats)."""

    def choose_action(self, observation, position, memory, social, causal, energy, health) -> Action:
        pos = (position.x, position.y)

        # Avoid hazards first (survival reflex).
        for hz in observation["hazards"]:
            if _distance(pos, hz) <= 1:
                return _best_direction_away(pos, hz)

        others = observation["others"]

        # Flee the most-threatening peer if close.
        if others:
            threats = [(oid, x, y) for (oid, x, y) in others if social.threat(oid) > 0.5]
            if threats and self.rng.random() < (1.0 - self.genome.risk_tolerance):
                oid, x, y = min(threats, key=lambda o: _distance(pos, (o[1], o[2])))
                if _distance(pos, (x, y)) <= 2:
                    return _best_direction_away(pos, (x, y))

        # Food-seeking.
        if observation["food"]:
            nearest = min(observation["food"], key=lambda f: _distance(pos, f))
            if nearest == pos:
                return "collect"
            # With social_learning_weight, prefer following a trusted peer if they're
            # near and we don't already have food in sight at our tile.
            if others and self.rng.random() < self.genome.social_learning_weight * 0.5:
                trusted = social.most_trusted([oid for (oid, _, _) in others])
                if trusted is not None and social.trust(trusted) > 0.6:
                    return "follow"
            return _best_direction_toward(pos, nearest)

        # No food visible → consult memory.
        if self.rng.random() < self.genome.memory_reliance:
            suggested = memory.most_common_successful_action(observation)
            if suggested is not None:
                return suggested

        # Share/withhold decisions based on reciprocity when peer adjacent.
        if others and energy > 30:
            adjacent = [(oid, x, y) for (oid, x, y) in others if _distance(pos, (x, y)) <= 1]
            if adjacent:
                oid = social.most_trusted([a[0] for a in adjacent])
                if oid is not None:
                    reciprocity = social.beliefs.get(oid)
                    recip_score = reciprocity.reciprocity_score if reciprocity else 0.5
                    if self.rng.random() < self.genome.cooperation_weight * recip_score:
                        return "share"
                    if self.rng.random() < self.genome.competition_weight * (1 - recip_score):
                        return "withhold"

        # Rest when hurt.
        if health < 25 and observation["shelters"]:
            nearest = min(observation["shelters"], key=lambda s: _distance(pos, s))
            if nearest == pos:
                return "rest"
            return _best_direction_toward(pos, nearest)

        # Exploration vs exploitation.
        if self.rng.random() < self.genome.exploration_weight:
            return self.rng.choice(["move_n", "move_s", "move_e", "move_w"])
        return "observe"


class FullPolicy(SocialMemoryPolicy):
    """Tier 3: memory + social + causal beliefs + curiosity."""

    def choose_action(self, observation, position, memory, social, causal, energy, health) -> Action:
        pos = (position.x, position.y)

        # Causal belief consultation: if we've learned (context, action) -> good outcome
        # with high confidence, and the context matches, act on it.
        ctx = _state_tag(observation)
        best_belief: Optional[CausalBelief] = None
        best_conf = 0.0
        for cb in causal.values():
            if cb.context == ctx and cb.observed_count >= 3 and cb.confidence > best_conf:
                best_conf = cb.confidence
                best_belief = cb
        if best_belief is not None and best_conf > 0.7 and self.rng.random() < self.genome.exploitation_weight:
            # Only commit to the belief's action if it's plausibly executable here.
            act = best_belief.action
            if act == "collect" and not (observation["food"] and pos in observation["food"]):
                # Can't collect without food underfoot; fall through to base policy.
                pass
            else:
                return act

        # Curiosity: occasionally explore unfamiliar state.
        if self.rng.random() < self.genome.curiosity_weight * 0.3:
            return "observe"

        return super().choose_action(observation, position, memory, social, causal, energy, health)


def build_policy(tier: str, genome: StrategyGenome, rng: random.Random) -> CognitionPolicy:
    tier = tier.lower()
    if tier == "reflex":
        return ReflexPolicy(genome, rng)
    if tier == "memory":
        return MemoryPolicy(genome, rng)
    if tier == "social":
        return SocialMemoryPolicy(genome, rng)
    return FullPolicy(genome, rng)
