import math
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point, Pose, Quaternion, Twist, Vector3
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class RF2oOdometryNode(Node):
    def __init__(self):
        super().__init__("rf2o_odometry_node")

        self.declare_parameter("laser_scan_topic", "/scan")
        self.declare_parameter("odom_topic", "/odom_rf2o")
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("base_frame_id", "base_link")
        self.declare_parameter("odom_frame_id", "odom")
        self.declare_parameter("freq", 20.0)

        scan_topic = self.get_parameter("laser_scan_topic").value
        odom_topic = self.get_parameter("odom_topic").value
        self.publish_tf = self.get_parameter("publish_tf").value
        self.base_frame_id = self.get_parameter("base_frame_id").value
        self.odom_frame_id = self.get_parameter("odom_frame_id").value

        self.subscription = self.create_subscription(
            LaserScan, scan_topic, self.scan_callback, 10
        )
        self.odom_pub = self.create_publisher(Odometry, odom_topic, 10)
        self.tf_broadcaster = TransformBroadcaster(self) if self.publish_tf else None

        self.prev_ranges = None
        self.prev_angle_min = None
        self.prev_angle_increment = None

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_time = None

        self.get_logger().info(
            f"RF2oOdometryNode started: {scan_topic} -> {odom_topic}"
        )

    def scan_callback(self, msg: LaserScan):
        current_time = self.get_clock().now()
        ranges = np.array(msg.ranges, dtype=np.float32)
        angles = msg.angle_min + np.arange(len(ranges)) * msg.angle_increment

        ranges = np.clip(ranges, msg.range_min, msg.range_max)
        valid = np.isfinite(ranges) & (ranges > msg.range_min)
        ranges[~valid] = 0.0

        if self.prev_ranges is not None and self.last_time is not None:
            dt = (current_time - self.last_time).nanoseconds * 1e-9
            if dt > 0:
                vx, vy, vyaw = self._compute_motion(
                    self.prev_ranges,
                    ranges,
                    self.prev_angle_min,
                    self.prev_angle_increment,
                    angles,
                    msg.angle_increment,
                )

                self.x += (vx * math.cos(self.yaw) - vy * math.sin(self.yaw)) * dt
                self.y += (vx * math.sin(self.yaw) + vy * math.cos(self.yaw)) * dt
                self.yaw += vyaw * dt

                self._publish_odometry(current_time, vx, vy, vyaw)

        self.prev_ranges = ranges.copy()
        self.prev_angle_min = msg.angle_min
        self.prev_angle_increment = msg.angle_increment
        self.last_time = current_time

    def _compute_motion(
        self, prev_ranges, curr_ranges, prev_amin, prev_ainc, curr_angles, curr_ainc
    ):
        prev_angles = prev_amin + np.arange(len(prev_ranges)) * prev_ainc

        px = prev_ranges * np.cos(prev_angles)
        py = prev_ranges * np.sin(prev_angles)
        cx = curr_ranges * np.cos(curr_angles)
        cy = curr_ranges * np.sin(curr_angles)

        prev_pts = np.column_stack((px, py))
        curr_pts = np.column_stack((cx, cy))

        prev_valid = np.isfinite(prev_ranges) & (prev_ranges > 0.01)
        curr_valid = np.isfinite(curr_ranges) & (curr_ranges > 0.01)
        if np.sum(prev_valid) < 10 or np.sum(curr_valid) < 10:
            return 0.0, 0.0, 0.0

        prev_centroid = np.mean(prev_pts[prev_valid], axis=0)
        curr_centroid = np.mean(curr_pts[curr_valid], axis=0)

        H = np.zeros((2, 2))
        pv = prev_pts[prev_valid] - prev_centroid
        cv = curr_pts[curr_valid] - curr_centroid
        n = min(len(pv), len(cv))
        H = pv[:n].T @ cv[:n]

        U, _, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T

        translation = curr_centroid - R @ prev_centroid

        vx = translation[0]
        vy = translation[1]
        vyaw = math.atan2(R[1, 0], R[0, 0])

        return vx, vy, vyaw

    def _publish_odometry(self, stamp, vx, vy, vyaw):
        q = self._yaw_to_quaternion(self.yaw)

        odom = Odometry()
        odom.header.stamp = stamp.to_msg()
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.base_frame_id
        odom.pose.pose = Pose(position=Point(x=self.x, y=self.y, z=0.0), orientation=q)
        odom.twist.twist = Twist(
            linear=Vector3(x=vx, y=vy, z=0.0), angular=Vector3(x=0.0, y=0.0, z=vyaw)
        )

        self.odom_pub.publish(odom)

        if self.tf_broadcaster:
            t = TransformStamped()
            t.header.stamp = stamp.to_msg()
            t.header.frame_id = self.odom_frame_id
            t.child_frame_id = self.base_frame_id
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation = q
            self.tf_broadcaster.sendTransform(t)

    @staticmethod
    def _yaw_to_quaternion(yaw):
        half = yaw * 0.5
        return Quaternion(x=0.0, y=0.0, z=math.sin(half), w=math.cos(half))


def main(args=None):
    rclpy.init(args=args)
    node = RF2oOdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
