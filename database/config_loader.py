import json
import os

CONFIG_FILE = "config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError("config.json not found in project root.")

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)