#!/bin/bash
# Robustness sweep: 5-seed firmness pass + knob-isolation pass.
# Runs at most $MAX simulations in parallel.
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

MAX=8
LOG_DIR=/tmp/pdi_sweep
mkdir -p "$LOG_DIR"

# Hard-env reference (E002): food=15, haz=20, respawn=0.02
# E001 baseline:               food=30, haz=8,  respawn=0.05
TIERS=(reflex memory social full)

# Helper: wait until fewer than MAX background jobs are running.
throttle() {
  while [ "$(jobs -rp | wc -l)" -ge "$MAX" ]; do
    sleep 1
  done
}

launch() {
  local run_id="$1"; shift
  echo "→ launching $run_id"
  pdi run --run-id "$run_id" --label "$run_id" "$@" \
    > "$LOG_DIR/$run_id.log" 2>&1 &
}

# ---- Part A: firmness pass at E002 config, new seeds ----
for SEED in 1 13 99; do
  for TIER in "${TIERS[@]}"; do
    throttle
    launch "e2_${TIER}_s${SEED}" \
      --generations 20 --agents 50 --episodes 10 \
      --grid 20 --steps 80 \
      --food 15 --hazards 20 --shelters 4 --respawn 0.02 \
      --tier "$TIER" --seed "$SEED"
  done
done

# ---- Part B: knob isolation at 2 seeds ----
# Each config changes ONE knob from E001 baseline.
for SEED in 42 7; do
  for TIER in "${TIERS[@]}"; do
    # e3a: food alone (15 instead of 30)
    throttle
    launch "e3a_${TIER}_s${SEED}" \
      --generations 20 --agents 50 --episodes 10 \
      --grid 20 --steps 80 \
      --food 15 --hazards 8 --shelters 4 --respawn 0.05 \
      --tier "$TIER" --seed "$SEED"

    # e3b: hazards alone (20 instead of 8)
    throttle
    launch "e3b_${TIER}_s${SEED}" \
      --generations 20 --agents 50 --episodes 10 \
      --grid 20 --steps 80 \
      --food 30 --hazards 20 --shelters 4 --respawn 0.05 \
      --tier "$TIER" --seed "$SEED"

    # e3c: respawn alone (0.02 instead of 0.05)
    throttle
    launch "e3c_${TIER}_s${SEED}" \
      --generations 20 --agents 50 --episodes 10 \
      --grid 20 --steps 80 \
      --food 30 --hazards 8 --shelters 4 --respawn 0.02 \
      --tier "$TIER" --seed "$SEED"
  done
done

echo "All runs queued. Waiting for completion..."
wait
echo "Sweep complete."
