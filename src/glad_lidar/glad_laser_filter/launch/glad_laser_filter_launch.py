#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("glad_laser_filter")
    laser_filter_config = os.path.join(pkg_share, "config", "laser_filter.yaml")

    glad_laser_filter_node = Node(
        package="glad_laser_filter",
        executable="laser_filter_node",
        name="laser_filter_node",
        parameters=[laser_filter_config],
        remappings=[
            ("/scan_unfiltered", "/scan_unfiltered"),
            ("/scan", "/scan"),
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            glad_laser_filter_node,
        ]
    )
