#!/usr/bin/env python3

from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD

from time import sleep, strftime
from datetime import datetime
import time
import threading
import DHT
import Relay

def get_cpu_temp():     # get CPU temperature and store it into file "/sys/class/thermal/thermal_zone0/temp"
    tmp = open('/sys/class/thermal/thermal_zone0/temp')
    cpu = tmp.read()
    tmp.close()
    return '{:.2f}'.format( float(cpu)/1000 ) + ' C'

def get_time_now():     # get system time
    return datetime.now().strftime('%H:%M:%S ')

def loop():
    #print("hi")
    mcp.output(3,1)     # turn on LCD backlight
    lcd.begin(16,2)     # set number of LCD lines and columns
    while(True):
        lcd.clear()
        lcd.setCursor(0,0)  # set cursor position
        lcd.message( 'CPU: ' + get_cpu_temp()+'\n' )# display CPU temperature
        lcd.message( get_time_now() )   # display the time
        sleep(1)

def display_cimis():#local_temp, local_hum, c_temp, c_hum, local_ET, cimis_ET, water_saving, addi_water):
    mcp.output(3,1)     # turn on LCD backlight
    lcd.begin(16,2)     # set number of LCD lines and columns
    mode = None #mode for when the water is on or off
    sleep(1) #wait for DHT thread to start
    while True:
        lcd.clear()
        if(Relay.output==False): #water mode
            mode = 'On'
        else:
            mode = 'Off'
#Create strings for the variables
#part of this was using codes from Haden Yu
        relay_str = 'Mode: ' + mode + ' '
        local_temp_str = 'Local Temp:' + str(DHT.localTemp) + ' '
        local_hum_str = 'Local Humidity:' + str(DHT.localHumidity) + ' '
        c_temp_str = 'CIMIS Temp:' + str(DHT.cimisTemp) + ' '
        c_hum_str = 'CIMIS Humidity:' + str(DHT.cimisHumidity) + ' '
        local_ET_str = 'Local ET:' + str(DHT.ET0) + ' '
        cimis_ET_str = 'CIMIS ET:' + str(DHT.cimisET) + ' '
        water_saving_str = 'Water Saved:' + str(DHT.waterSaved) + ' '
        addi_water_str = 'Additional Water Used:' + str(DHT.additionalWater) + ' '
#end of create strings
        top_line = get_time_now() + relay_str + local_temp_str + local_hum_str #concatenate strings for top line on LCD
        #print(DHT.displaycimis)
        if(DHT.displaycimis):
            start = time.time()
            bot_line = c_temp_str + c_hum_str + local_ET_str + cimis_ET_str + water_saving_str + addi_water_str #concatenate strings for bottom line on LCD
            while True:
                if (time.time() - start) > 60: #don't display cismis data after a minute
                    DHT.displaycimis = False
                    break
                lcd.setCursor(0,0) # cursor top line
                lcd.message(top_line[:16]) #display top line
                lcd.setCursor(0,1) # cursor bottom line
                lcd.message(bot_line[:16])# display bottom line
                top_line = top_line[1:]+top_line[0]# send first char to last
                bot_line = bot_line[1:]+bot_line[0]# send first char to last
                sleep(0.1)
        else:
            while DHT.display:
                lcd.setCursor(0,0) # cursor top line
                lcd.message(top_line[:16]) #display message onto LCD
                top_line = top_line[1:]+top_line[0]# send first char to last
                sleep(0.1)

        sleep(0.5) #DHT time buffer


def destroy():
    lcd.clear()

PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        print ('I2C Address Error !')
        exit(1)
# Create LCD, passing in MCP GPIO adapter.
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

if __name__ == "__main__":
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
