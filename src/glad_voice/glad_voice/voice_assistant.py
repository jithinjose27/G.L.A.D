import rclpy
from rclpy.node import Node
import re
import os
import subprocess
import tempfile
import speech_recognition as sr

# The modern Google GenAI SDK
from google import genai
from google.genai import types


# ------------------------------------------------------------
# 1. HARDWARE AUTO-DETECT
# ------------------------------------------------------------
def find_usb_audio():
    """Automatically finds the correct Microphone and Speaker IDs."""
    mic_idx = None
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        if "YM USB Audio Device" in name or "USB Audio" in name:
            mic_idx = i
            break

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

    return mic_idx, speaker_hw


DETECTED_MIC, DETECTED_SPEAKER = find_usb_audio()

# ------------------------------------------------------------
# 2. CONFIGURATION
# ------------------------------------------------------------


class Config:
    ASSISTANT_NAME = "GLAD"
    MIC_INDEX = DETECTED_MIC
    SPEAKER_HW = DETECTED_SPEAKER

    # ⚠️ PASTE YOUR REAL KEY HERE!
    GEMINI_API_KEY = os.getenv(
        "GEMINI_API_KEY", "AIzaSyA2MNXONtoeuV2oR1g5T8U4ElcWbBhi6f0"
    )
    GEMINI_MODEL_NAME = "gemini-2.5-flash-lite"

    # Wake words and common speech-to-text mishearings
    WAKE_WORDS = [
        "hello robo",
        "hi robo",
        "hey robo",
        "hello glad",
        "hey glad",
        "hi glad",
        "hi robo",
        "hello dad",
        "hey dad",
        "hey lad",
        "hi lad",
    ]

    # Words that put the robot back to sleep
    SLEEP_WORDS = [
        "thank you",
        "thanks",
        "stop glad",
        "go to sleep",
        "thank you robo",
        "bye",
        "thanks robo",
        "quiet",
    ]

    SYSTEM_INSTRUCTION = (
        f"You are {ASSISTANT_NAME}, a helpful robotics assistant. "
        "Keep your responses strictly to 2 or 3 short sentences. "
        "Be concise, direct, and conversational. Do not use markdown, "
        "bullet points, or special formatting."
    )


# ------------------------------------------------------------
# 3. GEMINI AI HANDLER
# ------------------------------------------------------------


def init_gemini():
    """Initialize Google GenAI SDK"""
    if not Config.GEMINI_API_KEY:
        print("\n⚠️ WARNING: API Key is missing.")
        return None

    try:
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        print(f"✓ Gemini ({Config.GEMINI_MODEL_NAME}) connected")
        return client
    except Exception as e:
        print(f"❌ Gemini Init Error: {e}")
        return None


def ask_gemini_stream(client, prompt):
    """Generator that streams Gemini response sentence by sentence."""
    if not prompt:
        return
    if not client:
        yield "My API key is missing."
        return

    print("🤖 Thinking...")
    try:
        response_stream = client.models.generate_content_stream(
            model=Config.GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=Config.SYSTEM_INSTRUCTION,
            ),
        )
        buffer = ""

        for chunk in response_stream:
            if chunk.text:
                buffer += chunk.text
                parts = re.split(r"([.?!:\n]+)", buffer)

                if len(parts) > 2:
                    for i in range(0, len(parts) - 1, 2):
                        sentence = parts[i] + parts[i + 1]
                        clean_sent = sentence.strip()
                        if clean_sent:
                            yield clean_sent
                    buffer = parts[-1]

        if buffer.strip():
            yield buffer.strip()

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            yield "I am receiving too many requests right now. Please give me about one minute to reset."
        else:
            yield "I encountered an unexpected error."
            print(f"❌ Actual Error: {error_msg}")


# ------------------------------------------------------------
# 4. AUDIO IN / OUT
# ------------------------------------------------------------


