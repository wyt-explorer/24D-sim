import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import Point, PointStamped
from std_msgs.msg import String
import tf2_ros
import tf2_geometry_msgs
from cv_bridge import CvBridge
import cv2
import numpy as np


class QRDetector(Node):
    """
    订阅无人机前置相机，检测二维码，将像素中心反投影到
    世界坐标系（earth / map），并在 /qr_position 发布。

    当相机指向白板时，白板平面近似 x = -0.03。
    """

    def __init__(self):
        super().__init__("qr_detector")

        self.declare_parameter("namespace", "drone0")
        self.declare_parameter("camera", "front_cam")
        self.declare_parameter("target_frame", "odom")

        ns = self.get_parameter("namespace").value
        cam = self.get_parameter("camera").value
        self.target_frame = self.get_parameter("target_frame").value

        image_topic = f"/{ns}/sensor_measurements/{cam}/image_raw"
        info_topic = f"/{ns}/sensor_measurements/{cam}/camera_info"

        self.bridge = CvBridge()
        self.detector = cv2.QRCodeDetector()
        self.K = None
        self.img_count = 0

        self.info_sub = self.create_subscription(
            CameraInfo, info_topic, self.on_info, 10)
        self.img_sub = self.create_subscription(
            Image, image_topic, self.on_image, 5)

        self.pos_pub = self.create_publisher(
            PointStamped, "/qr_position", 10)
        self.text_pub = self.create_publisher(
            String, "/qr_text", 10)

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.get_logger().info(
            f"QR detector started. image={image_topic}")

    def on_info(self, msg: CameraInfo):
        if self.K is None:
            self.K = np.array(msg.k, dtype=float).reshape(3, 3)
            self.get_logger().info(
                f"Got camera info, fx={self.K[0,0]:.1f} "
                f"fy={self.K[1,1]:.1f} cx={self.K[0,2]:.1f} cy={self.K[1,2]:.1f}")

    def on_image(self, msg: Image):
        self.img_count += 1
        if self.img_count % 5 != 0:  # 降频以节省 CPU
            return
        if self.K is None:
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().warn(f"cv_bridge decode fail: {e}")
            return

        try:
            data, points, _ = self.detector.detectAndDecode(frame)
        except Exception:
            return

        if not data or points is None:
            return

        pts = points[0]
        u = float(np.mean(pts[:, 0]))
        v = float(np.mean(pts[:, 1]))

        world_point = self._pixel_to_world(u, v, msg.header.frame_id, msg.header.stamp)
        if world_point is None:
            return

        ps = PointStamped()
        ps.header.stamp = msg.header.stamp
        ps.header.frame_id = self.target_frame
        ps.point.x = world_point[0]
        ps.point.y = world_point[1]
        ps.point.z = world_point[2]
        self.pos_pub.publish(ps)

        s = String()
        s.data = data
        self.text_pub.publish(s)

        self.get_logger().info(
            f"QR '{data}' pixel=({u:.0f},{v:.0f}) "
            f"world=({world_point[0]:.2f},{world_point[1]:.2f},{world_point[2]:.2f})"
        )

    def _pixel_to_world(self, u, v, cam_frame, stamp):
        """
        将像素反投影到白板表面所在的世界 x 平面。
        白板前表面位于 world x = -0.03（以 whiteboard model 为基准）。
        """
        try:
            t = self.tf_buffer.lookup_transform(
                self.target_frame, cam_frame, stamp,
                rclpy.duration.Duration(seconds=0.1))
        except Exception as e:
            self.get_logger().warn(f"tf lookup failed ({cam_frame}->{self.target_frame}): {e}")
            return None

        # 在相机坐标系中：
        # K = [[fx,0,cx],[0,fy,cy],[0,0,1]]
        # 射线方向 r_cam = K^{-1} * [u,v,1]^T  然后归一化
        fx = self.K[0, 0]
        fy = self.K[1, 1]
        cx = self.K[0, 2]
        cy = self.K[1, 2]
        ray_cam = np.array([(u - cx) / fx, (v - cy) / fy, 1.0], dtype=float)

        ray_ps = PointStamped(header=t.header, point=Point(
            x=ray_cam[0], y=ray_cam[1], z=ray_cam[2]))
        rot = tf2_geometry_msgs.do_transform_point(ray_ps, t).point
        origin_ps = PointStamped(header=t.header, point=Point())
        origin = tf2_geometry_msgs.do_transform_point(origin_ps, t).point

        ox, oy, oz = origin.x, origin.y, origin.z
        rx, ry, rz = rot.x - ox, rot.y - oy, rot.z - oz

        # 求射线原点 + t * ray 与 白板平面 x = -0.03（即 QR 前表面）的交点
        plane_x = -0.03
        if abs(rx) < 1e-6:
            return None
        t_param = (plane_x - ox) / rx
        if t_param <= 0:
            return None
        y_w = oy + ry * t_param
        z_w = oz + rz * t_param
        return (plane_x, y_w, z_w)


def main():
    rclpy.init()
    node = QRDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()