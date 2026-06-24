import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool


class LaserNode(Node):
    def __init__(self):
        super().__init__("laser_node")
        self.sub = self.create_subscription(
            Bool,
            "/laser",
            self.callback,
            10,
        )
        self.get_logger().info("Laser node started")

    def callback(self, msg: Bool):
        if msg.data:
            self.get_logger().info("🔴 LASER ON")
        else:
            self.get_logger().info("⚫ LASER OFF")


def main():
    rclpy.init()
    node = LaserNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()