def speak(text, print_text=True):
    """Generates ultra-realistic human speech using Microsoft Edge TTS."""
    if print_text:
        print(f"🤖 {Config.ASSISTANT_NAME}: {text}")

    clean_text = text.replace("*", "").replace("#", "")
    if not clean_text.strip():
        return

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            temp_mp3 = tmp.name

        # 1. Use Edge-TTS to instantly generate a realistic human voice
        # "en-US-AriaNeural" is a highly realistic female voice similar to Alexa.
        # Want a male voice? Change it to "en-US-ChristopherNeural"
        subprocess.run(
            [
                "edge-tts",
                "--voice",
                "en-US-AriaNeural",
                "--text",
                clean_text,
                "--write-media",
                temp_mp3,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # 2. Play the MP3 file directly through your USB speaker
        subprocess.run(
            ["mpg123", "-a", Config.SPEAKER_HW, "-q", temp_mp3],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # 3. Clean up the file to safely unlock the microphone
        try:
            os.remove(temp_mp3)
        except Exception:
            pass

    except Exception as e:
        print(f"🔊 TTS Error: {e}")


def listen_mic(status_message):
    """Listens to the mic with custom sensitivity to prevent self-triggering."""
    recognizer = sr.Recognizer()

    # --- SENSITIVITY TWEAKS ---
    # 1. Turn OFF dynamic adjustment so it doesn't automatically become super
    # sensitive when the room gets quiet.
    recognizer.dynamic_energy_threshold = False

    # 2. Hardcode the minimum volume required to wake up the mic.
    # Default is 300. We are bumping it up to ignore echoes.
    # (If it won't hear YOU, lower this number. If it still hears ITSELF, raise it).
    recognizer.energy_threshold = 1000

    recognizer.pause_threshold = 1.0

    with sr.Microphone(device_index=Config.MIC_INDEX) as source:
        try:
            # We no longer need it to adjust for ambient noise since we hardcoded it
            print(f"\n🎤 {status_message}")

            audio = recognizer.listen(source, timeout=7, phrase_time_limit=15)

            text = recognizer.recognize_google(audio)
            print(f"👤 User: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"❌ Connection error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


# ------------------------------------------------------------
# 5. ROS 2 NODE LOOP
# ------------------------------------------------------------


class VoiceAssistantNode(Node):
    def __init__(self):
        super().__init__("voice_assistant_node")
        self.get_logger().info(f"🚀 Starting {Config.ASSISTANT_NAME} Q&A Node")
        print(
            f"🔧 Hardware Detected -> Mic Index: {Config.MIC_INDEX} | Speaker ID: {Config.SPEAKER_HW}"
        )

        self.client = init_gemini()
        self.is_awake = False

        if self.client:
            speak("Hello, I'm glad, nice to meet you. Do you guys have any queries?")
            self.run_voice_loop()
        else:
            self.get_logger().error("Shutting down. Check API Key.")

    def run_voice_loop(self):
        """Infinite loop with Wake/Sleep state management."""
        while rclpy.ok():
            try:
                prompt_msg = (
                    "Listening for a question..."
                    if self.is_awake
                    else "Waiting for wake word ..."
                )
                command = listen_mic(prompt_msg)
            except KeyboardInterrupt:
                break

            if not command:
                continue

            if "shut down system" in command:
                speak("Shutting down the system. Goodbye.")
                break

            # --- STANDBY MODE (ASLEEP) ---
            if not self.is_awake:
                if any(wake_word in command for wake_word in Config.WAKE_WORDS):
                    self.is_awake = True
                    speak("I am listening.")
                continue

            # --- ACTIVE MODE (AWAKE) ---
            else:
                if any(sleep_word in command for sleep_word in Config.SLEEP_WORDS):
                    self.is_awake = False
                    speak("Going back to standby.")
                    continue

                clean_command = command
                for wake_word in Config.WAKE_WORDS:
                    clean_command = clean_command.replace(wake_word, "").strip()

                if clean_command:
                    print(f"🤖 {Config.ASSISTANT_NAME}: ", end="", flush=True)
                    for sentence in ask_gemini_stream(self.client, clean_command):
                        print(sentence + " ", end="", flush=True)
                        speak(sentence, print_text=False)
                    print()


def main(args=None):
    rclpy.init(args=args)
    node = VoiceAssistantNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
