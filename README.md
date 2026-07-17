# Aerostack2 QR Whiteboard Drone Demo

Sunny&Charlie Hu
This repository contains a ROS2 Humble demo where an Aerostack2 x500 drone flies in front of a QR-code whiteboard in Gazebo. The drone visits six QR-code positions in sequence, prints each QR code's world coordinate, turns on a simulated laser signal, and briefly highlights the QR-code center.

## 1. What this repository contains

This repository is an overlay project. It only contains the custom packages needed for the QR whiteboard mission:

```text
src/
├── as2_qr_mission/
└── qr_whiteboard_portable/
```

It does not vendor the whole Aerostack2 source tree. Aerostack2 is treated as an external dependency.

## 2. Package overview

### `qr_whiteboard_portable`

This package provides the QR-code whiteboard Gazebo assets.

Main contents:

```text
qr_whiteboard_portable/
├── worlds/
│   └── qr_whiteboard_model_only.world
├── models/
│   └── qr_whiteboard/
│       ├── model.sdf
│       ├── model.config
│       ├── meshes/
│       ├── materials/
│       └── qr_board.png
├── package.xml
└── setup.py
```

Function:

* Provides the whiteboard model.
* Provides the QR texture/image.
* Provides the Gazebo world used by the demo.
* Does not control the drone.
* Does not run mission logic.

The world used by the demo is:

```text
qr_whiteboard_model_only
```

In the Aerostack2 launch process, this world is referenced by the mission configuration file.

### `as2_qr_mission`

This package provides the mission logic.

Main contents:

```text
as2_qr_mission/
├── launch/
│   └── full_demo.launch.py
├── config/
│   └── qr_as2_world.yaml
├── as2_qr_mission/
│   ├── mission_node.py
│   ├── laser_node.py
│   └── qr_detector_node.py
├── package.xml
└── setup.py
```

Function:

* Starts the QR whiteboard Gazebo world.
* Spawns the Aerostack2 x500 drone through the Aerostack2 Gazebo launcher.
* Bridges Gazebo velocity control topics to ROS2.
* Runs the mission node.
* Sends velocity commands to `/model/drone0/cmd_vel`.
* Enables the Gazebo velocity controller through `/model/drone0/velocity_controller/enable`.
* Makes the drone visit six QR-code positions.
* Prints QR-code world coordinates.
* Publishes `/laser` messages when the drone reaches each QR code.
* Briefly spawns a visual flash marker at each QR-code center.

## 3. External dependencies

This repository depends on Aerostack2 and ROS2 Humble.

Tested environment:

```text
Ubuntu 22.04
ROS2 Humble
Gazebo / Ignition Gazebo used by Aerostack2
Aerostack2 workspace
```

Required external packages include:

```text
as2_gazebo_assets
ros_gz_bridge
ros_gz_sim
geometry_msgs
std_msgs
tf2_msgs
rclpy
```

These are expected to come from ROS2 Humble and Aerostack2.

## 4. Recommended workspace layout

Clone Aerostack2 first, then put this repository's packages into the Aerostack2 workspace.

Recommended final layout:

```text
~/aerostack2-main/
├── src/
│   ├── aerostack2 official packages...
│   ├── as2_qr_mission/
│   └── qr_whiteboard_portable/
├── build/
├── install/
└── log/
```

Only the two custom packages should be copied from this repository into `~/aerostack2-main/src/`.

## 5. Setup steps

### Step 1: Source ROS2 and Aerostack2

```bash
cd ~/aerostack2-main

source /opt/ros/humble/setup.bash
source install/setup.bash
```

### Step 2: Copy this repository's packages into Aerostack2 workspace

If this repository was cloned to `~/aerostack2_qr_demo`, run:

```bash
cp -r ~/aerostack2_qr_demo/src/as2_qr_mission ~/aerostack2-main/src/
cp -r ~/aerostack2_qr_demo/src/qr_whiteboard_portable ~/aerostack2-main/src/
```

### Step 3: Ensure the whiteboard world has an `.sdf` alias

Aerostack2's simulation launcher searches for `.sdf` world files. If the package only has a `.world` file, create an `.sdf` alias:

```bash
cd ~/aerostack2-main/src/qr_whiteboard_portable/worlds
ln -sf qr_whiteboard_model_only.world qr_whiteboard_model_only.sdf
```

