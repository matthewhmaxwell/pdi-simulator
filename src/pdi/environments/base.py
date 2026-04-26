"""Abstract base for environments.

The interface here is the contract that the evolution loop and cognition
policies depend on. Subclasses can change *how* food/hazards/shelters appear
(random vs cyclic vs procedural) but must expose the same query and mutation
methods so policies don't need to know which env they're in.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..config import EnvironmentConfig
from ..schemas import Position


@dataclass
class Tile:
    has_food: bool = False
    has_hazard: bool = False
    has_shelter: bool = False


class BaseEnvironment(ABC):
    """Contract every environment must satisfy.

    Subclasses get a `grid` of `Tile` objects and a `step_count`. They must
    implement `_populate` (initial layout) and `tick_respawn` (per-step
    dynamics). Everything else is shared.
    """

    name: str = "base"

    def __init__(self, cfg: EnvironmentConfig, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.grid: list[list[Tile]] = [
            [Tile() for _ in range(cfg.grid_size)] for _ in range(cfg.grid_size)
        ]
        self.step_count = 0
        self._populate()

    # ---- subclass-defined ----
    @abstractmethod
    def _populate(self) -> None:
        """Initial tile layout. Called once at construction."""
        ...

    @abstractmethod
    def tick_respawn(self) -> None:
        """Called once per env step. Increments step_count and applies dynamics."""
        ...

    # ---- shared queries ----
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.cfg.grid_size and 0 <= y < self.cfg.grid_size

    def tile(self, pos: Position) -> Tile:
        return self.grid[pos.x][pos.y]

    def random_empty_position(self) -> Position:
        for _ in range(200):
            x = self.rng.randrange(self.cfg.grid_size)
            y = self.rng.randrange(self.cfg.grid_size)
            t = self.grid[x][y]
            if not t.has_hazard:
                return Position(x=x, y=y)
        return Position(x=0, y=0)

    def local_view(self, pos: Position, agent_positions: dict[str, Position]) -> dict:
        r = self.cfg.vision_radius
        food, hazards, shelters, others = [], [], [], []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                nx, ny = pos.x + dx, pos.y + dy
                if not self.in_bounds(nx, ny):
                    continue
                t = self.grid[nx][ny]
                if t.has_food:
                    food.append((nx, ny))
                if t.has_hazard:
                    hazards.append((nx, ny))
                if t.has_shelter:
                    shelters.append((nx, ny))
        for other_id, p in agent_positions.items():
            if abs(p.x - pos.x) <= r and abs(p.y - pos.y) <= r:
                others.append((other_id, p.x, p.y))
        return {
            "position": (pos.x, pos.y),
            "food": food,
            "hazards": hazards,
            "shelters": shelters,
            "others": others,
            "step": self.step_count,
            "env": self.name,  # so policies can introspect if they want
        }

    def consume_food(self, pos: Position) -> bool:
        t = self.grid[pos.x][pos.y]
        if t.has_food:
            t.has_food = False
            return True
        return False

    def count_food(self) -> int:
        return sum(1 for row in self.grid for t in row if t.has_food)

    @staticmethod
    def move_delta(action: str) -> tuple[int, int]:
        return {
            "move_n": (0, -1),
            "move_s": (0, 1),
            "move_e": (1, 0),
            "move_w": (-1, 0),
        }.get(action, (0, 0))

    def clamp_move(self, pos: Position, dx: int, dy: int) -> Position:
        nx = max(0, min(self.cfg.grid_size - 1, pos.x + dx))
        ny = max(0, min(self.cfg.grid_size - 1, pos.y + dy))
        return Position(x=nx, y=ny)
