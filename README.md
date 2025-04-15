# Bird Call Detector

A python-based application that listens for bird calls 24/7 using a Raspberry Pi, identified species, and logs detections to a database

# Setup

1. clone the repo
2. clone the BirdNET-Lite model
    2a. git clone https://github.com/kahst/BirdNET-Lite.git
3. create a virtual environment
```bash
python -m venv venv
source venv/bin/activate
4. install numpy scipy tensorflow
(from within the python venv)
pip install numpy scipy tensorflow 
5. check if package installations were successful
python -c "import numpy; print(numpy.__version__)"
python -c "import tensorflow as tf; proint(tf.__version__)"
6. try to process some sample birdcalls (Note: I needed to install the librosa package:  pip3 install librosa)
cd BirdNET-Lite
mkdir output
python3 analyze.py --i example/"XC558716 - Soundscape.mp3" --o output/results.csv --lat 40.0 --lon -105.0
(check if the file output/results.csv contains valid data.  Should be some 20-odd lines of identified birds identified from the .mp3 file )

