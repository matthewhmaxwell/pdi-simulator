"""Evolutionary loop.

Runs episodes, scores agents, selects elites, and mutates offspring's
StrategyGenome weights to produce the next generation. Memory does NOT carry
over between generations — learning within a lifetime is the phenotype; what
gets inherited is the genome that shapes how learning happens.
"""
from __future__ import annotations

import random
import statistics
import uuid
from dataclasses import dataclass
from typing import Optional

from .agent import Agent
from .config import SimConfig
from .environments import BaseEnvironment, make_environment
from .schemas import (
    ALL_ACTIONS,
    Action,
    AgentState,
    EpisodeMetrics,
    GenerationMetrics,
    Position,
    StrategyGenome,
)


# ---------- episode runner ----------

@dataclass
class EpisodeResult:
    episode_id: str
    generation: int
    steps: int
    survivors: int
    total_food_collected: int
    cooperation_events: int
    betrayal_events: int
    avg_prediction_accuracy: float


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _apply_action(
    agent: Agent,
    action: Action,
    env: BaseEnvironment,
    agent_positions: dict[str, Position],
    agents_by_id: dict[str, Agent],
    observation: dict,
) -> tuple[float, str]:
    """Resolve one action. Returns (reward_delta, outcome_label).

    Mutates `agent.state` and `env` in place. Does NOT write to memory —
    the caller does that via `agent.learn_from_outcome`.
    """
    cfg = agent.cfg
    reward = 0.0
    outcome = "noop"

    # Per-step energy decay.
    agent.state.energy -= cfg.energy_decay

    if action in ("move_n", "move_s", "move_e", "move_w"):
        dx, dy = env.move_delta(action)
        new_pos = env.clamp_move(agent.state.location, dx, dy)
        agent.state.location = new_pos
        agent.state.energy -= cfg.move_cost
        agent_positions[agent.state.id] = new_pos
        tile = env.tile(new_pos)
        if tile.has_hazard:
            agent.state.health -= env.cfg.hazard_damage
            reward -= 5.0
            outcome = "stepped_on_hazard"
        else:
            outcome = "moved"

    elif action == "observe":
        # Free info gathering; tiny energy cost already applied.
        outcome = "observed"

    elif action == "collect":
        if env.consume_food(agent.state.location):
            agent.state.energy += env.cfg.food_energy
            agent.food_collected += 1
            reward += 4.0
            outcome = "collected_food"
        else:
            reward -= 0.2
            outcome = "no_food_to_collect"

    elif action == "share":
        # Find an adjacent agent and give them energy.
        target = _adjacent_agent(agent, agent_positions, agents_by_id)
        if target is not None and agent.state.energy > cfg.share_cost + 5:
            agent.state.energy -= cfg.share_cost
            target.state.energy += cfg.share_cost
            agent.cooperation_events += 1
            # Target updates its social belief about the giver.
            target.social.observe_share(agent.state.id)
            reward += 0.5
            outcome = "shared_with_peer"
        else:
            outcome = "share_failed"

    elif action == "withhold":
        target = _adjacent_agent(agent, agent_positions, agents_by_id)
        if target is not None:
            agent.betrayal_events += 1
            target.social.observe_withhold(agent.state.id)
            reward += 0.2  # short-term gain, long-term trust cost
            outcome = "withheld_from_peer"
        else:
            outcome = "withhold_noop"

    elif action == "signal":
        agent.state.energy -= cfg.signal_cost
        outcome = "signaled"

    elif action == "follow":
        target = _nearest_visible_peer(agent, observation, agents_by_id)
        if target is not None:
            dx = target.state.location.x - agent.state.location.x
            dy = target.state.location.y - agent.state.location.y
            step_dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
            step_dy = 0 if step_dx != 0 else (1 if dy > 0 else (-1 if dy < 0 else 0))
            new_pos = env.clamp_move(agent.state.location, step_dx, step_dy)
            agent.state.location = new_pos
            agent_positions[agent.state.id] = new_pos
            agent.state.energy -= cfg.move_cost
            # Credit the peer if following landed us next to food.
            tile = env.tile(new_pos)
            if tile.has_food:
                agent.social.observe_follow_success(target.state.id)
                reward += 0.3
            outcome = "followed_peer"
        else:
            outcome = "follow_no_peer"

    elif action == "avoid":
        target = _nearest_visible_peer(agent, observation, agents_by_id)
        if target is not None:
            dx = agent.state.location.x - target.state.location.x
            dy = agent.state.location.y - target.state.location.y
            step_dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
            step_dy = 0 if step_dx != 0 else (1 if dy > 0 else (-1 if dy < 0 else 0))
            new_pos = env.clamp_move(agent.state.location, step_dx, step_dy)
            agent.state.location = new_pos
            agent_positions[agent.state.id] = new_pos
            agent.state.energy -= cfg.move_cost
            outcome = "avoided_peer"
        else:
            outcome = "avoid_no_peer"

    elif action == "rest":
        tile = env.tile(agent.state.location)
        if tile.has_shelter:
            agent.state.health = min(100.0, agent.state.health + env.cfg.shelter_rest)
            agent.state.energy = min(100.0, agent.state.energy + env.cfg.shelter_rest)
            reward += 1.0
            outcome = "rested_at_shelter"
        else:
            outcome = "rest_no_shelter"

    # Boundary / death checks.
    if agent.state.energy <= 0 or agent.state.health <= 0:
        agent.state.alive = False
        reward -= 5.0
        outcome = "died_" + outcome

    return reward, outcome


