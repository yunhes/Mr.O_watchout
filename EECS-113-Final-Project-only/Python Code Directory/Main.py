# Imports 
import cimis_extract as CIMIS
from lib.adafruit import DHT11 as DHT
import sensor as PIR
import time
import threading
from project_threads import *      #threads.py 
from lib.adafruit import I2CLCD1602 as lcd_display
from lib.adafruit.PCF8574 import PCF8574_GPIO
from lib.adafruit.Adafruit_LCD1602 import Adafruit_CharLCD 
import RPi.GPIO as GPIO

# Pin Definitions 
infrared_sensor = 15
relayPin = 13
DHT_11 = 11
blue_LED = 16
button = 12

def main():
    # Setup function on main
    setup()

    ### Initialize all threads 
    t1 = threading.Thread(target = th_thread)
    t2 = threading.Thread(target = lcd_thread)  
    #t3 = threading.Thread(target = PIR_thread)
    ### Start all Threads 
    t1.start()
    t2.start()
    #t3.start()

    ### cleanup after threads are done (not sure if this is going to be called)
    #cleanup()

### Function used to set up and initialize all pins. Called in Main()
def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(relayPin, GPIO.OUT) #initialize Relay 
    GPIO.setup(infrared_sensor, GPIO.IN) # initialize PIR sensor

### Function used to cleanup and
def cleanup():
    GPIO.output(relayPin,GPIO.LOW) # lower relay pin
    GPIO.cleanup() 

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
