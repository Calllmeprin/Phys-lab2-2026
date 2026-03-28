from enum import Enum
from datetime import date
from .logger import log_event


class DispenseState(Enum):
    IDLE = "Standby"
    Validating = "Validating"
    CheckStock = "Checking Stock"
    WaitVerification = "Waiting For Verification"
    InventoryUpdate = "Updating Inventory"
    REJECTED = "Rejected"
    COMPLETED = "Completed"

class DispenseController:
    def verification_gate(self, med_name):
        self.log_state_change(DispenseState.WaitVerification)

        # Demo simulation, always true value for now
        verified = True

        if not verified:
            self.reject(med_name, "Verification failed")
            return False

        return True

    def reject(self, med_name, reason):
            self.log_state_change(DispenseState.REJECTED)

            log_event("REJECTION", med_name, reason)

            self.rejections.append({
                "medication": med_name,
                "reason": reason
            })
    
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.state = DispenseState.IDLE

        self.total_medications_processed = 0
        self.total_dispensed = 0
        self.total_shortage = 0
        self.total_warnings = 0
        self.rejections = []

    def log_state_change(self, state):          # Updates current state
        self.state = state
        print(f"[STATE] → {state.value}")
        log_event("STATE", "SYSTEM", state.value)

    def process_medication(self, med_name, requested):
        self.total_medications_processed += 1
        self.log_state_change(DispenseState.Validating)

        med = self.db.inventory.get(med_name)

        if not med:
            self.reject(med_name, "Medication not found in inventory")
            return

        today = date.today()

        # Expired Warning/Block
        if med.expiration_date < today:
            self.reject(med_name, f"Expired on {med.expiration_date}")
            self.total_warnings += 1
            return

        # Close to expiration Warning
        days_until_expiry = (med.expiration_date - today).days
        if days_until_expiry <= self.config["expiry_warning_days"]:
            print(f"⚠️ {med_name} expiring soon (in {days_until_expiry} days)")
            log_event("EXPIRY WARNING", med_name, f"Days until expiry: {days_until_expiry}")
            self.total_warnings += 1

        # ⚠️ High dosage warning
        if med.dosage > self.config["high_dosage_threshold"]:
            print(f"⚠️ High dosage warning for {med_name}: {med.dosage} mg")
            log_event("HIGH DOSAGE WARNING", med_name, f"Dosage: {med.dosage} mg")
            self.total_warnings += 1

        self.log_state_change(DispenseState.CheckStock)

        available = self.db.check_availability(med_name, requested)
        shortage = requested - available

        if requested <= 0:
            log_event("NO OPERATION", med_name, "Requested amount <= 0")
            return

        current_remaining = self.db.get_remaining(med_name)

        for i in range(available):

            if not self.verification_gate(med_name):
                return

            if self.config["dry_run_mode"]:
                simulated_remaining = current_remaining - (i + 1)
                print(f"[DRY RUN] Simulated dispense. Remaining would be: {simulated_remaining}")
                log_event("DRY RUN DISPENSE", med_name,
                          f"Simulated remaining: {simulated_remaining}")

            else:
                self.log_state_change(DispenseState.InventoryUpdate)

                self.db.dispense(med_name, 1)
                self.total_dispensed += 1

                remaining = self.db.get_remaining(med_name)
                print(f"Remaining packets: {remaining}")
                log_event("DISPENSE", med_name, f"Remaining: {remaining}")

                if remaining == 0:
                    print("🚨 OUT OF STOCK")
                    log_event("OUT OF STOCK", med_name, f"Remaining: {remaining}")

                elif remaining == self.config["low_stock_threshold"]:
                    print("⚠️ LOW STOCK")
                    log_event("LOW STOCK", med_name, f"Remaining: {remaining}")
                    self.total_warnings += 1

        print("============================================")

        if shortage > 0:
            print(
                f"⚠️ Insufficient stock: {med_name} short by {shortage} packets."
            )

            if self.config["dry_run_mode"]:
                simulated_remaining = self.db.get_remaining(med_name) - available
                log_event("INSUFFICIENT STOCK", med_name,
                          f"Simulated remaining: {simulated_remaining}")
            else:
                log_event("INSUFFICIENT STOCK", med_name,
                          f"Remaining: {self.db.get_remaining(med_name)}")

            log_event("INSUFFICIENT STOCK", med_name,
                      f"Short by: {shortage} | Requested: {requested} | Available: {available}")

            self.total_shortage += shortage

        self.log_state_change(DispenseState.COMPLETED)
        print("✅ End of operation for this medication.")
        print("============================================")