"""Grid world environment.

A simple 2D grid populated with food, hazards, shelters, and agents. The
environment exposes per-agent local observations (within `vision_radius`) and
resolves actions in a single step() pass per tick.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Optional

from .config import EnvironmentConfig
from .schemas import Position


@dataclass
class Tile:
    has_food: bool = False
    has_hazard: bool = False
    has_shelter: bool = False


class Environment:
    def __init__(self, cfg: EnvironmentConfig, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.grid: list[list[Tile]] = [[Tile() for _ in range(cfg.grid_size)] for _ in range(cfg.grid_size)]
        self.step_count = 0
        self._populate()

    # ---- setup ----
    def _populate(self) -> None:
        cells = [(x, y) for x in range(self.cfg.grid_size) for y in range(self.cfg.grid_size)]
        self.rng.shuffle(cells)
        idx = 0
        for _ in range(self.cfg.num_food):
            x, y = cells[idx]; idx += 1
            self.grid[x][y].has_food = True
        for _ in range(self.cfg.num_hazards):
            x, y = cells[idx]; idx += 1
            self.grid[x][y].has_hazard = True
        for _ in range(self.cfg.num_shelters):
            x, y = cells[idx]; idx += 1
            self.grid[x][y].has_shelter = True

    def random_empty_position(self) -> Position:
        for _ in range(200):
            x = self.rng.randrange(self.cfg.grid_size)
            y = self.rng.randrange(self.cfg.grid_size)
            t = self.grid[x][y]
            if not t.has_hazard:
                return Position(x=x, y=y)
        return Position(x=0, y=0)

    # ---- queries ----
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.cfg.grid_size and 0 <= y < self.cfg.grid_size

    def tile(self, pos: Position) -> Tile:
        return self.grid[pos.x][pos.y]

    def local_view(self, pos: Position, agent_positions: dict[str, Position]) -> dict:
        r = self.cfg.vision_radius
        food = []
        hazards = []
        shelters = []
        others = []
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
        }

    # ---- mutations ----
    def consume_food(self, pos: Position) -> bool:
        t = self.grid[pos.x][pos.y]
        if t.has_food:
            t.has_food = False
            return True
        return False

    def tick_respawn(self) -> None:
        """Occasionally respawn food on empty, non-hazard tiles."""
        self.step_count += 1
        for row in self.grid:
            for t in row:
                if t.has_food or t.has_hazard or t.has_shelter:
                    continue
                if self.rng.random() < self.cfg.food_respawn_rate / (self.cfg.grid_size * self.cfg.grid_size / self.cfg.num_food):
                    t.has_food = True

    def count_food(self) -> int:
        return sum(1 for row in self.grid for t in row if t.has_food)

    # ---- movement helper ----
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
