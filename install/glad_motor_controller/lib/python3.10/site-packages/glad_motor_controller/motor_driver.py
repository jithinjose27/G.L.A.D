#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped, Quaternion
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster
import serial
import threading
import time
import math

class ESP32MotorBridge(Node):
    def __init__(self):
        super().__init__('esp32_motor_bridge')
        
        # --- Parameters (Adjust these to match your robot!) ---
        self.declare_parameter('serial_port', '/dev/ttyUSB1')
        self.declare_parameter('baud_rate', 115200)
        
        # Robot Physical Properties 
        self.wheel_radius = 0.04     # Meters (3.2 cm)
        self.wheel_separation = 0.325  # Meters (19.5 cm) distance between wheels
        
        # Encoder Math: 7 PPR * 2 (Change Interrupt) * 71.2 Gear Ratio
        self.ticks_per_rev = 996.8     
        
        # Motor Limits
        self.max_pwm = 255.0           # Max PWM the ESP32 code accepts
        self.max_rpm = 100.0           # Max RPM of your motor at 12V
        
        # --- Serial Connection ---
        port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud = self.get_parameter('baud_rate').get_parameter_value().integer_value
        
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.get_logger().info(f"Connected to ESP32 on {port} at {baud}")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to connect to Serial: {e}")
            # We exit because the node is useless without the hardware connection
            exit(1)

        # --- Odometry State Variables ---
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        
        # Track previous tick counts to calculate delta
        self.prev_ticks_left = 0
        self.prev_ticks_right = 0
        
        self.last_odom_time = self.get_clock().now()
        
        # --- ROS 2 Publishers & Subscribers ---
        # Publisher: Where is the robot? (Odometry)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        
        # Publisher: TF (Coordinate transform for Rviz)
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Subscriber: Velocity Commands (from Nav2 or Teleop)
        self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        
        # --- Multi-Threading for Serial ---
        # We read serial in a background thread so it doesn't block ROS
        self.lock = threading.Lock()
        self.latest_ticks = [0, 0] # Stores [Left, Right] ticks safely
        self.stop_thread = False
        self.read_thread = threading.Thread(target=self.read_serial_loop)
        self.read_thread.start()

        # --- Timer Loop ---
        # Run the odometry calculation at 20Hz (every 0.05s)
        self.create_timer(0.05, self.update_odometry)

    def cmd_vel_callback(self, msg):
        """
        Receives Twist msg -> Calculates PWM -> Sends to ESP32
        """
        linear_x = msg.linear.x   # Forward/Backward speed (m/s)
        angular_z = msg.angular.z # Rotation speed (rad/s)

        # 1. Inverse Kinematics (Differential Drive)
        # Calculate individual wheel velocities (m/s)
        vel_right = linear_x + (angular_z * self.wheel_separation / 2.0)
        vel_left  = linear_x - (angular_z * self.wheel_separation / 2.0)

        # 2. Convert Velocity (m/s) to RPM
        # RPM = (Velocity / Wheel_Circumference) * 60
        circumference = 2 * math.pi * self.wheel_radius
        rpm_right = (vel_right / circumference) * 60.0
        rpm_left  = (vel_left / circumference) * 60.0

        # 3. Map RPM to PWM (Simple Linear Mapping)
        # PWM = (Target_RPM / Max_RPM) * 255
        pwm_right = int((rpm_right / self.max_rpm) * self.max_pwm)
        pwm_left  = int((rpm_left / self.max_rpm) * self.max_pwm)

        # 4. Clamp values to keep them within valid ESP32 range (-255 to 255)
        pwm_right = max(-255, min(255, pwm_right))
        pwm_left  = max(-255, min(255, pwm_left))

        # 5. Send Command to ESP32
        # Protocol: "PWM_LEFT,PWM_RIGHT\n" (e.g., "100,100\n")
        # NOTE: If your robot spins in place when told to go forward, swap these variables.
        command = f"{pwm_right},{pwm_left}\n"
        
        try:
            self.ser.write(command.encode('utf-8'))
        except Exception as e:
            self.get_logger().error(f"Serial Write Error: {e}")

    def read_serial_loop(self):
        """
        Background thread: Continuously reads "POS1,POS2" from ESP32
        """
        while not self.stop_thread and rclpy.ok():
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    # Expected format from ESP32: "1205,3004"
                    if ',' in line:
                        parts = line.split(',')
                        if len(parts) == 2:
                            with self.lock: # Thread-safe write
                                try:
                                    # Assuming ESP sends Motor1 (Left), Motor2 (Right)
                                    self.latest_ticks[0] = int(parts[1]) 
                                    self.latest_ticks[1] = int(parts[0])
                                except ValueError:
                                    pass # Ignore corrupted lines
            except Exception:
                pass 
            time.sleep(0.005) # Tiny sleep to prevent high CPU usage

    def update_odometry(self):
        """
        Calculates robot position from encoder ticks and publishes /odom
        """
        current_time = self.get_clock().now()
        
        # Thread-safe read of latest encoder data
        with self.lock:
            curr_ticks_left = self.latest_ticks[0]
            curr_ticks_right = self.latest_ticks[1]

        # Calculate Delta Ticks (Change since last loop)
        d_ticks_left = curr_ticks_left - self.prev_ticks_left
        d_ticks_right = curr_ticks_right - self.prev_ticks_right

        # Update history
        self.prev_ticks_left = curr_ticks_left
        self.prev_ticks_right = curr_ticks_right

        # 1. Convert Ticks to Distance (meters)
        # Distance = (DeltaTicks / TicksPerRev) * WheelCircumference
        d_left = (d_ticks_left / self.ticks_per_rev) * (2 * math.pi * self.wheel_radius)
        d_right = (d_ticks_right / self.ticks_per_rev) * (2 * math.pi * self.wheel_radius)

        # 2. Calculate Robot Motion
        # d_center: Distance the center of the robot moved
        # d_theta:  Angle the robot turned
        d_center = (d_right + d_left) / 2.0
        d_theta = (d_right - d_left) / self.wheel_separation

        # 3. Update Global Pose (x, y, theta)
        self.x += d_center * math.cos(self.th)
        self.y += d_center * math.sin(self.th)
        self.th += d_theta

        # Normalize angle to -pi to pi (standard practice)
        self.th = math.atan2(math.sin(self.th), math.cos(self.th))

        # 4. Create Quaternion for ROS (ROS uses Quaternions, not Euler angles)
        q = self.euler_to_quaternion(0, 0, self.th)

        # --- PUBLISH ODOMETRY ---
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"

        # Position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = q

        # Velocity (Optional, but helps Navigation Stack)
        # Velocity (Optional, but helps Navigation Stack)
        dt = (current_time - self.last_odom_time).nanoseconds / 1e9
        if dt > 0:
            odom.twist.twist.linear.x = d_center / dt
            odom.twist.twist.angular.z = d_theta / dt

        # --- NEW CODE: Add Covariance Matrix ---
        odom.pose.covariance = [
            0.1, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.1, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 1e-6, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1e-6, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1e-6, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.1
        ]
        odom.twist.covariance = odom.pose.covariance
        # ---------------------------------------

        self.odom_pub.publish(odom)

        # --- PUBLISH TF (Transform) ---
        # This connects the 'odom' frame to the 'base_link' frame
        # t = TransformStamped()
        # t.header.stamp = current_time.to_msg()
        # t.header.frame_id = "odom"
        # t.child_frame_id = "base_link"
        # t.transform.translation.x = self.x
        # t.transform.translation.y = self.y
        # t.transform.translation.z = 0.0
        # t.transform.rotation = q
        
        # self.tf_broadcaster.sendTransform(t)

        # CRITICAL FIX: Uncommented this so velocity calculates correctly!
        self.last_odom_time = current_time


    def euler_to_quaternion(self, roll, pitch, yaw):
        """Math helper to convert angles to Quaternions"""
        qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
        qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
        qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        return Quaternion(x=qx, y=qy, z=qz, w=qw)

    def on_shutdown(self):
        """Cleanup when node is killed"""
        self.stop_thread = True
        if self.read_thread.is_alive():
            self.read_thread.join()
        # Send Stop Command to Motors
        try:
            self.ser.write(b"0,0\n")
            self.ser.close()
        except:
            pass
        self.get_logger().info("Motors Stopped. Serial Closed.")

def main(args=None):
    rclpy.init(args=args)
    node = ESP32MotorBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.on_shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()