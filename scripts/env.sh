#!/usr/bin/env bash
# Source from the launch scripts so ROS/Conda variables cannot mix into Python 3.11.
GALLANT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export GALLANT_ROOT
unset PYTHONPATH LD_LIBRARY_PATH AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH
unset ISAAC_PATH CARB_APP_PATH EXP_PATH
export PYTHONNOUSERSITE=1
export OMNI_KIT_ACCEPT_EULA=YES
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export WANDB_MODE=offline
export WANDB_DIR="$GALLANT_ROOT/runs"
export WARP_CACHE_PATH="$GALLANT_ROOT/.cache/warp"
export MPLCONFIGDIR="$GALLANT_ROOT/.cache/matplotlib"
export HYDRA_FULL_ERROR=1
export PATH="$GALLANT_ROOT/.venv/bin:$PATH"
mkdir -p "$WANDB_DIR" "$WARP_CACHE_PATH" "$MPLCONFIGDIR"
cd "$GALLANT_ROOT"
