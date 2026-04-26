# Experiment NNN — <short title>

> **One-line question.** What this experiment is asking, in a single sentence.

## Setup

- **Configs run:** list of `data/runs/<run_id>/` directories
- **Knobs that vary from defaults:** food / hazards / respawn / cognition tier / etc.
- **Seeds:** list every seed used. n=2 is anecdote; aim for n=5 minimum if you want to claim a directional result.
- **Total runs:** number, and which ones are new vs. reused from earlier experiments.

## What changed since the last experiment

- Code changes (file:line, with brief reason)
- Config changes
- Knobs that were locked in earlier experiments and remain locked here

## Results

### Headline numbers
Tables of mean ± stdev (or ± half-spread for n=2). Always show per-seed values somewhere, not just aggregates.

### Sign consistency
For directional claims, report the per-seed sign. "5/5 seeds show full > reflex" is much stronger than "mean diff is positive."

### Anything surprising
What didn't match the prediction. Bugs found. Anomalies worth follow-up.

## What the evidence supports

Be specific. "Cognition wins in this regime, n=5 seeds, sign-consistent" is a claim. "Cognition wins" is overclaim.

## What the evidence does NOT support

List the obvious next questions you can't answer yet, the confounders you haven't ruled out, and any tautologies in the metric definitions.

## Caveats and known issues

- Tautologies in the metrics (e.g., fitness rewards cooperation directly)
- Sample size limitations
- Confounders not yet isolated
- Implementation oddities discovered during the run

## Suggested next experiments

Numbered list, ranked by what would most cleanly resolve an open question. Each entry should name the question and the minimum config to answer it.

---

**Reproduce:** `bash scripts/run_eNNN_<name>.sh`  
**Aggregate:** `python scripts/analyze_eNNN.py` (or extend `analyze_robustness.py`)
