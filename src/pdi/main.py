"""CLI entrypoint.

Commands:
    pdi run            Run a simulation with N generations x M episodes.
    pdi inspect-agent  Print the saved snapshot for an agent id.
    pdi summarize-run  Print headline metrics for a saved run.
    pdi export-metrics Re-export a run's metrics to CSV.

All artifacts land under data/runs/<run_id>/.
"""
from __future__ import annotations

import json
import random
import time
import uuid
from pathlib import Path

import click

from .config import AgentConfig, EnvironmentConfig, EvolutionConfig, FitnessWeights, SimConfig
from .evaluation import aggregate_generation, export_run_csv, export_run_json
from .evolution import run_episode, seed_population, select_and_breed
from .logging_utils import append_jsonl, get_logger

log = get_logger("pdi.cli")

# Project root: <repo>/data/runs
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "runs"


def _run_dir(run_id: str) -> Path:
    return DATA_DIR / run_id


def _save_final_agents(run_id: str, agents) -> None:
    agents_path = _run_dir(run_id) / "final_agents.jsonl"
    agents_path.parent.mkdir(parents=True, exist_ok=True)
    with agents_path.open("w", encoding="utf-8") as fh:
        for a in agents:
            payload = {
                **a.state.model_dump(),
                "memory_size": len(a.memory),
                "causal_beliefs": len(a.causal),
                "social_beliefs": len(a.social.beliefs),
                "self_model": a.state.self_model.model_dump(),
            }
            fh.write(json.dumps(payload, default=str) + "\n")


@click.group()
def cli() -> None:
    """Primate Developmental Intelligence Simulator."""
    pass


@cli.command("run")
@click.option("--generations", default=20, type=int, help="Number of generations.")
@click.option("--agents", "num_agents", default=50, type=int, help="Population size.")
@click.option("--episodes", default=10, type=int, help="Episodes per generation.")
@click.option("--grid", default=20, type=int, help="Grid size NxN.")
@click.option("--steps", default=80, type=int, help="Max steps per episode.")
@click.option("--food", default=30, type=int, help="Initial food count.")
@click.option("--hazards", default=8, type=int, help="Hazard count.")
@click.option("--shelters", default=4, type=int, help="Shelter count.")
@click.option("--respawn", default=0.05, type=float,
              help="Food respawn rate per step (cyclic env: 1/respawn = period).")
@click.option(
    "--env",
    "env_name",
    type=click.Choice(["grid", "cyclic"], case_sensitive=False),
    default="grid",
    help="Environment type. 'cyclic' has fixed feeding grounds with periodic respawn.",
)
@click.option(
    "--tier",
    type=click.Choice(["reflex", "memory", "social", "full", "llm"], case_sensitive=False),
    default="full",
    help="Cognition tier. Use to run comparison experiments.",
)
@click.option("--no-coop-fitness", is_flag=True,
              help="Zero out the cooperation fitness bonus (E008-style ablation).")
