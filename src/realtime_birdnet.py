import sounddevice as sd
import numpy as np
import tensorflow as tf
from scipy.signal import spectrogram
import time

# Constants
SAMPLE_RATE = 32000
DURATION = 3
MODEL_PATH = "../BirdNET-Lite/model/BirdNET_Lite_Model_FP32.tflite"
LABELS_PATH = "../BirdNET-Lite/model/labels.txt"
CONFIDENCE_THRESHOLD = 0.7

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
    audio = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
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

# 🔁 Real-time loop
while True:
    try:
        audio = capture_audio()
        species, confidence = classify(audio)
        if confidence > CONFIDENCE_THRESHOLD:
            print(f"[{time.strftime('%H:%M:%S')}] Detected: {species} ({confidence:.2f})")
    except Exception as e:
        print(f"Error: {e}")
