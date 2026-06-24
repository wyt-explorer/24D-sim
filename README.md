# aerostack2-main 二维码无人机 Demo 说明

本文档用于说明当前 `aerostack2-main` 工作区中各个 ROS 2 包的大致功能，以及如何只编译必要包并运行二维码白板无人机演示。

当前演示目标：在 Gazebo 中启动已有六二维码白板和 Aerostack2 x500 无人机，让无人机依次飞到每个二维码前方，到点后输出二维码世界坐标、打开激光提示，并在二维码中心短暂显示黄色发光点。

> 重要说明：最终 demo 保留了 Aerostack2 的 x500 模型和 AS2 Gazebo 启动器，但没有继续使用 AS2 的 `DroneInterface` / `takeoff_behavior` / `go_to_behavior` / `motion_controller` 控制链。原因是此前调试中 AS2 behavior/controller/TF 链存在控制模式和 TF 树不稳定问题；而 `/model/drone0/cmd_vel` 已经验证可以直接让 x500 升空，所以 demo 采用 Gazebo velocity controller 直控方案。

## 1. 包功能总览

| 包名 | 路径 | 构建类型 | 功能 |
|---|---|---|---|
| `aerostack2` | `src/aerostack2` | `ament_cmake` | 元包 / meta package，本身不跑节点，用来把 Aerostack2 主要功能包聚合成一个安装目标。 |
| `as2_platform_gazebo` | `src/as2_aerial_platforms/as2_platform_gazebo` | `ament_cmake` | AS2 官方 Gazebo 平台适配层，用于 AS2 controller/behavior 链路；当前最终 demo 不启动它。 |
| `as2_platform_multirotor_simulator` | `src/as2_aerial_platforms/as2_platform_multirotor_simulator` | `ament_cmake` | 轻量级多旋翼仿真平台，不依赖 Gazebo；当前 demo 不使用。 |
| `as2_behavior_tree` | `src/as2_behavior_tree` | `ament_cmake` | 行为树集成，用 BehaviorTree.CPP 编排任务。 |
| `as2_behavior` | `src/as2_behaviors/as2_behavior` | `ament_cmake` | AS2 behavior 基类和通用行为框架。 |
| `as2_behaviors_motion` | `src/as2_behaviors/as2_behaviors_motion` | `ament_cmake` | 运动行为：takeoff/go_to/land/follow path 等。当前最终 demo 不启动。 |
| `as2_behaviors_param_estimation` | `src/as2_behaviors/as2_behaviors_param_estimation` | `ament_cmake` | 质量/力等参数估计行为。 |
| `as2_behaviors_path_planning` | `src/as2_behaviors/as2_behaviors_path_planning` | `ament_cmake` | 路径规划行为，包括 A*、Voronoi 等插件。 |
| `as2_behaviors_payload` | `src/as2_behaviors/as2_behaviors_payload` | `ament_cmake` | 载荷行为，如云台、夹爪等。 |
| `as2_behaviors_perception` | `src/as2_behaviors/as2_behaviors_perception` | `ament_cmake` | 感知行为，如 ArUco 检测。 |
| `as2_behaviors_platform` | `src/as2_behaviors/as2_behaviors_platform` | `ament_cmake` | 平台行为：arm/offboard 等。当前最终 demo 不启动。 |
| `as2_behaviors_swarm_flocking` | `src/as2_behaviors/as2_behaviors_swarm_flocking` | `ament_cmake` | 蜂群/编队 flocking 行为。 |
| `as2_behaviors_trajectory_generation` | `src/as2_behaviors/as2_behaviors_trajectory_generation` | `ament_cmake` | 轨迹生成行为，用于生成多项式轨迹等。 |
| `as2_cli` | `src/as2_cli` | `ament_cmake` | 命令行辅助工具包。 |
| `as2_core` | `src/as2_core` | `ament_cmake` | AS2 核心基类、节点封装、平台接口、通用工具；大部分 C++ AS2 节点依赖它。 |
| `as2_realsense_interface` | `src/as2_hardware_drivers/as2_realsense_interface` | `ament_cmake` | Intel RealSense 相机驱动接口。 |
| `as2_usb_camera_interface` | `src/as2_hardware_drivers/as2_usb_camera_interface` | `ament_cmake` | USB 相机驱动接口。 |
| `as2_map_server` | `src/as2_map_server` | `ament_cmake` | 地图服务包，将 scan/depth/pointcloud 转占据栅格等。 |
| `as2_motion_controller` | `src/as2_motion_controller` | `ament_cmake` | AS2 运动控制器插件包，如 PID speed controller、differential flatness；当前最终 demo 不启动它。 |
| `as2_motion_reference_handlers` | `src/as2_motion_reference_handlers` | `ament_cmake` | AS2 运动参考输入处理模块，处理 position/speed/trajectory 等参考命令。 |
| `as2_msgs` | `src/as2_msgs` | `ament_cmake` | AS2 自定义消息、服务、Action 定义；其他 AS2 包之间通信的基础。 |
| `as2_python_api` | `src/as2_python_api` | `ament_python` | Python DroneInterface 等接口；适合用 Python 写任务脚本。当前二维码 demo 最终未走 DroneInterface，而是直控 Gazebo 速度话题。 |
| `as2_qr_mission` | `src/as2_qr_mission` | `ament_python` | 自定义任务包；启动白板 world 和 x500，桥接 Gazebo cmd_vel，按时间序列控制无人机依次飞到 6 个二维码前方并输出坐标/闪光。 |
| `as2_gazebo_assets` | `src/as2_simulation_assets/as2_gazebo_assets` | `ament_cmake` | Gazebo / Ignition 资源包，包含 x500 模型、world、bridge、launch_simulation.py；当前 demo 用它生成 x500 和启动 Gazebo。 |
| `as2_state_estimator` | `src/as2_state_estimator` | `ament_cmake` | AS2 状态估计器，提供 ground_truth/mocap/raw_odometry 等定位插件；当前最终 demo 不启动它。 |
| `as2_alphanumeric_viewer` | `src/as2_user_interfaces/as2_alphanumeric_viewer` | `ament_cmake` | 终端字符界面状态查看器。 |
| `as2_keyboard_teleoperation` | `src/as2_user_interfaces/as2_keyboard_teleoperation` | `ament_python` | 键盘遥控无人机工具。 |
| `as2_rviz_plugins` | `src/as2_user_interfaces/as2_visualization/as2_rviz_plugins` | `ament_cmake` | AS2 RViz 插件。 |
| `as2_visualization` | `src/as2_user_interfaces/as2_visualization/as2_visualization` | `ament_python` | RViz / Gazebo 可视化启动工具。 |
| `as2_external_object_to_tf` | `src/as2_utilities/as2_external_object_to_tf` | `ament_cmake` | 把外部物体位姿发布成 TF。 |
| `as2_geozones` | `src/as2_utilities/as2_geozones` | `ament_cmake` | 地理围栏 / geozone 相关工具。 |
| `mocap4r2_msgs` | `src/mocap4r2_msgs` | `ament_cmake` | mocap4r2 兼容消息定义。 |
| `qr_whiteboard_portable` | `src/qr_whiteboard_portable` | `ament_python` | 自定义二维码白板模型包，提供 qr_whiteboard_model_only.world、qr_whiteboard 模型、二维码纹理和资源路径。 |

