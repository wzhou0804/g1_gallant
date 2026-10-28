# Gallant G1 地形导航训练工作区

首次部署目录：`/home/zhouwei/Documents/g1_gllant`。克隆仓库后，以下命令中的工作目录改为实际克隆位置，先按“重建环境”运行安装脚本。

本工作区运行官方 Gallant 的 `G1LidarNew` 任务：三维地形、模拟激光雷达、体素观测、目标点命令和全身 PPO 控制。已完成单卡短训练、检查点保存和加载、无界面仿真及单机器人图形回放。当前示例检查点来自短训练，策略仍需继续训练才能稳定导航和上下楼梯。

## 环境

| 项目 | 配置 |
| --- | --- |
| Python | 本目录 `.python311`，Python 3.11.17 |
| 隔离虚拟环境 | 本目录 `.venv`，不继承系统包 |
| 仿真 | Isaac Sim 5.1.0.0 / Isaac Lab 2.3.2 |
| 学习框架 | PyTorch 2.7.0 CUDA 12.8 / TorchRL 0.8.1 / TensorDict 0.8.3 |
| 射线查询 | Warp 1.11.1 / simple-raycaster 0.4.2 |
| 默认训练 | RTX 4060 8 GB、32 个并行环境、无界面、W&B 本地离线记录 |
| 模型 | 上游 `g1_waist_unlocked`，29 个动作关节 |
| 观测 | 504 维机身/关节/目标观测，以及 `40×32×32` 体素观测 |

Python 和仿真包从本机已安装环境复制到本目录，后续安装只修改本目录。启动脚本会清除 ROS 的 Python/动态库路径。现有 `go2_omniverse` 项目的 27 轴 OpenHomie 环境保持原样。

代码位于 `vendor/Gallant` 和 `vendor/active-adaptation`；上游 URL 与固定提交见 `sources.json`，本机兼容修复见 `patches/`，完整包版本见 `requirements.lock.txt`。

## 开始训练

```bash
cd /home/zhouwei/Documents/g1_gllant
./scripts/train.sh
```

默认预算为 150,000,000 个环境采样帧，算法为 `ppo_gallant_concat`。训练从随机参数开始；地形包括平地、顶部障碍、树状障碍、门、平台、柱阵、上行和下行台阶，目标点由任务自动采样。

先运行一次短训练：

```bash
./scripts/train.sh total_frames=3072 checkpoint_interval=1
```

调整并行环境数量或训练预算：

```bash
./scripts/train.sh task.num_envs=16 total_frames=10000000
```

所有参数使用 Hydra 的 `key=value` 形式，命令末尾参数覆盖脚本默认值。图形训练可传 `headless=false`。RTX 4060 的 32 环境短测运行显存约 4.6–4.9 GB，采样速度约 900–950 帧/秒。

## 检查点和继续训练

运行配置及终端日志目录为 `outputs/日期/时间/`。W&B 的指标与模型保存在 `runs/wandb/offline-run-*/files/`：

- `cfg.yaml`：该次运行参数。
- `checkpoint_latest.pt`：最近保存的模型链接。
- `checkpoint_final.pt`：训练预算完成后的模型。

结束时终端打印 `Final checkpoint: ...`。W&B 默认离线，无需账号。

已有模型继续训练：

```bash
./scripts/train.sh checkpoint_path=/绝对路径/checkpoint_final.pt total_frames=10000000
```

上游检查点保存网络及归一化参数；上述命令加载模型参数并启动新训练，优化器和采样计数重新初始化。

## 图形回放与仿真验证

回放本次短训练模型，打开 Isaac Sim 图形窗口：

```bash
./scripts/play.sh checkpoints/smoke_final.pt
```

回放自己训练的模型：

```bash
./scripts/play.sh /绝对路径/checkpoint_final.pt
```

窗口会显示 G1、目标方向和局部体素点。该入口使用 Gallant 任务的自动目标采样，不依赖 Nav2。按 Ctrl+C 结束回放。

有界无界面验证，会执行 120 步、检查动作和奖励数值、验证体素非空及检查点加载：

```bash
./scripts/verify_sim.sh checkpoints/smoke_final.pt
```

单机器人图形验证并生成预览图：

```bash
./scripts/verify_sim.sh checkpoints/smoke_final.pt \
  task.num_envs=1 headless=false record_video=true +snapshot=true
```

结果写入 `logs/simulation_verification.json` 或 `logs/simulation_verification_gui.json`；截图为 `logs/simulation_preview.png`。验证报告中的 `passed` 表示仿真、感知和模型执行链路通过；导航能力由后续训练与到点评估衡量。

本次训练验证使用 32 个环境采样 3072 帧，完成 2 次 PPO 更新和 499 步最终评估，检查点中 57 个张量数值有限，其中 48 个相对第一次更新后的检查点发生变化。记录见 [训练验证](logs/training_verification.json)、[无界面仿真验证](logs/simulation_verification.json)、[图形仿真验证](logs/simulation_verification_gui.json)。

## 重建环境

现有环境已经配置完成。需要重装时运行：

```bash
./scripts/setup.sh
```

首次创建环境时，安装脚本以相邻 `go2_omniverse` 中的 `.cache-g1/python311` 和 `.venv-g1-sim` 为本机种子，复制独立文件，再安装固定版本训练依赖并应用补丁。也可指定相同版本的种子目录：

```bash
./scripts/setup.sh --seed /本机种子项目目录
```

## 本机兼容修复

1. 将随机化配置改为当前 Active Adaptation 的名称与参数格式，保持原有刚度/阻尼范围和默认转子惯量。
2. Gallant 奖励实现采用当前框架的 `_compute()` 接口，由框架统一乘权重并计数。
3. 接收新版 simple-raycaster 的命中点、距离和法线三个返回值。
4. 显式指定 `action_log_prob`，匹配 Gallant PPO 更新使用的键名。
5. 在离线 W&B 初始化时设置运行名称，修复训练结束评估的计时器层级切换。
6. 初始化单环境回放使用的地形起点，并显式关闭 SimulationApp。

官方来源：[Gallant](https://github.com/InternRobotics/Gallant)、[Active Adaptation](https://github.com/btx0424/active-adaptation)。公开仓库未附带本任务的预训练权重；本目录提供可自行训练的完整入口。
