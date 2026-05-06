#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # ==========================================
    # 1. ARGS & CONFIGURATION
    # ==========================================
    # Lidar Params
    channel_type = LaunchConfiguration('channel_type', default='serial')
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB0')
    serial_baudrate = LaunchConfiguration('serial_baudrate', default='115200')
    lidar_frame_id = LaunchConfiguration('lidar_frame_id', default='laser')
    inverted = LaunchConfiguration('inverted', default='false')
    angle_compensate = LaunchConfiguration('angle_compensate', default='true')
    scan_mode = LaunchConfiguration('scan_mode', default='Sensitivity')
    
    pkg_share = get_package_share_directory('bringup')
    ekf_config_path = os.path.join(pkg_share, 'config', 'ekf_config.yaml')
    
    # NEW: Path to the laser filter configuration
    laser_filter_path = os.path.join(pkg_share, 'config', 'laser_filter.yaml')

    # ==========================================
    # 2. NODES
    # ==========================================
    
    # --- A. LIDAR HARDWARE ---
    rplidar_node = Node(
        package='rplidar_ros',
        executable='rplidar_node',
        name='rplidar_node',
        parameters=[{
            'channel_type': channel_type,
            'serial_port': serial_port,
            'serial_baudrate': serial_baudrate,
            'frame_id': lidar_frame_id,
            'inverted': inverted,
            'angle_compensate': angle_compensate,
            'scan_mode': scan_mode
        }],
        # REMAP: Hide the raw laser data on a secret topic
        remappings=[('/scan', '/scan_unfiltered')],
        output='screen'
    )

    # --- NEW: LASER FILTER NODE ---
    laser_filter_node = Node(
        package='laser_filters',
        executable='scan_to_scan_filter_chain',
        name='laser_filter',
        parameters=[laser_filter_path],
        # REMAP: Catch the raw data, clean it, and publish it to the main /scan topic
        remappings=[
            ('scan', 'scan_unfiltered'),
            ('scan_filtered', 'scan')
        ],
        output='screen'
    )

    # --- B. IMU HARDWARE ---
    imu_driver_node = Node(
        package='myimu',
        executable='imupub',
        name='imu_hardware_driver',
        output='screen',
        emulate_tty=True,
        respawn=True,     
        respawn_delay=2.0,
        parameters=[]
    )

    # --- C. TF TRANSFORMS ---
    static_tf_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_laser',
        arguments=['--x', '0.10', '--y', '0.0', '--z', '0.05',
                   '--yaw', '0.0', '--pitch', '0.0', '--roll', '0.0',
                   '--frame-id', 'base_link', '--child-frame-id', 'laser']
    )

    static_tf_imu = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_imu',
        arguments=['--x', '0.05', '--y', '0.0', '--z', '0.0',
                   '--yaw', '0.0', '--pitch', '0.0', '--roll', '0.0',
                   '--frame-id', 'base_link', '--child-frame-id', 'imu_link']
    )

    # --- D. ODOMETRY & FILTERS ---
    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        arguments=['--ros-args', '--log-level', 'error'],
        parameters=[{
            'laser_scan_topic': '/scan',  # Now reads the CLEANED scan
            'odom_topic': '/odom_rf2o',
            'publish_tf': False,          
            'base_frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'init_pose_from_topic': '',
            'freq': 20.0
        }],
    )

    motor_node = Node(
        package='glad_motor_controller',
        executable='motor_driver',
        name='motor_controller',
        output='screen',
        respawn=True,
        respawn_delay=1.0,
        remappings=[
            ('/odom', '/motor/odom'),
        ]
    )

    madgwick_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        output='screen',
        respawn=True,
        respawn_delay=1.0,
        parameters=[{
            'use_mag': False,     
            'publish_tf': False,  
            'world_frame': 'enu',
            'fixed_frame': 'odom',
        }],
        remappings=[
            ('/imu/data_raw', '/imu/data_raw'),
            ('/imu/mag', '/imu/mag')
        ]
    )

    ekf_node = Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config_path],
            remappings=[('odometry/filtered', 'odom')]
        )

    # ==========================================
    # 3. BUILD LAUNCH DESCRIPTION
    # ==========================================
    return LaunchDescription([
        DeclareLaunchArgument('channel_type', default_value='serial'),
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0'),
        DeclareLaunchArgument('serial_baudrate', default_value='115200'),
        DeclareLaunchArgument('lidar_frame_id', default_value='laser'),
        DeclareLaunchArgument('inverted', default_value='false'),
        DeclareLaunchArgument('angle_compensate', default_value='true'),
        DeclareLaunchArgument('scan_mode', default_value='Sensitivity'),

        static_tf_laser,
        static_tf_imu,  
        rplidar_node,
        laser_filter_node,  # <--- ADDED THE FILTER HERE
        imu_driver_node,
        madgwick_node,
        motor_node,    
        TimerAction(
            period=3.0,
            actions=[rf2o_node, ekf_node]
        ),
    ])