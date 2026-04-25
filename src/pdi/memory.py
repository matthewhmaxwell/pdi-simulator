"""Structured memory system.

Not a transcript store. Each `MemoryEvent` captures what was observed, what
was done, what happened, who was around, and the agent's guess at the cause.
Supports retrieval, pattern summarization, decay, and usefulness ranking.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Optional

from .schemas import Action, MemoryEvent


def _state_tag(observation: dict) -> str:
    """Compress an observation to a short context tag."""
    tags = []
    if observation.get("food"):
        tags.append("food_near")
    if observation.get("hazards"):
        tags.append("hazard_near")
    if observation.get("shelters"):
        tags.append("shelter_near")
    if observation.get("others"):
        tags.append(f"peers_{min(len(observation['others']), 3)}")
    return "|".join(tags) if tags else "empty"


class MemoryStore:
    """Bounded, prioritized memory. Low-usefulness events get forgotten first."""

    def __init__(self, capacity: int = 200):
        self.capacity = capacity
        self.events: list[MemoryEvent] = []

    def __len__(self) -> int:
        return len(self.events)

    def add(self, event: MemoryEvent) -> None:
        self.events.append(event)
        if len(self.events) > self.capacity:
            self._forget_weakest()

    def _forget_weakest(self) -> None:
        """Evict the single lowest-usefulness event (with age as tiebreaker)."""
        if not self.events:
            return
        idx, _ = min(
            enumerate(self.events),
            key=lambda kv: (kv[1].usefulness, kv[1].timestamp),
        )
        self.events.pop(idx)

    def retrieve_similar(self, observation: dict, action: Optional[Action] = None, k: int = 5) -> list[MemoryEvent]:
        """Return top-k memories whose state tag overlaps the current observation."""
        current_tag = _state_tag(observation)
        current_tokens = set(current_tag.split("|"))

        def score(ev: MemoryEvent) -> float:
            ev_tokens = set(_state_tag(ev.observed_state).split("|"))
            overlap = len(current_tokens & ev_tokens)
            action_bonus = 0.5 if (action and ev.action_taken == action) else 0.0
            return overlap + action_bonus + 0.1 * ev.usefulness

        ranked = sorted(self.events, key=score, reverse=True)
        return [ev for ev in ranked[:k] if score(ev) > 0]

    def summarize_patterns(self) -> dict[str, dict]:
        """Group events by (context_tag, action) and report avg reward + frequency."""
        buckets: dict[tuple[str, str], list[float]] = {}
        for ev in self.events:
            key = (_state_tag(ev.observed_state), ev.action_taken)
            buckets.setdefault(key, []).append(ev.reward_delta)
        out: dict[str, dict] = {}
        for (ctx, act), rewards in buckets.items():
            out[f"{ctx}::{act}"] = {
                "count": len(rewards),
                "avg_reward": sum(rewards) / len(rewards),
            }
        return out

    def reinforce_retrieved(self, retrieved: Iterable[MemoryEvent], delta: float = 0.1) -> None:
        """Bump usefulness on retrieved memories so useful ones stick around."""
        for ev in retrieved:
            ev.usefulness = min(10.0, ev.usefulness + delta)

    def most_common_successful_action(self, observation: dict) -> Optional[Action]:
        tag = _state_tag(observation)
        successes: Counter[Action] = Counter()
        for ev in self.events:
            if _state_tag(ev.observed_state) == tag and ev.reward_delta > 0:
                successes[ev.action_taken] += 1
        if not successes:
            return None
        return successes.most_common(1)[0][0]
