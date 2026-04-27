#!/bin/bash
# E008: harden the E007 finding to n=20 seeds. We already have seeds
# 42, 7, 1, 13, 99 (5) from E007. Add 15 new seeds × 4 tiers × 2 envs = 120 runs.
#
# Sign-consistency at n=20 → binomial p ≤ 9.5e-7. Converts the +0.298 / +0.240
# finding from "suggestive" to "robust within this sandbox."
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

MAX=8
LOG_DIR=/tmp/pdi_e008
mkdir -p "$LOG_DIR"

TIERS=(reflex memory social full)
# 15 new seeds (small primes + 2,3 for variety, none overlap E007's 42/7/1/13/99).
NEW_SEEDS=(2 3 5 11 17 19 23 29 31 37 41 43 47 53 59)

throttle() {
  while [ "$(jobs -rp | wc -l)" -ge "$MAX" ]; do sleep 1; done
}

launch() {
  local run_id="$1"; shift
  echo "→ launching $run_id"
  pdi run --run-id "$run_id" --label "$run_id" "$@" \
    > "$LOG_DIR/$run_id.log" 2>&1 &
}

# Cyclic env (mirrors E007 e7c_*)
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

# Hard grid env (mirrors E007 e7g_*)
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
