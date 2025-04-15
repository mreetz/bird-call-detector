import csv
import os
import time
import sounddevice as sd
import numpy as np
import tensorflow as tf
from scipy.signal import spectrogram
from scipy.signal import resample

# Constants
SAMPLE_RATE = 16000 # Sample rate in Hz; my mic cannot do 32000
DEVICE_INDEX = 0 # Device index for the microphone; change if needed
DURATION = 3
MODEL_PATH = "../../BirdNET-Lite/model/BirdNET_Lite_Model_FP32.tflite"
LABELS_PATH = "../../BirdNET-Lite/model/labels.txt"
CONFIDENCE_THRESHOLD = 0.7
CSV_FILE = "detectons.csv"

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load labels
with open(LABELS_PATH, "r") as f:
    labels = [line.strip() for line in f.readlines()]

def capture_audio():
    print("Recording...")
    audio = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=DEVICE_INDEX)
    sd.wait()
    return np.squeeze(audio)

def preprocess(audio):
    # Spectrogram like BirdNET
    f, t, Sxx = spectrogram(audio, fs=SAMPLE_RATE, nperseg=512, noverlap=384, detrend=False)
    Sxx = np.log10(Sxx + 1e-10)
    Sxx = np.expand_dims(Sxx, axis=0)  # (1, height, width)
    Sxx = np.expand_dims(Sxx, axis=-1)  # (1, height, width, 1)
    return Sxx.astype(np.float32)

def classify(audio_array):
    input_tensor = preprocess(audio_array)
    interpreter.set_tensor(input_details[0]['index'], input_tensor)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])[0]  # probabilities
    top_idx = np.argmax(output_data)
    top_conf = output_data[top_idx]
    species = labels[top_idx]
    return species, top_conf

def upsample_audio(audio, original_rate=16000, target_rate=32000):
    # Resample audio to target rate
    duration = len(audio) / original_rate
    num_samples = int(duration * target_rate)
    return resample(audio, num_samples).astype(np.int16)

# csv file setup (later we will replace this with a database, but I want to run it and anaylze the data first to understand 
# the load and shapes of the data to better do pre-processing)
write_header = not os.path.exists(CSV_FILE)

csv_file = open(CSV_FILE, "a", newline="")
csv_writer = csv.writer(csv_file)

if write_header:
        csv_writer.writerow(["timestamp", "species", "confidence"])
    
    # 🔁 Real-time loop
try:
    while True:
        raw_audio = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=DEVICE_INDEX)
        audio = upsample_audio(raw_audio, 16000,32000)
        sd.wait()
        audio = np.squeeze(audio)

        # Preprocess
        f, t, Sxx = spectrogram(audio, fs=SAMPLE_RATE, nperseg=512, noverlap=384, detrend=False)
        Sxx = np.log10(Sxx + 1e-10)
        Sxx = np.expand_dims(Sxx, axis=(0, -1)).astype(np.float32)

        # Inference
        interpreter.set_tensor(input_details[0]['index'], Sxx)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])[0]
        top_idx = np.argmax(output_data)
        confidence = output_data[top_idx]
        species = labels[top_idx]

        # Log if confident enough
        if confidence > CONFIDENCE_THRESHOLD
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Detected: {species} ({confidence:.2f})")
            csv_writer.writerow([timestamp, species, round(confidence, 4)])
            csv_file.flush()
except KeyboardInterrupt:
    print("\nStopping detection...")
finally:
    csv_file.close()
    print("CSV file closed.")

