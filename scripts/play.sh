#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/env.sh"
if [[ $# -lt 1 ]]; then
  echo '用法：./scripts/play.sh /绝对路径/checkpoint_final.pt [headless=true] [其他 Hydra 参数]'
  exit 2
fi
checkpoint="$(realpath -- "$1")"
shift
exec "$GALLANT_ROOT/.venv/bin/python" -u \
  "$GALLANT_ROOT/vendor/active-adaptation/scripts/play.py" \
  task=G1LidarNew algo=ppo_gallant_concat task.num_envs=1 \
  "checkpoint_path=$checkpoint" "$@"
