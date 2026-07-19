# GLAD Navigation

ROS 2 navigation stack for the G.L.A.D robot based on **Nav2**. Bootstraps the full Nav2 pipeline: AMCL localization, global + local planning, control, behavior recovery, and lifecycle management.

## Overview

This package provides a launch file and parameter configuration that starts all Nav2 core nodes with settings tuned for the G.L.A.D robot platform.

**Nodes launched:**

| Node | Package | Role |
|------|---------|------|
| `glad_navigation_node` | `glad_navigation` | Lightweight wrapper node |
| `map_server` | `nav2_map_server` | Serves a pre-built occupancy grid map |
| `amcl` | `nav2_amcl` | Adaptive Monte Carlo localization |
| `controller_server` | `nav2_controller` | Path following (local control) |
| `planner_server` | `nav2_planner` | Global path planning |
| `behavior_server` | `nav2_behaviors` | Recovery behaviors (spin, backup, etc.) |
| `bt_navigator` | `nav2_bt_navigator` | Behavior-tree-based navigation |
| `lifecycle_manager` | `nav2_lifecycle_manager` | Autostart and lifecycle management |

**Topics:**

| Topic | Direction | Type | Description |
|-------|-----------|------|-------------|
| `/scan` | Subscribed | `sensor_msgs/LaserScan` | Filtered laser scan |
| `/map` | Published | `nav_msgs/OccupancyGrid` | Loaded static map |
| `/odom` | Subscribed | `nav_msgs/Odometry` | Wheel odometry |
| `/cmd_vel/nav` | Published | `geometry_msgs/Twist` | Velocity commands to twist mux (priority 40) |
| `/initialpose` | Subscribed | `geometry_msgs/PoseWithCovarianceStamped` | 2D pose estimate (RViz) |
| `/goal_pose` | Subscribed | `geometry_msgs/PoseStamped` | Navigation goal (RViz) |

## Configuration

All parameters are in `config/glad_nav2_params.yaml`.

### AMCL Localization

| Parameter | Value | Description |
|-----------|-------|-------------|
| `laser_model_type` | `likelihood_field` | Observation model |
| `min_particles` / `max_particles` | 500 / 1500 | Particle filter size |
| `update_min_d` / `update_min_a` | 0.1 m / 0.1 rad | Min travel before filter update |
| `initial_pose` | x: 0, y: 0, yaw: 0 | Default start pose |
| `scan_topic` | `/scan` | Input laser topic |

### Controller — Regulated Pure Pursuit

| Parameter | Value | Description |
|-----------|-------|-------------|
| `controller_frequency` | 20.0 Hz | Control loop rate |
| `desired_linear_vel` | 0.1 m/s | Max forward speed |
| `lookahead_dist` | 0.45 m | Pure pursuit lookahead |
| `min_lookahead_dist` / `max_lookahead_dist` | 0.25 / 0.7 m | Lookahead range |
| `rotate_to_heading_angular_vel` | 0.4 rad/s | In-place rotation speed |
| `allow_reversing` | false | Forward-only motion |
| `use_cost_regulated_linear_velocity_scaling` | true | Slow down near obstacles |
| `xy_goal_tolerance` / `yaw_goal_tolerance` | 0.30 m / 0.30 rad | Goal acceptance |

### Planner — NavFN

| Parameter | Value | Description |
|-----------|-------|-------------|
| `planner_plugin` | `nav2_navfn_planner/NavfnPlanner` | Global planner |
| `use_astar` | true | A* search algorithm |
| `tolerance` | 0.5 m | Search tolerance near obstacles |

### Costmaps

| Layer | Inflation Radius | Cost Scaling |
|-------|-----------------|-------------|
| Obstacle | — | — |
| Inflation | 0.30 m | 3.0 |

**Local costmap** — 5×5 m rolling window at 0.05 m resolution, in `odom` frame.

**Global costmap** — Full static map in `map` frame.

**Footprint:** `0.25 × 0.25 m` square.

### Recovery Behaviors

| Behavior | Plugin |
|----------|--------|
| Spin | `nav2_behaviors/Spin` |
| Backup | `nav2_behaviors/BackUp` |
| Drive on heading | `nav2_behaviors/DriveOnHeading` |
| Wait | `nav2_behaviors/Wait` |

### Behavior Tree Navigator

- Supports `navigate_to_pose` and `navigate_through_poses`.
- Default server timeout: 20 s.

## Launch

```
ros2 launch glad_navigation glad_nav2_launch.py map:=/path/to/map.yaml
```

The `map` argument is required — pass the full path to a YAML map file (produced by slam_toolbox or `nav2_map_server` map_saver).

## Usage

1. Launch the navigation stack with a map file.
2. Set the initial pose estimate in RViz (2D Pose Estimate).
3. Send a navigation goal (2D Nav Goal) or call the `/navigate_to_pose` action.

The controller publishes velocity commands to `/cmd_vel/nav`, which enters the twist multiplexer at priority 40 (below teleop, above idle).

## Dependencies

- ROS 2 (`rclpy`, `launch_ros`)
- `navigation2` (all Nav2 packages)
- `nav2_msgs`
- `nav2_map_server`, `nav2_amcl`, `nav2_controller`, `nav2_planner`, `nav2_behaviors`, `nav2_bt_navigator`, `nav2_lifecycle_manager`

## Build

```bash
colcon build --packages-select glad_navigation
source install/setup.bash
```