## 2. 与二维码任务最相关的包

### `qr_whiteboard_portable`

- 作用：提供可移植的 Gazebo 六二维码白板模型。
- 关键文件：
  - `src/qr_whiteboard_portable/worlds/qr_whiteboard_model_only.world`：只包含白板模型的测试 world。
  - `src/qr_whiteboard_portable/models/qr_whiteboard/model.sdf`：白板模型定义。
  - `src/qr_whiteboard_portable/models/qr_whiteboard/materials/textures/qr_board.png`：六二维码纹理。
  - `src/qr_whiteboard_portable/README.md`：白板模型说明。
- 本包不控制无人机，只负责让 Gazebo 能找到并显示二维码白板。

### `as2_qr_mission`

- 作用：二维码飞行任务包。
- 关键文件：
  - `src/as2_qr_mission/launch/full_demo.launch.py`：总启动文件。
  - `src/as2_qr_mission/config/qr_as2_world.yaml`：指定 world 和 x500 初始位置。
  - `src/as2_qr_mission/as2_qr_mission/mission_node.py`：任务逻辑，发布 `/model/drone0/cmd_vel` 控制 x500，按时间顺序飞到 6 个二维码前方。
  - `src/as2_qr_mission/as2_qr_mission/laser_node.py`：订阅 `/laser` 并打印激光开关。
  - `src/as2_qr_mission/package.xml`、`src/as2_qr_mission/setup.py`：ROS 2 Python 包声明和安装入口。