@click.option("--seed", default=42, type=int, help="Random seed.")
@click.option("--label", default="baseline", help="Human-readable label saved with the run.")
@click.option("--run-id", default=None, help="Override auto-generated run id.")
def run_cmd(generations, num_agents, episodes, grid, steps, food, hazards, shelters, respawn,
            env_name, tier, no_coop_fitness, seed, label, run_id):
    """Run a full simulation and save outputs under data/runs/<run_id>/."""
    fitness_weights = FitnessWeights()
    if no_coop_fitness:
        fitness_weights.cooperation = 0.0
        fitness_weights.betrayal_penalty = 0.0
    cfg = SimConfig(
        env=EnvironmentConfig(
            grid_size=grid,
            max_steps=steps,
            num_food=food,
            num_hazards=hazards,
            num_shelters=shelters,
            food_respawn_rate=respawn,
        ),
        agent=AgentConfig(),
        evo=EvolutionConfig(
            population_size=num_agents,
            generations=generations,
            episodes_per_generation=episodes,
            cognition_tier=tier.lower(),
            env_name=env_name.lower(),
            random_seed=seed,
        ),
        fitness=fitness_weights,
        run_label=label,
    )
    run_id = run_id or f"{int(time.time())}_{uuid.uuid4().hex[:6]}_{label}"
    rd = _run_dir(run_id)
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "config.json").write_text(json.dumps(cfg.to_dict(), indent=2))
    episode_log = rd / "episodes.jsonl"
    gen_log = rd / "generations.jsonl"

    rng = random.Random(cfg.evo.random_seed)
    log.info(
        f"[run {run_id}] env={env_name} tier={tier} pop={num_agents} "
        f"gens={generations} eps/gen={episodes} coop_fit={'off' if no_coop_fitness else 'on'}"
    )

    agents = seed_population(cfg, rng)
    all_gen_metrics = []
    baseline_fitness = 0.0

    for gen in range(cfg.evo.generations):
        # Reset fitness at the start of each generation so it reflects only
        # this generation's episodes, not accumulated across generations.
        for a in agents:
            a.state.fitness_score = 0.0

        episodes_this_gen = []
        for ep_idx in range(cfg.evo.episodes_per_generation):
            result = run_episode(
                agents, cfg.env, gen, rng,
                env_name=cfg.evo.env_name,
                fitness_weights=cfg.fitness,
            )
            episodes_this_gen.append(result)
            append_jsonl(episode_log, {
                "generation": gen,
                "episode_index": ep_idx,
                **result.__dict__,
            })

        gm = aggregate_generation(gen, episodes_this_gen, agents, baseline_fitness)
        if gen == 0:
            baseline_fitness = gm.avg_fitness
            gm.improvement_vs_baseline = 0.0
        all_gen_metrics.append(gm)
        append_jsonl(gen_log, gm.model_dump())

        log.info(
            f"[gen {gen:02d}] surv={gm.avg_survival_rate:.2f} "
            f"fit={gm.avg_fitness:.1f} food={gm.avg_resource_collection:.1f} "
            f"coop={gm.cooperation_frequency:.1f} betray={gm.betrayal_frequency:.1f} "
            f"pred={gm.prediction_accuracy:.2f} div={gm.strategy_diversity:.3f}"
        )

        # Breed next generation unless this is the last.
        if gen < cfg.evo.generations - 1:
            agents = select_and_breed(agents, gen + 1, cfg, rng)

    # Export summaries.
    export_run_csv(rd / "metrics.csv", all_gen_metrics)
    export_run_json(rd / "run.json", cfg.to_dict(), all_gen_metrics, agents)
    _save_final_agents(run_id, agents)

    click.echo(f"\nRun complete: {run_id}")
    click.echo(f"  dir:     {rd}")
    click.echo(f"  csv:     {rd / 'metrics.csv'}")
    click.echo(f"  json:    {rd / 'run.json'}")
    click.echo(f"  agents:  {rd / 'final_agents.jsonl'}")


