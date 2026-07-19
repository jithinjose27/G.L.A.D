from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="glad_static_tf",
                executable="static_tf_broadcaster",
                name="static_tf_broadcaster",
                output="screen",
            ),
        ]
    )