- 当前 `mission_node.py` 还会调用 `ros2 run ros_gz_sim create` 在二维码中心前方生成黄色发光小球，0.8 秒后删除，用于实现“二维码中间亮一下”。

### `as2_gazebo_assets`

- 作用：AS2 官方 Gazebo 仿真资源包。
- 当前 demo 主要使用它的 `launch/launch_simulation.py` 来启动 Gazebo、读取 `qr_as2_world.yaml`、生成 x500 模型。
- 需要它可用，但通常不需要每次修改任务代码后重新编译它。

## 3. 当前 demo 的运行链路

```text
ros2 launch as2_qr_mission full_demo.launch.py
        |
        +-- 设置 IGN_GAZEBO_RESOURCE_PATH / GZ_SIM_RESOURCE_PATH
        |
        +-- Include as2_gazebo_assets/launch/launch_simulation.py
        |       |
        |       +-- 读取 as2_qr_mission/config/qr_as2_world.yaml
        |       +-- 加载 qr_whiteboard_model_only world
        |       +-- 生成 x500，模型名 drone0
        |
        +-- 启动 ros_gz_bridge
        |       +-- /model/drone0/cmd_vel                      ROS -> Gazebo
        |       +-- /model/drone0/velocity_controller/enable   ROS -> Gazebo
        |       +-- /model/drone0/pose                         Gazebo -> ROS
        |
        +-- 启动 laser_node
        |       +-- 订阅 /laser，打印 LASER ON / OFF
        |
        +-- 启动 mission_node
                +-- 持续启用 velocity controller
                +-- 发布 /model/drone0/cmd_vel
                +-- 按时间段飞行：起飞 -> 前进 -> QR_A -> QR_B -> QR_C -> QR_D -> QR_E -> QR_F
                +-- 到点输出 QR 世界坐标
                +-- 发布 /laser=True
                +-- 生成二维码中心黄色闪光点
```

## 4. 编译哪些包

ROS 2 中通常说“编译包”，不是编译单个文件。当前二维码 demo 修改后通常只需要编译两个自定义包：

```bash
cd ~/aerostack2-main
source /opt/ros/humble/setup.bash

colcon build \
  --packages-select qr_whiteboard_portable as2_qr_mission \
  --symlink-install \
  --executor sequential \
  --parallel-workers 1

source install/setup.bash
```

说明：
- `qr_whiteboard_portable`：安装白板 world、model、纹理资源。
- `as2_qr_mission`：安装 launch、config、mission 节点、laser 节点。
- `as2_gazebo_assets` 等 AS2 官方包必须已经存在并能被 `source install/setup.bash` 找到；如果它们此前已经编译安装成功，不需要每次重编。
- 不建议随手全量编译整个 Aerostack2，因为包很多，耗时长，且容易被不相关包的依赖问题卡住。

## 5. 运行 launch 文件

先清理旧 Gazebo/ROS 进程：

```bash
pkill -f "ign gazebo" || true
pkill -f "gz sim" || true
pkill -f "ruby /usr/bin/ign" || true
pkill -f "parameter_bridge" || true
pkill -f "qr_mission" || true
pkill -f "laser" || true
pkill -f "as2_" || true
```

启动 demo：

```bash
cd ~/aerostack2-main
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch as2_qr_mission full_demo.launch.py
```

正常现象：
- Gazebo 打开后显示二维码白板和 x500。
- 约 8 秒后启动 bridge 和 laser 节点。
- 约 12 秒后启动 mission 节点。
- mission 开始后，无人机会先上升，再飞向白板前方，然后依次经过 6 个二维码位置。
- 终端会输出类似：
```text
ARRIVED QR_A: QR world_position=(-0.03, 0.70, 1.50)
FLASH QR_A: marker=(-0.11, 0.70, 1.50)
LASER ON QR_A
```

## 6. 如果无人机不飞，先做这个最小测试