def _adjacent_agent(
    agent: Agent,
    agent_positions: dict[str, Position],
    agents_by_id: dict[str, Agent],
) -> Optional[Agent]:
    pos = agent.state.location
    best = None
    best_d = 99
    for oid, p in agent_positions.items():
        if oid == agent.state.id:
            continue
        other = agents_by_id.get(oid)
        if other is None or not other.state.alive:
            continue
        d = abs(p.x - pos.x) + abs(p.y - pos.y)
        if d <= 1 and d < best_d:
            best = other
            best_d = d
    return best


def _nearest_visible_peer(
    agent: Agent,
    observation: dict,
    agents_by_id: dict[str, Agent],
) -> Optional[Agent]:
    pos = (agent.state.location.x, agent.state.location.y)
    best = None
    best_d = 99
    for (oid, x, y) in observation["others"]:
        if oid == agent.state.id:
            continue
        other = agents_by_id.get(oid)
        if other is None or not other.state.alive:
            continue
        d = abs(x - pos[0]) + abs(y - pos[1])
        if d < best_d:
            best = other
            best_d = d
    return best


def run_episode(
    agents: list[Agent],
    env_cfg,
    generation: int,
    rng: random.Random,
    env_name: str = "grid",
    fitness_weights=None,
) -> EpisodeResult:
    env = make_environment(env_name, env_cfg, rng)
    episode_id = f"g{generation}_e{uuid.uuid4().hex[:6]}"

    # Place agents.
    agent_positions: dict[str, Position] = {}
    for a in agents:
        a.reset_for_episode(env.random_empty_position())
        agent_positions[a.state.id] = a.state.location
    agents_by_id = {a.state.id: a for a in agents}

    step = 0
    while step < env_cfg.max_steps:
        step += 1
        # Order matters slightly; shuffle for fairness.
        order = list(agents)
        rng.shuffle(order)
        for a in order:
            if not a.state.alive:
                continue
            obs = env.local_view(a.state.location, agent_positions)
            action = a.decide(obs)
            reward, outcome = _apply_action(
                a, action, env, agent_positions, agents_by_id, obs
            )
            a.learn_from_outcome(
                episode_id=episode_id,
                timestamp=step,
                observation=obs,
                action=action,
                reward_delta=reward,
                outcome=outcome,
                other_agents_present=[o[0] for o in obs["others"]],
            )
        env.tick_respawn()
        if not any(a.state.alive for a in agents):
            break

    # Compute per-episode metrics.
    survivors = sum(1 for a in agents if a.state.alive)
    total_food = sum(a.food_collected for a in agents)
    coop = sum(a.cooperation_events for a in agents)
    betray = sum(a.betrayal_events for a in agents)
    accs = [
        a.predictions_correct / a.predictions_made
        for a in agents
        if a.predictions_made > 0
    ]
    avg_acc = statistics.mean(accs) if accs else 0.0

    # Update fitness & self-model per agent after episode.
    for a in agents:
        a.update_fitness(weights=fitness_weights)
        a.update_self_model()

    return EpisodeResult(
        episode_id=episode_id,
        generation=generation,
        steps=step,
        survivors=survivors,
        total_food_collected=total_food,
        cooperation_events=coop,
        betrayal_events=betray,
        avg_prediction_accuracy=avg_acc,
    )


