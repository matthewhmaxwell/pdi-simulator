import random

from pdi.config import AgentConfig, EnvironmentConfig, EvolutionConfig, SimConfig
from pdi.evolution import (
    crossover,
    mutate_genome,
    run_episode,
    seed_population,
    select_and_breed,
)
from pdi.schemas import StrategyGenome


def _small_cfg(pop=8, gens=2, eps=2) -> SimConfig:
    return SimConfig(
        env=EnvironmentConfig(grid_size=10, num_food=10, num_hazards=2, num_shelters=2, max_steps=15),
        agent=AgentConfig(memory_capacity=50),
        evo=EvolutionConfig(population_size=pop, generations=gens, episodes_per_generation=eps,
                            cognition_tier="full", random_seed=7),
    )


def test_mutation_preserves_schema_and_bounds():
    rng = random.Random(0)
    parent = StrategyGenome()
    child = mutate_genome(parent, rate=1.0, sigma=0.5, rng=rng)
    for k, v in child.model_dump().items():
        assert 0.0 <= v <= 1.0, f"{k}={v} out of bounds"


def test_crossover_fields_come_from_either_parent():
    rng = random.Random(0)
    a = StrategyGenome(exploration_weight=0.1, cooperation_weight=0.1)
    b = StrategyGenome(exploration_weight=0.9, cooperation_weight=0.9)
    c = crossover(a, b, rng)
    assert c.exploration_weight in (0.1, 0.9)
    assert c.cooperation_weight in (0.1, 0.9)


def test_seed_population_produces_diverse_genomes():
    cfg = _small_cfg(pop=20)
    rng = random.Random(cfg.evo.random_seed)
    pop = seed_population(cfg, rng)
    assert len(pop) == 20
    weights = [a.state.strategy.exploration_weight for a in pop]
    assert max(weights) - min(weights) > 0.1, "population should have variation"


def test_run_episode_completes_and_updates_fitness():
    cfg = _small_cfg()
    rng = random.Random(cfg.evo.random_seed)
    pop = seed_population(cfg, rng)
    result = run_episode(pop, cfg.env, generation=0, rng=rng)
    assert result.steps <= cfg.env.max_steps
    assert all(a.state.fitness_score != 0.0 for a in pop) or all(a.state.fitness_score == 0.0 for a in pop)
    # Fitness should be set for at least one agent.
    assert any(a.state.fitness_score > 0 for a in pop)


def test_select_and_breed_preserves_population_size():
    cfg = _small_cfg(pop=10)
    rng = random.Random(cfg.evo.random_seed)
    pop = seed_population(cfg, rng)
    run_episode(pop, cfg.env, generation=0, rng=rng)
    next_gen = select_and_breed(pop, next_generation=1, cfg=cfg, rng=rng)
    assert len(next_gen) == 10
    assert all(a.state.generation == 1 for a in next_gen)
    # Parent ids should reference the previous generation.
    parent_ids = {a.state.id for a in pop}
    assert any(a.state.parent_id in parent_ids for a in next_gen)


def test_full_evolutionary_loop_runs_multiple_generations():
    cfg = _small_cfg(pop=10, gens=3, eps=2)
    rng = random.Random(cfg.evo.random_seed)
    pop = seed_population(cfg, rng)
    for gen in range(cfg.evo.generations):
        for a in pop:
            a.state.fitness_score = 0.0
        for _ in range(cfg.evo.episodes_per_generation):
            run_episode(pop, cfg.env, generation=gen, rng=rng)
        if gen < cfg.evo.generations - 1:
            pop = select_and_breed(pop, next_generation=gen + 1, cfg=cfg, rng=rng)
    assert len(pop) == 10
    assert max(a.state.generation for a in pop) == cfg.evo.generations - 1
