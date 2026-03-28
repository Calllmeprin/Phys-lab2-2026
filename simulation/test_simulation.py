## This module is to purely test how the software handles and logs the operations ##

from database.config_loader import load_config
from database.models import ShelfLocation, Prescriptions
from database.pharmacy_db import PharmacyDatabase
from database.storage import save_inventory, load_inventory
from database.logger import log_event, log_sess_separator
from database.dispense_controller import DispenseController, DispenseState
from datetime import date, timedelta
from enum import Enum
import time

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

def validate_prescriptions(prescription_list):      # Function to look for duplicates in the prescription order and combine the amount.
    merged = {}

    for med_name, qty in prescription_list:
        if med_name in merged:
            merged[med_name] += qty
            print(f"⚠️  Duplicate medication detected: {med_name}. Quantities merged.")
            log_event("DUPLICATE MEDICATION", med_name, f"Merged quantity: {merged[med_name]}")
        else:
            merged[med_name] = qty

    return list(merged.items())

def safe_input(prompt):
    user_input = input(prompt).strip()

    if user_input.lower() == "cancel":
        print("\nReturning to main menu...\n")
        return None

    return user_input

def inventory_dashboard(db, config):

    today = date.today()
    expiry_warning_days = config["expiry_warning_days"]
    low_stock_threshold = config["low_stock_threshold"]

    total_medications = len(db.inventory)
    total_packets = 0
    low_stock_count = 0
    expired_count = 0
    expiring_soon_count = 0

    print("\n========== INVENTORY DASHBOARD ==========")

    for med_name, med in db.inventory.items():
        total_packets += med.quantity

        status_flags = []

        # Expired check
        if med.expiration_date < today:
            expired_count += 1
            status_flags.append("EXPIRED")

        # Expiring soon check
        days_until_expiry = (med.expiration_date - today).days
        if 0 <= days_until_expiry <= expiry_warning_days:
            expiring_soon_count += 1
            status_flags.append("EXPIRING SOON")

        # Low stock check
        if med.quantity <= low_stock_threshold:
            low_stock_count += 1
            status_flags.append("LOW STOCK")

        status_text = " | ".join(status_flags) if status_flags else "OK"

        print(
            f"{med_name} | {med.quantity} packets | "
            f"Exp: {med.expiration_date} | {status_text}"
        )

    print("------------------------------------------")
    print(f"Total medications: {total_medications}")
    print(f"Total packets in system: {total_packets}")
    print(f"Low stock items: {low_stock_count}")
    print(f"Expired items: {expired_count}")
    print(f"Expiring soon items: {expiring_soon_count}")
    print("==========================================\n")

