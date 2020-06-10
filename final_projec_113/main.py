import RPi.GPIO as GPIO
import threading
import time
from datetime import datetime
#dht imports
import Freenove_DHT as DHT
#cimis imports
from cimisAPI import get_cimis_data_for
from cimisAPI import cimis_data
#lcd imports
import lcdAPI as LCD

#constants
ONE_HOUR = 60*60
starting_hour = -1
hours_to_run = 24
temperature_array = [None] * 24
humidity_array = [None] * 24

#define the pins
relayPin = 33    #GPIO 13
dhtPin = 11		 #GPIO 17
pirPin = 22      #GPIO 25

#define class for dht sensor
dht = None

#returns the current time as a string
def time_now():
	return datetime.now().strftime('[%H:%M:%S]')

#console message from the data thread
def console_msg1(message):
	print( datetime.now().strftime('[%H:%M:%S]') + "[Data thread] " + message )

#Console message from the main loop
def console_msg2(message):
	print( datetime.now().strftime('[%H:%M:%S]') + "[Main thread] " + message )

#Setup all the sensor pins and GPIO library
def setup():
	global dht
	console_msg2("Setting up ...")
	GPIO.setmode(GPIO.BOARD)	   #number GPIOs by physical location

	#Setup relay
	GPIO.setup(relayPin, GPIO.OUT, initial = GPIO.LOW) #set relay pin's mode as output

	#Setup dht
	dht = DHT.DHT(dhtPin)	#create a DHT class object

	#Setup lcd
	LCD.lcd_setup()

	#Setup pir
	GPIO.setup(pirPin, GPIO.IN)

#Cleanup all the sensors
def cleanup():
	console_msg2("Cleaning up. Please wait ...")
	GPIO.output(relayPin, GPIO.LOW)
	LCD.lcd_cleanup()
	GPIO.cleanup()
	console_msg2("Program terminated.")

#Interface with local dht sensor
def get_local_temperature():
	chk = None
	while ( chk is not dht.DHTLIB_OK ):  #read DHT11 and get a return the temperature value.
		chk = dht.readDHT11()

	return dht.temperature

def get_local_humidity():
	chk = None
	while ( chk is not dht.DHTLIB_OK ):  #read DHT11 and get a return the humidity value.
		chk = dht.readDHT11()

	return dht.humidity

#Thread aquires local data every hour and stores it in the appropriate arrays
def data_acquisition_thread():
	current_index = starting_hour
	hours_elapsed = 0
	#repeat until enough hours elapsed
	while ( hours_elapsed < hours_to_run ):
		average_temp = 0
		average_humidity = 0
		for i in range (0,60,1): #get one hour worth of data
			acquisition_time = time.time()
			local_temperature = get_local_temperature()
			local_humidity = get_local_humidity()
			average_temp = average_temp + local_temperature
			average_humidity = average_humidity + local_humidity
			console_msg1("Aquired local data #"+ str(i+1) + ": Temp = " +  str(local_temperature) + " Humidity = " + str(local_humidity) )
			LCD.display_local_data(i+1, local_temperature, local_humidity)
			acquisition_time = time.time() - acquisition_time
			if i is not 59:
				time.sleep ( 60 - acquisition_time )  #wait one minute

		average_temp = average_temp/60
		average_humidity = average_humidity/60

		console_msg1("One hour elapsed. Writing local data")
		print("Ave Temp = " + str(round(average_temp,1)) + " Ave Humidity = " + str(round(average_humidity)) )
		LCD.display_average_data(current_index, average_temp, average_humidity)
		temperature_array[current_index] = average_temp
		humidity_array[current_index] = average_humidity
		print(temperature_array)
		print(humidity_array)
		time.sleep ( 60 - acquisition_time ) #wait one minute for next hour
		current_index = (current_index +1) % 24
		hours_elapsed = hours_elapsed + 1

