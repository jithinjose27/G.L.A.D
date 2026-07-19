# GLAD Static TF

ROS 2 package that publishes static transforms for the G.L.A.D robot's sensor mount offsets.

## Overview

Broadcasts the fixed poses of the LiDAR and IMU relative to the robot's `base_link` frame. These transforms are published once on startup and remain constant.

## Transforms Published

### `base_link → laser`

| Axis | Offset (m) |
|------|-----------|
| X | 0.10 (forward) |
| Y | 0.00 |
| Z | 0.05 (up) |

Orientation: identity (no rotation).

### `base_link → imu_link`

| Axis | Offset (m) |
|------|-----------|
| X | 0.05 (forward) |
| Y | 0.00 |
| Z | 0.00 |

Orientation: identity (no rotation).

## TF Tree

```
map ──► odom ──► base_link ──┬──► laser
                              └──► imu_link
```

`map → odom` is provided by AMCL (Nav2). `odom → base_link` is provided by the EKF filter or motor odometry. `base_link → laser` and `base_link → imu_link` are provided by this package.

## Launch

```
ros2 launch glad_static_tf glad_static_tf_launch.py
```

Or run directly:

```
ros2 run glad_static_tf static_tf_broadcaster
```

The node publishes both transforms once using `tf2_ros::StaticTransformBroadcaster` and then spins indefinitely to serve them to the TF buffer.

## Build

```bash
colcon build --packages-select glad_static_tf
source install/setup.bash
```
