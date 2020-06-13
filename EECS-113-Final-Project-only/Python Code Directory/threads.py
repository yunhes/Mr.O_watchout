# Imports 
import cimis_extract as CIMIS
from lib.adafruit import DHT11 as DHT
import sensor as PIR
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
#initilize global variables
msg = '\n'
scroll = 0
motor_state = False
irrigation = True
irrigation_time = 5
try:
   PCF8574_address = 0x27
   mcp = PCF8574_GPIO(PCF8574_address)  # I2C address of the PCF8574 chip.
   lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)
except:
    print("Unexpected Error")

def lcd_thread():           # LCD thread
    start = time.time()
    threshold = 300          # time in seconds the thread is alive
    mcp.output(3,1)         # turn on LCD backlight
    lcd.begin (16, 2)       # set number of LCD lines and columns
    global scroll
    global msg
#    msg = 'CIMIS Temp : ' + cimis_temp + 'CIMIS Humidity : ' + cimis_humidity + 'Local Temp : ' + local_temp + 'Local Humidity : ' + local_humidity + 'Water Saved : ' + water_saved

    while True:
        lcd.clear()
        if scroll == 1:
            counter = len(msg)
            while counter > 17:
                lcd.setCursor(0,0)      # set cursor position
                lcd.message(msg[:16])
                lcd.setCursor(0,1)
                time.sleep(0.5)     # rate at which we update the LCD
                msg = msg[1:] + msg[0]
                counter -= 1
            scroll = 0
        else:
            lcd.message(msg)
            time.sleep(1)
            lcd.clear() 
        if time.time() - start > threshold:
            break
    print("Exiting lcd thread")

def th_thread():            # temperature and humidity thread
    start = time.time()
    threshold = 300          # time in seconds the thread is alive
    count = 0.0             # counts the number of times we detect data
    sum_temperature = 0.0   # sum of the temperature in the past hour
    sum_humidity = 0.0      # sum of humidity in the past hour
    average_humidity = 1.0  # average humidity in the past hour
    average_temperature = 1.0 # average temperature in the past hour
    average_time = time.time()  #start time since last average taken
    global msg
    global scroll
    scroll = 0
    file = open("testfile.txt","w")
    while True:
      #  global TH
        # Does DHT.loop() actually return anything? Seems to be kicking syntax errors
        TH = DHT.loop()     # DHT.loop() return the temperature and humidity values in string format
        if scroll != 1:
            msg = TH        
        h = DHT.get_humidity()      # getting humidity
        t = DHT.get_temp()          # getting temperature
        c = DHT.get_chk()
        ch =  int(c)
        if ch == 0:
            sum_humidity = float(h) + sum_humidity      # adding humidity values
            sum_temperature = float(t) + sum_temperature    # adding temperature values
            count = count + 1.0
        time.sleep(10)          # waiting time to fetch signal
        if time.time() - start > threshold:
            break
            file.close()
        if time.time() - average_time >= 70:        # 300 = (time in seconds) time elapsed for the average
            if count != 0:
                average_humidity = sum_humidity/count      # computing averague humidity
                average_temperature = sum_temperature/count # computing average temperature
            print("average humidity : " + str(average_humidity))
            print("average temperature : " + str(average_temperature))

            ### CIMIS data are extracted and calculations are done ###
            cimis_et, cimis_h, cimis_t = CIMIS.getCimisData(CIMIS.extractData())	#get cimis et, hum, and temp values
            dft,dfh = CIMIS.getDeratingFactors(float(cimis_t),float(cimis_h),average_temperature,average_humidity)
            local_et = float(cimis_et) * dft * dfh
            msg = 'CIMIS ET = ' + "{0:.3f}".format(cimis_et) + ' CIMIS Temp = ' + "{0:.3f}".format(cimis_t) + ' CIMIS Hum = ' + "{0:.3f}".format(cimis_h)+ '\n Local ET = ' + "{0:.3f}".format(local_et) + ' Local Temp = ' + str(average_temperature) + ' Local Hum = ' + str(average_humidity) + '\n'
            file.write(msg)
            scroll = 1
            t5 = threading.Thread(target = motor_thread)
            t5.start()
            time.sleep(10)
            sum_humidity = 0.0
            sum_temperature = 0.0
            count = 0.0
            average_time = time.time()          # restarting time for new average
    print("Exiting th thread")

#thread use to check PIR movements
def PIR_thread():
    global msg
    global irrigation
    global motor_state
    start = time.time()
    threshold = 300
    counter = 0                     #counter using right now to count up to 60 seconds of max waiting time
    # PIR.setup()  # commenting for setup() in main
    while True:             
        if motor_state:
            #global irrigation       
            PIR_detect = PIR.loop()     #PIR.loop() returns boolean statement if movement is detected or not
            if (PIR_detect == True and irrigation == True): #if movement is detected while irrigation is on
                #if counter == 0:    #if counter is 0 (the first second it is detected)
                #lcd.clear()        #clear LCD to output message
                counter = time.time()
                irrigation = False  #set irrigation to false and stop sprinkler
                #    lcd.message ("Movement detect and turning off irrigation\n")    #output message on LCD
                print("movement detected and turning off irrigation")
                msg = "Movement detected \n Turning off irrigation"
                #else:   #wait for max a minute or when PIR is no longer detected
                #    lcd.message ("waiting")
                #    print("waiting")

            elif (PIR_detect == False): #if it is no longer detected
            #    print("movement no longer detected so irrigation turn to True")
                irrigation = True #change irrigation back to true
                counter = 0

            elif (time.time() - counter > 5): #if it is up to a minute
                #print("counter is up to 60 so irrigation turn to True")
                irrigation = True #change irrigation back to true
                counter = 0 #change counter back to 0
        #counter = counter + 1
        if time.time() - start > threshold:
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
    #threshold = 300       # total time the relay is alive
    while True:
        #if time.time() - time_irrigation > 5:   # after "5" seconds start irrigating
        if count == 0:                      # if irrigation hasn't started
            time_during_irrigation = time.time()       # timer for how long we are irrigating
            count = 1                       # irrigation started
            motor_state = True
        if irrigation:                         
            GPIO.output(relayPin, not relayState)   # if irrigation is true motor is on
        if not irrigation:
            GPIO.output(relayPin, relayState)       # if irrigation is false motor is off
            
        if time.time() - time_during_irrigation > irrigation_time:    # 5 is the amount of time we are irrigating in seconds
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

