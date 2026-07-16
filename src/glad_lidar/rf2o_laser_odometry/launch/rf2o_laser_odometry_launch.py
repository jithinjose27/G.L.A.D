#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("rf2o_laser_odometry")
    config_path = os.path.join(pkg_share, "config", "rf2o_odometry.yaml")

    rf2o_odometry_node = Node(
        package="rf2o_laser_odometry",
        executable="rf2o_odometry_node",
        name="rf2o_laser_odometry",
        parameters=[config_path],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("laser_scan_topic", default_value="/scan"),
            DeclareLaunchArgument("odom_topic", default_value="/odom_rf2o"),
            DeclareLaunchArgument("publish_tf", default_value="false"),
            DeclareLaunchArgument("base_frame_id", default_value="base_link"),
            DeclareLaunchArgument("odom_frame_id", default_value="odom"),
            DeclareLaunchArgument("freq", default_value="20.0"),
            rf2o_odometry_node,
        ]
    )
