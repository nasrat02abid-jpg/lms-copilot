import sounddevice as sd
import speech_recognition as sr
from scipy.io.wavfile import write
import tempfile
import os
import subprocess

recognizer = sr.Recognizer()

SAMPLE_RATE = 16000
RECORD_SECONDS = 6


def speak(text):
    print(f"\n🤖 LMS Copilot: {text}")

    subprocess.run([
        "say",
        text
    ])


def listen():
    print("\n🎤 Listening...")

    try:
        recording = sd.rec(
            int(RECORD_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        print("🔄 Understanding...")

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp_file:
            temp_path = temp_file.name

        write(
            temp_path,
            SAMPLE_RATE,
            recording
        )

        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)

        os.remove(temp_path)

        command = recognizer.recognize_google(
            audio
        )

        print(f"🧑 You: {command}")

        return command

    except sr.UnknownValueError:
        speak("Sorry, I could not understand you.")
        return None

    except sr.RequestError:
        speak(
            "Speech recognition service is unavailable."
        )
        return None

    except Exception as error:
        print(f"\n❌ Voice error: {error}")
        return None