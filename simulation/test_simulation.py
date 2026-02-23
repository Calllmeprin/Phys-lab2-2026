## This module is to purely test how the software handles and logs the process ##

from database.config_loader import load_config
from database.models import ShelfLocation, Prescriptions
from database.pharmacy_db import PharmacyDatabase
from database.storage import save_inventory, load_inventory
from database.logger import log_event, log_sess_separator
from datetime import date, timedelta


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

def validate_prescriptions(prescription_list):      # Function to detect for duplicates in prescription and combine the amount.
    merged = {}

    for med_name, qty in prescription_list:
        if med_name in merged:
            merged[med_name] += qty
            print(f"⚠️ Duplicate medication detected: {med_name}. Quantities merged.")
            log_event("DUPLICATE_MEDICATION", med_name, f"Merged quantity: {merged[med_name]}")
        else:
            merged[med_name] = qty

    return list(merged.items())

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

if __name__ == "__main__":
    import time

    db = PharmacyDatabase()
    load_inventory(db)

    config = load_config()

    LOW_STOCK_THRESHOLD =  config["low_stock_threshold"]
    HIGH_DOSAGE_THRESHOLD = config["high_dosage_threshold"]
    EXPIRY_WARNING_DAYS = config["expiry_warning_days"]
    DRY_RUN_MODE = config["dry_run_mode"]

    #small block for session report
    session_start_time = time.time()
    total_medications_processed = 0
    total_packets_dispensed = 0
    total_shortages = 0
    total_warnings = 0

    if not db.inventory:
        setup_demo(db)

    prescription_list = [
        ("Amoxicillin", 5),
        ("Amoxicillin", 3)                              # This is to test the merge function
    ]

    prescription_list = validate_prescriptions(prescription_list)

    for index, (med_name, requested) in enumerate(prescription_list):
        total_medications_processed += 1
        med = db.inventory.get(med_name)

        if med:
            today = date.today()

            # 🚨 Block expired medication
            if med.expiration_date < today:
                print(f"🚫 Medication expired: {med_name} (Expired on {med.expiration_date})")
                log_event(
                    "EXPIRED_MEDICATION",
                    med_name,
                    f"Expired on: {med.expiration_date}"
                )
                total_warnings += 1
                continue  # Skip dispensing this medication

            # ⚠️ Expiry warning window
            days_until_expiry = (med.expiration_date - today).days

            if days_until_expiry <= EXPIRY_WARNING_DAYS:
                print(
                    f"⚠️ {med_name} expiring soon "
                    f"(in {days_until_expiry} days)"
                )
                log_event(
                    "EXPIRY_WARNING",
                    med_name,
                    f"Days until expiry: {days_until_expiry}"
                )

        if med and med.dosage > HIGH_DOSAGE_THRESHOLD:
            print(f"⚠️ High dosage warning for {med_name}: {med.dosage} mg")
            log_event("HIGH_DOSAGE_WARNING", med_name, f"Dosage: {med.dosage} mg")
            total_warnings += 1

        available = db.check_availability(med_name, requested)
        shortage = requested - available

        if requested <= 0:
            print("ℹ️ No prescriptions to dispense. Ending operation.")
            log_event("NO_OPERATION", med_name, 0)
            continue

        current_remaining = db.get_remaining(med_name)

        for i in range(available):

            if DRY_RUN_MODE:
                simulated_remaining = current_remaining - (i + 1)

                print(f"[DRY RUN] Simulated dispense. Remaining would be: {simulated_remaining}")
                log_event(
                    "DRY_RUN_DISPENSE",
                    med_name,
                    f"Simulated remaining: {simulated_remaining}"
                )

            else:
                db.dispense(med_name, 1)
                total_packets_dispensed += 1
                remaining = db.get_remaining(med_name)

                print(f"Remaining packets: {remaining}")
                log_event("DISPENSE", med_name, f"Remaining: {remaining}")

                if remaining == 0:
                    print("🚨 OUT OF STOCK")
                    log_event("OUT OF STOCK", med_name, f"Remeaning: {remaining}")

                elif remaining == LOW_STOCK_THRESHOLD:
                    print("⚠️  LOW STOCK")
                    log_event("LOW STOCK", med_name, f"Remaining: {remaining}")
                    total_warnings += 1

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
                f"Remaining: {db.get_remaining(med_name)}"
            )
            total_shortages += shortage

            # Line 2 — detailed shortage info
            log_event(
                "INSUFFICIENT STOCK",
                med_name,
                f"Short by: {shortage} | Requested: {requested} | Available: {available}"
            )

        print("✅ End of operation for this medication.")
        print("============================================")


    print("\n============= SESSION REPORT =============")
    print(f"Medications processed: {total_medications_processed}")
    print(f"Total packets dispensed: {total_packets_dispensed}")
    print(f"Total shortage amount: {total_shortages}")
    print(f"Total warnings triggered: {total_warnings}")
    print("============================================")
    print("All prescriptions processed. End operation.")
    print("============================================")

    session_end_time= time.time()
    session_duration = round(session_end_time - session_start_time, 2)

    log_event(
        "END OF SESSION",
        "SYSTEM",
        "Dispensing process completed\n"
        f"Processed: {total_medications_processed} | "
        f"Dispensed: {total_packets_dispensed} | "
        f"Shortage: {total_shortages} | "
        f"Warnings: {total_warnings} | "
        f"Duration: {session_duration}s"
    )

    log_sess_separator()
    inventory_dashboard(db, config)

    if not DRY_RUN_MODE:
        save_inventory(db)
    else:
        print("DRY RUN: Inventory not saved.")