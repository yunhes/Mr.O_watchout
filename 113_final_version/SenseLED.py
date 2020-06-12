import RPi.GPIO as GPIO
import time

ledPin = 12
sensorPin = 16
senvar = 0          # variable to signal to relay thread to pause irrigation
start = True

def setup():
    print('IR Program is starting...')
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(ledPin, GPIO.OUT)
    GPIO.setup(sensorPin, GPIO.IN)

def loop():
    global senvar

    # use start variable from relay as interrupt for loop
    while start:
        # read the signal from the motion sensor pin
        i = GPIO.input(sensorPin)
        # if motion sensed by sensor, turn on LED
        if i == GPIO.HIGH:
            GPIO.output(ledPin, GPIO.HIGH)
            senvar = 1          # pause irrigation

        # if motion not sensed by sensor, turn off LED
        elif i == GPIO.LOW:
            GPIO.output(ledPin, GPIO.LOW)
            senvar = 0          # resume irrigation

        # small delay
        time.sleep(0.1)

    # when relay loop is finished, set all outputs to low
    GPIO.output(ledPin, GPIO.LOW)
    senvar = 0
    return

def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
