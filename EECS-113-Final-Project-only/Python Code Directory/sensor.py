import RPi.GPIO as GPIO

sensorPin = 15    # define the sensorPin

def setup():
#	print ('Program is starting...')
	GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
	GPIO.setup(sensorPin, GPIO.IN)    # Set sensorPin's mode is input

def loop():
	setup()
	if GPIO.input(sensorPin)==GPIO.HIGH:
#		print ("SENSOR DETECTED")
		return True
	else :
#		print ("SENSOR DID NOT DETECT")
		return False

def destroy():
	GPIO.cleanup()                     # Release resource

if __name__ == '__main__':     # Program start from here
	setup()
	try:
		loop()
	except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
		destroy()