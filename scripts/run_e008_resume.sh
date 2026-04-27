#!/bin/bash
# E008 resume: launch only the runs that don't already exist.
# This makes the sweep idempotent — safe to re-run if the master script dies.
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

MAX=8
LOG_DIR=/tmp/pdi_e008
mkdir -p "$LOG_DIR"

TIERS=(reflex memory social full)
NEW_SEEDS=(2 3 5 11 17 19 23 29 31 37 41 43 47 53 59)

throttle() {
  while [ "$(jobs -rp | wc -l)" -ge "$MAX" ]; do sleep 1; done
}

skip_if_exists() {
  local run_id="$1"
  if [ -f "data/runs/$run_id/metrics.csv" ]; then
    return 0  # exists, skip
  fi
  return 1
}

launch() {
  local run_id="$1"; shift
  if skip_if_exists "$run_id"; then
    echo "✓ already done: $run_id"
    return
  fi
  echo "→ launching $run_id"
  pdi run --run-id "$run_id" --label "$run_id" "$@" \
    > "$LOG_DIR/$run_id.log" 2>&1 &
}

# Cyclic env
for SEED in "${NEW_SEEDS[@]}"; do
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

# Hard grid env
for SEED in "${NEW_SEEDS[@]}"; do
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

echo "All E008 runs queued. Waiting for completion..."
wait
echo "Sweep complete. Running n=20 analysis..."

python scripts/analyze_e008.py > /tmp/pdi_e008_results.txt 2>&1
echo "Analysis written to /tmp/pdi_e008_results.txt"
echo "------ Summary ------"
cat /tmp/pdi_e008_results.txt
