"""
Read JSON lines from Serial (ESP32) and POST to local Flask server endpoint /ingest.
Usage: python serial_bridge.py --port COM3 --baud 115200
"""
import argparse
import serial
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--port', required=True)
parser.add_argument('--baud', type=int, default=115200)
parser.add_argument('--url', default='http://localhost:5000/ingest')
args = parser.parse_args()

with serial.Serial(args.port, args.baud, timeout=1) as ser:
    print('Connected to', args.port)
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue
        try:
            r = requests.post(args.url, json={'payload': line})
            print('Posted', line, '->', r.status_code)
        except Exception as e:
            print('Failed to post', e)
