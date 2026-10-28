#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.sh"
if [[ $# -lt 1 ]]; then
  echo '用法：./scripts/verify_sim.sh /绝对路径/checkpoint_final.pt [其他 Hydra 参数]'
  exit 2
fi
checkpoint="$(realpath -- "$1")"
shift
exec "$GALLANT_ROOT/.venv/bin/python" -u "$GALLANT_ROOT/scripts/verify_sim.py" \
  task=G1LidarNew algo=ppo_gallant_concat task.num_envs=4 headless=true \
  "checkpoint_path=$checkpoint" +verify_steps=120 "$@"
