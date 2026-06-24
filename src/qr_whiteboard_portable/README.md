# 六二维码白板模型交付说明

模型尺寸为 2.25 m（宽）× 2.0 m（高）× 0.06 m（厚），包含 3 列 ×
2 行、共 6 个二维码。模型为 static，不依赖 ROS。

先确认实际软件版本。Ubuntu 22.04 是操作系统版本，不是 Gazebo 版本：

```bash
gazebo --version
gz sim --versions
```

## Gazebo Classic 11

在解压目录中运行：

```bash
export GAZEBO_MODEL_PATH="$PWD/models:${GAZEBO_MODEL_PATH}"
gazebo worlds/qr_whiteboard_model_only.world
```

也可将 `models/qr_whiteboard` 整个目录复制到 `~/.gazebo/models/`，然后
从 Gazebo 的 Insert 面板插入 `QR Whiteboard`。

## 新 Gazebo（Fortress / Garden / Harmonic 等）

在解压目录中运行：

```bash
export GZ_SIM_RESOURCE_PATH="$PWD/models:${GZ_SIM_RESOURCE_PATH}"
gz sim worlds/qr_whiteboard_model_only.world
```

如果所装版本使用旧命令名：

```bash
export IGN_GAZEBO_RESOURCE_PATH="$PWD/models:${IGN_GAZEBO_RESOURCE_PATH}"
ign gazebo worlds/qr_whiteboard_model_only.world
```

## 文件说明

- `models/qr_whiteboard/model.sdf`：白板碰撞体与视觉模型。
- `models/qr_whiteboard/meshes/qr_plane.dae`：带 UV 的正面贴图平面。
- `models/qr_whiteboard/materials/textures/qr_board.png`：六二维码纹理。
- `models/qr_whiteboard/materials/textures/qr_board.json`：二维码内容和布局。
- `worlds/qr_whiteboard_model_only.world`：不含 ROS 插件的测试世界。

本包只负责显示白板模型。原开发机的 ROS 相机 world 使用 ROS 1 Noetic
和 Gazebo Classic 插件，不适合直接复制到 Ubuntu 22.04 的 ROS 2 环境。
