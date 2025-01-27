# led.py
# import RPi.GPIO as GPIO
from mock_gpio import GPIO

class LED:
    LED1 = 5
    LED2 = 6
    LED_MAX = 2
    LED_POSITION = 2
    
    def __init__(self):
        self.led_pin_table = [self.LED1, self.LED2]
        GPIO.setmode(GPIO.BCM)
        self.init_led()
    
    def init_led(self):
        for pin in self.led_pin_table:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
    
    def control_led(self, led_position):
        for i in range(self.LED_POSITION):
            if led_position & (1 << i):
                GPIO.output(self.led_pin_table[i], GPIO.HIGH)
            else:
                GPIO.output(self.led_pin_table[i], GPIO.LOW)