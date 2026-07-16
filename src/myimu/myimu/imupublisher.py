import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, MagneticField
import board
import busio
import adafruit_bno055
import yaml
import os
from ament_index_python.packages import get_package_share_directory


class BNO055Driver(Node):
    def __init__(self):
        super().__init__("bno055_driver")

        # 1. Setup Parameters and Load YAML
        pkg_share = get_package_share_directory("myimu")
        default_config_path = os.path.join(pkg_share, "config", "bno055_config.yaml")
        self.declare_parameter("config_file", default_config_path)
        config_path = self.get_parameter("config_file").value

        self.offsets = {
            "gyro": {"x": 0, "y": 0, "z": 0},
            "mag": {"x": 0, "y": 0, "z": 0},
        }
        self.deadzones = {"gyro": 0.0, "accel": 0.0}

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                self.offsets["gyro"] = config["gyro_offsets"]
                self.offsets["mag"] = config["mag_offsets"]
                self.deadzones = config["deadzones"]
                self.get_logger().info(f"Loaded calibration from {config_path}")
        except Exception as e:
            self.get_logger().warn(f"Could not load config: {e}. Using raw values.")

        # 2. Setup Hardware
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_bno055.BNO055_I2C(i2c)
        except Exception as e:
            self.get_logger().error(f"Sensor Connection Failed: {e}")
            return

        # 3. Publishers
        self.imu_raw_pub = self.create_publisher(Imu, "/imu/data_raw", 10)
        self.mag_pub = self.create_publisher(MagneticField, "/imu/mag", 10)

        self.timer = self.create_timer(0.02, self.update_sensor)  # 50Hz

    def apply_deadzone(self, val, threshold):
        if abs(val) < threshold:
            return 0.0
        return val

    def update_sensor(self):
        # Read BNO055 Data
        gyro = self.sensor.gyro
        accel = self.sensor.acceleration
        mag = self.sensor.magnetic

        if gyro[0] is None or accel[0] is None or mag[0] is None:
            return

        current_time = self.get_clock().now().to_msg()

        # --- PREPARE IMU MSG (Accel + Gyro) ---
        imu_msg = Imu()
        imu_msg.header.stamp = current_time
        imu_msg.header.frame_id = "imu_link"

        # 1. GYROSCOPE (Flip Y and Z for Upside-Down mount)
        gx = self.apply_deadzone(
            gyro[0] - self.offsets["gyro"]["x"], self.deadzones["gyro"]
        )
        gy = -self.apply_deadzone(
            gyro[1] - self.offsets["gyro"]["y"], self.deadzones["gyro"]
        )
        gz = -self.apply_deadzone(
            gyro[2] - self.offsets["gyro"]["z"], self.deadzones["gyro"]
        )

        # 2. ACCELEROMETER (Flip Y and Z, plus BNO055 gravity correction)
        # Normally ROS wants -ax, -ay, -az.
        # Flipped 180 degrees, the Y and Z negatives cancel out!
        ax = -self.apply_deadzone(accel[0], self.deadzones["accel"])
        ay = self.apply_deadzone(accel[1], self.deadzones["accel"])
        az = self.apply_deadzone(accel[2], self.deadzones["accel"])

        imu_msg.angular_velocity.x = gx
        imu_msg.angular_velocity.y = gy
        imu_msg.angular_velocity.z = gz
        imu_msg.linear_acceleration.x = ax
        imu_msg.linear_acceleration.y = ay
        imu_msg.linear_acceleration.z = az

        imu_msg.orientation_covariance[0] = -1.0
        imu_msg.angular_velocity_covariance = [
            0.01,
            0.0,
            0.0,
            0.0,
            0.01,
            0.0,
            0.0,
            0.0,
            0.01,
        ]
        imu_msg.linear_acceleration_covariance = [
            0.1,
            0.0,
            0.0,
            0.0,
            0.1,
            0.0,
            0.0,
            0.0,
            0.1,
        ]

        self.imu_raw_pub.publish(imu_msg)

        # --- PREPARE MAG MSG ---
        mag_msg = MagneticField()
        mag_msg.header.stamp = current_time
        mag_msg.header.frame_id = "imu_link"

        # 3. MAGNETOMETER (Flip Y and Z for Upside-Down mount)
        raw_mag_x = (mag[0] - self.offsets["mag"]["x"]) * 1e-6
        raw_mag_y = (mag[1] - self.offsets["mag"]["y"]) * 1e-6
        raw_mag_z = (mag[2] - self.offsets["mag"]["z"]) * 1e-6

        mag_msg.magnetic_field.x = raw_mag_x
        mag_msg.magnetic_field.y = -raw_mag_y  # Flipped!
        mag_msg.magnetic_field.z = -raw_mag_z  # Flipped!

        self.mag_pub.publish(mag_msg)


def main(args=None):
    rclpy.init(args=args)
    node = BNO055Driver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