@cli.command("transfer-eval")
@click.option("--source-run", required=True, help="Run id whose final_agents.jsonl supplies the genomes to evaluate.")
@click.option(
    "--env",
    "env_name",
    type=click.Choice(["grid", "cyclic"], case_sensitive=False),
    required=True,
    help="Environment to evaluate the transferred genomes in.",
)
@click.option("--episodes", default=20, type=int, help="Number of evaluation episodes.")
@click.option("--steps", default=80, type=int, help="Max steps per episode.")
@click.option("--grid", default=20, type=int, help="Grid size NxN.")
@click.option("--food", default=15, type=int, help="Initial food count.")
@click.option("--hazards", default=8, type=int, help="Hazard count.")
@click.option("--shelters", default=4, type=int, help="Shelter count.")
@click.option("--respawn", default=0.05, type=float, help="Food respawn rate per step.")
@click.option("--tier", default=None, help="Override the cognition tier (default: read from source run config).")
@click.option("--no-coop-fitness", is_flag=True, help="Use no-coop fitness weights for scoring.")
@click.option("--seed", default=42, type=int, help="Random seed for the evaluation env + episode order.")
@click.option("--label", default="transfer", help="Human label for the eval run.")
@click.option("--run-id", default=None, help="Override auto-generated run id.")
def transfer_eval_cmd(source_run, env_name, episodes, steps, grid, food, hazards, shelters,
                      respawn, tier, no_coop_fitness, seed, label, run_id):
    """Evaluate a population of evolved genomes in a different environment.

    Loads the final population from `--source-run`, recreates each agent with
    the same `StrategyGenome` but fresh memory/social/causal state, and runs
    `--episodes` episodes in `--env`. NO selection or breeding happens — this
    is a frozen-genome generalization test.

    Output: a `metrics.csv` (one row per episode) plus the usual config/run
    artifacts.
    """
    from .agent import Agent
    from .environments import make_environment
    from .evolution import run_episode
    from .schemas import StrategyGenome

    source_dir = _run_dir(source_run)
    agents_path = source_dir / "final_agents.jsonl"
    if not agents_path.exists():
        raise click.ClickException(f"No source run found: {source_run}")

    # Resolve cognition tier from source config if not overridden.
    src_cfg = json.loads((source_dir / "config.json").read_text()) if (source_dir / "config.json").exists() else {}
    src_tier = src_cfg.get("evo", {}).get("cognition_tier", "full")
    eval_tier = (tier or src_tier).lower()

    # Build the eval-time SimConfig (a fresh one — fitness weights, env config etc).
    fitness_weights = FitnessWeights()
    if no_coop_fitness:
        fitness_weights.cooperation = 0.0
        fitness_weights.betrayal_penalty = 0.0

    env_cfg = EnvironmentConfig(
        grid_size=grid, max_steps=steps,
        num_food=food, num_hazards=hazards,
        num_shelters=shelters, food_respawn_rate=respawn,
    )

    # Run id + dir.
    run_id = run_id or f"{int(time.time())}_{uuid.uuid4().hex[:6]}_{label}"
    rd = _run_dir(run_id)
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "config.json").write_text(json.dumps({
        "type": "transfer_eval",
        "source_run": source_run,
        "source_tier": src_tier,
        "eval_tier": eval_tier,
        "env": env_name,
        "episodes": episodes,
        "no_coop_fitness": no_coop_fitness,
        "seed": seed,
        "env_config": {
            "grid_size": grid, "max_steps": steps,
            "num_food": food, "num_hazards": hazards,
            "num_shelters": shelters, "food_respawn_rate": respawn,
        },
    }, indent=2))

    rng = random.Random(seed)

    # Recreate agents from saved genomes (fresh memory).
    agents = []
    for line in agents_path.read_text().splitlines():
        rec = json.loads(line)
        genome = StrategyGenome(**rec["strategy"])
        agents.append(Agent.spawn(
            generation=0, cfg=AgentConfig(),
            cognition_tier=eval_tier, rng=rng,
            strategy=genome,
        ))
    log.info(
        f"[transfer-eval {run_id}] tier={eval_tier} env={env_name} "
        f"agents={len(agents)} episodes={episodes} from source={source_run}"
    )

    # Run episodes WITHOUT breeding.
    episode_records = []
    for ep_idx in range(episodes):
        # Reset fitness on every agent so each episode score is independent.
        for a in agents:
            a.state.fitness_score = 0.0
        result = run_episode(agents, env_cfg, generation=0, rng=rng,
                             env_name=env_name, fitness_weights=fitness_weights)
        per_ep = {
            "episode": ep_idx,
            "survivors": result.survivors,
            "total_food_collected": result.total_food_collected,
            "cooperation_events": result.cooperation_events,
            "betrayal_events": result.betrayal_events,
            "avg_prediction_accuracy": result.avg_prediction_accuracy,
            "steps": result.steps,
            "survival_rate": result.survivors / max(len(agents), 1),
            "avg_fitness": sum(a.state.fitness_score for a in agents) / max(len(agents), 1),
        }
        episode_records.append(per_ep)
        log.info(
            f"  ep{ep_idx:02d}: surv={per_ep['survival_rate']:.2f} "
            f"food={per_ep['total_food_collected']} "
            f"coop={per_ep['cooperation_events']} fit={per_ep['avg_fitness']:.1f}"
        )

    # Export.
    import csv as _csv
    metrics_path = rd / "metrics.csv"
    if episode_records:
        with metrics_path.open("w", newline="", encoding="utf-8") as fh:
            writer = _csv.DictWriter(fh, fieldnames=list(episode_records[0].keys()))
            writer.writeheader()
            writer.writerows(episode_records)
    (rd / "summary.json").write_text(json.dumps({
        "run_id": run_id,
        "source_run": source_run,
        "eval_tier": eval_tier,
        "env": env_name,
        "n_agents": len(agents),
        "episodes": episodes,
        "mean_survival_rate": sum(r["survival_rate"] for r in episode_records) / max(len(episode_records), 1),
        "mean_food": sum(r["total_food_collected"] for r in episode_records) / max(len(episode_records), 1),
        "mean_fitness": sum(r["avg_fitness"] for r in episode_records) / max(len(episode_records), 1),
    }, indent=2))

    click.echo(f"\nTransfer eval complete: {run_id}")
    click.echo(f"  source:        {source_run} (tier={src_tier})")
    click.echo(f"  eval env+tier: {env_name} / {eval_tier}")
    click.echo(f"  csv:           {metrics_path}")
    click.echo(f"  summary:       {rd / 'summary.json'}")


