#!/usr/bin/env python3


import threading
import time
import RPi.GPIO as GPIO
import DHT
import SenseLED as PIR

thermoPin = 11
ledPin = 12
sensorPin = 16
relayPin = 7
output = True          # system initialized to off

def loop():
    global output

    # convert irrigation time from minutes to seconds
    runTime = DHT.irrigationTime*60

    if (runTime == 0):
        return

    start = time.time()     # get the start time of irrigation

    output = False

    # send signal to relay switch to turn on motor
    GPIO.output(relayPin, output)

    # loop to keep irrigation on
    print("Start irrigating")
    PIR.start = True

    # start a new thread for the PIR sensor
    t = None
    print("starting PIR thread")
    t = threading.Thread(target=PIR.loop)
    t.daemon = True
    t.start()

    while (True):
        # if the motion sensor triggered, pause system
        if (PIR.senvar == 1):
            print("Pause irrigation")
            output = True
            GPIO.output(relayPin, True) # send signal to relay to turn off the motor

            # loop to wait 1 min or until motion no longer detected
            pauseStart = time.time()
            while(True):
                # break loop and resume irrigation if 1 min exceeded
                if ((time.time()-pauseStart) > 60):
                    output = False
                    GPIO.output(relayPin, False)
                    break
                # resume irrigation if motion no longer detected
                if (PIR.senvar == 0):
                    output = False
                    GPIO.output(relayPin, False)
                    break

                runTime += 0.5      # add the extra paused time to the run time
                time.sleep(0.5)     # quick sleep delay
            print("Resume Irrigation")

        # if irrigation pause over a minute, resume irrigating
        if ((time.time()-start) > runTime):
            output = True
            GPIO.output(relayPin, True)
            break

        # 0.5 second sleep delay for loop/sensor
        time.sleep(0.5)

    # when finished irrigation time, kill PIR thread
    PIR.start = False
    print("Stop irrigation")

def setup():
    # setup the board input and output pins
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(sensorPin, GPIO.IN)
    GPIO.setup(relayPin, GPIO.OUT)
    GPIO.setup(ledPin, GPIO.OUT)

def destroy():
    GPIO.output(relayPin, True)
    GPIO.output(ledPin, GPIO.LOW)
    GPIO.cleanup()

# main function to start program
if __name__ == '__main__':
    global systemState
    print("Program starting...")
    setup()
    try:
        systemState = True
        loop()
    except KeyboardInterrupt:
        destroy()
        exit()
