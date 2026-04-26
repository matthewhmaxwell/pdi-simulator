"""Random-respawn grid world. The original Environment from E001-E004."""
from __future__ import annotations

from .base import BaseEnvironment


class GridWorldEnvironment(BaseEnvironment):
    """Food/hazards/shelters scattered randomly. Food respawns probabilistically
    on empty non-hazard tiles. No temporal structure — memory of past states
    has no predictive value here.
    """

    name = "grid"

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

    def tick_respawn(self) -> None:
        self.step_count += 1
        for row in self.grid:
            for t in row:
                if t.has_food or t.has_hazard or t.has_shelter:
                    continue
                if self.rng.random() < self.cfg.food_respawn_rate / (
                    self.cfg.grid_size * self.cfg.grid_size / max(self.cfg.num_food, 1)
                ):
                    t.has_food = True
