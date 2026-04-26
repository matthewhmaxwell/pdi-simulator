"""Tests for decoupled fitness components, novelty tracking, and LLM tier."""
import random

from pdi.agent import Agent
from pdi.cognition import LLMPolicy, build_policy
from pdi.config import AgentConfig, FitnessWeights
from pdi.schemas import Position, StrategyGenome


def _spawn(tier="full"):
    rng = random.Random(0)
    return Agent.spawn(generation=0, cfg=AgentConfig(), cognition_tier=tier, rng=rng,
                       position=Position(x=5, y=5))


def test_score_components_populated():
    a = _spawn()
    a.food_collected = 3
    a.cooperation_events = 2
    a.predictions_made = 4
    a.predictions_correct = 3
    a.update_fitness(weights=FitnessWeights())
    assert "survival" in a.score_components
    assert "foraging" in a.score_components
    assert "cooperation" in a.score_components
    assert a.score_components["foraging"] == 4.0 * 3
    assert a.score_components["cooperation"] == 2.0 * 2


def test_zeroing_cooperation_weight_eliminates_coop_contribution():
    a = _spawn()
    a.cooperation_events = 5
    weights = FitnessWeights(cooperation=0.0, betrayal_penalty=0.0)
    a.update_fitness(weights=weights)
    assert a.score_components["cooperation"] == 0.0


def test_default_fitness_matches_original_behavior():
    """Backward-compat: default weights reproduce the E001-E004 fitness formula."""
    a = _spawn()
    a.food_collected = 2
    a.cooperation_events = 1
    a.betrayal_events = 1
    a.predictions_made = 4
    a.predictions_correct = 3
    a.update_fitness()
    expected = (
        20.0  # alive
        + 4.0 * 2  # foraging
        + 2.0 * 1  # cooperation
        - 1.0 * 1  # betrayal
        + 5.0 * (3 / 4)  # prediction
        + 0.2 * a.state.energy
    )
    assert abs(a.state.fitness_score - expected) < 1e-6


def test_novelty_tracking_via_learn_from_outcome():
    a = _spawn()
    obs1 = {"food": [(1, 1)], "hazards": [], "shelters": [], "others": []}
    obs2 = {"food": [], "hazards": [(0, 0)], "shelters": [], "others": []}
    obs3 = {"food": [(1, 1)], "hazards": [], "shelters": [], "others": []}  # same tag as obs1
    for obs in [obs1, obs2, obs3]:
        a._pending_prediction = None
        a.learn_from_outcome(
            episode_id="e", timestamp=0, observation=obs,
            action="observe", reward_delta=0.0, outcome="ok", other_agents_present=[],
        )
    # obs1 and obs3 share a state tag (food_near). obs2 is hazard_near. → 2 unique tags.
    assert len(a.novel_state_tags) == 2


def test_llm_tier_buildable_and_falls_through_to_full():
    rng = random.Random(0)
    policy = build_policy("llm", StrategyGenome(), rng)
    assert isinstance(policy, LLMPolicy)
    obs = {"food": [(5, 5)], "hazards": [], "shelters": [], "others": [], "step": 0}
    # Should not crash; should return a valid action via FullPolicy fallback.
    from pdi.memory import MemoryStore
    from pdi.social import SocialModel
    act = policy.choose_action(
        observation=obs, position=Position(x=5, y=5),
        memory=MemoryStore(), social=SocialModel(), causal={},
        energy=50.0, health=50.0,
    )
    assert act in (
        "move_n", "move_s", "move_e", "move_w",
        "observe", "collect", "share", "withhold",
        "signal", "follow", "avoid", "rest",
    )
