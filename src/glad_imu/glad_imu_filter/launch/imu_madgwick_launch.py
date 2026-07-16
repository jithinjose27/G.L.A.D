import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("glad_imu_filter")
    config_path = os.path.join(pkg_share, "config", "madgwick_params.yaml")

    return LaunchDescription(
        [
            Node(
                package="glad_imu_filter",
                executable="imu_madgwick",
                name="imu_filter",
                output="screen",
                respawn=True,
                respawn_delay=1.0,
                parameters=[config_path],
                remappings=[
                    ("/imu/data_raw", "/imu/data_raw"),
                    ("/imu/mag", "/imu/mag"),
                ],
            ),
        ]
    )
