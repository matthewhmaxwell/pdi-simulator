#!/bin/bash
# E007: --no-coop-fitness ablation. Tests whether the full > reflex survival
# advantage holds when we zero out the cooperation/betrayal terms in fitness
# (the tautology flagged in E003).
#
# Two envs:
#   - cyclic (E005 config)        → e7c_<tier>_s<seed>
#   - hard grid (E002/E003 config) → e7g_<tier>_s<seed>
#
# 4 tiers × 5 seeds × 2 envs = 40 runs.
# Throttled to 8 parallel; ~25-30 min wall time.
# After all runs finish, runs the analysis and writes /tmp/pdi_e007_results.txt.
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

MAX=8
LOG_DIR=/tmp/pdi_e007
mkdir -p "$LOG_DIR"

TIERS=(reflex memory social full)
SEEDS=(42 7 1 13 99)

throttle() {
  while [ "$(jobs -rp | wc -l)" -ge "$MAX" ]; do sleep 1; done
}

launch() {
  local run_id="$1"; shift
  echo "→ launching $run_id"
  pdi run --run-id "$run_id" --label "$run_id" "$@" \
    > "$LOG_DIR/$run_id.log" 2>&1 &
}

# ---- Part A: cyclic env (mirrors E005 config) ----
for SEED in "${SEEDS[@]}"; do
  for TIER in "${TIERS[@]}"; do
    throttle
    launch "e7c_${TIER}_s${SEED}" \
      --env cyclic \
      --no-coop-fitness \
      --generations 20 --agents 50 --episodes 10 \
      --grid 20 --steps 80 \
      --food 15 --hazards 8 --shelters 4 --respawn 0.05 \
      --tier "$TIER" --seed "$SEED"
  done
done

# ---- Part B: hard grid env (mirrors E002/E003 config) ----
for SEED in "${SEEDS[@]}"; do
  for TIER in "${TIERS[@]}"; do
    throttle
    launch "e7g_${TIER}_s${SEED}" \
      --env grid \
      --no-coop-fitness \
      --generations 20 --agents 50 --episodes 10 \
      --grid 20 --steps 80 \
      --food 15 --hazards 20 --shelters 4 --respawn 0.02 \
      --tier "$TIER" --seed "$SEED"
  done
done

echo "All E007 runs queued. Waiting for completion..."
wait
echo "Sweep complete. Running analysis..."

# ---- Analysis: compare with-coop-fitness vs without, both envs ----
python scripts/analyze_e007.py > /tmp/pdi_e007_results.txt 2>&1
echo "Analysis written to /tmp/pdi_e007_results.txt"
echo "------ Summary ------"
cat /tmp/pdi_e007_results.txt
