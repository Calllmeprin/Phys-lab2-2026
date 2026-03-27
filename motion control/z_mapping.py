import RPi.GPIO as GPIO
import time

Z_STEP = 24
Z_DIR  = 23

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Z_STEP, GPIO.OUT)
GPIO.setup(Z_DIR, GPIO.OUT)

def pulse(steps=300, delay=0.0015):
    for _ in range(steps):
        GPIO.output(Z_STEP, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(Z_STEP, GPIO.LOW)
        time.sleep(delay)

try:
    print("DIR = HIGH")
    GPIO.output(Z_DIR, GPIO.HIGH)
    pulse()
    time.sleep(2)

    print("DIR = LOW")
    GPIO.output(Z_DIR, GPIO.LOW)
    pulse()

finally:
    GPIO.cleanup()