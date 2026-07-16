from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # Declare the path to config (robustness: allow passing config via CLI)
    # default_config = os.path.join(
    #     get_package_share_directory('myimu'), 'config', 'bno055_config.yaml'
    # )

    return LaunchDescription(
        [
            # 1. IMU DRIVER (Python)
            # Robustness features:
            # - respawn=True: If I2C fails and node crashes, it auto-restarts.
            # - respawn_delay: Waits 2s before restarting to let hardware reset.
            Node(
                package="myimu",
                executable="imupub",
                name="imu_hardware_driver",
                output="screen",
                emulate_tty=True,  # Better coloring in logs
                respawn=True,  # <--- KEY FEATURE: Auto-restart on crash
                respawn_delay=2.0,
                parameters=[
                    # {'config_file': default_config}
                ],
            ),
            # 2. MADGWICK FILTER (C++)
            # This usually doesn't crash, but we can respawn it too just in case.
            Node(
                package="imu_filter_madgwick",
                executable="imu_filter_madgwick_node",
                name="imu_filter",
                output="screen",
                respawn=True,  # Keep the filter alive even if driver restarts
                respawn_delay=1.0,
                parameters=[
                    {
                        "use_mag": True,
                        "publish_tf": False,  # Usually 'false' if robot_localization publishes TF
                        "world_frame": "enu",
                        "fixed_frame": "odom",  # Or 'map' depending on your TF tree
                    }
                ],
                remappings=[
                    ("/imu/data_raw", "/imu/data_raw"),
                    ("/imu/mag", "/imu/mag"),
                ],
            ),
        ]
    )
