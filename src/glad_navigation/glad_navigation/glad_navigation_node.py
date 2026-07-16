#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class GladNavigationNode(Node):
    def __init__(self):
        super().__init__("glad_navigation_node")

        self.declare_parameter("use_sim_time", False)

        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel/nav", 10)

        self.get_logger().info("GladNavigationNode started")

    def destroy_node(self):
        self.get_logger().info("GladNavigationNode shutting down")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GladNavigationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
