## This module is for core database logic only ##

from typing import Dict, Optional
from .models import Prescriptions


class PharmacyDatabase:
    def __init__(self):
        self.inventory: Dict[str, Prescriptions] = {}

    def add_prescription(self, prescription: Prescriptions):
        self.inventory[prescription.name] = prescription

    def check_availability(self, name: str, requested_packets: int) -> int:
        if name not in self.inventory:
            return 0
        available = self.inventory[name].quantity
        return min(available, requested_packets)

    def dispense(self, name: str, packets: int) -> bool:
        if name not in self.inventory:
            return False

        if self.inventory[name].quantity >= packets:
            self.inventory[name].quantity -= packets
            return True

        return False

    def get_remaining(self, name: str) -> Optional[int]:
        if name not in self.inventory:
            return None
        return self.inventory[name].quantity