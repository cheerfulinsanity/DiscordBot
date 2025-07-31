# bot/config.py

import json
import os

# Correct path to config.json in /data/
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'config.json')

with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)
