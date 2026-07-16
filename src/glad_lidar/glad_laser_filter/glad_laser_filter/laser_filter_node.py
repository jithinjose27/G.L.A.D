import math
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class LaserFilterNode(Node):
    def __init__(self):
        super().__init__("laser_filter_node")

        self.declare_parameter("input_scan_topic", "/scan_unfiltered")
        self.declare_parameter("output_scan_topic", "/scan")

        self.declare_parameter("filter1.name", "angle")
        self.declare_parameter("filter1.type", "angular_bounds")
        self.declare_parameter("filter1.lower_angle", 1.5708)
        self.declare_parameter("filter1.upper_angle", -1.5708)

        self.declare_parameter("filter2.name", "range")
        self.declare_parameter("filter2.type", "range_filter")
        self.declare_parameter("filter2.min_range", 0.20)
        self.declare_parameter("filter2.max_range", 12.0)

        input_topic = self.get_parameter("input_scan_topic").value
        output_topic = self.get_parameter("output_scan_topic").value

        self.lower_angle = self.get_parameter("filter1.lower_angle").value
        self.upper_angle = self.get_parameter("filter1.upper_angle").value

        self.min_range = self.get_parameter("filter2.min_range").value
        self.max_range = self.get_parameter("filter2.max_range").value

        self.subscription = self.create_subscription(
            LaserScan, input_topic, self.scan_callback, 10
        )
        self.publisher = self.create_publisher(LaserScan, output_topic, 10)

        self.get_logger().info(
            f"LaserFilterNode started: {input_topic} -> {output_topic}"
        )

    def scan_callback(self, msg: LaserScan):
        angles = [
            msg.angle_min + i * msg.angle_increment for i in range(len(msg.ranges))
        ]
        ranges = np.array(msg.ranges, dtype=np.float32)
        intensities = (
            np.array(msg.intensities, dtype=np.float32) if msg.intensities else None
        )

        lower = min(self.lower_angle, self.upper_angle)
        upper = max(self.lower_angle, self.upper_angle)

        for i, angle in enumerate(angles):
            angle_norm = math.atan2(math.sin(angle), math.cos(angle))

            if angle_norm < lower or angle_norm > upper:
                ranges[i] = float("inf")
                if intensities is not None:
                    intensities[i] = 0.0

            if ranges[i] < self.min_range:
                ranges[i] = float("-inf")
                if intensities is not None:
                    intensities[i] = 0.0
            elif ranges[i] > self.max_range:
                ranges[i] = float("inf")
                if intensities is not None:
                    intensities[i] = 0.0

        filtered = LaserScan()
        filtered.header = msg.header
        filtered.angle_min = msg.angle_min
        filtered.angle_max = msg.angle_max
        filtered.angle_increment = msg.angle_increment
        filtered.time_increment = msg.time_increment
        filtered.scan_time = msg.scan_time
        filtered.range_min = msg.range_min
        filtered.range_max = msg.range_max
        filtered.ranges = ranges.tolist()
        filtered.intensities = intensities.tolist() if intensities is not None else []

        self.publisher.publish(filtered)


def main(args=None):
    rclpy.init(args=args)
    node = LaserFilterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
