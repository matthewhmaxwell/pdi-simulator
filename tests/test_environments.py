"""Tests for the pluggable environments package."""
import random

from pdi.config import EnvironmentConfig
from pdi.environments import (
    BaseEnvironment,
    CyclicEnvironment,
    ENV_REGISTRY,
    GridWorldEnvironment,
    make_environment,
)
from pdi.schemas import Position


def _cfg(grid=10, food=5, hazards=2, shelters=2, respawn=0.05):
    return EnvironmentConfig(
        grid_size=grid, num_food=food, num_hazards=hazards,
        num_shelters=shelters, food_respawn_rate=respawn,
    )


def test_registry_has_grid_and_cyclic():
    assert "grid" in ENV_REGISTRY
    assert "cyclic" in ENV_REGISTRY


def test_make_environment_grid():
    env = make_environment("grid", _cfg(), random.Random(0))
    assert isinstance(env, GridWorldEnvironment)
    assert env.name == "grid"


def test_make_environment_cyclic():
    env = make_environment("cyclic", _cfg(), random.Random(0))
    assert isinstance(env, CyclicEnvironment)
    assert env.name == "cyclic"


def test_unknown_env_raises():
    try:
        make_environment("nope", _cfg(), random.Random(0))
        assert False, "expected ValueError"
    except ValueError as e:
        assert "nope" in str(e)


def test_cyclic_env_has_fixed_feeding_grounds():
    env = CyclicEnvironment(_cfg(food=5, respawn=0.1), random.Random(0))
    assert len(env.feeding_grounds) == 5
    # All feeding grounds should currently have food.
    assert all(env.tile(Position(x=x, y=y)).has_food for (x, y) in env.feeding_grounds)
    # No hazard or shelter overlaps a feeding ground.
    for (x, y) in env.feeding_grounds:
        t = env.tile(Position(x=x, y=y))
        assert not t.has_hazard
        assert not t.has_shelter


def test_cyclic_env_respawns_on_period():
    env = CyclicEnvironment(_cfg(food=3, respawn=0.1), random.Random(0))
    # respawn_period = round(1/0.1) = 10
    assert env.respawn_period == 10

    # Pick one feeding ground and consume it.
    fg = next(iter(env.feeding_grounds))
    consumed = env.consume_food(Position(x=fg[0], y=fg[1]))
    assert consumed
    assert not env.tile(Position(x=fg[0], y=fg[1])).has_food
    # It should be scheduled to respawn at step_count + 10.
    assert env.respawn_at[fg] == env.step_count + 10

    # Tick 9 steps — still no food.
    for _ in range(9):
        env.tick_respawn()
    assert not env.tile(Position(x=fg[0], y=fg[1])).has_food

    # Tick once more — respawn fires.
    env.tick_respawn()
    assert env.tile(Position(x=fg[0], y=fg[1])).has_food
    assert fg not in env.respawn_at  # cleared after firing


def test_cyclic_env_non_feeding_tiles_never_have_food():
    env = CyclicEnvironment(_cfg(food=3, respawn=0.1), random.Random(0))
    non_feeding = [
        (x, y) for x in range(10) for y in range(10)
        if (x, y) not in env.feeding_grounds
    ]
    # Run for a long time — non-feeding tiles must stay foodless.
    for _ in range(50):
        env.tick_respawn()
    for (x, y) in non_feeding:
        assert not env.tile(Position(x=x, y=y)).has_food


def test_local_view_includes_env_name():
    env = make_environment("cyclic", _cfg(), random.Random(0))
    view = env.local_view(Position(x=0, y=0), {})
    assert view["env"] == "cyclic"
