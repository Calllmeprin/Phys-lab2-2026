import RPi.GPIO as GPIO
import time

Y_STEP, Y_DIR = 22, 23
Z_STEP, Z_DIR = 24, 25

FORWARD = GPIO.HIGH
BACKWARD = GPIO.LOW

TEST_STEPS = 2000

Y_START_DELAY = 0.0015 # smooth start
Y_MIN_DELAY   = 0.0002 # +slow but smooth / - fast but loud
Y_RAMP_STEPS  = 380

Z_START_DELAY = 0.0015 # smooth start
Z_MIN_DELAY   = 0.0000 # +slow but smooth / - fast but loud
Z_RAMP_STEPS  = 380

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in [Y_STEP, Y_DIR, Z_STEP, Z_DIR]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def move_smooth(step_pin, dir_pin, steps, direction, start_delay, min_delay, ramp_steps):
    GPIO.output(dir_pin, direction)

    if steps < 2 * ramp_steps:
        ramp_steps = steps // 2 if steps >= 2 else 1

    for i in range(steps):
        if i < ramp_steps:
            delay = start_delay - (start_delay - min_delay) * (i / ramp_steps)
        elif i >= steps - ramp_steps:
            delay = min_delay + (start_delay - min_delay) * ((i - (steps - ramp_steps)) / ramp_steps)
        else:
            delay = min_delay

        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(delay)

try:
    print("Y forward")
    move_smooth(Y_STEP, Y_DIR, TEST_STEPS, FORWARD, Y_START_DELAY, Y_MIN_DELAY, Y_RAMP_STEPS)
    time.sleep(1)

    print("Y backward")
    move_smooth(Y_STEP, Y_DIR, TEST_STEPS, BACKWARD, Y_START_DELAY, Y_MIN_DELAY, Y_RAMP_STEPS)
    time.sleep(1)

    print("Z forward")
    move_smooth(Z_STEP, Z_DIR, TEST_STEPS, FORWARD, Z_START_DELAY, Z_MIN_DELAY, Z_RAMP_STEPS)
    time.sleep(1)

    print("Z backward")
    move_smooth(Z_STEP, Z_DIR, TEST_STEPS, BACKWARD, Z_START_DELAY, Z_MIN_DELAY, Z_RAMP_STEPS)

finally:
    GPIO.cleanup()