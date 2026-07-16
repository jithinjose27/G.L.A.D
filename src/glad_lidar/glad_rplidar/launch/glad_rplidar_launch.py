#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("glad_rplidar")
    config_path = os.path.join(pkg_share, "config", "rplidar_params.yaml")

    rplidar_node = Node(
        package="glad_rplidar",
        executable="rplidar_node",
        name="rplidar_node",
        parameters=[config_path],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("channel_type", default_value="serial"),
            DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB0"),
            DeclareLaunchArgument("serial_baudrate", default_value="115200"),
            DeclareLaunchArgument("frame_id", default_value="laser"),
            DeclareLaunchArgument("inverted", default_value="false"),
            DeclareLaunchArgument("angle_compensate", default_value="true"),
            DeclareLaunchArgument("scan_mode", default_value="Sensitivity"),
            rplidar_node,
        ]
    )
