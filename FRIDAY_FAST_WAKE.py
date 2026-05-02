import os
import json
import time
import subprocess
import threading
from pathlib import Path

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import pyaudio
    import audioop
except Exception:
    pyaudio = None
    audioop = None


APP = Path(os.getenv("APPDATA") or Path.home()) / "FridayFast"
MIC_FILE = APP / "mic.json"
VOICE_BAT = r"C:\FridayV8\START_FRIDAY_FAST_VOICE.bat"


def load_mic():
    if not MIC_FILE.exists():
        return None
    try:
        data = json.loads(MIC_FILE.read_text(encoding="utf-8"))
        idx = data.get("mic")
        return None if idx in ("", None, "default") else int(idx)
    except Exception:
        return None


def launch_friday_voice():
    print("Launching Friday Fast Voice Mode...")
    subprocess.Popen(["cmd", "/c", "start", "Friday Fast Voice", VOICE_BAT], shell=True)


def voice_wake_loop():
    if sr is None:
        print("SpeechRecognition missing. Install with:")
        print("python -m pip install SpeechRecognition pyaudio")
        return

    recognizer = sr.Recognizer()
    cooldown_until = 0

    while True:
        try:
            if time.time() < cooldown_until:
                time.sleep(1)
                continue

            mic_index = load_mic()
            with sr.Microphone(device_index=mic_index) as source:
                print("Wake listener: say 'hello friday'")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=3)

            text = recognizer.recognize_google(audio, language="en-IN").lower()
            print("Heard:", text)

            if "hello friday" in text or "hey friday" in text:
                launch_friday_voice()
                cooldown_until = time.time() + 10

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print("Voice wake error:", e)
            print("If this repeats, run FRIDAY_FAST_MODE.py -> option 3 and select mic 2 or 28.")
            time.sleep(3)


def clap_wake_loop():
    if pyaudio is None or audioop is None:
        print("PyAudio/audioop missing. Double clap disabled.")
        return

    chunk = 1024
    rate = 44100
    threshold = 16000
    clap_window = 0.85
    cooldown_until = 0

    try:
        mic_index = load_mic()
        pa = pyaudio.PyAudio()
        kwargs = {
            "format": pyaudio.paInt16,
            "channels": 1,
            "rate": rate,
            "input": True,
            "frames_per_buffer": chunk,
        }
        if mic_index is not None:
            kwargs["input_device_index"] = mic_index

        stream = pa.open(**kwargs)
    except Exception as e:
        print("Could not start clap listener:", e)
        print("Double clap disabled. Voice wake may still work.")
        return

    last_clap = 0
    print("Double clap listener active.")

    while True:
        try:
            if time.time() < cooldown_until:
                time.sleep(1)
                continue

            data = stream.read(chunk, exception_on_overflow=False)
            rms = audioop.rms(data, 2)

            if rms > threshold:
                now = time.time()
                if now - last_clap < clap_window:
                    print("Double clap detected.")
                    launch_friday_voice()
                    cooldown_until = time.time() + 10
                    last_clap = 0
                else:
                    last_clap = now

            time.sleep(0.03)

        except Exception as e:
            print("Clap error:", e)
            time.sleep(2)


def main():
    print("==========================================")
    print("FRIDAY FAST WAKE LISTENER")
    print("Say: hello friday")
    print("Or: double clap")
    print("Keep this window open.")
    print("==========================================")

    t1 = threading.Thread(target=voice_wake_loop, daemon=True)
    t2 = threading.Thread(target=clap_wake_loop, daemon=True)

    t1.start()
    t2.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
