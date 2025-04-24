# BirdNET Raspberry Pi Realtime Detection Setup

This project sets up a 24/7 bird call detection system using the BirdNET-Analyzer, a Raspberry Pi, and a connected microphone. It runs as a systemd service and logs bird detections to a MariaDB or SQLite database.

---

## 📦 Installation Overview

### 1. Clone and Navigate to the Project Directory

```bash
cd /home/<YOUR USERNAME>
mkdir birdnet
cd birdnet
```

> Place your `birdnet_realtime.py` script here.

---

### 2. Create and Activate a Python Virtual Environment

```bash
python3 -m venv ~/venv
source ~/venv/bin/activate
```

---

### 3. Install Required Python Packages

```bash
pip install sounddevice soundfile numpy scipy mariadb birdnetlib
```

> For SQLite setup, omit `mariadb` and ensure `sqlite3` (built-in with Python) is available.

---

### 4. Create a RAM Disk for Temporary Audio

```bash
sudo mkdir -p /mnt/ramdisk
sudo mount -t tmpfs -o size=128m tmpfs /mnt/ramdisk
```

To make this persistent, add to `/etc/fstab`:

```ini
tmpfs   /mnt/ramdisk   tmpfs   defaults,size=128m,noatime,nosuid,nodev   0   0
```

---

### 5. Configure `birdnet_realtime.py`

Update this section of the script:

```python
RAW_SAMPLE_RATE = 48000  # or what your microphone supports
DEVICE_INDEX = 0  # use test_microphones.py to determine this
DEBUG = False  # set to True for debug WAV capture
```

Update the database connection in db_config.py

#### For Remote MariaDB:
```python
MYSQL_CONFIG = {
    'host': '<HOSTNAME OR IP>',
    'user': '<DATABASE USER WITH PERMISSIONS TO THE DATABASE>',
    'password': '<DATABASE PASSWORD FOR user>',
    'database': '<NAME OF THE DATABASE>',
    'port': 3306
}
```

#### Alternate: Use SQLite Instead of MariaDB

Replace the `log_detection()` and `summarize_daily_counts()` functions in the script with versions that use `sqlite3`:

```python
import sqlite3

DB_FILE = "birdnet_local.db"

def log_detection(timestamp, species, confidence, audio_file):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        species TEXT,
        confidence REAL,
        audio_file TEXT
    )''')
    cursor.execute("INSERT INTO detections (timestamp, species, confidence, audio_file) VALUES (?, ?, ?, ?)",
                   (timestamp, species, confidence, audio_file))
    conn.commit()
    conn.close()


def summarize_daily_counts():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        summary_date TEXT,
        species TEXT,
        count INTEGER
    )''')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    cursor.execute("DELETE FROM daily_summary WHERE summary_date = ?", (yesterday,))
    cursor.execute("""
        INSERT INTO daily_summary (summary_date, species, count)
        SELECT DATE(timestamp), species, COUNT(*)
        FROM detections
        WHERE DATE(timestamp) = ?
        GROUP BY species
    """, (yesterday,))
    conn.commit()
    conn.close()
```

---

### 6. Set Up `systemd` Service

Create the service file:

```bash
sudo vi /etc/systemd/system/birdnet.service
```

Paste and customize:

```ini
[Unit]
Description=BirdNET Realtime Detection Service
After=network.target sound.target

[Service]
ExecStart=/home/<YOUR USERNAME>/venv/bin/python /home/<YOUR USERNAME>/birdnet/birdnet_realtime.py
WorkingDirectory=/home/<YOURU USERNAME>/birdnet
StandardOutput=journal
StandardError=journal
Restart=always
RestartSec=5
User=mreetz

[Install]
WantedBy=multi-user.target
```

Reload and enable:

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable birdnet.service
sudo systemctl start birdnet.service
```

View logs:
```bash
journalctl -u birdnet.service -f
```

---

## ✅ Summary

Your Raspberry Pi now:
- Records audio continuously
- Identifies birds via BirdNET-Analyzer
- Logs detections to MariaDB or SQLite
- Cleans up debug audio files
- Summarizes daily counts
- Starts automatically on boot

---

For issues or enhancements (like web dashboard, rare bird alerts, or external APIs), extend from this foundation! 🐦💻