### Step 4: Build only the required packages

```bash
cd ~/aerostack2-main

source /opt/ros/humble/setup.bash
source install/setup.bash

colcon build \
  --packages-select qr_whiteboard_portable as2_qr_mission \
  --symlink-install \
  --executor sequential \
  --parallel-workers 1

source install/setup.bash
```

Only these two packages need to be built for this demo after Aerostack2 itself has already been built.

## 6. Run the demo

Clean old Gazebo and ROS processes first:

```bash
pkill -f "ign gazebo"
pkill -f "gz sim"
pkill -f "ruby /usr/bin/ign"
pkill -f "parameter_bridge"
pkill -f "qr_mission"
pkill -f "laser"
pkill -f "as2_"
```

Then launch the demo:

```bash
cd ~/aerostack2-main

source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch as2_qr_mission full_demo.launch.py
```

## 7. How the launch file works

The main launch file is:

```text
as2_qr_mission/launch/full_demo.launch.py
```

It performs these actions:

1. Locates the custom mission package.
2. Locates the QR whiteboard package.
3. Locates Aerostack2 Gazebo assets.
4. Adds the QR whiteboard world and model paths to Gazebo resource paths.
5. Starts Aerostack2's Gazebo simulation launcher.
6. Loads the `qr_whiteboard_model_only` world.
7. Spawns the Aerostack2 x500 drone named `drone0`.
8. Starts ROS-Gazebo bridges for:

   * `/model/drone0/cmd_vel`
   * `/model/drone0/velocity_controller/enable`
   * `/model/drone0/pose`
9. Starts the laser node.
10. Starts the mission node.

## 8. Mission behavior

The main mission logic is:

```text
as2_qr_mission/as2_qr_mission/mission_node.py
```

The mission currently uses direct Gazebo velocity control because manual testing confirmed that `/model/drone0/cmd_vel` can successfully lift the x500 drone.

The mission sequence is:

1. Take off by publishing positive Z velocity.
2. Move toward the QR whiteboard.
3. Visit QR_A.
4. Visit QR_B.
5. Visit QR_C.
6. Move to the lower row.
7. Visit QR_D.
8. Visit QR_E.
9. Visit QR_F.
10. Stop and hold position.

At each QR code, the node prints the QR-code world coordinate and turns on the simulated laser signal.

## 9. QR code coordinates

The QR-code world coordinates used by the mission are:

```text
QR_A: (-0.03,  0.70, 1.50)
QR_B: (-0.03,  0.00, 1.50)
QR_C: (-0.03, -0.70, 1.50)
QR_D: (-0.03,  0.70, 0.50)
QR_E: (-0.03,  0.00, 0.50)
QR_F: (-0.03, -0.70, 0.50)
```

## 10. Recommended reading order

To understand the framework, read the files in this order:

1. `README.md`
2. `src/as2_qr_mission/launch/full_demo.launch.py`
3. `src/as2_qr_mission/config/qr_as2_world.yaml`
4. `src/as2_qr_mission/as2_qr_mission/mission_node.py`
5. `src/as2_qr_mission/as2_qr_mission/laser_node.py`
6. `src/as2_qr_mission/setup.py`
7. `src/as2_qr_mission/package.xml`
8. `src/qr_whiteboard_portable/README.md`
9. `src/qr_whiteboard_portable/worlds/qr_whiteboard_model_only.world`
10. `src/qr_whiteboard_portable/models/qr_whiteboard/model.sdf`

## 11. Why this demo does not use DroneInterface

An earlier version attempted to use the full Aerostack2 behavior chain:

```text
DroneInterface
as2_platform_gazebo
as2_state_estimator
as2_motion_controller
takeoff_behavior
go_to_behavior
land_behavior
```

However, in this environment the TF and control-mode chain caused the drone to spin on the ground and fail to take off. Manual testing showed that the Gazebo velocity controller works correctly with:

```bash
ros2 topic pub /model/drone0/cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.5}, angular: {x: 0.0, y: 0.0, z: 0.0}}" -r 20
```

Therefore, this demo keeps the Aerostack2 x500 model and Gazebo launcher, but controls the drone directly through the Gazebo velocity controller.

## 12. Troubleshooting

### The drone does not take off

Test the velocity controller manually:

