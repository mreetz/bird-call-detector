import sounddevice as sd

YOUR_DEVICE_INDEX = 0  # Replace with your device index as output from teh test_microphones.py script

for rate in [8000, 16000, 22050, 24000, 32000, 44100, 48000, 96000]:
    try:
        sd.check_input_settings(device=YOUR_DEVICE_INDEX, samplerate=rate)
        print(f"? Works: {rate} Hz")
    except Exception as e:
        print(f"? {rate} Hz not supported - {e}")
