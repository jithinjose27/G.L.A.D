# GLAD LiDAR

ROS 2 packages for RPLidar-based laser sensing pipeline: hardware driver, scan filtering, and range-flow laser odometry.

## Packages

### `glad_rplidar` — RPLidar Driver

Serial driver for Slamtec RPLidar (A1/A2/A3 series). Connects via UART at 115200 baud, sends scan commands, parses the proprietary response protocol, and publishes `LaserScan` messages.

**Topic published:**

| Topic | Type | Description |
|-------|------|-------------|
| `/scan` | `sensor_msgs/LaserScan` | Raw scan with ranges (meters) and intensities (quality 0–63) sorted by ascending angle |

**Parameters** (`config/rplidar_params.yaml`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `serial_port` | `/dev/ttyUSB0` | Serial device path |
| `serial_baudrate` | `115200` | Baud rate |
| `frame_id` | `laser` | Frame ID for the scan header |
| `inverted` | `false` | Mirror scan angles (2π − θ) |
| `angle_compensate` | `true` | Enable angle compensation |
| `scan_mode` | `Sensitivity` | RPLidar scan mode |

Points with zero distance or the sync flag set are discarded. Remaining points are sorted by angle and published as a single `LaserScan` message per read cycle.

**Executable:** `rplidar_node`

```
ros2 run glad_rplidar rplidar_node
```

---

### `glad_laser_filter` — Scan Filter & Resampler

Filters and resamples raw `LaserScan` data before it reaches navigation or odometry nodes.

**Topics:**

| Topic | Direction | Type |
|-------|-----------|------|
| `/scan_unfiltered` | Subscribed | `sensor_msgs/LaserScan` |
| `/scan` | Published | `sensor_msgs/LaserScan` |

**Filters applied (in order):**

1. **Angular bounds** — Masks out readings outside [`lower_angle`, `upper_angle`] (radians). Default: ±90° front-facing field of view.
2. **Range filter** — Clamps readings below `min_range` to `-inf` and above `max_range` to `inf`. Default: 0.20–12.0 m.

**Resampling:** The output scan is padded (with `inf`) or truncated to exactly `target_beams` (default 544). The `angle_increment` is recomputed accordingly for the fixed beam count.

**Parameters** (`config/laser_filter.yaml`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `input_scan_topic` | `/scan_unfiltered` | Input scan topic |
| `output_scan_topic` | `/scan` | Output scan topic |
| `target_beams` | `544` | Fixed number of output beams |
| `filter1.lower_angle` | `1.5708` | Lower angular bound (rad) |
| `filter1.upper_angle` | `-1.5708` | Upper angular bound (rad) |
| `filter2.min_range` | `0.20` | Minimum valid range (m) |
| `filter2.max_range` | `12.0` | Maximum valid range (m) |

**Executable:** `laser_filter_node`

```
ros2 run glad_laser_filter laser_filter_node
```

---

### `rf2o_laser_odometry` — Range-Flow Laser Odometry

Estimates robot 2D pose and twist from consecutive laser scans using a range-flow / ICP-like correspondence method (SVD-based least-squares alignment).

**Topics:**

| Topic | Direction | Type |
|-------|-----------|------|
| `/scan` | Subscribed | `sensor_msgs/LaserScan` |
| `/odom_rf2o` | Published | `nav_msgs/Odometry` |

**Algorithm:**

1. Converts consecutive scans to Cartesian point clouds.
2. Computes centroids and cross-covariance matrix H between matched points.
3. Solves for rotation via SVD (Kabsch algorithm) and extracts translation and yaw rate.
4. Integrates velocities over time to accumulate pose: x, y, yaw.
5. Publishes `Odometry` and optionally broadcasts `odom → base_link` TF.

**Parameters** (`config/rf2o_odometry.yaml`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `laser_scan_topic` | `/scan` | Input laser scan topic |
| `odom_topic` | `/odom_rf2o` | Output odometry topic |
| `publish_tf` | `false` | Broadcast `odom → base_link` transform |
| `base_frame_id` | `base_link` | Robot base frame |
| `odom_frame_id` | `odom` | Odometry reference frame |
| `freq` | `20.0` | Expected scan rate (Hz) |

**Executable:** `rf2o_odometry_node`

```
ros2 run rf2o_laser_odometry rf2o_odometry_node
```

---

## Data Flow

```
RPLidar (UART)
  │
  ▼
glad_rplidar ──► /scan_unfiltered ──► glad_laser_filter ──► /scan
(rplidar_node)     (raw, unsorted       (angle crop,         (filtered,
                   angles, all 360°)     range clip,          resampled
                                         resample to 544)     544 beams)
                                                              │
                                                              ▼
                                                   rf2o_laser_odometry ──► /odom_rf2o
                                                   (range-flow odometry)   (pose + twist)
```

The pipeline reads raw lidar data via serial, publishes it unfiltered, passes it through an angular/range filter and resampler, and then feeds the clean scan into a laser odometry estimator.

## Launch Files

### Combined pipeline

```
ros2 launch glad_laser_filter glad_laser_filter_launch.py
```

### Individual launches

```
ros2 launch glad_rplidar glad_rplidar_launch.py
ros2 launch rf2o_laser_odometry rf2o_laser_odometry_launch.py
```

## Dependencies

- ROS 2 (`rclpy`, `launch_ros`)
- `sensor_msgs`, `nav_msgs`, `geometry_msgs`
- `tf2_ros`
- `pyserial`
- `numpy`

## Build

```bash
colcon build --packages-select glad_rplidar glad_laser_filter rf2o_laser_odometry
source install/setup.bash
```
