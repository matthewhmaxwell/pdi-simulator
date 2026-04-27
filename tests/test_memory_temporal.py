"""Tests for the time-aware memory retrieval added in E006."""
from pdi.memory import MemoryStore


def test_observe_tile_records_history():
    m = MemoryStore()
    m.observe_tile((3, 4), step=5, has_food=True)
    m.observe_tile((3, 4), step=15, has_food=False)
    m.observe_tile((3, 4), step=25, has_food=True)
    history = m.tile_food_observations[(3, 4)]
    assert history == [(5, True), (15, False), (25, True)]


def test_observe_tile_history_bounded():
    m = MemoryStore(tile_history_capacity=3)
    for s in range(10):
        m.observe_tile((0, 0), step=s, has_food=False)
    assert len(m.tile_food_observations[(0, 0)]) == 3
    # Oldest dropped first.
    assert m.tile_food_observations[(0, 0)][0][0] == 7


def test_observe_local_view_records_self_and_food_tiles():
    m = MemoryStore()
    obs = {
        "position": (5, 5),
        "food": [(5, 5), (6, 7)],  # standing on food + visible food elsewhere
        "hazards": [], "shelters": [], "others": [], "step": 10,
    }
    m.observe_local_view(obs, step=10)
    assert (5, 5) in m.tile_food_observations
    assert (6, 7) in m.tile_food_observations
    # Self-tile should record has_food=True (we're on a food tile).
    assert m.tile_food_observations[(5, 5)][-1] == (10, True)
    assert m.tile_food_observations[(6, 7)][-1] == (10, True)


def test_predict_food_return_with_periodic_history():
    m = MemoryStore()
    # Food at this tile every 10 steps starting at step 0.
    for s in [0, 10, 20, 30]:
        m.observe_tile((1, 1), step=s, has_food=True)
    # Now at step 35, food was last seen at 30, period is 10 → wait 5 more steps.
    pred = m.predict_food_return((1, 1), current_step=35)
    assert pred == 5


def test_predict_food_return_returns_none_for_unobserved_tile():
    m = MemoryStore()
    assert m.predict_food_return((9, 9), current_step=10) is None


def test_predict_food_return_returns_none_for_single_observation():
    m = MemoryStore()
    m.observe_tile((1, 1), step=5, has_food=True)
    # Only one food sighting → can't compute period.
    assert m.predict_food_return((1, 1), current_step=10) is None


def test_predict_food_return_zero_when_overdue():
    m = MemoryStore()
    for s in [0, 10, 20]:
        m.observe_tile((1, 1), step=s, has_food=True)
    # Step 35, last food at 20, period 10 → predicted next at 30, so we're
    # overdue by 5 steps. Should clamp to 0.
    pred = m.predict_food_return((1, 1), current_step=35)
    assert pred == 0


def test_known_feeding_ground_threshold():
    m = MemoryStore()
    m.observe_tile((2, 2), step=1, has_food=True)
    assert not m.known_feeding_ground((2, 2))  # only 1 observation
    m.observe_tile((2, 2), step=11, has_food=True)
    assert m.known_feeding_ground((2, 2))  # now 2
    # Tiles never seen with food don't count.
    m.observe_tile((3, 3), step=5, has_food=False)
    m.observe_tile((3, 3), step=15, has_food=False)
    assert not m.known_feeding_ground((3, 3))
