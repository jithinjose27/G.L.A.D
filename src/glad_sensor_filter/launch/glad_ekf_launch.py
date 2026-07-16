#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    config_path = os.path.join(
        get_package_share_directory("glad_sensor_filter"),
        "config",
        "glad_ekf_params.yaml",
    )

    return LaunchDescription(
        [
            Node(
                package="glad_sensor_filter",
                executable="glad_ekf_node",
                name="glad_ekf_node",
                parameters=[config_path],
                output="screen",
                remappings=[("odometry/filtered", "odom")],
            ),
        ]
    )
