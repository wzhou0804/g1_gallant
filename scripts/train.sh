#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.sh"
exec "$GALLANT_ROOT/.venv/bin/python" -u \
  "$GALLANT_ROOT/vendor/active-adaptation/scripts/train_ppo.py" \
  task=G1LidarNew algo=ppo_gallant_concat \
  task.num_envs=32 headless=true wandb.mode=offline \
  "hydra.run.dir=$GALLANT_ROOT/outputs/\${now:%Y-%m-%d}/\${now:%H-%M-%S}" \
  "$@"
