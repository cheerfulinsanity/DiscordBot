import json
import os

# Path to config.json (assumes it's at the root level of the project)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')

# Load the config file contents
with open(CONFIG_PATH, 'r') as f:
    CONFIG = json.load(f)

