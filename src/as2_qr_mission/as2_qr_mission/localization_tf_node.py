import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_ros import TransformBroadcaster


class LocalizationTfNode(Node):
    def __init__(self):
        super().__init__("localization_tf_node")

        self.declare_parameter("parent_frame", "drone0/odom")
        self.declare_parameter("child_frame", "drone0/base_link")

        self.parent_frame = self.get_parameter("parent_frame").value
        self.child_frame = self.get_parameter("child_frame").value

        self.tf_broadcaster = TransformBroadcaster(self)

        self.sub = self.create_subscription(
            PoseStamped,
            "/drone0/self_localization/pose",
            self.pose_callback,
            10,
        )

        self.get_logger().info(
            f"Publishing TF from /drone0/self_localization/pose: "
            f"{self.parent_frame} -> {self.child_frame}"
        )

    def pose_callback(self, msg: PoseStamped):
        tf_msg = TransformStamped()

        tf_msg.header.stamp = msg.header.stamp
        tf_msg.header.frame_id = self.parent_frame
        tf_msg.child_frame_id = self.child_frame

        tf_msg.transform.translation.x = msg.pose.position.x
        tf_msg.transform.translation.y = msg.pose.position.y
        tf_msg.transform.translation.z = msg.pose.position.z

        tf_msg.transform.rotation = msg.pose.orientation

        self.tf_broadcaster.sendTransform(tf_msg)


def main():
    rclpy.init()
    node = LocalizationTfNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
