import subprocess
from pathlib import Path

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


WORLD_NAME = "qr_whiteboard_model_only"

QR_SEQUENCE = [
    {"name": "QR_A", "qr_pos": (-0.03,  0.7, 1.5)},
    {"name": "QR_B", "qr_pos": (-0.03,  0.0, 1.5)},
    {"name": "QR_C", "qr_pos": (-0.03, -0.7, 1.5)},
    {"name": "QR_D", "qr_pos": (-0.03,  0.7, 0.5)},
    {"name": "QR_E", "qr_pos": (-0.03,  0.0, 0.5)},
    {"name": "QR_F", "qr_pos": (-0.03, -0.7, 0.5)},
]


class MissionNode(Node):
    def __init__(self):
        super().__init__("qr_mission")

        self.cmd_pub = self.create_publisher(
            Twist,
            "/model/drone0/cmd_vel",
            10,
        )

        self.enable_pub = self.create_publisher(
            Bool,
            "/model/drone0/velocity_controller/enable",
            10,
        )

        self.laser_pub = self.create_publisher(
            Bool,
            "/laser",
            10,
        )

        self.tick = 0
        self.announced_qrs = set()
        self.active_flashes = {}

        self.timer = self.create_timer(0.1, self.step)

        self.get_logger().info(
            "QR mission started: open-loop direct velocity control with QR flash markers."
        )

    def enable_controller(self):
        msg = Bool()
        msg.data = True
        self.enable_pub.publish(msg)

    def set_laser(self, state: bool):
        msg = Bool()
        msg.data = state
        self.laser_pub.publish(msg)

    def send_cmd(self, x=0.0, y=0.0, z=0.0, yaw=0.0):
        cmd = Twist()
        cmd.linear.x = float(x)
        cmd.linear.y = float(y)
        cmd.linear.z = float(z)
        cmd.angular.z = float(yaw)
        self.cmd_pub.publish(cmd)

    def stop(self):
        self.send_cmd(0.0, 0.0, 0.0, 0.0)

    def flash_sdf(self):
        return """<?xml version="1.0"?>
<sdf version="1.9">
  <model name="qr_flash_marker">
    <static>true</static>
    <link name="link">
      <visual name="bright_dot">
        <geometry>
          <sphere>
            <radius>0.085</radius>
          </sphere>
        </geometry>
        <material>
          <ambient>1.0 0.85 0.05 1.0</ambient>
          <diffuse>1.0 0.85 0.05 1.0</diffuse>
          <emissive>1.0 0.85 0.05 1.0</emissive>
        </material>
      </visual>

      <light name="qr_flash_light" type="point">
        <diffuse>1.0 0.85 0.05 1.0</diffuse>
        <specular>1.0 0.85 0.05 1.0</specular>
        <attenuation>
          <range>2.0</range>
          <linear>0.1</linear>
          <constant>0.2</constant>
          <quadratic>0.01</quadratic>
        </attenuation>
        <cast_shadows>false</cast_shadows>
      </light>
    </link>
  </model>
</sdf>
"""

    def remove_flash(self, model_name: str):
        cmd = [
            "ign",
            "service",
            "-s",
            f"/world/{WORLD_NAME}/remove",
            "--reqtype",
            "ignition.msgs.Entity",
            "--reptype",
            "ignition.msgs.Boolean",
            "--timeout",
            "200",
            "--req",
            f'name: "{model_name}" type: 2',
        ]

        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    def spawn_flash(self, qr_index: int):
        item = QR_SEQUENCE[qr_index]
        name = item["name"]
        qx, qy, qz = item["qr_pos"]

        model_name = f"qr_flash_{name}"

        # 防止上次残留。
        self.remove_flash(model_name)

        sdf_path = Path(f"/tmp/{model_name}.sdf")
        sdf_path.write_text(self.flash_sdf(), encoding="utf-8")

        # 白板正面朝无人机，稍微放在二维码前方，避免被白板挡住。
        flash_x = qx - 0.08
        flash_y = qy
        flash_z = qz

        cmd = [
            "ros2",
            "run",
            "ros_gz_sim",
            "create",
            "-name",
            model_name,
            "-file",
            str(sdf_path),
            "-x",
            f"{flash_x:.3f}",
            "-y",
            f"{flash_y:.3f}",
            "-z",
            f"{flash_z:.3f}",
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=3.0,
        )

        if result.returncode != 0:
            self.get_logger().warn(
                f"Failed to spawn flash marker for {name}: {result.stderr}"
            )
            return

        # 0.8 秒后删除发光点。
        self.active_flashes[model_name] = self.tick + 8

        self.get_logger().info(
            f"FLASH {name}: marker=({flash_x:.2f}, {flash_y:.2f}, {flash_z:.2f})"
        )

    def update_flashes(self):
        for model_name, remove_tick in list(self.active_flashes.items()):
            if self.tick >= remove_tick:
                self.remove_flash(model_name)
                self.active_flashes.pop(model_name, None)

    def arrive_qr(self, qr_index: int):
        if qr_index in self.announced_qrs:
            return

        self.announced_qrs.add(qr_index)

        item = QR_SEQUENCE[qr_index]
        name = item["name"]
        qx, qy, qz = item["qr_pos"]

        self.get_logger().info(
            f"ARRIVED {name}: QR world_position=({qx:.2f}, {qy:.2f}, {qz:.2f})"
        )

        self.get_logger().info(f"LASER ON {name}")
        self.spawn_flash(qr_index)

    def step(self):
        self.enable_controller()
        self.update_flashes()

        t = self.tick * 0.1
        self.tick += 1

        # 0 - 4 s: 原地升空。
        if 0.0 <= t < 4.0:
            self.set_laser(False)
            self.send_cmd(0.0, 0.0, 0.45, 0.0)
            if self.tick % 10 == 0:
                self.get_logger().info("TAKEOFF: sending z velocity 0.45")
            return

        # 4 - 8.5 s: 向白板方向飞，从 x=-3 附近飞到 x=-1.5 附近。
        if 4.0 <= t < 8.5:
            self.set_laser(False)
            self.send_cmd(0.35, 0.0, 0.0, 0.0)
            if self.tick % 10 == 0:
                self.get_logger().info("FORWARD: moving toward QR board")
            return

        # 8.5 - 10.5 s: 移到右上 QR_A 附近。
        if 8.5 <= t < 10.5:
            self.set_laser(False)
            self.send_cmd(0.0, 0.35, 0.0, 0.0)
            return

        # QR_A 停留并亮一下。
        if 10.5 <= t < 12.5:
            self.stop()
            self.set_laser(True)
            self.arrive_qr(0)
            return

        # QR_A -> QR_B。
        if 12.5 <= t < 14.7:
            self.set_laser(False)
            self.send_cmd(0.0, -0.32, 0.0, 0.0)
            return

        # QR_B 停留并亮一下。
        if 14.7 <= t < 16.7:
            self.stop()
            self.set_laser(True)
            self.arrive_qr(1)
            return

        # QR_B -> QR_C。
        if 16.7 <= t < 18.9:
            self.set_laser(False)
            self.send_cmd(0.0, -0.32, 0.0, 0.0)
            return

        # QR_C 停留并亮一下。
        if 18.9 <= t < 20.9:
            self.stop()
            self.set_laser(True)
            self.arrive_qr(2)
            return

        # QR_C -> QR_D：移动回右侧并下降到下排高度。
        if 20.9 <= t < 25.3:
            self.set_laser(False)
            self.send_cmd(0.0, 0.32, -0.20, 0.0)
            return

        # QR_D 停留并亮一下。
        if 25.3 <= t < 27.3:
            self.stop()
            self.set_laser(True)
            self.arrive_qr(3)
            return

        # QR_D -> QR_E。
        if 27.3 <= t < 29.5:
            self.set_laser(False)
            self.send_cmd(0.0, -0.32, 0.0, 0.0)
            return

        # QR_E 停留并亮一下。
        if 29.5 <= t < 31.5:
            self.stop()
            self.set_laser(True)
            self.arrive_qr(4)
            return

        # QR_E -> QR_F。
        if 31.5 <= t < 33.7:
            self.set_laser(False)
            self.send_cmd(0.0, -0.32, 0.0, 0.0)
            return

        # QR_F 停留并亮一下。
        if 33.7 <= t < 35.7:
            self.stop()
            self.set_laser(True)
            self.arrive_qr(5)
            return

        # 结束：停住，关激光。
        self.stop()
        self.set_laser(False)

        if self.tick % 30 == 0:
            self.get_logger().info("Mission finished. Drone holding with zero velocity.")


def main():
    rclpy.init()
    node = MissionNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.stop()
    node.set_laser(False)

    for model_name in list(node.active_flashes.keys()):
        node.remove_flash(model_name)

    node.destroy_node()

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()