if __name__ == "__main__":              # Recently underwent huge revamp for command-based system like Aj. Poom's ATM code assignment

    db = PharmacyDatabase()
    load_inventory(db)

    config = load_config()

    if not db.inventory:
        setup_demo(db)

    controller = DispenseController(db, config)

    while True:

        print("\n===== PHARMACY SYSTEM MENU =====")
        print("1. Run prescription")
        print("2. Show inventory dashboard")
        print("3. Restock medication")
        print("4. Remove stock")
        print("5. Add new medication")
        print("6. Exit")

        choice = input("\nSelect option: ")

        # -------------------------------------------------
        # OPTION 1: Run Prescription
        # -------------------------------------------------
        if choice == "1":

            session_start_time = time.time()

            prescription_list = []
            
            while True:
                print("\n========== PRESCRIPTION INTERFACE ==========")
                print("Enter prescription details below:\n")

                print("========== ADD MEDICATION ==========")

                while True:
                    med_name = safe_input("Medication name: ")
                    if med_name is None:
                        break

                    qty_input = safe_input("Number of packets: ")
                    if qty_input is None:
                        break
                    
                    try:
                        qty = int(qty_input)
                    except ValueError:
                        print("Invalid number.")
                        continue

                    prescription_list.append((med_name, qty))

                    more = safe_input("Add another medication? (y/n): ")
                    if more is None:
                        break

                    if more == "y":
                        print("\n========== ADD MEDICATION ==========")
                        continue

                    elif more == "n":
                        print("\n========== STARTING DISPENSING PROCESS ==========")
                        break

                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")

                prescription_list = validate_prescriptions(prescription_list)

                # Reset controller counters for fresh session
                controller.total_medications_processed = 0
                controller.total_dispensed = 0
                controller.total_shortage = 0
                controller.total_warnings = 0
                controller.rejections = []

                for med_name, requested in prescription_list:
                    controller.process_medication(med_name, requested)

                print("\n============= SESSION REPORT =============")
                print(f"Medications processed: {controller.total_medications_processed}")
                print(f"Total packets dispensed: {controller.total_dispensed}")
                print(f"Total shortage amount: {controller.total_shortage}")
                print(f"Total warnings triggered: {controller.total_warnings}")

                print("\nRejections:")
                if controller.rejections:
                    for r in controller.rejections:
                        print(f"- {r[0]} → {r[1]}")
                else:
                    print("None")

                print("============================================")

                session_end_time = time.time()
                session_duration = round(session_end_time - session_start_time, 2)

                log_event(
                    "END OF SESSION",
                    "SYSTEM",
                    f"Processed: {controller.total_medications_processed} | "
                    f"Dispensed: {controller.total_dispensed} | "
                    f"Shortage: {controller.total_shortage} | "
                    f"Warnings: {controller.total_warnings} | "
                    f"Duration: {session_duration}s"
                )

                log_sess_separator()

        # -------------------------------------------------
        # OPTION 2: Show Dashboard
        # -------------------------------------------------
        elif choice == "2":
            inventory_dashboard(db, config)

        # -------------------------------------------------
        # OPTION 3: Restock Medication
        # -------------------------------------------------
        elif choice == "3":

            med_name = safe_input("Medication name: ")
            if med_name is None:
                continue
            try:
                amount_input = safe_input("Amount to add: ")
                if amount_input is None:
                    continue
            except ValueError:
                print("Invalid number.")
                continue

            if med_name in db.inventory:
                db.inventory[med_name].quantity += amount
                new_total = db.inventory[med_name].quantity

                print(f"Added {amount} packets to {med_name}.")
                
                log_event(
                    "RESTOCK",
                    med_name,
                    f"Added: {amount} | New total: {new_total}"
                )

            else:
                print("Medication not found.")

        # -------------------------------------------------
        # OPTION 4: Remove Stock
        # -------------------------------------------------
        elif choice == "4":
            print("\n========== REMOVE FROM STOCK ==========")
            med_name = safe_input("Medication name: ")
            if med_name is None:
                continue
            try:
                amount = int(input("Amount to remove: "))
            except ValueError:
                print("Invalid number.")
                continue

            if med_name in db.inventory:
                if db.inventory[med_name].quantity >= amount:
                    db.inventory[med_name].quantity -= amount
                    new_total = db.inventory[med_name].quantity
                
                    print(f"Removed {amount} packets from {med_name}.")

                    log_event(
                        "MANUAL REMOVE",
                        med_name,
                        f"Removed: {amount} | New total: {new_total}"
                    )
                else:
                    print("Not enough stock to remove that amount.")
            else:
                print("Medication not found.")

        # -------------------------------------------------
        # OPTION 5: Add new medication
        # -------------------------------------------------
        elif choice == "5":
            print("\n========== ADD NEW MEDICATION ==========")
            name = safe_input("Medication name: ")
            if name is None:
                continue

            try:
                dosage = float(input("Dosage (mg): "))
                packets = int(input("Number of packets: "))
                tablets_per_packet = int(input("Tablets per packet: "))
            except ValueError:
                print("Invalid input.")
                continue

            expiry_input = input("Expiration date (YYYY-MM-DD): ")

            try:
                expiration = date.fromisoformat(expiry_input)
            except ValueError:
                print("Invalid date format.")
                continue

            shelf_id = input("Shelf ID (e.g. A1): ")

            try:
                x = float(input("Shelf X coordinate: "))
                y = float(input("Shelf Y coordinate: "))
                z = float(input("Shelf Z coordinate: "))
            except ValueError:
                print("Invalid coordinates.")
                continue

            location = ShelfLocation(shelf_id, x, y)

            new_med = Prescriptions(
                name=name,
                dosage=dosage,
                expiration_date=expiration,
                tablets_per_packets=tablets_per_packet,
                quantity=packets,
                location=location
            )

            db.add_prescription(new_med)

            print(f"{name} successfully added to inventory.")

        # -------------------------------------------------
        # OPTION 6: Exit
        # -------------------------------------------------
        elif choice == "6":

            if not config["dry_run_mode"]:
                save_inventory(db)
            else:
                print("DRY RUN: Inventory not saved.")

            print("Exiting system.")
            break

        else:
            print("Invalid option. Please select 1-6.")