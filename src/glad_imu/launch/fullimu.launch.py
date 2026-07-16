from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="glad_imu",
                executable="imupub",
                name="imu_hardware_driver",
                output="screen",
                emulate_tty=True,
                respawn=True,
                respawn_delay=2.0,
                parameters=[],
            ),
            Node(
                package="imu_filter_madgwick",
                executable="imu_filter_madgwick_node",
                name="imu_filter",
                output="screen",
                respawn=True,
                respawn_delay=1.0,
                parameters=[
                    {
                        "use_mag": True,
                        "publish_tf": False,
                        "world_frame": "enu",
                        "fixed_frame": "odom",
                    }
                ],
                remappings=[
                    ("/imu/data_raw", "/imu/data_raw"),
                    ("/imu/mag", "/imu/mag"),
                ],
            ),
        ]
    )
