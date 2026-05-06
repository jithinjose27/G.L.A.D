#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
import math
import numpy as np

class ImuToOdom(Node):
    def __init__(self):
        super().__init__('imu_to_odom_node')

        # 1. Configuration
        self.declare_parameter('imu_topic', '/imu/data')
        self.declare_parameter('odom_topic', '/imu/odometry')
        self.declare_parameter('publish_tf', False) # Set to True if you need it to link frames in RViz

        imu_topic = self.get_parameter('imu_topic').value
        self.odom_topic = self.get_parameter('odom_topic').value
        self.publish_tf = self.get_parameter('publish_tf').value

        # 2. State Variables (Position is no longer integrated)
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.last_time = None

        # 3. Subscribers and Publishers
        self.sub = self.create_subscription(Imu, imu_topic, self.imu_callback, 10)
        self.pub = self.create_publisher(Odometry, self.odom_topic, 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.get_logger().info(f"IMU Odom Node Started. Subscribing to: {imu_topic}")

    def imu_callback(self, msg):
        current_time = self.get_clock().now()
        
        # Handle first message
        if self.last_time is None:
            self.last_time = current_time
            return

        # Calculate dt (delta time)
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time

        # --- MATH SECTION ---
        
        # 1. Extract Orientation (Quaternion)
        # This is the only thing we care about now
        q = msg.orientation
        
        # 2. LOCK POSITION TO ZERO
        # We explicitly ignore acceleration and velocity to prevent drift.
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0

        # --- PUBLISH SECTION ---

        # Create Odometry Message
        odom = Odometry()
        odom.header.stamp = msg.header.stamp
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"

        # Position (Hardcoded to 0.0)
        odom.pose.pose.position.x = 0.0
        odom.pose.pose.position.y = 0.0
        odom.pose.pose.position.z = 0.0
        
        # Orientation (Directly from IMU - this is what we are testing)
        odom.pose.pose.orientation = q

        # Twist (Velocity) - Report zero
        odom.twist.twist.linear.x = 0.0
        odom.twist.twist.linear.y = 0.0
        odom.twist.twist.angular.z = msg.angular_velocity.z

        self.pub.publish(odom)

        # Broadcast TF (Required for RViz to link 'odom' to 'base_link')
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = msg.header.stamp
            t.header.frame_id = "odom"
            t.child_frame_id = "base_link"
            t.transform.translation.x = 0.0
            t.transform.translation.y = 0.0
            t.transform.translation.z = 0.0
            t.transform.rotation = q
            self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = ImuToOdom()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()