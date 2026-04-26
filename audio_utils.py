import json
import os
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wavfile
import sounddevice as sd
import speech_recognition as sr

CONFIG_FILE = Path("mic_config.json")


def input_devices():
    devices = []
    try:
        all_devices = sd.query_devices()
    except Exception as exc:
        print(f"Could not query devices: {exc}")
        return devices
    for idx, dev in enumerate(all_devices):
        try:
            inputs = int(dev.get("max_input_channels", 0))
            if inputs > 0:
                rate = int(float(dev.get("default_samplerate", 44100) or 44100))
                name = str(dev.get("name", "Unknown"))
                devices.append({"id": idx, "name": name, "inputs": inputs, "rate": rate})
        except Exception:
            continue
    return devices


def is_bad_device_name(name: str) -> bool:
    n = name.lower()
    bad_words = ["stereo mix", "midi", "speaker", "output", "mapper"]
    return any(w in n for w in bad_words)


def score_device(dev: dict) -> int:
    name = dev["name"].lower()
    score = 0
    if "microphone array" in name:
        score += 80
    if "realtek" in name:
        score += 40
    if "microphone" in name:
        score += 30
    if "headset" in name:
        score += 5
    if is_bad_device_name(name):
        score -= 200
    # 44100 is stable for SpeechRecognition on many Windows systems.
    if int(dev.get("rate", 0)) == 44100:
        score += 10
    return score


def recommended_device():
    devices = input_devices()
    if not devices:
        return None
    return sorted(devices, key=score_device, reverse=True)[0]


def save_config(device_id: int, sample_rate: int):
    CONFIG_FILE.write_text(json.dumps({"device_id": int(device_id), "sample_rate": int(sample_rate)}, indent=2), encoding="utf-8")


def load_config():
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return int(data["device_id"]), int(data["sample_rate"])
        except Exception:
            pass
    rec = recommended_device()
    if rec:
        save_config(rec["id"], rec["rate"])
        return rec["id"], rec["rate"]
    return None, 44100


def print_devices(current_id=None, show_tips=True):
    devices = input_devices()
    for dev in devices:
        line = f"[{dev['id']}] {dev['name']} | inputs={dev['inputs']} | rate={dev['rate']}"
        if current_id is not None and dev["id"] == current_id:
            line += "  <-- CURRENT"
        elif score_device(dev) > 100:
            line += "  <-- BEST TRY"
        elif is_bad_device_name(dev["name"]):
            line += "  <-- AVOID"
        print(line)
    if show_tips:
        rec = recommended_device()
        if rec:
            print(f"\nRecommended: [{rec['id']}] {rec['name']}")
        print("Tip: choose Microphone Array / Realtek. Avoid Stereo Mix, MIDI and speaker devices.")
    return devices


def record_wav(filename="mic_test.wav", seconds=5, device_id=None, sample_rate=None):
    if device_id is None or sample_rate is None:
        device_id, sample_rate = load_config()
    if device_id is None:
        raise RuntimeError("No microphone input device found.")

    print(f"Recording {seconds} seconds from device {device_id} at {sample_rate} Hz...")
    audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="float32", device=device_id)
    sd.wait()

    audio = np.asarray(audio).reshape(-1)
    rms = float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0

    clipped = np.clip(audio, -1.0, 1.0)
    int_audio = (clipped * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, int_audio)

    print(f"Saved {filename}")
    print(f"Audio level: RMS={rms:.5f}, PEAK={peak:.5f}")
    if peak < 0.005 or rms < 0.0007:
        print("Result: VERY LOW / SILENT. Wrong mic selected or mic volume is muted.")
    elif peak > 0.98:
        print("Result: TOO LOUD / CLIPPING. Lower microphone volume.")
    else:
        print("Result: Audio level looks OK.")
    return filename, rms, peak


def recognize_wav(filename="mic_test.wav"):
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 250
    recognizer.dynamic_energy_threshold = True
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language="en-IN")
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as exc:
        print(f"Speech recognition internet/API error: {exc}")
        return ""
