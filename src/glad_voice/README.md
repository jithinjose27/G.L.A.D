# GLAD Voice

Voice-activated AI assistant for the G.L.A.D robot. Listens for a wake word, streams questions to Google Gemini, and responds aloud via realistic Edge TTS.

## Overview

Runs a ROS 2 node that manages a wake/sleep voice loop:

1. Standby mode — listens for a wake word (`"hey glad"`, `"hello robo"`, etc.).
2. Active mode — captures speech, sends it to Gemini (`gemini-2.5-flash-lite`), and speaks the streamed response.
3. Sleep mode — triggered by `"thank you"`, `"go to sleep"`, `"bye"`, etc.
4. Shutdown — `"shut down system"` exits the node.

## Configuration

### Hardware Auto-Detection

On startup, the node scans:

- **Microphone** — enumerates `speech_recognition` microphone names for `"YM USB Audio Device"` or `"USB Audio"`.
- **Speaker** — runs `aplay -l` to find the USB audio card and builds a `plughw:N,0` ALSA device string.

Falls back to `device_index=None` (default mic) and `"default"` speaker if no USB device is found.

### Wake / Sleep Words

| Mode | Trigger words |
|------|--------------|
| Wake | `"hello robo"`, `"hi robo"`, `"hey robo"`, `"hello glad"`, `"hey glad"`, `"hi glad"`, `"hello dad"`, `"hey dad"`, `"hey lad"`, `"hi lad"` |
| Sleep | `"thank you"`, `"thanks"`, `"stop glad"`, `"go to sleep"`, `"thank you robo"`, `"bye"`, `"thanks robo"`, `"quiet"` |
| Shutdown | `"shut down system"` |

### Microphone Sensitivity

| Parameter | Value | Description |
|-----------|-------|-------------|
| `dynamic_energy_threshold` | `False` | Fixed threshold (no auto-adjustment) |
| `energy_threshold` | `1000` | Minimum volume to trigger (higher = less self-triggering) |
| `pause_threshold` | `1.0` | Seconds of silence before end of phrase |
| `timeout` | `7s` | Wait for speech before giving up |
| `phrase_time_limit` | `15s` | Maximum recording length |

### Gemini Model

| Parameter | Value |
|-----------|-------|
| Model | `gemini-2.5-flash-lite` |
| API key | `GEMINI_API_KEY` env var (fallback hardcoded key for development) |
| System instruction | Respond as "GLAD", a helpful robotics assistant, in 2–3 short conversational sentences without markdown |

Response streaming is used for low-latency output — sentences are yielded to the TTS engine as soon as they are punctuated.

## Audio Pipeline

1. **STT** — Google Speech Recognition via `speech_recognition` (requires internet).
2. **LLM** — Google Gemini AI with streaming response.
3. **TTS** — Microsoft Edge TTS (`edge-tts` CLI with `en-US-AriaNeural` voice) → temp MP3 → `mpg123` plays through USB speaker.

The temp MP3 is deleted immediately after playback to avoid blocking the microphone for the next cycle.

## Launch

```
ros2 run glad_voice voice_assistant
```

No launch file is provided — run directly.

## Dependencies

- ROS 2 (`rclpy`)
- `SpeechRecognition` (Python package)
- `google-genai` (Python package)
- `edge-tts` (Python package / CLI)
- `mpg123` (system package)

## Environment

```bash
export GEMINI_API_KEY="your_api_key_here"
```

## Build

```bash
colcon build --packages-select glad_voice
source install/setup.bash
```