@cli.command("inspect-agent")
@click.argument("agent_id")
@click.option("--run-id", required=True, help="Run id containing the agent.")
def inspect_agent(agent_id, run_id):
    """Print the saved snapshot for an agent from a completed run."""
    path = _run_dir(run_id) / "final_agents.jsonl"
    if not path.exists():
        raise click.ClickException(f"No such run: {run_id}")
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record["id"] == agent_id:
            click.echo(json.dumps(record, indent=2))
            return
    raise click.ClickException(f"Agent {agent_id} not found in run {run_id}")


@cli.command("summarize-run")
@click.argument("run_id")
def summarize_run(run_id):
    """Print headline metrics for a saved run."""
    rd = _run_dir(run_id)
    metrics_path = rd / "metrics.csv"
    config_path = rd / "config.json"
    if not metrics_path.exists():
        raise click.ClickException(f"No metrics.csv in run {run_id}")

    cfg = json.loads(config_path.read_text()) if config_path.exists() else {}
    click.echo(f"Run: {run_id}")
    click.echo(f"Label: {cfg.get('run_label', '?')}")
    click.echo(f"Tier:  {cfg.get('evo', {}).get('cognition_tier', '?')}")
    click.echo(f"Pop:   {cfg.get('evo', {}).get('population_size', '?')}")

    import csv
    with metrics_path.open() as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        click.echo("  (no generations recorded)")
        return

    first, last = rows[0], rows[-1]
    click.echo("\nGeneration 0 vs final:")
    for k in ("avg_survival_rate", "avg_fitness", "avg_resource_collection",
              "cooperation_frequency", "prediction_accuracy", "strategy_diversity"):
        click.echo(f"  {k:30s} {float(first[k]):8.3f}  →  {float(last[k]):8.3f}")


@cli.command("export-metrics")
@click.argument("run_id")
@click.option("--out", default=None, type=click.Path(), help="Output CSV path.")
def export_metrics(run_id, out):
    """Re-export metrics.csv from a completed run (already written by `run`)."""
    src = _run_dir(run_id) / "metrics.csv"
    if not src.exists():
        raise click.ClickException(f"No metrics in run {run_id}")
    dst = Path(out) if out else src
    if dst != src:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    click.echo(f"Metrics at: {dst}")


if __name__ == "__main__":
    cli()
