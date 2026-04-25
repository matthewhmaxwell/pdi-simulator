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

from .config import AgentConfig, EnvironmentConfig, EvolutionConfig, SimConfig
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
@click.option("--respawn", default=0.05, type=float, help="Food respawn rate per step.")
@click.option(
    "--tier",
    type=click.Choice(["reflex", "memory", "social", "full"], case_sensitive=False),
    default="full",
    help="Cognition tier. Use to run comparison experiments.",
)
@click.option("--seed", default=42, type=int, help="Random seed.")
@click.option("--label", default="baseline", help="Human-readable label saved with the run.")
@click.option("--run-id", default=None, help="Override auto-generated run id.")
def run_cmd(generations, num_agents, episodes, grid, steps, food, hazards, shelters, respawn,
            tier, seed, label, run_id):
    """Run a full simulation and save outputs under data/runs/<run_id>/."""
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
            random_seed=seed,
        ),
        run_label=label,
    )
    run_id = run_id or f"{int(time.time())}_{uuid.uuid4().hex[:6]}_{label}"
    rd = _run_dir(run_id)
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "config.json").write_text(json.dumps(cfg.to_dict(), indent=2))
    episode_log = rd / "episodes.jsonl"
    gen_log = rd / "generations.jsonl"

    rng = random.Random(cfg.evo.random_seed)
    log.info(f"[run {run_id}] tier={tier} pop={num_agents} gens={generations} eps/gen={episodes}")

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
            result = run_episode(agents, cfg.env, gen, rng)
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
