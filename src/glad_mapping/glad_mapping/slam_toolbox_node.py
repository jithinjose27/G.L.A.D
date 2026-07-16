#!/usr/bin/env python3

import rclpy
from rclpy.node import Node


class SlamToolboxNode(Node):
    def __init__(self):
        super().__init__("slam_toolbox")

        self.declare_parameter("mode", "mapping")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("resolution", 0.05)
        self.declare_parameter("map_update_interval", 2.0)
        self.declare_parameter("max_laser_range", 10.0)
        self.declare_parameter("min_laser_range", 0.05)
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("map_file_name", "my_map")
        self.declare_parameter("do_loop_closing", True)
        self.declare_parameter("transform_timeout", 0.5)
        self.declare_parameter("tf_buffer_duration", 30.0)
        self.declare_parameter("use_sim_time", False)
        self.declare_parameter("solver_plugin", "solver_plugins::CeresSolver")

        self.get_logger().info("SlamToolboxNode started (mapping mode)")

    def destroy_node(self):
        self.get_logger().info("SlamToolboxNode shutting down")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SlamToolboxNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
