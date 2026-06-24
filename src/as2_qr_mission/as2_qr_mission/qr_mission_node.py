import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
import math

class Mission(Node):
    def __init__(self):
        super().__init__('qr_mission')

        self.sub = self.create_subscription(Point, '/qr_position', self.cb, 10)
        self.laser_pub = self.create_publisher(Bool, '/laser', 10)

        self.targets = []
        self.current = 0

    def cb(self, msg):
        self.targets.append((msg.x, msg.y, msg.z))

        if len(self.targets) >= 3:  # 假设3个QR
            self.execute()

    def execute(self):
        for i, t in enumerate(self.targets):
            x, y, z = t

            self.get_logger().info(f"Flying to QR {i}: {t}")

            # 👉 这里用 Aerostack2 接口替换
            # 例如 /as2/go_to

            self.sleep(3)

            self.laser(True)
            self.sleep(2)
            self.laser(False)

    def laser(self, state: bool):
        msg = Bool()
        msg.data = state
        self.laser_pub.publish(msg)

    def sleep(self, sec):
        import time
        time.sleep(sec)

def main():
    rclpy.init()
    node = Mission()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()