import random

from pdi.config import EnvironmentConfig
from pdi.environment import Environment
from pdi.schemas import Position


def _env(seed=1, grid=10):
    return Environment(EnvironmentConfig(grid_size=grid, num_food=5, num_hazards=2, num_shelters=2), random.Random(seed))


def test_environment_populates_correctly():
    env = _env()
    total_food = sum(1 for row in env.grid for t in row if t.has_food)
    total_hazards = sum(1 for row in env.grid for t in row if t.has_hazard)
    total_shelters = sum(1 for row in env.grid for t in row if t.has_shelter)
    assert total_food == 5
    assert total_hazards == 2
    assert total_shelters == 2


def test_in_bounds_and_clamp():
    env = _env(grid=10)
    assert env.in_bounds(0, 0)
    assert not env.in_bounds(-1, 0)
    assert not env.in_bounds(10, 0)
    p = Position(x=0, y=0)
    assert env.clamp_move(p, -1, -1).as_tuple() == (0, 0)
    assert env.clamp_move(p, 5, 5).as_tuple() == (5, 5)


def test_local_view_reports_visible_entities():
    env = _env(grid=10)
    p = Position(x=5, y=5)
    view = env.local_view(p, {})
    assert "food" in view and "hazards" in view and "shelters" in view
    assert view["position"] == (5, 5)


def test_consume_food_removes_food():
    env = _env(grid=10)
    # Find a food tile.
    food_pos = None
    for x in range(10):
        for y in range(10):
            if env.grid[x][y].has_food:
                food_pos = Position(x=x, y=y)
                break
        if food_pos:
            break
    assert food_pos is not None
    assert env.consume_food(food_pos) is True
    assert env.consume_food(food_pos) is False


def test_random_empty_position_avoids_hazards():
    env = _env()
    for _ in range(20):
        p = env.random_empty_position()
        assert not env.tile(p).has_hazard
