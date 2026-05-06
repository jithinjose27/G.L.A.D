#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # ==========================================
    # 1. Configuration Constants & Arguments
    # ==========================================
    # Lidar configuration parameters (exposed as arguments for flexibility)
    channel_type = LaunchConfiguration('channel_type', default='serial')
    serial_port = LaunchConfiguration('serial_port', default='/dev/ttyUSB0')
    serial_baudrate = LaunchConfiguration('serial_baudrate', default='115200')
    lidar_frame_id = LaunchConfiguration('frame_id', default='laser')
    inverted = LaunchConfiguration('inverted', default='false')
    angle_compensate = LaunchConfiguration('angle_compensate', default='true')
    scan_mode = LaunchConfiguration('scan_mode', default='Sensitivity')

    # ==========================================
    # 2. Node Definitions
    # ==========================================
    
    # Node 1: RPLidar Node
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
        output='screen'
    )

    # Node 2: Static TF Publisher (base_link -> laser)
    # Using new-style arguments (flags) to avoid warnings
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_to_laser_broadcaster',
        arguments=[
            '--x', '0',
            '--y', '0',
            '--z', '0',
            '--yaw', '0',
            '--pitch', '0',
            '--roll', '0',
            '--frame-id', 'base_link',
            '--child-frame-id', 'laser'
        ],
        output='screen'
    )

    # Node 3: RF2O Laser Odometry
    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[{
            'laser_scan_topic': '/scan',
            'odom_topic': '/odom_rf2o',
            'publish_tf': False,
            'base_frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'init_pose_from_topic': '',
            'freq': 20.0
        }],
    )

    # ==========================================
    # 3. Launch Description Construction
    # ==========================================
    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument('channel_type', default_value='serial', description='Channel type of lidar'),
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0', description='USB port for lidar'),
        DeclareLaunchArgument('serial_baudrate', default_value='115200', description='Baudrate for lidar'),
        DeclareLaunchArgument('frame_id', default_value='laser', description='Frame ID of lidar'),
        DeclareLaunchArgument('inverted', default_value='false', description='Invert scan data'),
        DeclareLaunchArgument('angle_compensate', default_value='true', description='Enable angle compensation'),
        DeclareLaunchArgument('scan_mode', default_value='Sensitivity', description='Scan mode of lidar'),

        # Nodes
        static_tf_node,
        rplidar_node,
        rf2o_node,
    ])