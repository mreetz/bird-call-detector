# test_microphones.py
# Script to help identify audio input devices and their supported sample rates on Raspberry Pi

import sounddevice as sd

TARGET_SAMPLE_RATE = 32000

print("\n🎙 Available Audio Input Devices:")
input_devices = [dev for dev in sd.query_devices() if dev['max_input_channels'] > 0]

for i, dev in enumerate(input_devices):
    print(f"\n[{i}] {dev['name']} (Index: {dev['index']})")
    try:
        sd.check_input_settings(device=dev['index'], samplerate=TARGET_SAMPLE_RATE)
        print(f"  ✅ Supports {TARGET_SAMPLE_RATE} Hz")
    except Exception as e:
        print(f"  ❌ Does NOT support {TARGET_SAMPLE_RATE} Hz")
        print(f"     Reason: {e}")

print("\nTo use a different device in your main script:")
print("- Set DEVICE_INDEX = <Index shown above>")
print("- Set RAW_SAMPLE_RATE = 32000 if your device supports it")
print("- If not, leave RAW_SAMPLE_RATE at 16000 and keep upsampling enabled")

print("\nTip: You can run a short recording test with:")
print("  import sounddevice as sd")
print("  sd.rec(int(3 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, device=DEVICE_INDEX)")
