from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    config_file = os.path.join(
        get_package_share_directory("glad_trajectory_controller"),
        "config",
        "trajectory_controller.yaml",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_file",
                default_value=config_file,
                description="Path to trajectory controller parameters YAML file",
            ),
            Node(
                package="glad_trajectory_controller",
                executable="trajectory_controller_node",
                name="trajectory_controller",
                output="screen",
                parameters=[LaunchConfiguration("config_file")],
            ),
        ]
    )