当前方案依赖 Gazebo 的 velocity controller。若 demo 不动，先单独测试控制话题：

```bash
source /opt/ros/humble/setup.bash
source ~/aerostack2-main/install/setup.bash

ros2 topic pub /model/drone0/velocity_controller/enable std_msgs/msg/Bool "{data: true}" -r 10
```

另开一个终端：

```bash
source /opt/ros/humble/setup.bash
source ~/aerostack2-main/install/setup.bash

ros2 topic pub /model/drone0/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.5}, angular: {x: 0.0, y: 0.0, z: 0.0}}" \
  -r 20
```

如果这条命令能让无人机升空，说明 Gazebo x500 和 velocity controller 正常，问题通常在 mission/bridge 启动顺序或话题名。

## 7. 推荐阅读顺序

想快速理解整个二维码 demo，按下面顺序读：

1. `src/as2_qr_mission/launch/full_demo.launch.py`  \
   先看启动了哪些节点、哪些 bridge、哪个 world。
2. `src/as2_qr_mission/config/qr_as2_world.yaml`  \
   看 world 名称、无人机模型名 `drone0`、初始位置。
3. `src/as2_qr_mission/as2_qr_mission/mission_node.py`  \
   看无人机起飞、移动、到点输出坐标、二维码闪光的具体逻辑。
4. `src/as2_qr_mission/as2_qr_mission/laser_node.py`  \
   看 `/laser` 如何显示开关。
5. `src/qr_whiteboard_portable/README.md`  \
   看白板模型尺寸、文件组成、Gazebo 资源说明。
6. `src/qr_whiteboard_portable/worlds/qr_whiteboard_model_only.world` 和 `src/qr_whiteboard_portable/models/qr_whiteboard/model.sdf`  \
   看白板是怎么被 world 加载的。
7. `src/as2_simulation_assets/as2_gazebo_assets/launch/launch_simulation.py`  \
   如果想了解 AS2 是如何根据 `qr_as2_world.yaml` 启动 Gazebo 和生成 x500，再读这个。

## 8. 当前 mission 的二维码顺序和坐标

| 顺序 | 名称 | 二维码世界坐标 | 飞行动作含义 |
|---|---|---|---|
| 1 | `QR_A` | `(-0.03, 0.70, 1.50)` | 飞到该二维码前方，输出坐标，打开 laser，并让二维码中心短暂亮一下 |
| 2 | `QR_B` | `(-0.03, 0.00, 1.50)` | 飞到该二维码前方，输出坐标，打开 laser，并让二维码中心短暂亮一下 |
| 3 | `QR_C` | `(-0.03, -0.70, 1.50)` | 飞到该二维码前方，输出坐标，打开 laser，并让二维码中心短暂亮一下 |
| 4 | `QR_D` | `(-0.03, 0.70, 0.50)` | 飞到该二维码前方，输出坐标，打开 laser，并让二维码中心短暂亮一下 |
| 5 | `QR_E` | `(-0.03, 0.00, 0.50)` | 飞到该二维码前方，输出坐标，打开 laser，并让二维码中心短暂亮一下 |
| 6 | `QR_F` | `(-0.03, -0.70, 0.50)` | 飞到该二维码前方，输出坐标，打开 laser，并让二维码中心短暂亮一下 |

## 9. 哪些文件暂时不用读

- `build/`、`install/`、`log/`：编译产物和日志，不是源码入口。
- `__pycache__/`、`*.pyc`：Python 缓存文件，不需要读，也不需要提交。
- 大部分 AS2 官方 behavior/controller 包：除非要恢复 `DroneInterface`/AS2 behavior 控制链，否则当前二维码 demo 不需要先读。
- `qr_detector_node.py`：目前 demo 用固定二维码世界坐标输出，不依赖相机实时识别；后续做真正视觉识别时再读。

## 10. 一句话总结

当前可运行二维码 demo 的最小关键路径是：

```text
qr_whiteboard_portable 提供白板 world/model
        +
as2_gazebo_assets 负责启动 Gazebo 并生成 AS2 x500
        +
as2_qr_mission/full_demo.launch.py 启动 bridge、laser、mission
        +
as2_qr_mission/mission_node.py 直接发布 /model/drone0/cmd_vel，让 x500 依次飞到 6 个二维码前方并输出坐标
```