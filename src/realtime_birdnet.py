import sounddevice as sd
import numpy as np
import tensorflow as tf
from scipy.signal import spectrogram, resample
from scipy.ndimage import zoom
from scipy.io.wavfile import write as wav
import time
import csv
import os

# Configuration
RAW_SAMPLE_RATE = 16000          # Your mic's sample rate
TARGET_SAMPLE_RATE = 32000       # BirdNET model expects 32kHz
DURATION = 3                     # Duration of each audio capture in seconds
DEVICE_INDEX = 0                 # Your confirmed mic index
MODEL_PATH = "../BirdNET-Lite/model/BirdNET_6K_GLOBAL_MODEL.tflite"
LABELS_PATH = "./BirdNET-Litemodel/labels.txt"
CONFIDENCE_THRESHOLD = 0.7
CSV_FILE = "detections.csv"

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
model_input_shape = input_details[0]['shape']  # Expected model input shape

# Load species labels
with open(LABELS_PATH, "r") as f:
    labels = [line.strip() for line in f.readlines()]

def capture_audio():
    print("Recording...")
    audio = sd.rec(
        int(RAW_SAMPLE_RATE * DURATION),
        samplerate=RAW_SAMPLE_RATE,
        channels=1,
        dtype='int16',
        device=DEVICE_INDEX
    )
    sd.wait()
    # optionally save the audio to a file for debugging
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"recordings/recording_{timestamp}.wav"
    wav.write(filename, RAW_SAMPLE_RATE, audio)
    return np.squeeze(audio)

def upsample_audio(audio):
    duration = len(audio) / RAW_SAMPLE_RATE
    num_samples = int(duration * TARGET_SAMPLE_RATE)
    return resample(audio, num_samples).astype(np.int16)

def preprocess(audio):
    f, t, Sxx = spectrogram(audio, fs=TARGET_SAMPLE_RATE, nperseg=512, noverlap=384, detrend=False)
    Sxx = np.log10(Sxx + 1e-10)

    # Resize to model's expected shape
    if len(model_input_shape) == 3:
        resized = zoom(Sxx, (
            model_input_shape[1] / Sxx.shape[0],
            model_input_shape[2] / Sxx.shape[1]
        ))
        return np.expand_dims(resized.astype(np.float32), axis=0)
    elif len(model_input_shape) == 2:
        resized = zoom(Sxx, (
            model_input_shape[0] / Sxx.shape[0],
            model_input_shape[1] / Sxx.shape[1]
        ))
        return resized.astype(np.float32)
    else:
        raise ValueError(f"Unsupported model input shape: {model_input_shape}")

# Prepare CSV logging
write_header = not os.path.exists(CSV_FILE)
csv_file = open(CSV_FILE, mode='a', newline='')
csv_writer = csv.writer(csv_file)
if write_header:
    csv_writer.writerow(["timestamp", "species", "confidence"])

# Main loop
try:
    while True:
        raw_audio = capture_audio()
        upsampled_audio = upsample_audio(raw_audio)
        input_tensor = preprocess(upsampled_audio)

        interpreter.set_tensor(input_details[0]['index'], input_tensor)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])[0]

        top_idx = np.argmax(output_data)
        confidence = output_data[top_idx]
        species = labels[top_idx]

        if confidence > CONFIDENCE_THRESHOLD:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Detected: {species} ({confidence:.2f})")
            csv_writer.writerow([timestamp, species, round(confidence, 4)])
            csv_file.flush()
except KeyboardInterrupt:
    print("\nStopping detection...")
finally:
    csv_file.close()
    print("CSV file closed.")
