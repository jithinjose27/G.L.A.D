#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
import sys
import select
import termios
import tty


class TeleopKeyboard(Node):
    def __init__(self):
        super().__init__("teleop_keyboard")

        self.declare_parameter("linear_speed", 0.1)
        self.declare_parameter("angular_speed", 0.2)

        self.linear_speed = self.get_parameter("linear_speed").value
        self.angular_speed = self.get_parameter("angular_speed").value

        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel/teleop", 10)
        self.stop_pub = self.create_publisher(Bool, "/cmd_vel/stop", 10)

        self.msg = Twist()
        self.emergency_stop = False
        self.running = True
        self.settings = termios.tcgetattr(sys.stdin)

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            return key
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return None

    def run(self):
        self.get_logger().info(
            f"Teleop started — linear: {self.linear_speed} m/s, angular: {self.angular_speed} rad/s"
        )
        self.get_logger().info(
            "W: forward  X: reverse  A: left  D: right  S: stop  Space: emergency stop  Q: quit"
        )
        self.get_logger().info("---")

        while self.running and rclpy.ok():
            key = self.get_key()
            if key is None:
                continue

            if key == " ":
                self.emergency_stop = not self.emergency_stop
                self.stop_pub.publish(Bool(data=self.emergency_stop))
                if self.emergency_stop:
                    self.get_logger().warn("EMERGENCY STOP ENGAGED")
                    self.cmd_pub.publish(Twist())
                else:
                    self.get_logger().info("Emergency stop released")
                continue

            if self.emergency_stop:
                continue

            self.msg.linear.x = 0.0
            self.msg.angular.z = 0.0

            if key == "w":
                self.msg.linear.x = self.linear_speed
            elif key == "x":
                self.msg.linear.x = -self.linear_speed
            elif key == "a":
                self.msg.angular.z = self.angular_speed
            elif key == "d":
                self.msg.angular.z = -self.angular_speed
            elif key == "s":
                pass
            elif key.lower() == "q":
                self.running = False
                continue
            else:
                continue

            self.cmd_pub.publish(self.msg)


def main(args=None):
    rclpy.init(args=args)
    node = TeleopKeyboard()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, node.settings)
        node.cmd_pub.publish(Twist())
        node.stop_pub.publish(Bool(data=False))
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
