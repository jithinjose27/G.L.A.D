#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
from gtts import gTTS
import os
import subprocess
import tempfile
import re

# The modern Google GenAI SDK
from google import genai
from google.genai import types


# ------------------------------------------------------------
# 1. HARDWARE AUTO-DETECT FOR SPEAKER
# ------------------------------------------------------------
def find_usb_speaker():
    speaker_hw = "default"
    try:
        out = subprocess.check_output(["aplay", "-l"]).decode()
        for line in out.split("\n"):
            if "card" in line.lower() and (
                "YM USB Audio Device" in line or "USB Audio" in line
            ):
                card_num = re.search(r"card (\d+)", line).group(1)
                speaker_hw = f"plughw:{card_num},0"
                break
    except Exception:
        pass
    return speaker_hw


SPEAKER_HW = find_usb_speaker()

# ------------------------------------------------------------
# 2. GEMINI AI INITIALIZATION & GENERATION
# ------------------------------------------------------------
# ⚠️ PASTE YOUR REAL API KEY HERE!
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA2MNXONtoeuV2oR1g5T8U4ElcWbBhi6f0")
GEMINI_MODEL_NAME = "gemini-2.5-flash-lite"

# Tell Gemini exactly who it is so it stays in character
SYSTEM_INSTRUCTION = (
    "You are G.L.A.D. (Guide Lab Assistant Droid), a helpful and intelligent "
    "autonomous tour guide robot working in the Robotics and Automation department. "
    "Keep your responses strictly to 2 or 3 short sentences. Be conversational, "
    "welcoming, and professional. Do not use asterisks or markdown."
)


def init_gemini():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        print("\n⚠️ WARNING: API Key is missing. I will not be able to speak!")
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"✓ Gemini ({GEMINI_MODEL_NAME}) connected successfully.")
        return client
    except Exception as e:
        print(f"❌ Gemini Init Error: {e}")
        return None


def generate_speech(client, prompt):
    """Pings Gemini to write a custom speech on the spot."""
    if not client:
        return "I am sorry, my AI brain is disconnected."

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,  # Slight creativity so it sounds different each time
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini Generation Error: {e}")
        return "I apologize, I am having trouble connecting to my knowledge base right now."


# ------------------------------------------------------------
# 3. TEXT-TO-SPEECH FUNCTION
# ------------------------------------------------------------
def speak(text):
    """Generates an MP3 from text and plays it out loud."""
    print(f"\n🤖 G.L.A.D.: {text}\n")
    clean_text = text.replace("*", "").replace("#", "")
    if not clean_text.strip():
        return

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            temp_mp3 = tmp.name

        tts = gTTS(text=clean_text, lang="en", slow=False)
        tts.save(temp_mp3)

        subprocess.run(
            ["mpg123", "-a", SPEAKER_HW, "-q", temp_mp3],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            os.remove(temp_mp3)
        except Exception:
            pass
    except Exception as e:
        print(f"🔊 TTS Error: {e}")


# ------------------------------------------------------------
# 4. MAIN NAVIGATION TOUR
# ------------------------------------------------------------
def main():
    rclpy.init()

    print("Waking up AI Brain...")
    gemini_client = init_gemini()

    navigator = BasicNavigator()

    # --- AUTO-INITIALIZE STARTING POSITION ---
    print("Setting initial pose...")
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = "map"
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()

    # Change these to the exact X and Y coordinates of G.L.A.D.'s charging dock / start point
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.w = 1.0

    navigator.setInitialPose(initial_pose)
    # -----------------------------------------

    print("Waiting for Nav2 to become active...")
    navigator.waitUntilNav2Active()

    speak("Navigation systems are online. Let's begin the tour.")

    # Waypoints with AI Prompts instead of hardcoded text!
    waypoints = [
        {
            "name": "Point 1",
            "x": 3.44,
            "y": 0.595,
            "w": 0.348,
            "prompt": "We have just arrived at the programming Lab. Greet the guests and give a brief overview of programming lab.",
        },
        {
            "name": "Point 2",
            "x": 3.17,
            "y": 3.66,
            "w": 0.221,
            "prompt": "Next this is our main robotics Lab. Greet the guests and give a brief overview of robotics lab and the kuka robot present inside the lab.",
        },
        {
            "name": "Point 3",
            "x": 3.6,
            "y": 0.452,
            "w": 0.1192,
            "prompt": "This is our final destination and our Automation Lab. Briefly explain about pneumatic system and hydraulic system that we have on our automation lab.",
        },
    ]

    for point in waypoints:
        print(f"Driving to {point['name']} (x: {point['x']}, y: {point['y']})...")

        goal_pose = PoseStamped()
        goal_pose.header.frame_id = "map"
        goal_pose.header.stamp = navigator.get_clock().now().to_msg()

        goal_pose.pose.position.x = point["x"]
        goal_pose.pose.position.y = point["y"]
        goal_pose.pose.position.z = 0.0

        goal_pose.pose.orientation.x = 0.0
        goal_pose.pose.orientation.y = 0.0
        goal_pose.pose.orientation.z = 0.0
        goal_pose.pose.orientation.w = point["w"]

        navigator.goToPose(goal_pose)

        while not navigator.isTaskComplete():
            pass  # Robot is driving...

        result = navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            print(f"Successfully arrived at {point['name']}!")

            # 1. Ask Gemini to generate the speech in real-time
            print("🤖 Generating speech...")
            generated_speech = generate_speech(gemini_client, point["prompt"])

            # 2. Speak the AI-generated text
            speak(generated_speech)

        elif result == TaskResult.FAILED:
            print(f"Failed to reach {point['name']}!")
            speak(
                "I am sorry, my path is blocked. I cannot reach the next destination."
            )
            break

    print("Tour completed! Shutting down brain.")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
