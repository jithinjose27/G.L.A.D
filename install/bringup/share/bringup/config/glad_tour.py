#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

def main():
    # 1. Start the ROS 2 Python interface
    rclpy.init()
    
    # 2. Create the Nav2 simple commander object
    navigator = BasicNavigator()

    # Wait for the Nav2 stack to be fully up and running

    # --- AUTO-INITIALIZE STARTING POSITION ---
    print("Setting initial pose...")
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()
    
    # Change these to the exact X and Y coordinates of G.L.A.D.'s charging dock / start point
    initial_pose.pose.position.x = 0.0 
    initial_pose.pose.position.y = 0.0 
    initial_pose.pose.orientation.w = 1.0
    
    navigator.setInitialPose(initial_pose)
    # -----------------------------------------

    print("Waiting for Nav2 to become active...")
    navigator.waitUntilNav2Active()
    
    print("Nav2 is ready! Commencing tour.")

    # 3. Your custom waypoints from the RViz map
    # 'w': 1.0 tells the robot to face the default forward direction at each stop
    waypoints = [
        {'name': 'Point 1', 'x': 1.37, 'y': -0.101, 'w': 1.0},
        {'name': 'Point 2', 'x': 2.69, 'y': 0.428,  'w': 1.0},
        {'name': 'Point 3', 'x': 4.43, 'y': 0.446,  'w': 1.0}
    ]

    # 4. Loop through each point and send the robot there
    for point in waypoints:
        print(f"Driving to {point['name']} (x: {point['x']}, y: {point['y']})...")
        
        # Create the exact Pose message Nav2 expects
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = navigator.get_clock().now().to_msg()
        
        goal_pose.pose.position.x = point['x']
        goal_pose.pose.position.y = point['y']
        goal_pose.pose.position.z = 0.0
        
        # Keep the robot flat on the ground
        goal_pose.pose.orientation.x = 0.0
        goal_pose.pose.orientation.y = 0.0
        goal_pose.pose.orientation.z = 0.0
        goal_pose.pose.orientation.w = point['w']

        # Send the goal to Nav2!
        navigator.goToPose(goal_pose)

        # Wait inside this loop until the robot physically arrives
        while not navigator.isTaskComplete():
            pass # The robot is currently driving

        # Check if it succeeded or failed to reach the point
        result = navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            print(f"Successfully arrived at {point['name']}!\n")
        elif result == TaskResult.FAILED:
            print(f"Failed to reach {point['name']}! Obstacle blocking the path?\n")
            break # Stop the script if it fails

    print("Tour completed! Shutting down brain.")
    rclpy.shutdown()

if __name__ == '__main__':
    main()