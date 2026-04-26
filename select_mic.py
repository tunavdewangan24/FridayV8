from audio_utils import print_devices, recommended_device, save_config

print("FRIDAY V5 - Microphone Selector")
print("=" * 55)
print("Detected input devices:")
devices = print_devices(show_tips=True)
if not devices:
    print("No input devices found.")
    raise SystemExit(1)

rec = recommended_device()
default_id = rec["id"] if rec else devices[0]["id"]
choice = input(f"Enter microphone number, or press Enter for [{default_id}]: ").strip()
if choice == "":
    device_id = default_id
else:
    try:
        device_id = int(choice)
    except ValueError:
        print("Invalid number.")
        raise SystemExit(1)

selected = next((d for d in devices if d["id"] == device_id), None)
if not selected:
    print("That device number was not found.")
    raise SystemExit(1)

save_config(selected["id"], selected["rate"])
print(f"Saved microphone: [{selected['id']}] {selected['name']} at {selected['rate']} Hz")
print("Now run MIC_TEST, then START_FRIDAY.")
