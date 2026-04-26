#!/bin/bash
# E004: Re-run all 4 tiers at E002 config across 5 seeds, post-fix.
# Compares against the pre-fix e2_* runs to measure fix impact.
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

MAX=8
LOG_DIR=/tmp/pdi_e4
mkdir -p "$LOG_DIR"

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

for SEED in 42 7 1 13 99; do
  for TIER in reflex memory social full; do
    throttle
    launch "e4_${TIER}_s${SEED}" \
      --generations 20 --agents 50 --episodes 10 \
      --grid 20 --steps 80 \
      --food 15 --hazards 20 --shelters 4 --respawn 0.02 \
      --tier "$TIER" --seed "$SEED"
  done
done

echo "All 20 runs queued. Waiting..."
wait
echo "E004 sweep complete."
