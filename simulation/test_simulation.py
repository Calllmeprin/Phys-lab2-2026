## This module is to purely test how the software handles and logs the process ##

from database.models import ShelfLocation, Prescriptions
from database.pharmacy_db import PharmacyDatabase
from database.storage import save_inventory, load_inventory
from database.logger import log_event
from datetime import date

LOW_STOCK_THRESHOLD = 5


def setup_demo(db):
    db.add_prescription(
        Prescriptions(
            name="Amoxicillin",
            dosage=250,
            expiration_date=date(2026, 11, 15),
            tablets_per_packets=10,
            quantity=6,
            location=ShelfLocation("B2", 2.2, 1.3)
        )
    )


if __name__ == "__main__":
    db = PharmacyDatabase()
    load_inventory(db)

    if not db.inventory:
        setup_demo(db)

    prescription_list = [
        ("Amoxicillin", 8)
    ]

    for index, (med_name, requested) in enumerate(prescription_list):

        available = db.check_availability(med_name, requested)
        shortage = requested - available

        if requested <= 0:
            print("ℹ️ No prescriptions to dispense. Ending operation.")
            log_event("NO_OPERATION", med_name, 0)
            continue

        for _ in range(available):
            db.dispense(med_name, 1)
            remaining = db.get_remaining(med_name)

            print(f"Remaining packets: {remaining}")
            log_event("DISPENSE", med_name, remaining)

            if remaining == 0:
                print("🚨 OUT OF STOCK")
                log_event("OUT OF STOCK", med_name, remaining)

            elif remaining == LOW_STOCK_THRESHOLD:
                print("⚠️  LOW STOCK")
                log_event("LOW STOCK", med_name, remaining)

        print("============================================")

        if shortage > 0:
            print(
                f"⚠️  Insufficient stock: {med_name} short by {shortage} packets. "
                "Continuing to next prescribed medication."
            )
            # Line 1 — remaining stock
            log_event(
                "INSUFFICIENT STOCK",
                med_name,
                f"Remaining: {remaining}"
            )

            # Line 2 — detailed shortage info
            log_event(
                "INSUFFICIENT STOCK",
                med_name,
                f"Short by: {shortage} | Requested: {requested} | Available: {available}"
            )

        print("✅ End of operation for this medication.")
        print("============================================")
    print("All prescriptions processed. End operation.")
    print("============================================")

    log_event(
        "END OF SESSION",
        "SYSTEM",
        "Dispensing process completed"
    )

    save_inventory(db)