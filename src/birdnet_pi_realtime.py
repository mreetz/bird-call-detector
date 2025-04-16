# birdnet_pi_realtime.py
# Real-time bird detection using BirdNET-Analyzer with MySQL logging and debug cleanup
#
# UPDATE all UPDATE_ME fields before running

import os
import time
import sounddevice as sd
import numpy as np
import soundfile as sf
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from datetime import datetime, timedelta
import csv
from scipy.signal import resample
import mariadb

# ================================
# CONFIGURATION
# ================================
RAW_SAMPLE_RATE = 16000
TARGET_SAMPLE_RATE = 32000
DURATION = 3.0
DEVICE_INDEX = 0
CONFIDENCE_THRESHOLD = 0.7
LATITUDE = 40.0
LONGITUDE = -105.0
DEBUG = True
CSV_LOG = "detections.csv"
DEBUG_AUDIO_DIR = "/mnt/ramdisk/debug_audio"
RAMDISK_WARNING_THRESHOLD_MB = 100

# MariaDB configuration
MYSQL_CONFIG = {
    'host': '192.168.86.240',
    'user': 'birdnet_user',
    'password': 'UPDATE_ME',
    'database': 'birdcall',
    'port': 3307
}

# ================================
# SETUP
# ================================
os.makedirs(DEBUG_AUDIO_DIR, exist_ok=True)
write_header = not os.path.exists(CSV_LOG)
csv_file = open(CSV_LOG, mode='a', newline='')
csv_writer = csv.writer(csv_file)
if write_header:
    csv_writer.writerow(["timestamp", "species", "confidence", "audio_file"])

print("Loading BirdNET-Analyzer...")
analyzer = Analyzer()
print("Analyzer ready.")

# ================================
# FUNCTIONS
# ================================
def record_audio():
    print("\nRecording audio...")
    audio = sd.rec(int(RAW_SAMPLE_RATE * DURATION), samplerate=RAW_SAMPLE_RATE, channels=1, dtype='int16', device=DEVICE_INDEX)
    sd.wait()
    return np.squeeze(audio)

def upsample_audio(audio_data):
    num_samples = int(DURATION * TARGET_SAMPLE_RATE)
    return resample(audio_data, num_samples).astype(np.int16)

def save_debug_audio(audio_data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(DEBUG_AUDIO_DIR, f"debug_{timestamp}.wav")
    sf.write(filename, audio_data, TARGET_SAMPLE_RATE, subtype='PCM_16')
    return filename

def analyze_audio_file(file_path):
    recording = Recording(
        analyzer,
        file_path,
        lat=LATITUDE,
        lon=LONGITUDE,
        date=datetime.now(),
        min_conf=CONFIDENCE_THRESHOLD
    )
    recording.analyze()
    return recording.detections

def log_detection(timestamp, species, confidence, audio_file):
    csv_writer.writerow([timestamp, species, round(confidence, 4), audio_file])
    csv_file.flush()
    try:
        conn = mariadb.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO detections (timestamp, species, confidence)
            VALUES (%s, %s, %s)
            """,
            (timestamp, species, confidence)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except mariadb.Error as err:
        print(f"MySQL error: {err}")

def summarize_daily_counts():
    try:
        conn = mariadb.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO daily_summary (summary_date, species, count)
            SELECT DATE(timestamp), species, COUNT(*)
            FROM detections
            WHERE DATE(timestamp) = %s
            GROUP BY species
        """, (yesterday,))
        conn.commit()
        cursor.close()
        conn.close()
        print("[Summary] Daily summary inserted.")
    except mariadb.Error as err:
        print(f"MySQL summary error: {err}")

def cleanup_debug_audio(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def get_dir_size_mb(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)

def enforce_ramdisk_limit():
    usage_mb = get_dir_size_mb(DEBUG_AUDIO_DIR)
    if usage_mb > RAMDISK_WARNING_THRESHOLD_MB:
        print(f"[Warning] RAM disk usage high: {usage_mb:.1f}MB. Cleaning up oldest files...")
        files = sorted(
            [os.path.join(DEBUG_AUDIO_DIR, f) for f in os.listdir(DEBUG_AUDIO_DIR)],
            key=os.path.getctime
        )
        while get_dir_size_mb(DEBUG_AUDIO_DIR) > RAMDISK_WARNING_THRESHOLD_MB * 0.8 and files:
            oldest = files.pop(0)
            os.remove(oldest)
            print(f"Removed {oldest} to free space.")

# ================================
# MAIN LOOP
# ================================
try:
    print("Starting real-time bird detection... Press Ctrl+C to stop.")
    last_summary_date = datetime.now().date()
    while True:
        try:
            enforce_ramdisk_limit()

            # 1. Record audio
            raw_audio = record_audio()

            # 2. Resample to 32kHz
            upsampled_audio = upsample_audio(raw_audio)

            # 3. Save debug audio if enabled
            debug_audio_path = save_debug_audio(upsampled_audio) if DEBUG else ""

            # 4. Analyze audio file
            detections = analyze_audio_file(debug_audio_path)

            # 5. Log and print detections
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if detections:
                for detection in detections:
                    species = detection['common_name']
                    confidence = detection['confidence']
                    print(f"[{timestamp}] Detected: {species} ({confidence:.2f})")
                    log_detection(timestamp, species, confidence, debug_audio_path if DEBUG else "")
            else:
                if DEBUG and debug_audio_path:
                    cleanup_debug_audio(debug_audio_path)

            # 6. Run daily summarization once per day
            today = datetime.now().date()
            if today != last_summary_date:
                summarize_daily_counts()
                last_summary_date = today

        except Exception as e:
            print(f"Error during detection: {e}")
            time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping real-time detection...")

finally:
    csv_file.close()
    print("CSV log closed.")
