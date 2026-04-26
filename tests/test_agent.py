import random

from pdi.agent import Agent
from pdi.config import AgentConfig
from pdi.memory import MemoryStore
from pdi.schemas import MemoryEvent, Position, StrategyGenome
from pdi.social import SocialModel


def test_memory_add_and_retrieve_similar():
    store = MemoryStore(capacity=10)
    obs = {"food": [(1, 1)], "hazards": [], "shelters": [], "others": []}
    store.add(MemoryEvent(
        timestamp=1, episode_id="e1",
        observed_state=obs, action_taken="collect",
        outcome="collected_food", reward_delta=4.0,
    ))
    store.add(MemoryEvent(
        timestamp=2, episode_id="e1",
        observed_state={"food": [], "hazards": [(0, 0)], "shelters": [], "others": []},
        action_taken="move_n", outcome="moved", reward_delta=-1.0,
    ))
    retrieved = store.retrieve_similar(obs, action="collect", k=3)
    assert retrieved, "expected at least one match"
    assert retrieved[0].action_taken == "collect"


def test_memory_forgets_low_usefulness_first():
    store = MemoryStore(capacity=3)
    for i in range(4):
        ev = MemoryEvent(
            timestamp=i, episode_id="e",
            observed_state={"food": [], "hazards": [], "shelters": [], "others": []},
            action_taken="observe", outcome="ok", reward_delta=float(i),
            usefulness=float(i),
        )
        store.add(ev)
    assert len(store) == 3
    # The least-useful event (usefulness=0) should be gone.
    assert all(ev.usefulness > 0 for ev in store.events)


def test_social_model_updates_after_share():
    s = SocialModel()
    s.observe_share("peer1")
    s.observe_share("peer1")
    b = s.beliefs["peer1"]
    assert b.trust_score > 0.5
    assert b.observed_helpful_actions == 2
    assert b.predicted_behavior == "cooperator"


def test_social_model_updates_after_withhold():
    s = SocialModel()
    s.observe_withhold("peer2")
    b = s.beliefs["peer2"]
    assert b.trust_score < 0.5
    assert b.predicted_behavior == "defector"


def test_agent_spawn_and_decide():
    rng = random.Random(0)
    agent = Agent.spawn(generation=0, cfg=AgentConfig(), cognition_tier="full", rng=rng)
    obs = {
        "position": (5, 5), "food": [(5, 5)], "hazards": [],
        "shelters": [], "others": [], "step": 0,
    }
    act = agent.decide(obs)
    assert act in ("collect", "observe", "move_n", "move_s", "move_e", "move_w",
                   "share", "withhold", "signal", "follow", "avoid", "rest")


def test_agent_learn_updates_memory_and_causal():
    rng = random.Random(0)
    agent = Agent.spawn(generation=0, cfg=AgentConfig(), cognition_tier="full", rng=rng)
    obs = {"food": [(1, 1)], "hazards": [], "shelters": [], "others": []}
    agent._pending_prediction = True
    agent.learn_from_outcome(
        episode_id="e1", timestamp=1, observation=obs,
        action="collect", reward_delta=4.0, outcome="collected_food",
        other_agents_present=[],
    )
    assert len(agent.memory) == 1
    assert any(cb.action == "collect" for cb in agent.causal.values())


def test_memory_policy_walks_toward_visible_food_not_consults_memory():
    """Regression test for the bug found in E003: MemoryPolicy used to skip
    food-seeking and consult memory instead, causing it to underperform reflex.
    Memory must be a fallback after goal-directed behavior, not a replacement.
    """
    rng = random.Random(0)
    # Force memory_reliance=1.0 so that, before the fix, memory consultation
    # would always preempt food-seeking.
    agent = Agent.spawn(
        generation=0, cfg=AgentConfig(), cognition_tier="memory", rng=rng,
        strategy=StrategyGenome(memory_reliance=1.0),
        position=Position(x=5, y=5),
    )
    # Seed memory with a wildly suboptimal action ("observe") that "succeeded"
    # in food_near contexts. Pre-fix, the policy would return "observe" instead
    # of moving toward the visible food.
    obs_with_food = {
        "food": [(7, 5)], "hazards": [], "shelters": [], "others": [],
    }
    for _ in range(5):
        agent._pending_prediction = None  # bypass prediction-tracking path
        agent.learn_from_outcome(
            episode_id="seed", timestamp=0,
            observation=obs_with_food, action="observe",
            reward_delta=10.0, outcome="trick", other_agents_present=[],
        )

    # Now ask for a decision in the same context. Should walk EAST toward food
    # at (7,5), not return "observe".
    act = agent.decide(obs_with_food)
    assert act == "move_e", (
        f"MemoryPolicy must walk toward visible food before consulting memory; "
        f"got {act!r}"
    )


def test_self_model_updates_reflect_episode():
    rng = random.Random(0)
    agent = Agent.spawn(generation=0, cfg=AgentConfig(), cognition_tier="full", rng=rng,
                        strategy=StrategyGenome(cooperation_weight=0.9, competition_weight=0.1))
    agent.food_collected = 4
    agent.cooperation_events = 2
    agent.update_self_model()
    assert "foraging" in agent.state.self_model.strengths
    assert "cooperation" in agent.state.self_model.strengths
    assert agent.state.self_model.preferred_strategy == "cooperator"
