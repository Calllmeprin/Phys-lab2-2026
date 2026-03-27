import RPi.GPIO as GPIO
import time

Y_STEP = 22
Y_DIR  = 23

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Y_STEP, GPIO.OUT)
GPIO.setup(Y_DIR, GPIO.OUT)

def move(direction, steps=500, delay=0.002):
    GPIO.output(Y_DIR, direction)
    for _ in range(steps):
        GPIO.output(Y_STEP, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(Y_STEP, GPIO.LOW)
        time.sleep(delay)

try:
    print("Y DIR=HIGH")
    move(GPIO.HIGH)
    time.sleep(2)

    print("Y DIR=LOW")
    move(GPIO.LOW)

finally:
    GPIO.cleanup()