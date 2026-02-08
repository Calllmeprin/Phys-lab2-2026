import cv2
import os
import pytesseract
import RPi.GPIO
import time
GPIO = RPi.GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# motion controls value, currently all are placeholder values and are subject to change
x_step = 67 
x_dir = 67
x_enable = 67
X_limit = 67

y_step = 16
y_dir = 24
y_enable = 11
y_limit = 17

z_step = 21
z_dir = 20
z_enable = 16
z_dir = 20
z_enable = 16
z_dir_limit = 25

ServoPin = 12
RelayPin = 18

GPIO.setup([x_step, x_dir, x_enable, y_step, y_dir, y_enable, z_step, z_dir, z_enable, z_dir_limit, RelayPin,ServoPin], GPIO.OUT)
GPIO.setup([X_limit, z_dir_limit, y_limit], GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.output(x_enable, GPIO.LOW)
GPIO.output(y_enable, GPIO.LOW)
GPIO.output(z_enable, GPIO.LOW)

class Axis:
    def __init__(self, step_pin, dir_pin, enable_pin, X_limit, step_per_unit):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.X_limit = X_limit
        self.current_position = 0
        self.step_per_unit = step_per_unit 
        
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.output(self.enable_pin, GPIO.LOW)
        GPIO.setup(self.X_limit, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def dir(self, direction):
        GPIO.output(self.dir_pin, direction)

    def home(self, direction, delay=0.002): 
        GPIO.pulse(self.dir_pin, direction) 
            
    def pulse(self, direction,delay=0.002): #send a simgle pulse to the stepper motor
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(delay)

        GPIO.output(self.dir_pin, direction)

    def hit_limit(self):
        return GPIO.input(self.X_limit) == GPIO.LOW

def move_xyz_absolute(self, x_target, y_target, z_target, delay=0.002): 
         
    x_steps = int(abs(x_target - x.current_position) * x.step_per_unit)
    y_steps = int(abs(y_target - y.current_position) * y.step_per_unit)
    z_steps = int(abs(z_target - z.current_position) * z.step_per_unit)

    x_dir = GPIO.HIGH if x_target > x.current_position else GPIO.LOW
    y_dir = GPIO.HIGH if y_target > y.current_position else GPIO.LOW  
    z_dir = GPIO.HIGH if z_target > z.current_position else GPIO.LOW

    while x_steps > 0 or y_steps > 0 or z_steps > 0:
        if x_steps > 0:
            x_pulse(x_dir, delay)
            x_steps -=1

        if y_steps > 0:
            y_pulse(y_dir, delay)
            y_steps -=1

        if z_steps > 0:
            z_pulse(z_dir, delay)
            z_steps -=1

        x.current_position = x_target
        y.current_position = y_target
        z.current_position = z_target

        for _ in range(int(x_steps)):
            GPIO.output(x.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(x.step_pin, GPIO.LOW)
            time.sleep(delay)

        for _ in range(int(y_steps)):
            GPIO.output(y.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(y.step_pin, GPIO.LOW)
            time.sleep(delay)

        for _ in range(int(z_steps)):
            GPIO.output(z.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(z.step_pin, GPIO.LOW)
            time.sleep(delay)

def home_axis(axis, direction, delay=0.002):
    axis.dir(direction)
    while not axis.hit_limit():
        axis.pulse(axis, direction, delay)
    axis.current_position = 0

def home_all_axes():
    z_dir = GPIO.HIGH
    x_dir = GPIO.LOW

    z.home(z, GPIO.HIGH)
    x.home(x, GPIO.LOW)

servo = GPIO.PWM(ServoPin, 50)
servo.start(0)
servo.ChangeDutyCycle(7.5)  # 90 degrees
servo.ChangeDutyCycle(0)    # Stop sending signal to servo

RelayPin = 18 
GPIO.setup(RelayPin, GPIO.OUT)
GPIO.output(RelayPin, GPIO.HIGH)  # Turn relay ON

pytesseract.pytesseract.tesseract_cmd='/usr/bin/tesseract'  

pill_labels = "labels"
output = "ocrfinished"

for i in range (1,101):
    filename= f"label{i:02d}.jpg"
    img_path= os.path.join(pill_labels, filename)

    img= cv2.imread(img_path)
    if img is None:
            print(f"File{filename}notfound")

    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray,lang= 'eng',config='--psm 6')
    print(f"Extracted text from file {i}: {text}")