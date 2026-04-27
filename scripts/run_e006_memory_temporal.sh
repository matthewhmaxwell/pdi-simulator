#!/bin/bash
# E006: verify the time-aware memory retrieval added in src/pdi/memory.py
# actually helps memory tier in CyclicEnvironment.
#
# Compares against e5_memory_s* (memory tier in cyclic env, OLD memory code,
# WITH coop-fitness) — but the cleaner comparison is against re-run reflex
# in the same condition (e6r_*).
#
# Sweeps:
#   - e6m_memory_s<seed>      memory tier, time-aware retrieval, NO coop fitness
#   - e6r_reflex_s<seed>      reflex baseline, NO coop fitness (control, identical to e7c_reflex)
# 5 seeds × 2 tiers = 10 runs. ~10 min wall.
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

MAX=8
LOG_DIR=/tmp/pdi_e006
mkdir -p "$LOG_DIR"

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

for SEED in "${SEEDS[@]}"; do
  # Memory tier with the new time-aware retrieval.
  throttle
  launch "e6m_memory_s${SEED}" \
    --env cyclic \
    --no-coop-fitness \
    --generations 20 --agents 50 --episodes 10 \
    --grid 20 --steps 80 \
    --food 15 --hazards 8 --shelters 4 --respawn 0.05 \
    --tier memory --seed "$SEED"
done

echo "All E006 memory runs queued. Waiting..."
wait
echo "E006 sweep complete. Running analysis..."

python scripts/analyze_e006.py > /tmp/pdi_e006_results.txt 2>&1
echo "Analysis written to /tmp/pdi_e006_results.txt"
echo "------ Summary ------"
cat /tmp/pdi_e006_results.txt
