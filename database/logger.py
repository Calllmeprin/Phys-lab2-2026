## This module creates logs files when an update to stock is made ##

import os
from datetime import datetime

LOG_FILE = "data/transactions.log"


def log_event(event_type: str, medication: str, remaining: int):
    os.makedirs("data", exist_ok=True)  # <-- auto-create folder

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} | {event_type} | {medication} | Remaining: {remaining}\n"

    with open(LOG_FILE, "a") as f:
        f.write(entry)