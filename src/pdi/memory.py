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
    """Bounded, prioritized memory. Low-usefulness events get forgotten first.

    In addition to the event log, the store maintains *per-tile food observation
    history* — a `dict[(x,y) → list[(step, had_food)]]` populated by
    `observe_tile()`. This is what lets the memory tier exploit temporal
    patterns in env types like `CyclicEnvironment` (E006). The event log alone
    cannot do this because retrieval is by state-tag overlap; you need
    position-keyed timing data to predict periodic events.
    """

    def __init__(self, capacity: int = 200, tile_history_capacity: int = 50):
        self.capacity = capacity
        self.events: list[MemoryEvent] = []
        # Per-tile food-observation log: position → list of (step, had_food).
        # Bounded per-tile to keep memory usage proportional to vision range.
        self._tile_history_capacity = tile_history_capacity
        self.tile_food_observations: dict[tuple[int, int], list[tuple[int, bool]]] = {}

    def __len__(self) -> int:
        return len(self.events)

    def add(self, event: MemoryEvent) -> None:
        self.events.append(event)
        if len(self.events) > self.capacity:
            self._forget_weakest()

    # ---- per-tile food-history tracking (E006) ----
    def observe_tile(self, pos: tuple[int, int], step: int, has_food: bool) -> None:
        """Record whether `pos` had food at `step`. Bounded per-tile."""
        history = self.tile_food_observations.setdefault(pos, [])
        history.append((step, has_food))
        if len(history) > self._tile_history_capacity:
            # Drop the oldest entry.
            history.pop(0)

    def observe_local_view(self, observation: dict, step: int) -> None:
        """Convenience: record food state for every visible tile in one call.

        Visible tiles with food are exactly `observation["food"]`. Visible
        tiles without food are inferred from the agent's vision radius around
        its position; we don't enumerate all of them (would explode memory)
        and instead record only the agent's own tile state, plus any visible
        food tiles. This is enough signal for periodic-respawn detection at
        tiles the agent actually visits.
        """
        # Be defensive: tests sometimes pass abbreviated obs dicts.
        if "position" not in observation:
            return
        my_pos = tuple(observation["position"])
        food_positions = {tuple(p) for p in observation.get("food", [])}
        # Record agent's own tile.
        self.observe_tile(my_pos, step, my_pos in food_positions)
        # Record visible food tiles too — useful even if not standing on them.
        for fp in food_positions:
            if fp != my_pos:
                self.observe_tile(fp, step, True)

    def predict_food_return(
        self,
        pos: tuple[int, int],
        current_step: int,
        max_lookback: int = 100,
    ) -> Optional[int]:
        """Predict how many steps until food reappears at `pos`.

        Returns the median step-period between consecutive food observations
        at this tile, minus the time since the last food was seen. If we have
        not observed food at this tile at least twice, returns None.

        This is a deliberately simple estimator. It assumes locally periodic
        respawn (true in `CyclicEnvironment`). It will produce noise on tiles
        with random respawn (`GridWorldEnvironment`) — that's fine, the
        consumer (`MemoryPolicy`) only acts on it when confidence is high.
        """
        history = self.tile_food_observations.get(pos)
        if not history:
            return None
        food_steps = [s for (s, had) in history if had]
        if len(food_steps) < 2:
            return None
        # Compute consecutive deltas; take the median as the period estimate.
        deltas = sorted(
            food_steps[i + 1] - food_steps[i]
            for i in range(len(food_steps) - 1)
        )
        period = deltas[len(deltas) // 2]
        if period <= 0:
            return None
        last_food_step = food_steps[-1]
        elapsed = current_step - last_food_step
        if elapsed > max_lookback:
            return None
        # Steps until next predicted food. Can be negative if we're "overdue".
        return max(0, period - elapsed)

    def known_feeding_ground(
        self,
        pos: tuple[int, int],
        min_observations: int = 2,
    ) -> bool:
        """True if we've observed food at this tile at least `min_observations` times."""
        history = self.tile_food_observations.get(pos)
        if not history:
            return False
        return sum(1 for (_, had) in history if had) >= min_observations

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
