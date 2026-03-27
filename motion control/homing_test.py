import RPi.GPIO as GPIO
import time

# ── Pin Definitions ─────────────────────────────
Y_STEP, Y_DIR, Y_LIMIT = 22, 23, 6
Z_STEP, Z_DIR, Z_LIMIT = 24, 25, 13

# ── Direction (adjust if needed) ────────────────
Y_POSITIVE = GPIO.HIGH   # right
Y_NEGATIVE = GPIO.LOW    # left

Z_POSITIVE = GPIO.LOW  # up   
Z_NEGATIVE = GPIO.HIGH # down 

# ── Motion Settings ─────────────────────────────
START_DELAY = 0.0020
MIN_DELAY   = 0.0010
RAMP_STEPS  = 300

# ── Position Tracking ───────────────────────────
current_pos = {"y": 0, "z": 0}

# ── GPIO Setup ──────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [Y_STEP, Y_DIR, Z_STEP, Z_DIR]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

for pin in [Y_LIMIT, Z_LIMIT]:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ── Limit Switch (NC) ───────────────────────────
def limit_hit(pin):
    return GPIO.input(pin) == GPIO.HIGH

# ── Ramp Motion ─────────────────────────────────
def move_ramp(step_pin, dir_pin, steps, direction):
    GPIO.output(dir_pin, direction)

    ramp = RAMP_STEPS
    if steps < 2 * ramp:
        ramp = steps // 2 if steps >= 2 else 1

    for i in range(steps):

        if i < ramp:
            delay = START_DELAY - (START_DELAY - MIN_DELAY) * (i / ramp)

        elif i >= steps - ramp:
            delay = MIN_DELAY + (START_DELAY - MIN_DELAY) * (
                (i - (steps - ramp)) / ramp
            )

        else:
            delay = MIN_DELAY

        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(delay)

# ── HOMING ──────────────────────────────────────
def home_axis(step_pin, dir_pin, limit_pin, axis_name):
    print(f"Homing {axis_name}...")

    if axis_name == "Y":
        GPIO.output(dir_pin, Y_NEGATIVE)   # left = home
    elif axis_name == "Z":
        GPIO.output(dir_pin, Z_NEGATIVE)   # down = home

# ── MOVE TO TARGET USING DELTA ──────────────────
def move_to(target_y, target_z):
    global current_pos

    dy = target_y - current_pos["y"]
    dz = target_z - current_pos["z"]

    print(f"\nMoving to target (Y={target_y}, Z={target_z})")
    print(f"Delta: dY={dy}, dZ={dz}")

    # Move Y
    if dy != 0:
        direction = Y_POSITIVE if dy > 0 else Y_NEGATIVE
        move_ramp(Y_STEP, Y_DIR, abs(dy), direction)

    # Move Z
    if dz != 0:
        direction = Z_POSITIVE if dz > 0 else Z_NEGATIVE
        move_ramp(Z_STEP, Z_DIR, abs(dz), direction)

    current_pos["y"] = target_y
    current_pos["z"] = target_z

    print(f"Arrived at (Y={current_pos['y']}, Z={current_pos['z']})")

# ── MAIN ────────────────────────────────────────
try:
    print("=== STAGE 1: HOMING → TARGET → RETURN ===")

    # 1. HOMING
    home_axis(Y_STEP, Y_DIR, Y_LIMIT, "Y")
    home_axis(Z_STEP, Z_DIR, Z_LIMIT, "Z")

    # 2. SET HOME POSITION
    current_pos = {"y": 0, "z": 0}
    print("Set HOME = (0,0)")

    time.sleep(1)

    # 3. MOVE TO TARGET
    target_y = 1500   # adjust for your system
    target_z = 500

    move_to(target_y, target_z)

    time.sleep(2)

    # 4. RETURN HOME
    move_to(0, 0)

    print("\nReturned HOME ✅")

except KeyboardInterrupt:
    print("\nStopped")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up")