# GLAD Start

Top-level bringup packages for the G.L.A.D robot. Orchestrate the entire sensor, navigation, and autonomy pipeline through time-sequenced launch files.

## Packages

### `glad_bringup` — Full System Bringup

Use this launch file when you simply want to navigate the robot — for testing the navigation stack or demonstrating teleoperation to someone.

Starts every ROS 2 node in the G.L.A.D stack with configurable SLAM vs. localization mode.

**Launch arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `use_sim_time` | `false` | Use simulation clock |
| `enable_slam` | `false` | Start slam_toolbox for online mapping (vs. using a pre-built map) |
| `map_yaml` | `/home/.../robotics_floor.yaml` | Path to map file (used when `enable_slam:=false`) |

**Launch sequence:**

| Step | Package | Delay | Description |
|------|---------|-------|-------------|
| — | `glad_static_tf` | 0s | Static transforms (base_link → laser, base_link → imu_link) |
| 1 | `glad_rplidar` | 0s | RPLidar serial driver → `/scan_unfiltered` |
| 2 | `glad_laser_filter` | 1.0s | Angle crop + range filter + resample → `/scan` |
| 3 | `glad_imu_publisher` | 1.5s | BNO055 I2C driver → `/imu/data_raw`, `/imu/mag` |
| 4 | `glad_imu_filter` | 2.0s | Madgwick orientation filter → `/imu/data` |
| 5 | `rf2o_laser_odometry` | 2.5s | Range-flow laser odometry → `/odom_rf2o` |
| 6 | `glad_ekf` | 3.0s | robot_localization EKF → `odom` |
| 7 | `slam_toolbox` | 3.5s | SLAM mapping *(only if `enable_slam:=true`)* |
| 8 | `glad_teleop` + motion control | 4.0s | Teleop, twist mux, trajectory controller, motor bridge |
| 9 | `glad_nav2` | 6.0s | Nav2 localization + planning + control *(only if `enable_slam:=false`)* |

**Usage:**

```bash
# Localization mode (using pre-built map)
ros2 launch glad_bringup glad_bringup_launch.py

# SLAM mode (build a new map)
ros2 launch glad_bringup glad_bringup_launch.py enable_slam:=true
```

---

### `glad_final_tour` — Autonomous Tour Bringup

Use this launch file for the final project showcase — it launches everything including the autonomous tour, demonstrating the full capabilities of the G.L.A.D robot.

Extends `glad_bringup` with the tour guide application. After all sensor and navigation nodes are running, launches the autonomous tour node.

**Launch arguments:** Same as `glad_bringup`.

**Launch sequence:** Identical to `glad_bringup` for steps 1–9, plus:

| Step | Package | Delay | Description |
|------|---------|-------|-------------|
| 10 | `glad_tour` | 10.0s | Autonomous tour guide — navigates 3 waypoints with AI commentary |

The 10-second delay before the tour starts gives Nav2 time to fully initialize, receive the initial pose, and load the costmaps.

**Usage:**

```bash
# Full autonomous tour with pre-built map
ros2 launch glad_final_tour glad_final_tour_launch.py

# Tour with live SLAM mapping
ros2 launch glad_final_tour glad_final_tour_launch.py enable_slam:=true
```

---

## System Architecture

### Data Flow

```
RPLidar ──► glad_rplidar ──► /scan_unfiltered ──► glad_laser_filter ──► /scan ──┐
                                                                                   │
BNO055 ──► glad_imu_publisher ──► /imu/data_raw ──► glad_imu_filter ──► /imu/data │
                                  /imu/mag ──────────────┘                        │
                                                                                   │
┌─────────────────────────────────────────────────────────────────────────────────┘
│
▼  /scan + /odom (EKF)
rf2o_laser_odometry ──► /odom_rf2o ──┐
                                      ▼
                              glad_ekf (robot_localization) ──► /odom
                                      ▲
motor encoders ──► glad_motor_controller ──► /motor/odom
```

### TF Tree

```
map ──► odom ──► base_link ──┬──► laser (static)
                              └──► imu_link (static)
```

- `map → odom`: AMCL (Nav2) or slam_toolbox.
- `odom → base_link`: EKF filter.
- `base_link → laser`, `base_link → imu_link`: Static transforms.

### Command Flow

```
Teleop Keyboard ──► /cmd_vel/teleop ──┐
                                       ├──► glad_twist_mux ──► /cmd_vel/raw ──► glad_trajectory_controller ──► /cmd_vel ──► glad_motor_controller ──► ESP32
Nav2 ──► /cmd_vel/nav ────────────────┘
```

## Dependencies

Requires all G.L.A.D packages to be built:

- `glad_rplidar`, `glad_laser_filter`
- `glad_imu_publisher`, `glad_imu_filter`
- `rf2o_laser_odometry`
- `glad_sensor_filter`
- `glad_mapping`
- `glad_static_tf`
- `glad_teleop`, `glad_twist_mux`, `glad_trajectory_controller`, `glad_motor_controller`
- `glad_navigation`
- `glad_tour` (for `glad_final_tour`)

## Build

```bash
colcon build
source install/setup.bash
```
