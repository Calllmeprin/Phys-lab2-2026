# motion_test.py — Cartesian Robot 3-Axis Test
# TMC2209 drivers | NC Limit Switches | 1/16 Microstepping
# Workflow: PSU → RPi4 → Buck Converter → Components
#           1x shared GND (brown wire) for all switches → Pi GND

import RPi.GPIO as GPIO
import time

# ── Pin Definitions ──────────────────────────────────────────
ENABLE = 18          # Shared ENABLE (LOW = motors ON for TMC2209)

X_STEP,  X_DIR,  X_LIMIT  = 17, 27,  5
Y_STEP,  Y_DIR,  Y_LIMIT  = 22, 23,  6
Z_STEP,  Z_DIR,  Z_LIMIT  = 24, 25, 13

# TMC2209 Microstep pins (MS1, MS2 per axis)
# 1/16 step = MS1 HIGH, MS2 HIGH  (per TMC2209 truth table)
X_MS1, X_MS2 = 7,  8
Y_MS1, Y_MS2 = 9,  10
Z_MS1, Z_MS2 = 11, 12
# !! Change these pin numbers to match YOUR actual wiring !!

# ── Settings ─────────────────────────────────────────────────
STEP_DELAY  = 0.001   # seconds per half-step (lower = faster)
TEST_STEPS  = 400     # full steps per move segment
BOUNCE_MS   = 50      # software debounce time (milliseconds)

# ── GPIO Setup ───────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

OUTPUT_PINS = [
    ENABLE,
    X_STEP, X_DIR, X_MS1, X_MS2,
    Y_STEP, Y_DIR, Y_MS1, Y_MS2,
    Z_STEP, Z_DIR, Z_MS1, Z_MS2,
]
for pin in OUTPUT_PINS:
    GPIO.setup(pin, GPIO.OUT)

# NC Limit Switches — shared GND brown wire → Pi GND
# PUD_UP so floating reads HIGH when switch opens (triggered)
for pin in [X_LIMIT, Y_LIMIT, Z_LIMIT]:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ── Apply 1/16 Microstepping (TMC2209 truth table) ───────────
# MS1=HIGH, MS2=HIGH → 1/16 microstep
for ms1, ms2 in [(X_MS1, X_MS2), (Y_MS1, Y_MS2), (Z_MS1, Z_MS2)]:
    GPIO.output(ms1, GPIO.HIGH)
    GPIO.output(ms2, GPIO.HIGH)

# ── Enable all motors (LOW = enabled on TMC2209) ─────────────
GPIO.output(ENABLE, GPIO.LOW)
time.sleep(0.1)   # let drivers wake up

# ── Helper: read limit switch with debounce ──────────────────
def limit_hit(pin):
    """
    NC switch + PUD_UP logic:
      Normal    → circuit closed → GND → LOW  (0) = NOT hit
      Triggered → circuit open  → 3.3V → HIGH (1) = HIT ✅
    """
    if GPIO.input(pin) == GPIO.HIGH:
        time.sleep(BOUNCE_MS / 1000)          # debounce
        return GPIO.input(pin) == GPIO.HIGH   # confirm
    return False

# ── Move with live limit-switch safety check ─────────────────
def move_safe(step_pin, dir_pin, limit_pin, steps, direction):
    """
    Moves 'steps' pulses in 'direction'.
    Stops immediately if limit switch is hit mid-move.
    Returns True if completed, False if stopped by limit.
    """
    GPIO.output(dir_pin, direction)
    for i in range(steps):
        if limit_hit(limit_pin):
            print(f"  ⚠️  Limit triggered at step {i}/{steps} — stopping!")
            return False
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(STEP_DELAY)
    return True

# ── Wait for operator to manually toggle switch ───────────────
def wait_for_switch_toggle(limit_pin, axis_name):
    """
    For manual test: waits for switch to be pressed then released.
    NC logic: triggered = HIGH, released = LOW
    """
    print(f"  [{axis_name}] Waiting for limit switch press (trigger)...")
    timeout = 30   # seconds
    start = time.time()

    # Wait until triggered (HIGH)
    while not limit_hit(limit_pin):
        if time.time() - start > timeout:
            print(f"  [{axis_name}] ⏰ Timeout! No switch press detected.")
            return False
        time.sleep(0.01)

    print(f"  [{axis_name}] ✅ Switch HIT detected (HIGH=1)")

    # Wait until released (LOW)
    while limit_hit(limit_pin):
        time.sleep(0.01)

    print(f"  [{axis_name}] ✅ Switch RELEASED (LOW=0) — circuit restored")
    return True

# ── Per-axis test routine ─────────────────────────────────────
def test_axis(name, step_pin, dir_pin, limit_pin):
    print(f"\n{'─'*40}")
    print(f"  Testing {name}-Axis  |  1/16 microstep  |  NC switch")
    print(f"{'─'*40}")

    # Forward
    print(f"  [{name}] Moving FORWARD {TEST_STEPS} steps...")
    completed = move_safe(step_pin, dir_pin, limit_pin, TEST_STEPS, GPIO.HIGH)
    if not completed:
        print(f"  [{name}] ⛔ Forward move aborted by limit switch!")
        return False
    time.sleep(0.5)

    # Backward
    print(f"  [{name}] Moving BACKWARD {TEST_STEPS} steps...")
    completed = move_safe(step_pin, dir_pin, limit_pin, TEST_STEPS, GPIO.LOW)
    if not completed:
        print(f"  [{name}] ⛔ Backward move aborted by limit switch!")
        return False
    time.sleep(0.5)

    # Manual switch toggle test
    print(f"  [{name}] Manually toggle the limit switch now:")
    success = wait_for_switch_toggle(limit_pin, name)
    if not success:
        return False

    print(f"  [{name}] ✅ Axis test PASSED!")
    return True

# ── Main ─────────────────────────────────────────────────────
try:
    print("=" * 40)
    print("  Cartesian Robot — Motion Test")
    print("  Microstepping : 1/16 (TMC2209)")
    print("  Limit Switches: NC type")
    print("=" * 40)

    results = {}
    for axis, sp, dp, lp in [
        ("X", X_STEP, X_DIR, X_LIMIT),
        ("Y", Y_STEP, Y_DIR, Y_LIMIT),
        ("Z", Z_STEP, Z_DIR, Z_LIMIT),
    ]:
        results[axis] = test_axis(axis, sp, dp, lp)

    print("\n" + "=" * 40)
    print("  RESULTS:")
    for axis, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"    {axis}-Axis : {status}")
    print("=" * 40)

except KeyboardInterrupt:
    print("\n⚠️  Test interrupted by user (Ctrl+C)")

finally:
    GPIO.output(ENABLE, GPIO.HIGH)   # Disable all motors
    GPIO.cleanup()
    print("GPIO cleaned up ✅")