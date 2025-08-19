"""
Simple Flask server to collect incoming feature JSON and visualize basic stats.
Run: python server.py
POST /ingest  accepts JSON {"payload": "<json-line-from-esp32>"}
GET /stats returns simple counts per class
"""
from flask import Flask, request, jsonify
from collections import Counter
import json

app = Flask(__name__)
COUNTS = Counter()
RECENT = []

@app.route('/ingest', methods=['POST'])
def ingest():
    data = request.get_json()
    if not data or 'payload' not in data:
        return 'bad', 400
    try:
        j = json.loads(data['payload'])
    except Exception:
        return 'invalid json', 400
    cls = j.get('class', 'unknown')
    COUNTS[cls] += 1
    RECENT.append(j)
    if len(RECENT) > 200:
        RECENT.pop(0)
    return 'ok', 200

@app.route('/stats')
def stats():
    return jsonify({'counts': dict(COUNTS), 'recent': RECENT[-20:]})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
