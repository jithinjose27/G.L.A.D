from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="glad_tour",
                executable="glad_tour",
                name="glad_tour",
                output="screen",
            ),
        ]
    )
