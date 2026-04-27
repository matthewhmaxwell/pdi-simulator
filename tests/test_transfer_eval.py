"""Tests for the transfer-eval CLI command (E009 generalization tests)."""
import json
import random
from pathlib import Path

import pytest
from click.testing import CliRunner

from pdi.agent import Agent
from pdi.config import AgentConfig
from pdi.main import cli
from pdi.schemas import Position, StrategyGenome


@pytest.fixture
def tmp_source_run(tmp_path, monkeypatch):
    """Create a fake completed source run with 3 saved agents."""
    monkeypatch.setattr("pdi.main.DATA_DIR", tmp_path)
    run_id = "fake_source"
    run_dir = tmp_path / run_id
    run_dir.mkdir()

    # Minimal config.json (transfer-eval reads cognition_tier from this).
    (run_dir / "config.json").write_text(json.dumps({
        "evo": {"cognition_tier": "full"},
    }))

    # 3 fake agents with distinct genomes.
    rng = random.Random(0)
    with (run_dir / "final_agents.jsonl").open("w") as fh:
        for _ in range(3):
            agent = Agent.spawn(
                generation=5, cfg=AgentConfig(),
                cognition_tier="full", rng=rng,
                strategy=StrategyGenome(
                    exploration_weight=rng.random(),
                    cooperation_weight=rng.random(),
                ),
                position=Position(x=0, y=0),
            )
            fh.write(json.dumps(agent.state.model_dump(), default=str) + "\n")
    return tmp_path, run_id


def test_transfer_eval_missing_source(tmp_path, monkeypatch):
    monkeypatch.setattr("pdi.main.DATA_DIR", tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, [
        "transfer-eval", "--source-run", "nonexistent",
        "--env", "grid", "--episodes", "1",
    ])
    assert result.exit_code != 0
    assert "No source run found" in result.output


def test_transfer_eval_runs_and_writes_outputs(tmp_source_run):
    tmp_path, run_id = tmp_source_run
    runner = CliRunner()
    result = runner.invoke(cli, [
        "transfer-eval",
        "--source-run", run_id,
        "--env", "grid",
        "--episodes", "2",
        "--steps", "10",  # tiny for speed
        "--grid", "8",
        "--food", "5",
        "--hazards", "1",
        "--shelters", "1",
        "--run-id", "xfer_out",
        "--seed", "1",
    ])
    assert result.exit_code == 0, result.output
    out_dir = tmp_path / "xfer_out"
    assert (out_dir / "metrics.csv").exists()
    assert (out_dir / "summary.json").exists()
    summary = json.loads((out_dir / "summary.json").read_text())
    assert summary["source_run"] == run_id
    assert summary["env"] == "grid"
    assert summary["n_agents"] == 3
    assert summary["episodes"] == 2
    assert 0.0 <= summary["mean_survival_rate"] <= 1.0


def test_transfer_eval_inherits_tier_from_source(tmp_source_run):
    tmp_path, run_id = tmp_source_run
    runner = CliRunner()
    result = runner.invoke(cli, [
        "transfer-eval", "--source-run", run_id,
        "--env", "cyclic", "--episodes", "1", "--steps", "10",
        "--grid", "8", "--food", "3", "--hazards", "0", "--shelters", "1",
        "--run-id", "xfer_inherit",
    ])
    assert result.exit_code == 0, result.output
    cfg = json.loads((tmp_path / "xfer_inherit" / "config.json").read_text())
    assert cfg["source_tier"] == "full"
    assert cfg["eval_tier"] == "full"


def test_transfer_eval_tier_override(tmp_source_run):
    tmp_path, run_id = tmp_source_run
    runner = CliRunner()
    result = runner.invoke(cli, [
        "transfer-eval", "--source-run", run_id,
        "--env", "grid", "--episodes", "1", "--steps", "10",
        "--grid", "8", "--food", "3", "--hazards", "0", "--shelters", "1",
        "--tier", "reflex",
        "--run-id", "xfer_override",
    ])
    assert result.exit_code == 0
    cfg = json.loads((tmp_path / "xfer_override" / "config.json").read_text())
    assert cfg["source_tier"] == "full"  # source unchanged
    assert cfg["eval_tier"] == "reflex"  # override applied