#Main loop of the program. Aquires cimis data every hour and waits for local data
#Computes time to irrigate and turns on the relay
def mainloop():
	console_msg2("Starting main loop")
	current_hour = starting_hour
	hours_elapsed = 0
	#wait one hour for data acquisition thread to get one hour of local data
	time.sleep( ONE_HOUR )

	total_delay = 0
	#begin irrigation loop
	while ( hours_elapsed < hours_to_run ):
		delay_this_hour = time.time()
		console_msg2("Attempting to get Cimis data for hour " + str(current_hour) + ":00")

		#Retrieve the cimis data for the past hour
		data = get_cimis_data_for(current_hour )
		while( data is None or data.get_humidity() is None or data.get_temperature() is None ):
			if data is None:
				console_msg2("A problem occured requesting data from Cimis. Will try again in one hour")
			else:
				console_msg2("Cimis data not yet available. Will try again in one hour")
			time.sleep( ONE_HOUR )	#try again after 1 hour

			console_msg2("Attempting to get Cimis data for hour " + str(current_hour) + ":00")
			data = get_cimis_data_for( current_hour )

		console_msg2("Obtained Cimis data for hour " + str(current_hour) + ":00")
		print("Date = "+ data.get_date()+ " Hour = "+ data.get_hour()+ " Humidity = "+ data.get_humidity(),
			  " Temperature = "+ data.get_temperature()+ " Eto = "+ data.get_eto())
		LCD.display_cimis_data(current_hour, data.get_temperature(), data.get_humidity())

		console_msg2("Attempting to get local data for hour " + str(current_hour) + ":00")
		#Retrieve the local data aquired by the data aquisition thread
		while(temperature_array[current_hour] is None or humidity_array[current_hour] is None):
			console_msg2("Local data for hour "+ str(current_hour) + ":00 not available. Will try again in 1 minute")
			time.sleep(60) #waits 60 seconds more if sensor is having trouble acquiring last data

		console_msg2("Obtained Local data for hour "+ str(current_hour) + ":00")
		local_temp = temperature_array[current_hour]
		local_humidity = humidity_array[current_hour]

		console_msg2("Local data ready for "+ str(current_hour) + ":00 ready: Ave Temp = " + str(round(local_temp,2)) + " Ave Humidity = " + str(round(local_humidity)) )

		temperature_array[current_hour] = None
		humidity_array[current_hour] = None

		#Calculate how long to irrigate for the current hour based on cimis data and local temperature
		time_to_irrigate = get_time_to_irrigate(data, local_temp, local_humidity)

		if time_to_irrigate == 0 :
			console_msg2("Eto is zero for hour "+ str(current_hour) + ":00. No need to irrigate for this hour")
		else:
			console_msg2("Turning on relay. Irrigate for " + str(time_to_irrigate) + " seconds")
			GPIO.output(relayPin, GPIO.HIGH)
			start_time = time.time()
			pause_time = 0
			while( time.time() < start_time + time_to_irrigate + pause_time  ):
				if( GPIO.input(pirPin) == GPIO.HIGH and pause_time < 60 ):
					console_msg2("Motion detected. Turning off irrigation for 10 seconds")
					GPIO.output(relayPin,GPIO.LOW)
					time.sleep(10)
					pause_time = pause_time + 10
					GPIO.output(relayPin,GPIO.HIGH)

			console_msg2("Turning off relay. Finished irrigation for hour " + str(current_hour) + ":00")
			GPIO.output(relayPin, GPIO.LOW)
#here

#Irrigation done
		current_hour = (current_hour +1) % 24
		hours_elapsed = hours_elapsed + 1

		delay_this_hour = time.time() - delay_this_hour
		total_delay = total_delay + delay_this_hour

		if( total_delay < ONE_HOUR):
			time.sleep(ONE_HOUR - total_delay)
			total_delay = 0
		else:
			total_delay = total_delay - ONE_HOUR


#returns the time to irrigate in seconds based on the cimis data and local average temperature and humidity
def get_time_to_irrigate(data, local_temperature, local_humidity):
	PF = 1.0  #plant factor for grass
	SF = 200 #area to irrigate (sq ft)
	IE = 0.75 #irrigation efficiency for sprinkler
	WD = 1020 #water debit per hour (gallons per hour)

	modified_eto = float(data.get_eto())* ( float(data.get_humidity()) / local_humidity )     \
										* ( local_temperature / float(data.get_temperature()) )

	gallons_needed_per_hour = modified_eto * PF * SF * 0.62 / IE / float(24)  #gallons needed per hour
	time_needed = gallons_needed_per_hour / WD #time needed to irrigate ( in hours )

	return time_needed * 60 * 60 #*ONE_HOUR

#main program
if __name__ == '__main__':
	t = None

	try:
		print("Starting program at",time.strftime( "%H:%M:%S" ,time.localtime(time.time())) )
		starting_hour = time.localtime(time.time()).tm_hour

		#setup gpio library
		setup()
		#create and start data aquisition thread
		t = threading.Thread(target = data_acquisition_thread)
		t.daemon = True
		console_msg2("Starting data aquisition thread")
		t.start()

		mainloop()

		t.join()
	except KeyboardInterrupt:
		print("Program interrupted")
	finally:
		cleanup()
