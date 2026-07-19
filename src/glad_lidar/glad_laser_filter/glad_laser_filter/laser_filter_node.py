import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class LaserFilterNode(Node):
    def __init__(self):
        super().__init__("laser_filter_node")

        self.declare_parameter("input_scan_topic", "/scan_unfiltered")
        self.declare_parameter("output_scan_topic", "/scan")
        self.declare_parameter("target_beams", 544)

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
        self.target_beams = self.get_parameter("target_beams").value

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
        ranges = np.array(msg.ranges, dtype=np.float32)
        intensities = (
            np.array(msg.intensities, dtype=np.float32) if msg.intensities else None
        )

        ranges[np.isnan(ranges) | np.isinf(ranges)] = float("inf")

        angles = msg.angle_min + np.arange(len(ranges)) * msg.angle_increment
        lower = min(self.lower_angle, self.upper_angle)
        upper = max(self.lower_angle, self.upper_angle)
        angle_norm = np.arctan2(np.sin(angles), np.cos(angles))
        angle_mask = (angle_norm < lower) | (angle_norm > upper)
        ranges[angle_mask] = float("inf")
        if intensities is not None:
            intensities[angle_mask] = 0.0

        range_mask = ranges < self.min_range
        ranges[range_mask] = float("-inf")
        if intensities is not None:
            intensities[range_mask] = 0.0

        range_mask = ranges > self.max_range
        ranges[range_mask] = float("inf")
        if intensities is not None:
            intensities[range_mask] = 0.0

        n_input = len(ranges)
        target = self.target_beams if self.target_beams > 0 else n_input

        if n_input == target:
            final_ranges = ranges
            final_intensities = intensities
        elif n_input < target:
            pad = target - n_input
            final_ranges = np.pad(ranges, (0, pad), constant_values=float("inf"))
            if intensities is not None:
                final_intensities = np.pad(intensities, (0, pad), constant_values=0.0)
            else:
                final_intensities = None
        else:
            final_ranges = ranges[:target]
            if intensities is not None:
                final_intensities = intensities[:target]
            else:
                final_intensities = None

        filtered = LaserScan()
        filtered.header = msg.header
        filtered.header.stamp = self.get_clock().now().to_msg()
        filtered.angle_min = msg.angle_min
        filtered.angle_max = msg.angle_max
        filtered.angle_increment = (
            (msg.angle_max - msg.angle_min) / (target - 1)
            if target > 1
            else msg.angle_increment
        )
        filtered.time_increment = msg.time_increment
        filtered.scan_time = msg.scan_time
        filtered.range_min = self.min_range
        filtered.range_max = self.max_range
        filtered.ranges = final_ranges.tolist()
        filtered.intensities = (
            final_intensities.tolist() if final_intensities is not None else []
        )

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
