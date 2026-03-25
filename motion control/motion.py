import RPi.GPIO as GPIO
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.models import ShelfLocation
from database.pharmacy_db import PharmacyDatabase

# ── Pin Definitions ──────────────────────────────
X_STEP, X_DIR = 17, 27
Y_STEP, Y_DIR = 22, 23
Z_STEP, Z_DIR = 24, 25
SUCTION_PIN   = 16  # ← change this to your actual relay pin later

# ── Settings ─────────────────────────────────────
STEP_DELAY    = 0.001
SUCTION_TIME  = 3    # ← seconds to hold suction (adjust as needed)

# Drop-off point (change when you decide the fixed point)
DROP_OFF = ShelfLocation(shelf_id="DROP", x=0, y=0, z=0)

# ── Current Position Tracker ─────────────────────
current_pos = {"x": 0, "y": 0, "z": 0}

# ── Setup ─────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [X_STEP, X_DIR, Y_STEP, Y_DIR, Z_STEP, Z_DIR, SUCTION_PIN]:
    GPIO.setup(pin, GPIO.OUT)

GPIO.output(SUCTION_PIN, GPIO.LOW)  # suction OFF at start

# ── Motor Functions ───────────────────────────────
def move_axis(step_pin, dir_pin, steps):
    if steps == 0:
        return
    direction = GPIO.HIGH if steps > 0 else GPIO.LOW
    GPIO.output(dir_pin, direction)
    for _ in range(abs(steps)):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(STEP_DELAY)

def move_to(target: ShelfLocation):
    global current_pos

    delta_x = int(target.x - current_pos["x"])
    delta_y = int(target.y - current_pos["y"])
    delta_z = int(target.z - current_pos["z"])

    print(f"  Moving to {target.shelf_id} → ΔX:{delta_x} ΔY:{delta_y} ΔZ:{delta_z}")

    move_axis(X_STEP, X_DIR, delta_x)
    move_axis(Y_STEP, Y_DIR, delta_y)
    move_axis(Z_STEP, Z_DIR, delta_z)

    # Update current position
    current_pos["x"] = target.x
    current_pos["y"] = target.y
    current_pos["z"] = target.z

    print(f"  Arrived at {target.shelf_id} ✅")

# ── Suction Functions ─────────────────────────────
def suction_on():
    GPIO.output(SUCTION_PIN, GPIO.HIGH)
    print("  Suction ON 🟢")

def suction_off():
    GPIO.output(SUCTION_PIN, GPIO.LOW)
    print("  Suction OFF 🔴")

# ── Dispense Function ─────────────────────────────
def dispense_medicine(medicine_name: str, db: PharmacyDatabase):
    print(f"\n=== Dispensing: {medicine_name} ===")

    # Look up medicine in database
    if medicine_name not in db.inventory:
        print(f"  ERROR: {medicine_name} not found in database!")
        return False

    prescription = db.inventory[medicine_name]
    target_shelf  = prescription.location

    # Check availability
    if prescription.quantity <= 0:
        print(f"  ERROR: {medicine_name} is out of stock!")
        return False

    # Move to shelf
    print(f"  Going to shelf {target_shelf.shelf_id}...")
    move_to(target_shelf)

    # Pick medicine with suction
    print("  Picking medicine...")
    suction_on()
    time.sleep(SUCTION_TIME)

    # Move to drop-off
    print("  Going to drop-off point...")
    move_to(DROP_OFF)

    # Release medicine
    suction_off()
    print("  Medicine dropped off ✅")

    # Update stock
    db.dispense(medicine_name, 1)
    print(f"  Stock updated. Remaining: {db.get_remaining(medicine_name)} packets")

    return True

# ── Main ──────────────────────────────────────────
if __name__ == "__main__":
    # Setup database with sample medicines
    db = PharmacyDatabase()
    db.add_prescription(__import__('database.models', fromlist=['Prescriptions']).Prescriptions(
        name="Paracetamol",
        dosage=500,
        expiration_date=__import__('datetime').date(2026, 12, 31),
        tablets_per_packets=10,
        quantity=5,
        location=ShelfLocation(shelf_id="A1", x=400, y=800, z=200)
    ))
    db.add_prescription(__import__('database.models', fromlist=['Prescriptions']).Prescriptions(
        name="Ibuprofen",
        dosage=400,
        expiration_date=__import__('datetime').date(2026, 12, 31),
        tablets_per_packets=10,
        quantity=3,
        location=ShelfLocation(shelf_id="B2", x=800, y=400, z=300)
    ))

    try:
        # Example: Jennifer's order
        order = ["Paracetamol", "Ibuprofen"]
        print("=== Starting Dispensing System ===")
        print(f"Order: {order}")

        for medicine in order:
            dispense_medicine(medicine, db)

        print("\n=== All medicines dispensed! ===")

    except KeyboardInterrupt:
        print("\nStopped by user")

    finally:
        suction_off()
        GPIO.cleanup()
        print("GPIO cleaned up ✅")