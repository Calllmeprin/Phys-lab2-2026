import RPi.GPIO as GPIO
import time
import sys
import os
from datetime import date

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.models import ShelfLocation, Prescriptions
from database.pharmacy_db import PharmacyDatabase

# ── Pin Definitions ──────────────────────────────────────────
X_STEP, X_DIR = 17, 27
Y_STEP, Y_DIR = 22, 23
Z_STEP, Z_DIR = 24, 25
SUCTION_PIN   = 16

# ── Motion Parameters ────────────────────────────────────────
# Tune these values on real hardware
X_START_DELAY = 0.0015
X_MIN_DELAY   = 0.0010
X_RAMP_STEPS  = 250

Y_START_DELAY = 0.0015
Y_MIN_DELAY   = 0.0010
Y_RAMP_STEPS  = 250

Z_START_DELAY = 0.0015
Z_MIN_DELAY   = 0.0010
Z_RAMP_STEPS  = 250

SUCTION_TIME  = 2.0
PICK_Z_OFFSET = 120      # extra downward steps to touch/grab bag
DROP_Z_OFFSET = 120      # extra downward steps to release at drop-off
SAFE_Z        = 0        # safe travel height; change after homing/calibration

# Drop-off point
DROP_OFF = ShelfLocation(shelf_id="DROP", x=0, y=0, z=0)

# ── Current Position Tracker ─────────────────────────────────
current_pos = {"x": 0, "y": 0, "z": 0}

# ── GPIO Setup ───────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [X_STEP, X_DIR, Y_STEP, Y_DIR, Z_STEP, Z_DIR, SUCTION_PIN]:
    GPIO.setup(pin, GPIO.OUT)

GPIO.output(SUCTION_PIN, GPIO.LOW)  # suction OFF at start

# ── Utility: Axis Parameter Lookup ───────────────────────────
def get_axis_params(axis_name: str):
    if axis_name == "X":
        return X_START_DELAY, X_MIN_DELAY, X_RAMP_STEPS
    if axis_name == "Y":
        return Y_START_DELAY, Y_MIN_DELAY, Y_RAMP_STEPS
    if axis_name == "Z":
        return Z_START_DELAY, Z_MIN_DELAY, Z_RAMP_STEPS
    raise ValueError(f"Unknown axis: {axis_name}")