```bash
ros2 topic pub /model/drone0/velocity_controller/enable std_msgs/msg/Bool "{data: true}" -r 10
```

In another terminal:

```bash
ros2 topic pub /model/drone0/cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.5}, angular: {x: 0.0, y: 0.0, z: 0.0}}" -r 20
```

If the drone rises, the Gazebo velocity controller is working.

### The world does not load

Check that the `.sdf` alias exists:

```bash
ls ~/aerostack2-main/src/qr_whiteboard_portable/worlds/
```

Expected:

```text
qr_whiteboard_model_only.world
qr_whiteboard_model_only.sdf
```

### The QR board is missing

Check that Gazebo can find the model paths. The launch file sets:

```text
IGN_GAZEBO_RESOURCE_PATH
GZ_SIM_RESOURCE_PATH
```

These should include:

```text
qr_whiteboard_portable/worlds
qr_whiteboard_portable/models
as2_gazebo_assets/worlds
as2_gazebo_assets/models
```

## 13. Repository scope

This repository is not a full Aerostack2 fork. It is a small overlay demo that depends on Aerostack2.

The purpose is to show:

* A QR whiteboard world.
* An Aerostack2 x500 drone.
* A simple QR visiting mission.
* Simulated laser output.
* QR coordinate reporting.
* QR center flash marker.





# Aerostack2 二维码白板无人机 Demo

本项目是一个基于 ROS2 Humble、Gazebo 和 Aerostack2 x500 无人机模型的二维码白板巡航演示。

无人机会在 Gazebo 中生成，并依次飞到 6 个二维码前方。到达每个二维码位置时，程序会输出该二维码的世界坐标，打开模拟激光信号，并在二维码中心生成一个短暂的亮点标记。

## 1. 项目说明

本仓库不是完整的 Aerostack2 源码仓库，而是一个基于 Aerostack2 的 overlay demo。

也就是说，本仓库只包含本项目自己新增或修改的包：

```text
src/
├── as2_qr_mission/
└── qr_whiteboard_portable/
```

Aerostack2 官方包不放在本仓库里，而是作为外部依赖使用。

使用者需要先安装或克隆 Aerostack2，然后把本仓库里的两个包复制到 Aerostack2 工作区的 `src/` 目录下，再进行编译和运行。

## 2. 项目功能

本项目实现了以下功能：

1. 在 Gazebo 中加载二维码白板场景。
2. 使用 Aerostack2 官方的 x500 无人机模型。
3. 通过 Aerostack2 的 Gazebo launcher 生成无人机。
4. 使用 ROS2 与 Gazebo 的 bridge 连接控制话题。
5. 直接向 `/model/drone0/cmd_vel` 发布速度指令控制无人机。
6. 让无人机依次飞到 6 个二维码前方。
7. 到达每个二维码时输出二维码世界坐标。
8. 到达每个二维码时发布 `/laser` 信号。
9. 到达每个二维码时在二维码中心生成一个短暂的亮点。

## 3. 包结构说明

### 3.1 `qr_whiteboard_portable`

该包负责提供二维码白板的 Gazebo 资源。

主要功能：

* 提供二维码白板模型。
* 提供二维码图片纹理。
* 提供 Gazebo world 文件。
* 让 Gazebo 能显示白板和 6 个二维码。

典型结构：

```text
qr_whiteboard_portable/
├── worlds/
│   └── qr_whiteboard_model_only.world
├── models/
│   └── qr_whiteboard/
│       ├── model.sdf
│       ├── model.config
│       ├── meshes/
│       ├── materials/
│       └── qr_board.png
├── package.xml
└── setup.py
```

该包只负责场景和模型，不负责控制无人机。

本 demo 使用的 world 名称是：

```text
qr_whiteboard_model_only
```

### 3.2 `as2_qr_mission`

该包负责启动仿真和执行无人机任务。

主要功能：

* 启动 Gazebo 仿真。
* 加载二维码白板 world。
* 通过 Aerostack2 Gazebo launcher 生成 x500 无人机。
* 启动 ROS-Gazebo bridge。
* 启动 mission 节点。
* 控制无人机依次飞到二维码前方。
* 输出二维码坐标。
* 控制模拟激光。
* 生成二维码中心闪光标记。

典型结构：

