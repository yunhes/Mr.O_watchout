#!/usr/bin/python
# Assignment 4 #

### import Python Modules ###
import threading
import RPi.GPIO as GPIO
import time
from datetime import datetime
import DHT
import LCD
import SenseLED

thermoPin = 11  # pin for the thermo sensor
ledPin = 12     # pin for motion LED
sensorPin = 16  # pin for the motion sensor
relayPin = 7 # pin for the relay

def setup():
    # setup the board input and output pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(sensorPin, GPIO.IN)
    GPIO.setup(relayPin, GPIO.OUT)
    GPIO.setup(ledPin, GPIO.OUT)
    GPIO.output(relayPin, True)         # initialize relay switch to off

def loop():
    #Start threads
    t_DHT = None
    print("starting DHT thread")
    t_DHT = threading.Thread(target=DHT.loop)
    t_DHT.daemon = True
    t_DHT.start()
    t_LCD = None
    print("starting LCD Thread")
    t_LCD = threading.Thread(target=LCD.display_cimis)
    t_LCD.daemon = True
    t_LCD.start()
    while(True):#function loops forever
        time.sleep(0.1)

def destroy():
    GPIO.output(relayPin, True)
    GPIO.output(ledPin, GPIO.LOW)
    GPIO.cleanup()

# main function to start program
if __name__ == '__main__':
    print("Program starting...")
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        LCD.destroy()
        destroy()
        exit()
