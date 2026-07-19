# GLAD Motion Control

ROS 2 motion control pipeline: keyboard teleop → twist multiplexer → trajectory smoothing → motor driver with odometry.

## Packages

### `glad_teleop` — Keyboard Teleoperation

Terminal-based keyboard teleop node. Reads single keypresses and publishes velocity commands.

**Topics published:**

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel/teleop` | `geometry_msgs/Twist` | Linear/angular velocity from key input |
| `/cmd_vel/stop` | `std_msgs/Bool` | Emergency stop toggle status |

**Controls:**

| Key | Action |
|-----|--------|
| `W` | Forward (linear +x) |
| `X` | Reverse (linear −x) |
| `A` | Rotate left (angular +z) |
| `D` | Rotate right (angular −z) |
| `S` | Stop (zero velocity) |
| `Space` | Toggle emergency stop |
| `Q` | Quit |

**Parameters** (`config/teleop.yaml`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `linear_speed` | `0.1` | Forward/backward speed (m/s) |
| `angular_speed` | `0.2` | Rotation speed (rad/s) |

**Executable:** `teleop_node`

```
ros2 run glad_teleop teleop_node
```

---

### `glad_twist_mux` — Priority-Based Twist Multiplexer

Merges multiple Twist sources based on priority. The highest-priority source with a recent message wins.

**Topics subscribed:**

| Topic | Type | Priority | Source |
|-------|------|----------|--------|
| `/cmd_vel/stop` | `std_msgs/Bool` | 100 | Emergency stop (highest) |
| `/cmd_vel/teleop` | `geometry_msgs/Twist` | 70 | Keyboard teleop |
| `/cmd_vel/nav` | `geometry_msgs/Twist` | 40 | Nav2 autonomy |

**Topic published:**

| Topic | Type |
|-------|------|
| `/cmd_vel/raw` | `geometry_msgs/Twist` |

If `stop` is active, a zero Twist is locked regardless of other sources. Each source has a timeout; if no message arrives within `timeout` seconds the mux falls through to the next priority. If all sources are stale, a zero Twist is published.

**Parameters** (`config/twist_mux.yaml`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `timeout` | `0.5` | Source timeout (s) |
| `priority_stop` | `100` | Emergency stop priority |
| `priority_teleop` | `70` | Teleop priority |
| `priority_nav` | `40` | Nav2 priority |

**Executable:** `twist_mux_node`

```
ros2 run glad_twist_mux twist_mux_node
```

---

### `glad_trajectory_controller` — Slew-Rate Limiter

Applies acceleration and deceleration ramps to smooth velocity commands before they reach the motor driver.

**Topics:**

| Topic | Direction | Type |
|-------|-----------|------|
| `/cmd_vel/raw` | Subscribed | `geometry_msgs/Twist` |
| `/cmd_vel` | Published | `geometry_msgs/Twist` |

The node ramps linear and angular velocities independently. When the target magnitude is smaller than the current output, the deceleration rate is used (softer stop); otherwise the acceleration rate is used. If no command arrives within `timeout` seconds, velocity ramps back to zero.

**Parameters** (`config/trajectory_controller.yaml`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `timeout` | `0.5` | Command timeout before ramping to zero (s) |
| `accel_linear` | `0.2` | Linear acceleration limit (m/s²) |
| `decel_linear` | `0.4` | Linear deceleration limit (m/s²) |
| `accel_angular` | `0.4` | Angular acceleration limit (rad/s²) |
| `decel_angular` | `0.8` | Angular deceleration limit (rad/s²) |

**Executable:** `trajectory_controller_node`

```
ros2 run glad_trajectory_controller trajectory_controller_node
```

---

### `glad_motor_controller` — ESP32 Differential Drive Bridge

Serial bridge to an ESP32 motor controller. Handles inverse kinematics, PWM mapping, encoder-based odometry, and TF.

**Serial protocol:**

| Direction | Format | Description |
|-----------|--------|-------------|
| TX → ESP32 | `PWM_RIGHT,PWM_LEFT\n` | Motor PWM commands (−255 to 255) |
| RX ← ESP32 | `TICKS_LEFT,TICKS_RIGHT\n` | Encoder tick counts |

**Topics:**

| Topic | Direction | Type | Description |
|-------|-----------|------|-------------|
| `cmd_vel` | Subscribed | `geometry_msgs/Twist` | Velocity commands |
| `odom` | Published | `nav_msgs/Odometry` | Wheel odometry (pose + twist with covariance) |

**Pipeline:**

1. Receives `Twist` on `cmd_vel`.
2. Differential-drive inverse kinematics → left/right wheel velocities (m/s).
3. Wheel velocities → RPM → PWM (−255 to 255) via linear mapping.
4. Sends `PWM_R,PWM_L\n` over serial to ESP32.
5. Background thread reads `TICKS_L,TICKS_R\n` from serial at ~200 Hz.
6. On a 20 Hz timer: delta ticks → distance (m) → pose update (x, y, θ) → publish `Odometry`.

**Parameters** (`config/motor_controller_params.yaml`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `serial_port` | `/dev/ttyUSB1` | Serial device to ESP32 |
| `baud_rate` | `115200` | Serial baud rate |
| `wheel_radius` | `0.04` | Wheel radius (m) |
| `wheel_separation` | `0.325` | Distance between wheels (m) |
| `ticks_per_rev` | `996.8` | Encoder ticks per full wheel revolution |
| `max_pwm` | `255.0` | Maximum PWM value |
| `max_rpm` | `100.0` | Maximum wheel RPM at max PWM |

**Executable:** `motor_controller_node`

```
ros2 run glad_motor_controller motor_controller_node
```

---

## Data Flow

```
Teleop Keyboard         Nav2 Autonomy
  │                       │
  │ /cmd_vel/teleop       │ /cmd_vel/nav
  ▼                       ▼
┌─────────────────────────────────┐
│      glad_twist_mux              │  Priority: stop(100) > teleop(70) > nav(40)
│  ─► /cmd_vel/stop (Bool)        │
└─────────┬───────────────────────┘
          │ /cmd_vel/raw
          ▼
┌─────────────────────────────────┐
│  glad_trajectory_controller     │  Accel/decel ramping
└─────────┬───────────────────────┘
          │ /cmd_vel
          ▼
┌─────────────────────────────────┐
│  glad_motor_controller          │  Inverse kinematics → PWM → serial → ESP32
│  ─► odom (encoder-based)        │
└─────────────────────────────────┘
```

## Combined Launch

The teleop launch file starts all four nodes plus the trajectory and mux as dependencies:

```
ros2 launch glad_teleop teleop_launch.py
```

### Individual launches

```
ros2 launch glad_motor_controller motor_controller.launch.py
ros2 launch glad_trajectory_controller trajectory_controller_launch.py
ros2 launch glad_twist_mux twist_mux_launch.py
ros2 run glad_teleop teleop_node
```

## Dependencies

- ROS 2 (`rclpy`, `launch_ros`)
- `geometry_msgs`, `nav_msgs`, `std_msgs`
- `tf2_ros`
- `pyserial`

## Build

```bash
colcon build --packages-select glad_teleop glad_twist_mux glad_trajectory_controller glad_motor_controller
source install/setup.bash
```
