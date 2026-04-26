"""Pluggable environments for the PDI simulator.

Each environment subclass exposes the same interface (`local_view`, `consume_food`,
`tick_respawn`, `random_empty_position`, etc.) so the cognition policies and
evolution loop are environment-agnostic. Add a new env by subclassing
[`base.BaseEnvironment`][] and registering it in [`registry.ENV_REGISTRY`][].

Available envs:
- `grid` — the original random-respawn grid world (BaseEnvironment subclass).
- `cyclic` — food respawns at fixed locations on a known period; tests whether
  memory tier can learn temporal patterns.
"""
from __future__ import annotations

from .base import BaseEnvironment, Tile
from .grid_world import GridWorldEnvironment
from .cyclic import CyclicEnvironment

ENV_REGISTRY: dict[str, type[BaseEnvironment]] = {
    "grid": GridWorldEnvironment,
    "cyclic": CyclicEnvironment,
}


def make_environment(name: str, cfg, rng) -> BaseEnvironment:
    """Factory: instantiate an environment by registry name."""
    if name not in ENV_REGISTRY:
        raise ValueError(f"Unknown environment {name!r}. Available: {list(ENV_REGISTRY)}")
    return ENV_REGISTRY[name](cfg, rng)


__all__ = [
    "BaseEnvironment",
    "Tile",
    "GridWorldEnvironment",
    "CyclicEnvironment",
    "ENV_REGISTRY",
    "make_environment",
]
