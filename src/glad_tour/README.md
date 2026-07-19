# GLAD Tour

Autonomous tour guide package for the G.L.A.D robot. Navigates a predefined set of waypoints and delivers AI-generated spoken commentary at each stop via Google Gemini and text-to-speech.

## Overview

The robot follows a route through three lab locations, stopping at each to deliver a verbal introduction generated on the fly by a language model. The tour script uses `nav2_simple_commander` for navigation and `gTTS` (Google Text-to-Speech) for audio playback through a USB speaker.

## Tour Waypoints

| Stop | Name | X (m) | Y (m) | Orientation (w) | Description |
|------|------|-------|-------|-----------------|-------------|
| 1 | Point 1 | 3.44 | 0.595 | 0.348 | Programming Lab — greet guests and describe the lab |
| 2 | Point 2 | 3.17 | 3.66 | 0.221 | Robotics Lab — describe the lab and KUKA robot |
| 3 | Point 3 | 3.60 | 0.452 | 0.119 | Automation Lab — explain pneumatic and hydraulic systems |

Each waypoint has a custom prompt sent to Gemini. The LLM's 2–3 sentence response is spoken aloud via the USB speaker.

## How It Works

1. Initializes Gemini client (model `gemini-2.5-flash-lite`).
2. Creates a `BasicNavigator` and sets the initial pose (0, 0).
3. Waits for Nav2 to become active (`waitUntilNav2Active`).
4. For each waypoint:
   - Sends a `goToPose` navigation goal.
   - Blocks until the task completes.
   - On success: sends the waypoint's prompt to Gemini, generates speech via `gTTS`, and plays it through the USB speaker.
   - On failure: speaks an apology and stops the tour.
5. Shuts down after the last waypoint.

## Audio Output

- Automatically detects a USB audio device via `aplay -l` (looks for `YM USB Audio Device` or `USB Audio`).
- Falls back to `default` ALSA device if no USB speaker is found.
- Speech generated with `gTTS` (Google's cloud TTS, requires internet), saved to a temp MP3, and played with `mpg123`.

## LLM Integration

- **Model:** `gemini-2.5-flash-lite` (fast, low-cost)
- **API key:** Read from `GEMINI_API_KEY` environment variable, with a hardcoded fallback (development only).
- **System instruction:** Guides the model to respond as a helpful, professional tour guide robot named G.L.A.D. in 2–3 short sentences without markdown.
- **Temperature:** 0.7 (balanced creativity/determinism).

If the API key is missing or the call fails, the robot falls back to a canned apology message.

## Launch

```
ros2 launch glad_tour glad_tour_launch.py
```

## Dependencies

- ROS 2 (`rclpy`, `launch_ros`)
- `nav2_simple_commander`
- `gTTS` (Python package)
- `mpg123` (system package for MP3 playback)
- `google-genai` (Python package for Gemini API)

## Environment Setup

```bash
export GEMINI_API_KEY="your_api_key_here"
```

## Build

```bash
colcon build --packages-select glad_tour
source install/setup.bash
```
