import RPi.GPIO as GPIO
import time

# ── Pin Definitions ─────────────────────────────
Y_STEP, Y_DIR = 22, 23
Z_STEP, Z_DIR = 24, 25

FORWARD  = GPIO.HIGH
BACKWARD = GPIO.LOW

# ── Motion Settings ─────────────────────────────
TEST_STEPS  = 2000

START_DELAY = 0.0015
MIN_DELAY   = 0.0010
RAMP_STEPS  = 300

# ── GPIO Setup ──────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [Y_STEP, Y_DIR, Z_STEP, Z_DIR]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# ── Ramp Motion Function ────────────────────────
def move_ramp(step_pin, dir_pin, steps, direction):
    GPIO.output(dir_pin, direction)

    ramp_steps = RAMP_STEPS
    if steps < 2 * ramp_steps:
        ramp_steps = steps // 2

    for i in range(steps):

        # ramp up
        if i < ramp_steps:
            delay = START_DELAY - (START_DELAY - MIN_DELAY) * (i / ramp_steps)

        # ramp down
        elif i >= steps - ramp_steps:
            delay = MIN_DELAY + (START_DELAY - MIN_DELAY) * (
                (i - (steps - ramp_steps)) / ramp_steps
            )

        # constant
        else:
            delay = MIN_DELAY

        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(delay)

# ── Axis Test ───────────────────────────────────
def test_axis(name, step_pin, dir_pin):
    print(f"\n--- {name} AXIS ---")

    print(f"{name}: FORWARD")
    move_ramp(step_pin, dir_pin, TEST_STEPS, FORWARD)
    time.sleep(1)

    print(f"{name}: BACKWARD")
    move_ramp(step_pin, dir_pin, TEST_STEPS, BACKWARD)
    time.sleep(1)

# ── Main Loop ───────────────────────────────────
try:
    while True:
        test_axis("Y", Y_STEP, Y_DIR)
        test_axis("Z", Z_STEP, Z_DIR)

except KeyboardInterrupt:
    print("\nStopped")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up")