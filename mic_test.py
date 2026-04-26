from audio_utils import load_config, print_devices, record_wav, recognize_wav

print("FRIDAY V5 microphone test")
print("=" * 55)
device_id, sample_rate = load_config()
print("Using saved mic_config.json. Run SELECT_MIC to change mic.")
print(f"Current device id: {device_id}, sample rate: {sample_rate}")
print("\nInput devices:")
print_devices(current_id=device_id, show_tips=False)
print("\nRecording 5 seconds. Say clearly: hello friday")
record_wav("mic_test.wav", seconds=5, device_id=device_id, sample_rate=sample_rate)
print("\nRecognizing using internet...")
text = recognize_wav("mic_test.wav")
if text:
    print(f"Recognized: {text}")
    print("Mic + speech recognition are working.")
else:
    print("Could not recognize speech.")
    print("Open mic_test.wav and check if your voice is clear. If not, run SELECT_MIC and try another mic.")
