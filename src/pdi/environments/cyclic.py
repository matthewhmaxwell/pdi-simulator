"""Cyclic-respawn environment.

Food appears at a FIXED set of "feeding ground" tiles on a FIXED period.
After being consumed, a feeding-ground tile regrows its food exactly
`respawn_period` steps later. Other tiles never have food.

This is the first environment with **temporal structure** — an agent that
remembers "tile X had food at step 0 → it'll have food again at step
respawn_period" can outperform reflex agents that just react to currently
visible food. The cognition tier whose policy actually exploits this is
the test of whether the memory tier is useful.

Hazards and shelters are placed once, randomly. They don't move.
"""
from __future__ import annotations

from .base import BaseEnvironment


class CyclicEnvironment(BaseEnvironment):
    """Fixed feeding grounds with periodic respawn.

    Config knobs reused:
    - `num_food` — number of feeding-ground tiles (smaller = more competition)
    - `num_hazards`, `num_shelters` — same as grid world
    - `food_respawn_rate` — interpreted here as 1/period. So 0.05 → period 20.

    State added:
    - `feeding_grounds: set[(x,y)]` — fixed positions
    - `respawn_at: dict[(x,y), int]` — step at which each consumed tile regrows
    """

    name = "cyclic"

    def _populate(self) -> None:
        cells = [(x, y) for x in range(self.cfg.grid_size) for y in range(self.cfg.grid_size)]
        self.rng.shuffle(cells)
        idx = 0

        self.feeding_grounds: set[tuple[int, int]] = set()
        for _ in range(self.cfg.num_food):
            x, y = cells[idx]; idx += 1
            self.grid[x][y].has_food = True
            self.feeding_grounds.add((x, y))

        for _ in range(self.cfg.num_hazards):
            x, y = cells[idx]; idx += 1
            # Avoid placing hazards on feeding grounds.
            while (x, y) in self.feeding_grounds:
                x, y = cells[idx]; idx += 1
            self.grid[x][y].has_hazard = True

        for _ in range(self.cfg.num_shelters):
            x, y = cells[idx]; idx += 1
            while (x, y) in self.feeding_grounds:
                x, y = cells[idx]; idx += 1
            self.grid[x][y].has_shelter = True

        # Period: agents must learn it implicitly through repeated exposure.
        # We expose it as 1/respawn_rate so users tune in familiar units.
        self.respawn_period = max(2, int(round(1.0 / max(self.cfg.food_respawn_rate, 1e-6))))
        self.respawn_at: dict[tuple[int, int], int] = {}

    def consume_food(self, pos):
        """Override: schedule a regrowth when food is taken."""
        t = self.grid[pos.x][pos.y]
        if t.has_food:
            t.has_food = False
            if (pos.x, pos.y) in self.feeding_grounds:
                self.respawn_at[(pos.x, pos.y)] = self.step_count + self.respawn_period
            return True
        return False

    def tick_respawn(self) -> None:
        self.step_count += 1
        # Regrow any feeding ground whose timer has elapsed.
        ready = [pos for pos, when in self.respawn_at.items() if when <= self.step_count]
        for pos in ready:
            x, y = pos
            self.grid[x][y].has_food = True
            del self.respawn_at[pos]
