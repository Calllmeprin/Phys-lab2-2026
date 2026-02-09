# This file is a DB (Database) for the pharmacy end.
# For the project, we will assume that all the medications will be stored in packets in the form of tablets/capsules

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import date

## ======================== for shelf ======================== ##
@dataclass
class ShelfLocation:
    shelf_id: str           # e.g. "A1", alphabet for row and num for column
    x: float                     
    y: float            

## ======================== for prescriptions ======================== ##
@dataclass
class Prescriptions:
    name: str
    dosage: float                # in unit of mg (e.g. 500mg.)
    expiration_date: date        # in format of YYYY-MM-DD
    tablets_per_packets: int     
    quantity: int                # amount of packets in stock/shelf
    location: ShelfLocation

class PharmacyDatabase:
    def __init__(self):                                                 # Dictionary mapping medication name → Prescriptions object
        self.inventory: Dict[str, Prescriptions] = {}

    def add_prescription(self, prescription: Prescriptions):            # Add a new medication to the database.
        self.inventory[prescription.name] = prescription

    def check_availability(self, name: str, requested_packets: int) -> int: # Check how many packets are available. Returns 0 if medication does not exist.
        if name not in self.inventory:
            return 0
        available = self.inventory[name].quantity
        return min(available, requested_packets)

    def dispense(self, name: str, packets: int) -> bool:                # Reduce packet quantity after successful robot pickup + OCR verification sequence.
        if name not in self.inventory:                                  
            return False
        if self.inventory[name].quantity >= packets:                    # Returns True if packet passes verification
            self.inventory[name].quantity -= packets
            return True

        return False

    def get_location(self, name: str) -> Optional[ShelfLocation]:           # Return shelf location for robot navigation.
        if name not in self.inventory:
            return None
        return self.inventory[name].location
    
    def get_remaining_packets(self, name: str) -> Optional[int]:            # Prints remaining packet quantity each pick up sequence.
        if name not in self.inventory:
            return None
        return self.inventory[name].quantity

    def is_low_stock(self, name: str, threshold: int = 5) -> bool:          # Check if a medication is at or below the low-stock threshold.
        if name not in self.inventory:
            return False
        return self.inventory[name].quantity <= threshold


## ========================= Test data ========================= ##
# This is test DB for the simulation code below

def create_demo_database() -> PharmacyDatabase:
    db = PharmacyDatabase()

    db.add_prescription(
        Prescriptions(
            name="Paracetamol",
            dosage=500,
            expiration_date=date(2027, 6, 30),
            tablets_per_packets=10,
            quantity=20,
            location=ShelfLocation("A1", x=1.0, y=0.5)
        )
    )

    db.add_prescription(
        Prescriptions(
            name="Amoxicillin",
            dosage=250,
            expiration_date=date(2026, 11, 15),
            tablets_per_packets=10,
            quantity=6,
            location=ShelfLocation("B2", x=2.2, y=1.3)
        )
    )
    return db

## ========================= Simulation Example ========================= ##
# This block will test what the system will do with the data above

if __name__ == "__main__":
    db = create_demo_database()

    requested_packets = 8
    med_name = "Amoxicillin"

    available = db.check_availability(med_name, requested_packets)

    if available > 0:
        location = db.get_location(med_name)
        print(f"Robot moving to shelf {location.shelf_id} at ({location.x}, {location.y})")

        for i in range(available):
            print(f"Picking packet {i + 1}...")
            # Simulate successful OCR + pick
            db.dispense(med_name, 1)

            remaining = db.get_remaining_packets(med_name)
            print(f"Remaining packets: {remaining}")

            # Low stock warning
            if remaining == 5:
                print("⚠️  WARNING: Stock has reached LOW LEVEL (5 packets remaining)")

            # Out-of-stock alert (sends pop-up alert)
            if remaining == 0:
                print("🚨 POP-UP ALERT: MEDICATION OUT OF STOCK 🚨")


        db.dispense(med_name, available)

        if available < requested_packets:
            print("⚠️  Alert: insufficient stock")

        remaining = db.get_remaining_packets(med_name)

        if remaining > 0 and remaining <= 5:
             print(f"⚠️  Alert: Low stock ({remaining} packets remaining)")

    else:
        print("Alert: medication not in stock")