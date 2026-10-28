"""Bounded simulation and checkpoint reload verification for the Gallant task."""
import json
from pathlib import Path

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from torchrl.envs.utils import ExplorationType, set_exploration_type

import active_adaptation as aa

ROOT = Path(__file__).resolve().parents[1]


@hydra.main(
    config_path=str(ROOT / "vendor/active-adaptation/cfg"),
    config_name="play",
    version_base=None,
)
def main(cfg: DictConfig):
    OmegaConf.resolve(cfg)
    OmegaConf.set_struct(cfg, False)
    aa.init(cfg, auto_rank=True)
    from active_adaptation.helpers import make_env_policy
    from active_adaptation.utils.wandb import parse_checkpoint

    checkpoint = parse_checkpoint(cfg.checkpoint_path)
    env, policy = make_env_policy(cfg, checkpoint)
    state = torch.load(checkpoint.get_path(), map_location=env.device, weights_only=False)
    failures = policy.load_state_dict(state["policy"], strict=True)
    assert not failures, f"Checkpoint modules failed to load: {failures}"
    env.eval()
    carry = env.reset()
    base = env.base_env
    rollout = policy.get_rollout_policy("eval")
    shapes = {key: list(carry[key].shape) for key in ("policy", "grid_map_")}
    resets = 0
    occupied_max = 0
    reward_sum = 0.0
    steps = int(cfg.get("verify_steps", 120))
    snapshot = None
    with torch.inference_mode(), set_exploration_type(ExplorationType.MODE):
        for _ in range(steps):
            carry = rollout(carry)
            assert torch.isfinite(carry["action"]).all(), "Non-finite policy action"
            transition, carry = env.step_and_maybe_reset(carry)
            reward = transition["next", "reward"]
            assert torch.isfinite(reward).all(), "Non-finite reward"
            assert torch.isfinite(carry["policy"]).all(), "Non-finite proprioception"
            resets += int(transition["next", "done"].sum())
            occupied_max = max(occupied_max, int(carry["grid_map_"].count_nonzero()))
            reward_sum += float(reward.sum())
            if cfg.get("snapshot", False) and snapshot is None:
                from PIL import Image

                center = base.scene.articulations["robot"].data.root_pos_w[0].cpu()
                base.sim.set_camera_view(
                    eye=(center + torch.tensor([3.0, 3.0, 2.0])).tolist(),
                    target=center.tolist(),
                )
                for _ in range(6):
                    frame = base.render("rgb_array")
                snapshot = ROOT / "logs/simulation_preview.png"
                Image.fromarray(frame).save(snapshot)
    assert occupied_max > 0, "LiDAR voxel map remained empty"
    result = {
        "status": "passed",
        "purpose": "simulation, voxel perception, policy inference and checkpoint reload",
        "checkpoint": str(cfg.checkpoint_path),
        "steps": steps,
        "num_envs": env.num_envs,
        "simulation_seconds_per_env": steps * base.step_dt,
        "observation_shapes": shapes,
        "action_shape": list(carry["action"].shape),
        "max_occupied_voxels": occupied_max,
        "episode_resets": resets,
        "reward_sum": reward_sum,
        "navigation_policy_trained_to_convergence": False,
        "snapshot": str(snapshot) if snapshot else None,
        "target_pos_w": base.command_manager.target_pos_w.cpu().tolist(),
        "root_pos_w": base.scene.articulations["robot"].data.root_pos_w.cpu().tolist(),
    }
    report_name = "simulation_verification.json" if cfg.headless else "simulation_verification_gui.json"
    output = ROOT / "logs" / report_name
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    env.close()
    aa.close()


if __name__ == "__main__":
    main()
