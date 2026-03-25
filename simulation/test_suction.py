import RPi.GPIO as GPIO
import time

# ── Pin Setup ─────────────────────────
SUCTION_PIN = 16   # change if needed

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(SUCTION_PIN, GPIO.OUT)

# Start with suction OFF
GPIO.output(SUCTION_PIN, GPIO.LOW)

print("=== Suction Test Start ===")

try:
    while True:
        print("\n1. Turn ON suction")
        print("2. Turn OFF suction")
        print("3. Pulse test (ON → OFF)")
        print("4. Exit")

        choice = input("Select option: ")

        if choice == "1":
            GPIO.output(SUCTION_PIN, GPIO.HIGH)
            print("Suction ON 🟢")

        elif choice == "2":
            GPIO.output(SUCTION_PIN, GPIO.LOW)
            print("Suction OFF 🔴")

        elif choice == "3":
            print("Suction ON...")
            GPIO.output(SUCTION_PIN, GPIO.HIGH)
            time.sleep(3)

            print("Suction OFF...")
            GPIO.output(SUCTION_PIN, GPIO.LOW)

        elif choice == "4":
            break

        else:
            print("Invalid option")

except KeyboardInterrupt:
    print("\nStopped manually")

finally:
    GPIO.output(SUCTION_PIN, GPIO.LOW)
    GPIO.cleanup()
    print("GPIO cleaned up ✅")