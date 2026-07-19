# GLAD IMU

ROS 2 packages for BNO055 IMU data acquisition and Madgwick orientation filtering.

## Packages

### `glad_imu_publisher` — Hardware Driver

Reads raw data from an **Adafruit BNO055** IMU over I2C and publishes it as ROS 2 topics.

**Topics published:**

| Topic | Type | Rate | Description |
|-------|------|------|-------------|
| `/imu/data_raw` | `sensor_msgs/Imu` | 50 Hz | Raw gyroscope (rad/s) and linear acceleration (m/s²). Orientation covariance first element set to `-1.0` (orientation not provided). |
| `/imu/mag` | `sensor_msgs/MagneticField` | 50 Hz | Calibrated magnetometer field vector (Tesla). |

**Calibration:**

Per-device offsets and deadzones are loaded from `config/bno055_config.yaml`:

- `gyro_offsets` — Static bias subtracted from raw gyro readings per axis.
- `mag_offsets` — Static bias subtracted from raw magnetometer readings.
- `deadzones.accel` / `deadzones.gyro` — Threshold below which readings are zeroed (noise gate).

Axis sign corrections are applied inline in code (Y/Z gyro negation, X accel negation, Y/Z mag negation) to match the desired convention.

**Executable:** `imupub`

```
ros2 run glad_imu_publisher imupub
```

---

### `glad_imu_filter` — Madgwick Orientation Filter

Subscribes to raw IMU and magnetometer data and publishes fused orientation.

**Topics subscribed:**

| Topic | Type | Description |
|-------|------|-------------|
| `/imu/data_raw` | `sensor_msgs/Imu` | Raw gyroscope + accelerometer |
| `/imu/mag` | `sensor_msgs/MagneticField` | Magnetometer field (optional) |

**Topic published:**

| Topic | Type | Description |
|-------|------|-------------|
| `/imu/data` | `sensor_msgs/Imu` | Fused IMU with orientation (quaternion) filled in |

**Parameters** (loaded from `config/madgwick_params.yaml`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `beta` | `0.1` | Madgwick filter gain. Higher values trust the gyroscope more; lower values blend in more accelerometer/magnetometer correction. |
| `use_mag` | `true` | Whether to incorporate magnetometer data into the filter. |
| `world_frame` | `"enu"` | World frame convention (East-North-Up). |
| `fixed_frame` | `"odom"` | Fixed reference frame name. |

The filter is a pure-Python implementation of the Madgwick algorithm, which uses gradient descent to compute the optimal quaternion orientation from gyroscope, accelerometer, and optional magnetometer measurements.

**Executable:** `imu_madgwick`

```
ros2 run glad_imu_filter imu_madgwick
```

---

## Data Flow

```
BNO055 (I2C)
  │
  ▼
glad_imu_publisher  ──►  /imu/data_raw  ──►  glad_imu_filter  ──►  /imu/data
  │                      (sensor_msgs/Imu)      (Madgwick)        (fused orientation)
  └──►  /imu/mag
        (sensor_msgs/MagneticField)
```

The publisher reads the sensor at 50 Hz, applies calibration offsets, deadzone filtering, and axis sign corrections, then publishes raw data. The filter subscribes to both topics, runs the Madgwick algorithm on each sample, and publishes an `Imu` message with the fused orientation quaternion.

## Launch Files

### Combined launch (both nodes)

```
ros2 launch glad_imu_publisher imu_publisher_launch.py
```

Single launch file that starts both the BNO055 driver and the Madgwick filter together with the correct topic remappings.

### Individual launch

```
ros2 launch glad_imu_filter imu_madgwick_launch.py
```

Starts only the filter node (useful when running the publisher separately or using recorded data).

## Dependencies

- ROS 2 (rclpy)
- `sensor_msgs`, `geometry_msgs`
- `adafruit-bno055` (I2C driver for the BNO055 sensor)
- `numpy`

## Build

```bash
colcon build --packages-select glad_imu_publisher glad_imu_filter
source install/setup.bash
```
