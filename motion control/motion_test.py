# TEST all 3 axes with limit switches together
import RPi.GPIO as GPIO 
import time

# ── Pin Definitions ──────────────────────────────
ENABLE = 18

X_STEP, X_DIR, X_LIMIT = 17, 27, 5
Y_STEP, Y_DIR, Y_LIMIT = 22, 23, 6
Z_STEP, Z_DIR, Z_LIMIT = 24, 25, 13

# ── Settings ─────────────────────────────────────
STEP_DELAY = 0.001   # speed (lower = faster)
TEST_STEPS = 400     # steps to move forward and back

# ── Setup ─────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [ENABLE, X_STEP, X_DIR, Y_STEP, Y_DIR, Z_STEP, Z_DIR]:
    GPIO.setup(pin, GPIO.OUT)

for pin in [X_LIMIT, Y_LIMIT, Z_LIMIT]:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Enable motors (LOW = enabled for A4988)
GPIO.output(ENABLE, GPIO.LOW)

# ── Functions ─────────────────────────────────────
def move(step_pin, dir_pin, steps, direction):
    GPIO.output(dir_pin, direction)
    for _ in range(steps):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(STEP_DELAY)

def toggle_limit_switch(limit_pin, axis_name):
    print(f"  Waiting for {axis_name} limit switch...")
    while GPIO.input(limit_pin) == GPIO.HIGH:
        time.sleep(0.01)
    print(f"  {axis_name} limit switch triggered! ✅")
    while GPIO.input(limit_pin) == GPIO.LOW:
        time.sleep(0.01)

def test_axis(name, step_pin, dir_pin, limit_pin):
    print(f"\n── Testing {name} Axis ──")

    print(f"  Moving {name} forward...")
    move(step_pin, dir_pin, TEST_STEPS, GPIO.HIGH)
    time.sleep(0.5)

    print(f"  Moving {name} back...")
    move(step_pin, dir_pin, TEST_STEPS, GPIO.LOW)
    time.sleep(0.5)

    print(f"  Toggle {name} limit switch once:")
    toggle_limit_switch(limit_pin, name)

    print(f"  {name} axis test complete! ✅")

# ── Main ──────────────────────────────────────────
try:
    print("=== Cartesian Robot Motion Test ===")
    test_axis("X", X_STEP, X_DIR, X_LIMIT)
    test_axis("Y", Y_STEP, Y_DIR, Y_LIMIT)
    test_axis("Z", Z_STEP, Z_DIR, Z_LIMIT)
    print("\n=== All axes tested successfully! ===")

except KeyboardInterrupt:
    print("\nTest stopped by user")

finally:
    GPIO.output(ENABLE, GPIO.HIGH)  # Disable motors
    GPIO.cleanup()
    print("GPIO cleaned up ✅")