```text
as2_qr_mission/
├── launch/
│   └── full_demo.launch.py
├── config/
│   └── qr_as2_world.yaml
├── as2_qr_mission/
│   ├── mission_node.py
│   ├── laser_node.py
│   └── qr_detector_node.py
├── package.xml
└── setup.py
```

## 4. 依赖环境

推荐环境：

```text
Ubuntu 22.04
ROS2 Humble
Gazebo / Ignition Gazebo
Aerostack2
```

需要提前准备好 Aerostack2 工作区，例如：

```text
~/aerostack2-main/
```

本项目依赖的主要外部包包括：

```text
as2_gazebo_assets
ros_gz_bridge
ros_gz_sim
geometry_msgs
std_msgs
tf2_msgs
rclpy
```

这些依赖通常来自 ROS2 Humble 和 Aerostack2。

## 5. 推荐工作区结构

推荐最终结构如下：

```text
~/aerostack2-main/
├── src/
│   ├── Aerostack2 官方包...
│   ├── as2_qr_mission/
│   └── qr_whiteboard_portable/
├── build/
├── install/
└── log/
```

本仓库中的两个包需要放到：

```text
~/aerostack2-main/src/
```

下面。

## 6. 安装和使用步骤

### 第一步：准备 Aerostack2 工作区

进入 Aerostack2 工作区：

```bash
cd ~/aerostack2-main
```

加载 ROS2 环境：

```bash
source /opt/ros/humble/setup.bash
```

如果 Aerostack2 已经编译过，再加载 Aerostack2 环境：

```bash
source install/setup.bash
```

### 第二步：复制本仓库的两个包

假设本仓库克隆到了：

```text
~/aerostack2_qr_demo
```

执行：

```bash
cp -r ~/aerostack2_qr_demo/src/as2_qr_mission ~/aerostack2-main/src/
cp -r ~/aerostack2_qr_demo/src/qr_whiteboard_portable ~/aerostack2-main/src/
```

### 第三步：确认 world 文件有 `.sdf` 别名

Aerostack2 的仿真启动器通常会查找 `.sdf` world 文件。

如果 `qr_whiteboard_portable/worlds/` 里只有：

```text
qr_whiteboard_model_only.world
```

需要创建一个 `.sdf` 软链接：

```bash
cd ~/aerostack2-main/src/qr_whiteboard_portable/worlds

ln -sf qr_whiteboard_model_only.world qr_whiteboard_model_only.sdf
```

检查：

```bash
ls
```

应该能看到：

```text
qr_whiteboard_model_only.world
qr_whiteboard_model_only.sdf
```

### 第四步：只编译本 demo 需要的两个包

不要全量编译整个 Aerostack2 工作区。

执行：

```bash
cd ~/aerostack2-main

source /opt/ros/humble/setup.bash
source install/setup.bash

colcon build \
  --packages-select qr_whiteboard_portable as2_qr_mission \
  --symlink-install \
  --executor sequential \
  --parallel-workers 1

source install/setup.bash
```

本 demo 只需要重新编译：

```text
qr_whiteboard_portable
as2_qr_mission
```

Aerostack2 官方包作为依赖使用。

## 7. 运行 demo

建议先清理旧的 Gazebo 和 ROS 进程：

```bash
pkill -f "ign gazebo"
pkill -f "gz sim"
pkill -f "ruby /usr/bin/ign"
pkill -f "parameter_bridge"
pkill -f "qr_mission"
pkill -f "laser"
pkill -f "as2_"
```

然后运行 launch 文件：

```bash
cd ~/aerostack2-main

source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch as2_qr_mission full_demo.launch.py
```

## 8. 运行后效果

启动后，Gazebo 中会出现：

1. 一个二维码白板。
2. 一架 Aerostack2 x500 无人机。
3. 无人机会起飞。
4. 无人机会依次飞到 6 个二维码前方。
5. 到每个二维码时，终端会输出该二维码的世界坐标。
6. 到每个二维码时，`/laser` 会发布开启信号。
7. 到每个二维码时，二维码中心会出现短暂亮点。

终端输出示例：

```text
ARRIVED QR_A: QR world_position=(-0.03, 0.70, 1.50)
LASER ON QR_A
FLASH QR_A: marker=(-0.11, 0.70, 1.50)

ARRIVED QR_B: QR world_position=(-0.03, 0.00, 1.50)
LASER ON QR_B
FLASH QR_B: marker=(-0.11, 0.00, 1.50)
```

