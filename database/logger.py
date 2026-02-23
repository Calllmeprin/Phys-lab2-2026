## This module creates logs files when an update to stock is made ##

import os
from datetime import datetime

LOG_FILE = "data/transactions.log"


def log_event(event_type: str, source: str, message: str):
    os.makedirs("data", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} | {event_type} | {source} | {message}\n"

    with open(LOG_FILE, "a") as f:
        f.write(entry)

from datetime import datetime
import os

LOG_FILE = "data/transactions.log"


def log_sess_separator():
    os.makedirs("data", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    separator_line = (
        f"========================== SESSION ENDED {timestamp} ==========================\n"
    )

    with open(LOG_FILE, "a") as f:
        f.write(separator_line)