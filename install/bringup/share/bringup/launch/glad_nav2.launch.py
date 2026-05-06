import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 1. Get the paths to your package and the official Nav2 package
    bringup_pkg_dir = get_package_share_directory('bringup')
    nav2_bringup_pkg_dir = get_package_share_directory('nav2_bringup')

    # 2. Define the absolute paths to your custom configuration files
    # This assumes your files are inside the 'config' folder of your 'bringup' package
    default_map_path = os.path.join(bringup_pkg_dir, 'config', 'robotics_floor.yaml')
    default_params_path = os.path.join(bringup_pkg_dir, 'config', 'my_nav2_params.yaml')

    # 3. Create Launch Configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')

    # 4. Declare Launch Arguments (Allows overriding from terminal if needed)
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time', default_value='false', description='Use simulation clock if true')

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart', default_value='true', description='Automatically startup the nav2 stack')

    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map', default_value=default_map_path, description='Full path to map yaml file to load')

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file', default_value=default_params_path, description='Full path to the ROS 2 parameters file')

    # 5. Include the official Nav2 bringup launch file and pass your custom arguments
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_pkg_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_yaml_file,
            'use_sim_time': use_sim_time,
            'autostart': autostart,
            'params_file': params_file
        }.items()
    )

    # 6. Return the Launch Description
    return LaunchDescription([
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_map_yaml_cmd,
        declare_params_file_cmd,
        nav2_bringup_launch
    ])