## 9. Launch 文件说明

主 launch 文件是：

```text
src/as2_qr_mission/launch/full_demo.launch.py
```

它主要做以下事情：

1. 找到 `as2_qr_mission` 包路径。
2. 找到 `qr_whiteboard_portable` 包路径。
3. 找到 Aerostack2 的 `as2_gazebo_assets` 包路径。
4. 设置 Gazebo 资源路径，使 Gazebo 能找到白板 world、白板模型和 x500 模型。
5. 调用 Aerostack2 官方的 Gazebo simulation launcher。
6. 根据 `qr_as2_world.yaml` 加载二维码白板 world。
7. 生成名为 `drone0` 的 x500 无人机。
8. 启动 ROS-Gazebo bridge。
9. 启动 `laser_node`。
10. 启动 `mission_node`。

## 10. 关键配置文件

### 10.1 `qr_as2_world.yaml`

路径：

```text
src/as2_qr_mission/config/qr_as2_world.yaml
```

该文件指定 Gazebo world 和无人机生成参数。

示例：

```yaml
world_name: "qr_whiteboard_model_only"

origin:
  latitude: 40.4405287
  longitude: -3.6898277
  altitude: 100.0

drones:
  - model_type: "x500"
    model_name: "drone0"
    flight_time: 60
    xyz: [-3.0, 0.0, 0.5]
    rpy: [0.0, 0.0, 0.0]
    payload: []

objects: []
```

其中：

```text
world_name
```

指定要加载的二维码白板 world。

```text
model_type: "x500"
```

表示生成 Aerostack2 的 x500 无人机模型。

```text
model_name: "drone0"
```

表示无人机在 Gazebo 中的名字是 `drone0`。

### 10.2 `full_demo.launch.py`

路径：

```text
src/as2_qr_mission/launch/full_demo.launch.py
```

该文件负责启动整个 demo。

它会启动：

```text
Gazebo 仿真
二维码白板 world
Aerostack2 x500 无人机
ROS-Gazebo bridge
laser_node
mission_node
```

### 10.3 `mission_node.py`

路径：

```text
src/as2_qr_mission/as2_qr_mission/mission_node.py
```

该文件负责无人机任务逻辑。

它会发布速度指令到：

```text
/model/drone0/cmd_vel
```

并启用 Gazebo velocity controller：

```text
/model/drone0/velocity_controller/enable
```

任务流程包括：

1. 起飞。
2. 向二维码白板移动。
3. 到达 QR_A。
4. 到达 QR_B。
5. 到达 QR_C。
6. 移动到下排。
7. 到达 QR_D。
8. 到达 QR_E。
9. 到达 QR_F。
10. 停止。

### 10.4 `laser_node.py`

路径：

```text
src/as2_qr_mission/as2_qr_mission/laser_node.py
```

该节点订阅：

```text
/laser
```

当收到 `True` 时输出激光开启信息。

当收到 `False` 时输出激光关闭信息。

## 11. 二维码坐标

当前 demo 使用的二维码世界坐标如下：

```text
QR_A: (-0.03,  0.70, 1.50)
QR_B: (-0.03,  0.00, 1.50)
QR_C: (-0.03, -0.70, 1.50)

QR_D: (-0.03,  0.70, 0.50)
QR_E: (-0.03,  0.00, 0.50)
QR_F: (-0.03, -0.70, 0.50)
```

无人机飞到的是二维码前方位置，不是直接撞到二维码所在平面。

## 12. 为什么不上传整个 Aerostack2

本仓库只上传两个自定义包，而不上传完整 Aerostack2，原因是：

1. Aerostack2 是外部依赖，不是本项目新增代码。
2. 完整 Aerostack2 体积较大。
3. 上传完整工作区容易包含 `build/`、`install/`、`log/` 等本地编译产物。
4. 只上传自定义包更清晰，读者能更容易看懂本项目到底改了什么。
5. README 已经说明需要先准备 Aerostack2 工作区。

本项目的定位是：

```text
Aerostack2 overlay demo
```

也就是基于 Aerostack2 的附加 demo 包。

