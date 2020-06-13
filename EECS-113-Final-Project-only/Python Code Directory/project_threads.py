# Imports 
import cimis_extract as CIMIS
from lib.adafruit import DHT11 as DHT
import sensor as PIR
import datetime
import time
import threading
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
#global variables
global msg              # messages that LCD display will need to print
global scroll		# check if we should scroll lcd or not
global motor_state
global irrigation
global irrigation_time
global done
#initilize global variables
msg = '\n'
scroll = 0
motor_state = False
irrigation = True
irrigation_time = 5
done  = 0 
try:
   PCF8574_address = 0x27
   mcp = PCF8574_GPIO(PCF8574_address)  # I2C address of the PCF8574 chip.
   lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)
except:
    print("Unexpected Error")

def lcd_thread():           # LCD thread
    start = time.time()
    threshold = 86400          # time in seconds the thread is alive
    mcp.output(3,1)         # turn on LCD backlight
    lcd.begin (16, 2)       # set number of LCD lines and columns
    global scroll
    global msg
    #msg = 'CIMIS Temp : ' + cimis_temp + 'CIMIS Humidity : ' + cimis_humidity + 'Local Temp : ' + local_temp + 'Local Humidity : ' + local_humidity + 'Water Saved : ' + water_saved

    while True:
        lcd.clear()
        if scroll == 1:
            counter = len(msg)
            while counter > 17:
                lcd.setCursor(0,0)      # set cursor position
                lcd.message(msg[:16])
                lcd.setCursor(0,1)
                time.sleep(0.1)     # rate at which we update the LCD
                msg = msg[1:] + msg[0]
                counter -= 1
            scroll = 0
            msg = '\n'
        else:
            lcd.message(msg)
            time.sleep(5)
            lcd.clear() 
        if time.time() - start > threshold:
            global done
            done = 1
            break
    print("Exiting lcd thread")

def th_thread():            # temperature and humidity thread
    start = time.time()
    threshold = 86400          # time in seconds the thread is alive
    count = 0.0             # counts the number of times we detect data
    sum_temperature = 0.0   # sum of the temperature in the past hour
    sum_humidity = 0.0      # sum of humidity in the past hour
    average_humidity = 1.0  # average humidity in the past hour
    average_temperature = 1.0 # average temperature in the past hour
    average_time = time.time()  #start time since last average taken
    total_irrigation_time_local = 0
    total_irrigation_time_cimis = 0
    gallons_of_water_cimis = 0.0
    gallons_of_water_local = 0.0
    global msg
    global scroll
    global irrigation_time
    scroll = 0
    file = open("testfile.txt","w")
    while True:
        TH = DHT.loop()     # DHT.loop() return the temperature and humidity values in string format
        if scroll != 1:
            msg = TH        
        h = DHT.get_humidity()      # getting humidity
        t = DHT.get_temp()          # getting temperature
        c = DHT.get_chk()
        ch =  int(c)
        if ch == 0 and float(h) < 100.0:
            sum_humidity = float(h) + sum_humidity      # adding humidity values
            sum_temperature = float(t) + sum_temperature    # adding temperature values
            count = count + 1.0
        time.sleep(60)          # waiting time to fetch signal

        if time.time() - average_time >= 3600:       #computing the average once per hour
            if count != 0:
                average_humidity = sum_humidity/count      # computing averague humidity
                average_temperature = sum_temperature/count # computing average temperature
            print("DHT Average Values")
            print("average humidity : " + str(average_humidity))
            print("average temperature : " + str(average_temperature))

            ### CIMIS data are extracted and calculations are done ###
            ###  extractData(date1, date2) param format 'MM-DD-YYYY'
            date1 = datetime.datetime.now()
            date_1 = date1.strftime('%m-%d-%y')             #put date1 into MM-DD-YYYY format
            date2 = datetime.datetime.now()
            date_2 = date2.strftime('%m-%d-%y')              #put date1 into MM-DD-YYYY format
            cimis_et, cimis_h, cimis_t = CIMIS.getCimisData(CIMIS.extractData(date_1,date_2))	#get cimis et, hum, and temp values
            dft,dfh = CIMIS.getDeratingFactors(float(cimis_t),float(cimis_h),average_temperature,average_humidity)
            local_et = float(cimis_et) * dft * dfh
        
            scroll = 1


            water_local = CIMIS.getWateringInformation(local_et)
            water_cimis = CIMIS.getWateringInformation(cimis_et)

            if water_cimis >= 0:
                gallons_of_water_local = water_local + gallons_of_water_local
                gallons_of_water_cimis = water_cimis + gallons_of_water_cimis

            irrigation_time = (water_local/17)*60
            irrigation_time_cimis = (water_cimis/17)*60

            water_saved = float(gallons_of_water_local) - float(gallons_of_water_cimis)


            print("Irrigation time Local: " + str(irrigation_time) + '\n')
            print("Irrigation time CIMIS: " + str(irrigation_time_cimis) + '\n')

            total_irrigation_time_local = total_irrigation_time_local + irrigation_time
            total_irrigation_time_cimis = total_irrigation_time_cimis + irrigation_time_cimis

            print("Total Irrigation time so far (LOCAL_ET): " + str(total_irrigation_time_local) + '\n')
            print("Total Irrigation time so far (CIMIS_ET): " + str(total_irrigation_time_cimis) + '\n')


            msg = 'CIMIS ET = ' + "{0:.3f}".format(cimis_et) + ' CIMIS Temp = ' + "{0:.3f}".format(cimis_t) + ' CIMIS Hum = ' + "{0:.3f}".format(cimis_h)+ ' Local ET = ' + "{0:.3f}".format(local_et) + ' Local Temp = ' + "{0:.3f}".format(average_temperature) + ' Local Hum = ' + "{0:.3f}".format(average_humidity) + " Water Saved : " + "{0:.3f}".format(water_saved)
            file.write(msg + '\n' + 'Irrigation time (local_et + cimis_et): ' +  "{0:.3f}".format(irrigation_time) + 'Irrigation time (cimis et): ' +  "{0:.3f}".format(irrigation_time_cimis) + "Total Irrigation time (local): " +  "{0:.3f}".format(total_irrigation_time_local) + 'Total Irrigation time (cimis): ' +  "{0:.3f}".format(total_irrigation_time_cimis) + '\n')
            print("Data Pulling and analyzing results.")
            print(msg + "\n")
                
            time.sleep(40)
            t5 = threading.Thread(target = motor_thread)
            t3 =  threading.Thread(target = PIR_thread)
            t5.start()
            t3.start()
            
            
            sum_humidity = 0.0
            sum_temperature = 0.0
            count = 0.0
            average_time = time.time()          # restarting time for new average
        global done
        if done ==1:
            break

        #if time.time() - start > threshold:
        #    break
    
    file.close()
    print("Exiting th thread")

