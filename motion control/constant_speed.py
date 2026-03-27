import RPi.GPIO as GPIO
import time

Y_STEP, Y_DIR = 22, 23
Z_STEP, Z_DIR = 24, 25

FORWARD = GPIO.HIGH
BACKWARD = GPIO.LOW

TEST_STEPS = 1000
STEP_DELAY = 0.0015   # same speed for every step

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [Y_STEP, Y_DIR, Z_STEP, Z_DIR]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def move_constant(step_pin, dir_pin, steps, direction, delay):
    GPIO.output(dir_pin, direction)

    for _ in range(steps):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(delay)

try:
    print("Y forward")
    move_constant(Y_STEP, Y_DIR, TEST_STEPS, FORWARD, STEP_DELAY)
    time.sleep(1)

    print("Y backward")
    move_constant(Y_STEP, Y_DIR, TEST_STEPS, BACKWARD, STEP_DELAY)
    time.sleep(1)

    print("Z down")
    move_constant(Z_STEP, Z_DIR, TEST_STEPS, FORWARD, STEP_DELAY)
    time.sleep(1)

    print("Z up")
    move_constant(Z_STEP, Z_DIR, TEST_STEPS, BACKWARD, STEP_DELAY)

finally:
    GPIO.cleanup()