## 13. 为什么这个 demo 直接使用 `/model/drone0/cmd_vel`

早期版本尝试使用完整 Aerostack2 控制链路：

```text
DroneInterface
as2_platform_gazebo
as2_state_estimator
as2_motion_controller
takeoff_behavior
go_to_behavior
land_behavior
```

但是在当前环境中，TF 和 control mode 链路存在问题，导致无人机在地面旋转，无法稳定起飞。

经过手动测试，确认 Gazebo velocity controller 可以正常控制 x500 起飞：

```bash
ros2 topic pub /model/drone0/cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.5}, angular: {x: 0.0, y: 0.0, z: 0.0}}" -r 20
```

因此当前 demo 保留 Aerostack2 x500 模型和 Aerostack2 Gazebo launcher，但任务控制直接通过 Gazebo velocity controller 实现。

## 14. 推荐阅读顺序

如果想理解整个框架，建议按下面顺序阅读：

1. `README.md`
2. `src/as2_qr_mission/launch/full_demo.launch.py`
3. `src/as2_qr_mission/config/qr_as2_world.yaml`
4. `src/as2_qr_mission/as2_qr_mission/mission_node.py`
5. `src/as2_qr_mission/as2_qr_mission/laser_node.py`
6. `src/as2_qr_mission/setup.py`
7. `src/as2_qr_mission/package.xml`
8. `src/qr_whiteboard_portable/README.md`
9. `src/qr_whiteboard_portable/worlds/qr_whiteboard_model_only.world`
10. `src/qr_whiteboard_portable/models/qr_whiteboard/model.sdf`

先看 launch，再看 config，再看 mission，是最快理解这个 demo 的方式。

## 15. 常见问题

### 15.1 `colcon` 找不到包

先检查包是否放在正确位置：

```bash
ls ~/aerostack2-main/src/as2_qr_mission
ls ~/aerostack2-main/src/qr_whiteboard_portable
```

再检查 colcon 是否识别：

```bash
cd ~/aerostack2-main
source /opt/ros/humble/setup.bash
colcon list | grep -E "as2_qr_mission|qr_whiteboard_portable"
```

### 15.2 world 加载失败

检查 `.sdf` 别名：

```bash
ls ~/aerostack2-main/src/qr_whiteboard_portable/worlds
```

应该能看到：

```text
qr_whiteboard_model_only.world
qr_whiteboard_model_only.sdf
```

如果没有 `.sdf`，执行：

```bash
cd ~/aerostack2-main/src/qr_whiteboard_portable/worlds
ln -sf qr_whiteboard_model_only.world qr_whiteboard_model_only.sdf
```

### 15.3 无人机不起飞

手动测试速度控制：

```bash
ros2 topic pub /model/drone0/velocity_controller/enable std_msgs/msg/Bool "{data: true}" -r 10
```

另开一个终端：

```bash
ros2 topic pub /model/drone0/cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.5}, angular: {x: 0.0, y: 0.0, z: 0.0}}" -r 20
```

如果无人机能上升，说明 Gazebo velocity controller 正常。

### 15.4 二维码白板不显示

检查 Gazebo 资源路径是否包含：

```text
qr_whiteboard_portable/worlds
qr_whiteboard_portable/models
as2_gazebo_assets/worlds
as2_gazebo_assets/models
```

这些路径在 `full_demo.launch.py` 中通过下面两个环境变量设置：

```text
IGN_GAZEBO_RESOURCE_PATH
GZ_SIM_RESOURCE_PATH
```

## 16. GitHub 仓库内容说明

推荐上传到 GitHub 的内容是：

```text
aerostack2_qr_demo/
├── README.md
├── .gitignore
└── src/
    ├── as2_qr_mission/
    └── qr_whiteboard_portable/
```

不要上传：

```text
build/
install/
log/
__pycache__/
*.pyc
*.bag
*.db3
```

这些文件是本地生成的，不属于源码。

## 17. 一句话总结

本项目是一个基于 Aerostack2 x500 和 Gazebo 的二维码白板巡航 demo。

它通过两个自定义 ROS2 包实现：

```text
qr_whiteboard_portable：提供二维码白板场景
as2_qr_mission：启动仿真并控制无人机依次飞到二维码前方
```

运行入口是：

```bash
ros2 launch as2_qr_mission full_demo.launch.py
```