# ---------- selection & mutation ----------

def mutate_genome(parent: StrategyGenome, rate: float, sigma: float, rng: random.Random) -> StrategyGenome:
    fields = parent.model_dump()
    for k, v in fields.items():
        if rng.random() < rate:
            fields[k] = _clip(v + rng.gauss(0, sigma))
    return StrategyGenome(**fields)


def crossover(a: StrategyGenome, b: StrategyGenome, rng: random.Random) -> StrategyGenome:
    af = a.model_dump()
    bf = b.model_dump()
    child = {k: (af[k] if rng.random() < 0.5 else bf[k]) for k in af}
    return StrategyGenome(**child)


def select_and_breed(
    agents: list[Agent],
    next_generation: int,
    cfg: SimConfig,
    rng: random.Random,
) -> list[Agent]:
    # Rank by fitness descending.
    ranked = sorted(agents, key=lambda a: a.state.fitness_score, reverse=True)
    n = cfg.evo.population_size
    elite_count = max(2, int(n * cfg.evo.elite_fraction))
    elites = ranked[:elite_count]

    offspring: list[Agent] = []
    # Carry elite genomes forward as fresh agents (not their memories).
    for parent in elites:
        child_strategy = mutate_genome(
            parent.state.strategy,
            rate=cfg.evo.mutation_rate * 0.5,  # elites mutate gently
            sigma=cfg.evo.mutation_sigma * 0.5,
            rng=rng,
        )
        child = Agent.spawn(
            generation=next_generation,
            cfg=cfg.agent,
            cognition_tier=cfg.evo.cognition_tier,
            rng=rng,
            parent_id=parent.state.id,
            strategy=child_strategy,
        )
        offspring.append(child)

    # Fill the rest via tournament-pick crossover of elites.
    while len(offspring) < n:
        p1 = rng.choice(elites)
        p2 = rng.choice(elites)
        child_strategy = crossover(p1.state.strategy, p2.state.strategy, rng)
        child_strategy = mutate_genome(
            child_strategy,
            rate=cfg.evo.mutation_rate,
            sigma=cfg.evo.mutation_sigma,
            rng=rng,
        )
        child = Agent.spawn(
            generation=next_generation,
            cfg=cfg.agent,
            cognition_tier=cfg.evo.cognition_tier,
            rng=rng,
            parent_id=p1.state.id,
            strategy=child_strategy,
        )
        offspring.append(child)

    return offspring


def seed_population(cfg: SimConfig, rng: random.Random) -> list[Agent]:
    pop: list[Agent] = []
    for _ in range(cfg.evo.population_size):
        # Randomize starting genomes so selection has variation to work with.
        genome = StrategyGenome(
            exploration_weight=rng.random(),
            exploitation_weight=rng.random(),
            cooperation_weight=rng.random(),
            competition_weight=rng.random() * 0.6,
            risk_tolerance=rng.random(),
            memory_reliance=rng.random(),
            social_learning_weight=rng.random(),
            curiosity_weight=rng.random(),
            deception_tolerance=rng.random() * 0.5,
            reciprocity_weight=rng.random(),
        )
        agent = Agent.spawn(
            generation=0,
            cfg=cfg.agent,
            cognition_tier=cfg.evo.cognition_tier,
            rng=rng,
            strategy=genome,
        )
        pop.append(agent)
    return pop
