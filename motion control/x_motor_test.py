# TEST all 3 motors without limit switches (basic step/dir test)
import RPi.GPIO as GPIO
import time

# ── Pin Definitions ──
X_STEP, X_DIR = 17, 27
Y_STEP, Y_DIR = 22, 23
Z_STEP, Z_DIR = 24, 25

# ── Settings ──
STEP_DELAY = 0.001
TEST_STEPS = 400

# ── Setup ──
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [X_STEP, X_DIR, Y_STEP, Y_DIR, Z_STEP, Z_DIR]:
    GPIO.setup(pin, GPIO.OUT)

# ── Test ──
try:
    print("=== X Motor Test ===")
    print("Rotating X forward...")
    GPIO.output(X_DIR, GPIO.HIGH)
    for _ in range(TEST_STEPS):
        GPIO.output(X_STEP, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(X_STEP, GPIO.LOW)
        time.sleep(STEP_DELAY)
    print("X motor OK! ")
    time.sleep(0.5)

    print("\n=== Y Motor Test ===")
    print("Rotating Y forward...")
    GPIO.output(Y_DIR, GPIO.HIGH)
    for _ in range(TEST_STEPS):
        GPIO.output(Y_STEP, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(Y_STEP, GPIO.LOW)
        time.sleep(STEP_DELAY)
    print("Y motor OK! ")
    time.sleep(0.5)

    print("\n=== Z Motor Test ===")
    print("Rotating Z forward...")
    GPIO.output(Z_DIR, GPIO.HIGH)
    for _ in range(TEST_STEPS):
        GPIO.output(Z_STEP, GPIO.HIGH)
        time.sleep(STEP_DELAY)
        GPIO.output(Z_STEP, GPIO.LOW)
        time.sleep(STEP_DELAY)
    print("Z motor OK! ")

except KeyboardInterrupt:
    print("\nStopped by user")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up ")