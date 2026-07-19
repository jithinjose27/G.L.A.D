# GLAD Mapping

ROS 2 mapping package wrapping **slam_toolbox** for laser-based SLAM.

## Overview

Starts a `slam_toolbox` node configured for online mapping. It subscribes to filtered laser scans and odometry, performs scan matching and loop closure via Ceres solver, and publishes an occupancy grid map.

**Topics subscribed:**

| Topic | Type | Description |
|-------|------|-------------|
| `/scan` | `sensor_msgs/LaserScan` | Filtered laser scan (544 beams, front-facing) |
| `/tf` | `tf2_msgs/TFMessage` | Transform tree (`odom → base_link`) |

**Topics published:**

| Topic | Type | Description |
|-------|------|-------------|
| `/map` | `nav_msgs/OccupancyGrid` | Occupancy grid map |
| `/map_metadata` | `nav_msgs/MapMetaData` | Map metadata |
| `/tf` | `tf2_msgs/TFMessage` | Transform `map → odom` |

## Parameters

Full configuration in `config/slam_toolbox.yaml`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `mode` | `mapping` | SLAM mode (mapping / localization) |
| `solver_plugin` | `solver_plugins::CeresSolver` | Scan matching solver |
| `resolution` | `0.05` | Map resolution (m/cell) |
| `map_update_interval` | `2.0` | Seconds between map publications |
| `max_laser_range` | `10.0` | Maximum laser range (m) |
| `min_laser_range` | `0.05` | Minimum laser range (m) |
| `scan_topic` | `/scan` | Input scan topic |
| `do_loop_closing` | `true` | Enable loop closure detection |
| `loop_search_maximum_distance` | `3.0` | Max distance for loop closure search (m) |
| `loop_match_minimum_response_coarse` | `0.35` | Minimum correlation for coarse loop match |
| `loop_match_minimum_response_fine` | `0.45` | Minimum correlation for fine loop match |
| `correlation_search_space_dimension` | `0.5` | Local search window (m) |
| `correlation_search_space_resolution` | `0.01` | Search space resolution (m) |
| `coarse_angle_resolution` | `0.0349` | ~2° coarse angle search step (rad) |
| `fine_search_angle_offset` | `0.00349` | ~0.2° fine angle search step (rad) |
| `transform_timeout` | `0.5` | TF lookup timeout (s) |
| `tf_buffer_duration` | `30.0` | TF buffer duration (s) |
| `scan_buffer_size` | `100` | Number of scans stored for matching |
| `minimum_travel_distance` | `0.05` | Min travel before adding a scan node (m) |
| `minimum_travel_heading` | `0.05` | Min heading change before adding node (rad) |
| `minimum_time_interval` | `0.5` | Min time between scan nodes (s) |
| `map_file_name` | `"my_map"` | Base filename for saving the map |
| `use_map_saver` | `true` | Enable map saver service |
| `enable_interactive_mode` | `true` | Allow interactive mode |

## Launch

```
ros2 launch glad_mapping slam_toolbox_launch.py
```

Starts the `slam_toolbox` node with parameters loaded from `config/slam_toolbox.yaml`.

## Saving a Map

With `use_map_saver: true`, call the map saver service:

```
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "{name: {data: 'my_map'}}"
```

Maps are saved to the current working directory as `my_map.yaml` + `my_map.pgm`.

## Dependencies

- ROS 2 (`rclpy`, `launch_ros`)
- `sensor_msgs`, `nav_msgs`
- `slam_toolbox` (binary, not included in this package)

## Build

```bash
colcon build --packages-select glad_mapping
source install/setup.bash
```
