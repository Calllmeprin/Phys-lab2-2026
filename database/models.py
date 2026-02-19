## This file is just a module for dataclass structures to be called for by other modules. ##

from dataclasses import dataclass
from datetime import date

## ======================== for shelf ======================== ##

@dataclass
class ShelfLocation:
    shelf_id: str               # e.g. "A1", alphabet for row and num for column
    x: float
    y: float

## ======================== for prescriptions ======================== ##

@dataclass
class Prescriptions:
    name: str
    dosage: float               # in unit of mg (e.g. 500mg.)
    expiration_date: date       # in format of YYYY-MM-DD
    tablets_per_packets: int
    quantity: int               # amount of packets in stock/shelf
    location: ShelfLocation