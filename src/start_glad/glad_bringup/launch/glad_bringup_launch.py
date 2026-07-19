from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _include(package: str, filename: str, launch_arguments: dict = None):
    if launch_arguments is None:
        launch_arguments = {}
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package), "launch", filename])
        ),
        launch_arguments=launch_arguments.items(),
    )


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    enable_slam = LaunchConfiguration("enable_slam")
    map_yaml = LaunchConfiguration("map_yaml")

    args = [
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock source (/clock topic).",
        ),
        DeclareLaunchArgument(
            "enable_slam",
            default_value="false",
            description="Start slam_toolbox online async mapping.",
        ),
        DeclareLaunchArgument(
            "map_yaml",
            default_value="/home/inevitable/G.L.A.D/src/glad_maps/robotics_floor/robotics_floor.yaml",
            description="Absolute path to map YAML file (actively utilized when enable_slam:=false).",
        ),
    ]
    base_args = {"use_sim_time": use_sim_time}

    glad_rplidar_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 1. Activating RPLidar Sensor Driver..."),
            _include("glad_rplidar", "glad_rplidar_launch.py", base_args),
        ]
    )

    glad_laser_filter_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 2. Initializing Laser Filter Node..."),
            _include("glad_laser_filter", "glad_laser_filter_launch.py", base_args),
        ]
    )

    glad_imu_publisher_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 3. Activating IMU Hardware Driver..."),
            _include("glad_imu_publisher", "imu_publisher_launch.py", base_args),
        ]
    )

    glad_imu_filter_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 4. Booting IMU Madgwick Filter..."),
            _include("glad_imu_filter", "imu_madgwick_launch.py", base_args),
        ]
    )

    rf2o_laser_odometry_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 5. Starting rf2o Laser Odometry..."),
            _include("rf2o_laser_odometry", "rf2o_laser_odometry_launch.py", base_args),
        ]
    )

    glad_ekf_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 6. Deploying Extended Kalman Filter..."),
            _include("glad_sensor_filter", "glad_ekf_launch.py", base_args),
        ]
    )

    slam_toolbox_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 7. Launching SLAM Toolbox..."),
            _include("glad_mapping", "slam_toolbox_launch.py", base_args),
        ],
        condition=IfCondition(enable_slam),
    )

    static_tf = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 8. Mounting Static Transforms..."),
            _include("glad_static_tf", "glad_static_tf_launch.py", base_args),
        ]
    )

    teleop_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 9. Activating Teleop and Motion Control..."),
            _include("glad_teleop", "teleop_launch.py", base_args),
        ]
    )

    glad_nav2_launch = GroupAction(
        [
            LogInfo(msg="[GLAD Bringup] 10. Launching Nav2 Stack..."),
            _include(
                "glad_navigation",
                "glad_nav2_launch.py",
                {**base_args, "map": map_yaml},
            ),
        ],
        condition=UnlessCondition(enable_slam),
    )

    return LaunchDescription(
        args
        + [
            LogInfo(msg="========== GLAD SYSTEM BRINGUP LAUNCHED =========="),
            static_tf,
            glad_rplidar_launch,
            TimerAction(period=1.0, actions=[glad_laser_filter_launch]),
            TimerAction(period=1.5, actions=[glad_imu_publisher_launch]),
            TimerAction(period=2.0, actions=[glad_imu_filter_launch]),
            TimerAction(period=2.5, actions=[rf2o_laser_odometry_launch]),
            TimerAction(period=3.0, actions=[glad_ekf_launch]),
            TimerAction(period=3.5, actions=[slam_toolbox_launch]),
            TimerAction(period=4.0, actions=[teleop_launch]),
            TimerAction(period=6.0, actions=[glad_nav2_launch]),
        ]
    )
