## ======================== IMPORTANT ======================== ##
## This module handles JSON persistence to make sure that the inventory info is not lost upon restarts
## ============================================================ ##

import json
from datetime import date
from .models import Prescriptions, ShelfLocation

INVENTORY_FILE = "data/inventory.json"

def save_inventory(database):
    data = {}

    for name, med in database.inventory.items():
        data[name] = {
            "dosage": med.dosage,
            "expiration_date": med.expiration_date.isoformat(),
            "tablets_per_packets": med.tablets_per_packets,
            "quantity": med.quantity,
            "location": {
                "shelf_id": med.location.shelf_id,
                "x": med.location.x,
                "y": med.location.y
            }
        }

    with open(INVENTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_inventory(database):
    try:
        with open(INVENTORY_FILE, "r") as f:
            data = json.load(f)

        for name, info in data.items():
            database.add_prescription(
                Prescriptions(
                    name=name,
                    dosage=info["dosage"],
                    expiration_date=date.fromisoformat(info["expiration_date"]),
                    tablets_per_packets=info["tablets_per_packets"],
                    quantity=info["quantity"],
                    location=ShelfLocation(**info["location"])
                )
            )
    except FileNotFoundError:
        pass