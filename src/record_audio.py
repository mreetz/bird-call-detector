import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from datetime import datetime

DURATION = 5  # seconds
SAMPLE_RATE = 44100  # samples per second

def record_audio(filename):
    print(f"Recording {DURATION} seconds of audio...")
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    wav.write(filename, SAMPLE_RATE, audio)
    print(f"Saved audio to {filename}")

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recordings/recording_{timestamp}.wav"
    import os
    os.makedirs("recordings", exist_ok=True)
    record_audio(filename)
# This script records audio for a specified duration and saves it to a WAV file.
# It uses the sounddevice library to capture audio and scipy to save it.
# The filename includes a timestamp to ensure uniqueness.
# The script creates a "recordings" directory if it doesn't exist.
# The recording duration and sample rate are defined as constants.
# The script can be run directly to record audio.
# It imports necessary libraries, defines constants, and implements the recording function.
# The script is designed to be run as a standalone program.
