#!/bin/bash
# E005: tier ablation in CyclicEnvironment.
# Hypothesis: with fixed feeding grounds + periodic respawn, memory tier
# can learn the period and outperform reflex (it couldn't in grid env).
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

MAX=8
LOG_DIR=/tmp/pdi_e005
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

# Cyclic env config: 15 feeding grounds, period 20 (respawn=0.05),
# moderate hazards so survival is challenged but not catastrophic.
for SEED in "${SEEDS[@]}"; do
  for TIER in "${TIERS[@]}"; do
    throttle
    launch "e5_${TIER}_s${SEED}" \
      --env cyclic \
      --generations 20 --agents 50 --episodes 10 \
      --grid 20 --steps 80 \
      --food 15 --hazards 8 --shelters 4 --respawn 0.05 \
      --tier "$TIER" --seed "$SEED"
  done
done

echo "All E005 runs queued. Waiting for completion..."
wait
echo "E005 sweep complete."
