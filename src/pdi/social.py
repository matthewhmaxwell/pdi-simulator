"""Social model: per-agent beliefs about every other agent it encounters.

Tracks helpful/harmful actions, updates trust and reciprocity, and supplies
`predict_behavior()` so an agent can decide whether to cooperate, avoid, or
follow a peer based on prior experience.
"""
from __future__ import annotations

from typing import Optional

from .schemas import SocialBelief


class SocialModel:
    """Maintains a dict of SocialBelief keyed by other_agent_id."""

    def __init__(self) -> None:
        self.beliefs: dict[str, SocialBelief] = {}

    def _get_or_create(self, other_id: str) -> SocialBelief:
        if other_id not in self.beliefs:
            self.beliefs[other_id] = SocialBelief(other_agent_id=other_id)
        return self.beliefs[other_id]

    def observe_share(self, other_id: str) -> None:
        b = self._get_or_create(other_id)
        b.observed_helpful_actions += 1
        b.trust_score = min(1.0, b.trust_score + 0.15)
        b.reciprocity_score = min(1.0, b.reciprocity_score + 0.1)
        b.threat_score = max(0.0, b.threat_score - 0.05)
        b.predicted_behavior = "cooperator"

    def observe_withhold(self, other_id: str) -> None:
        b = self._get_or_create(other_id)
        b.observed_harmful_actions += 1
        b.trust_score = max(0.0, b.trust_score - 0.1)
        b.reciprocity_score = max(0.0, b.reciprocity_score - 0.05)
        b.predicted_behavior = "defector"

    def observe_aggression(self, other_id: str) -> None:
        b = self._get_or_create(other_id)
        b.observed_harmful_actions += 1
        b.threat_score = min(1.0, b.threat_score + 0.2)
        b.trust_score = max(0.0, b.trust_score - 0.2)
        b.predicted_behavior = "threat"

    def observe_follow_success(self, other_id: str) -> None:
        """Credit peer when following them led to resource discovery."""
        b = self._get_or_create(other_id)
        b.trust_score = min(1.0, b.trust_score + 0.05)

    def predict_behavior(self, other_id: str) -> str:
        b = self.beliefs.get(other_id)
        if b is None:
            return "unknown"
        return b.predicted_behavior

    def trust(self, other_id: str) -> float:
        b = self.beliefs.get(other_id)
        return b.trust_score if b else 0.5

    def threat(self, other_id: str) -> float:
        b = self.beliefs.get(other_id)
        return b.threat_score if b else 0.0

    def most_trusted(self, candidates: list[str]) -> Optional[str]:
        if not candidates:
            return None
        return max(candidates, key=lambda c: self.trust(c))

    def snapshot(self) -> dict[str, dict]:
        return {k: v.model_dump() for k, v in self.beliefs.items()}