# ── Ramp-Speed Stepper Motion ────────────────────────────────
def move_axis_ramp(step_pin, dir_pin, steps, axis_name="AXIS"):
    """
    Move one axis using simple linear acceleration/deceleration.
    Positive steps -> GPIO.HIGH direction
    Negative steps -> GPIO.LOW direction
    """
    if steps == 0:
        return

    start_delay, min_delay, ramp_steps = get_axis_params(axis_name)

    direction = GPIO.HIGH if steps > 0 else GPIO.LOW
    total_steps = abs(int(steps))
    GPIO.output(dir_pin, direction)

    if total_steps < 2 * ramp_steps:
        ramp_steps = max(1, total_steps // 2)

    for i in range(total_steps):
        # Ramp up
        if i < ramp_steps:
            delay = start_delay - (start_delay - min_delay) * (i / ramp_steps)
        # Ramp down
        elif i >= total_steps - ramp_steps:
            delay = min_delay + (start_delay - min_delay) * (
                (i - (total_steps - ramp_steps)) / ramp_steps
            )
        # Cruise
        else:
            delay = min_delay

        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(delay)

# ── Low-Level Position Moves ─────────────────────────────────
def move_z_to(target_z: int):
    global current_pos
    delta_z = int(target_z - current_pos["z"])
    if delta_z != 0:
        print(f"  Z move -> {target_z} (ΔZ={delta_z})")
        move_axis_ramp(Z_STEP, Z_DIR, delta_z, "Z")
        current_pos["z"] = target_z

def move_x_to(target_x: int):
    global current_pos
    delta_x = int(target_x - current_pos["x"])
    if delta_x != 0:
        print(f"  X move -> {target_x} (ΔX={delta_x})")
        move_axis_ramp(X_STEP, X_DIR, delta_x, "X")
        current_pos["x"] = target_x

def move_y_to(target_y: int):
    global current_pos
    delta_y = int(target_y - current_pos["y"])
    if delta_y != 0:
        print(f"  Y move -> {target_y} (ΔY={delta_y})")
        move_axis_ramp(Y_STEP, Y_DIR, delta_y, "Y")
        current_pos["y"] = target_y

def move_to(target: ShelfLocation, use_safe_z=True):
    """
    Safer travel sequence:
    1) raise/lower to SAFE_Z first
    2) move X and Y
    3) move Z to target
    """
    print(
        f"Moving to {target.shelf_id} "
        f"(target: X={target.x}, Y={target.y}, Z={target.z})"
    )

    if use_safe_z:
        move_z_to(SAFE_Z)

    move_x_to(int(target.x))
    move_y_to(int(target.y))
    move_z_to(int(target.z))

    print(f"Arrived at {target.shelf_id} ✅")

# ── Suction Functions ────────────────────────────────────────
def suction_on():
    GPIO.output(SUCTION_PIN, GPIO.HIGH)
    print("Suction ON")

def suction_off():
    GPIO.output(SUCTION_PIN, GPIO.LOW)
    print("Suction OFF")

# ── Pick / Drop Sequences ────────────────────────────────────
def pick_from_shelf(target_shelf: ShelfLocation):
    print(f"Going to shelf {target_shelf.shelf_id}...")
    move_to(target_shelf, use_safe_z=True)

    print("Lowering for pickup...")
    move_z_to(current_pos["z"] + PICK_Z_OFFSET)

    print("Picking medicine...")
    suction_on()
    time.sleep(SUCTION_TIME)

    print("Returning to target shelf Z...")
    move_z_to(int(target_shelf.z))

    print("Raising to safe travel height...")
    move_z_to(SAFE_Z)

def drop_at_point(drop_point: ShelfLocation):
    print("Going to drop-off point...")
    move_to(drop_point, use_safe_z=True)

    print("Lowering for release...")
    move_z_to(current_pos["z"] + DROP_Z_OFFSET)

    suction_off()
    print("Medicine dropped off ✅")

    print("Returning to drop-off Z...")
    move_z_to(int(drop_point.z))

    print("Raising to safe travel height...")
    move_z_to(SAFE_Z)

# ── Main Dispense Function ───────────────────────────────────
def dispense_medicine(medicine_name: str, db: PharmacyDatabase):
    print(f"\n=== Dispensing: {medicine_name} ===")

    if medicine_name not in db.inventory:
        print(f"ERROR: {medicine_name} not found in database!")
        return False

    prescription = db.inventory[medicine_name]
    target_shelf = prescription.location

    if prescription.quantity <= 0:
        print(f"ERROR: {medicine_name} is out of stock!")
        return False

    pick_from_shelf(target_shelf)
    drop_at_point(DROP_OFF)

    db.dispense(medicine_name, 1)
    print(f"Stock updated. Remaining: {db.get_remaining(medicine_name)} packets")
    return True

def process_order(order_list, db: PharmacyDatabase):
    print("=== Starting Dispensing System ===")
    print(f"Order: {order_list}")

    for medicine in order_list:
        ok = dispense_medicine(medicine, db)
        if not ok:
            print(f"Skipping {medicine} due to error.")

    print("\n=== All medicines processed! ===")

# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    db = PharmacyDatabase()

    db.add_prescription(Prescriptions(
        name="Paracetamol",
        dosage=500,
        expiration_date=date(2026, 12, 31),
        tablets_per_packets=10,
        quantity=5,
        location=ShelfLocation(shelf_id="A1", x=400, y=800, z=200)
    ))

    db.add_prescription(Prescriptions(
        name="Ibuprofen",
        dosage=400,
        expiration_date=date(2026, 12, 31),
        tablets_per_packets=10,
        quantity=3,
        location=ShelfLocation(shelf_id="B2", x=800, y=400, z=300)
    ))

    try:
        order = ["Paracetamol", "Ibuprofen"]
        process_order(order, db)

    except KeyboardInterrupt:
        print("\nStopped by user")

    finally:
        suction_off()
        GPIO.cleanup()
        print("GPIO cleaned up ✅")