#thread use to check PIR movements
def PIR_thread():
    global msg
    global irrigation
    global motor_state
    global irrigation_time
    start = time.time()
    #threshold = 86400
    counter = 0                     #counter using right now to count up to 60 seconds of max waiting time
    while True:             
        if motor_state:    
            PIR_detect = PIR.loop()     #PIR.loop() returns boolean statement if movement is detected or not
            if (PIR_detect == True and irrigation == True): #if movement is detected while irrigation is on
                counter = time.time()
                irrigation = False  #set irrigation to false and stop sprinkler
                print("movement detected and turning off irrigation")
                if scroll == 0:
                    msg = "Movement detected \n Turning off irrigation"

            elif (PIR_detect == False): #if it is no longer detected
                irrigation = True #change irrigation back to true
                counter = 0
                if scroll == 0:
                    msg = "Irrigation ON"
            elif (time.time() - counter > 60): #if it is up to a minute
                irrigation = True #change irrigation back to true
                counter = 0 #change counter back to 0
                if scroll == 0:
                    msg = "Irrigation ON"
        if time.time() - start > irrigation_time:
            break
        
    print("exiting PIR thread")

def motor_thread(): # motor thread
    # setup()                 # setting up motor, commenting for setup() in Main
    global irrigation       
    global irrigation_time
    global motor_state
    relayState = False      # relay on or off
    count = 0               # count = 0 means irrigation has not started
    time_irrigation = time.time()   # starting time to next irrigation
    start = time.time()
    while True:
        if count == 0:                      # if irrigation hasn't started
            time_during_irrigation = time.time()       # timer for how long we are irrigating
            count = 1                       # irrigation started
            motor_state = True
        if irrigation:                         
            GPIO.output(relayPin, not relayState)   # if irrigation is true motor is on
        if not irrigation:
            GPIO.output(relayPin, relayState)       # if irrigation is false motor is off
            
        if time.time() - time_during_irrigation > irrigation_time:    # irrigation_time is the amount of time we are irrigating in seconds
            time_irrigation = time.time()               # after we finish irrigating, restart time for next irrigation
            count = 0                                   # set irrigation to "not started"
            time_during_irrigation = 0                  # reset the time we are irrigating
            GPIO.output(relayPin, relayState)           # turn off the motor/ sprinkler after we finish irrigating
            motor_state = False
            break
        #if time.time() - start > threshold:
         #   break
    #turn_off_motor()
    GPIO.output(relayPin, relayState)           # turn off the motor/ sprinkler after we finish irrigating
    print("Exiting motor thread")

