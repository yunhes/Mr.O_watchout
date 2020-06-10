###Name: Yiyu Qian
###ID: 26072996

import RPi.GPIO as GPIO
import time
import Freenove_DHT as DHT
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
from time import sleep, strftime
from datetime import datetime
from datetime import date
import urllib.request
import codecs
import csv

DHTPin = 11 #define the pin of DHT11

#read values from dht sensor and return normal values only 
def read_Sensor(): 
    dht = DHT.DHT(DHTPin) #create a DHT class object
    chk = dht.readDHT11() #read DHT11 and get a return value.

    if (chk is dht.DHTLIB_OK): #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
        print("DHT11,OK!")

    elif(chk is dht.DHTLIB_ERROR_CHECKSUM): #data check has errors
        print("DHTLIB_ERROR_CHECKSUM!!")

    elif(chk is dht.DHTLIB_ERROR_TIMEOUT): #reading DHT times out
        print("DHTLIB_ERROR_TIMEOUT!")

    else:                               #other errors 
        print("Other error!")
  

    print("Humidity : %.2f \t Temperature : %.2f \n"%(dht.humidity,dht.temperature))

    return (dht.humidity, dht.temperature)

    
def destroy():
    lcd.clear()

#calculate average temperature and humidity 
def get_Avg(humidity, temperature):
    
    avg_humidity = sum(humidity) / len (humidity)
    avg_temperature = sum(temperature)/ len(temperature) 

    return (avg_humidity, avg_temperature)

def CIMIS_data(date, hour):   #read data from CIMIS
    
    ftp = urllib.request.urlopen("ftp://ftpcimis.water.ca.gov/pub2/hourly/hourly075.csv")
    csv_file = csv.reader(codecs.iterdecode(ftp, 'utf-8'))

    data = [] #list stores dictionaries

    date_list = [] # list stores all dates in csv file

    counter = 0; #count row number as index
    
   # store every row as a dictionary in the data list 
    for row in csv_file:
        d = dict(index = counter, date = row[1], hour = row[2], ETo = row[4], Air_Temperature = row[12], Rel_Hum = row[14])
        data.append(d)
        if (row[1] not in date_list):
            date_list.append(row[1])
        counter += 1

    # in case the CIMIS has not updated today's data yet. ex. 6/6/2020, 0:42, but CIMIS only has data up to 6/5/2020
    if (date not in date_list): 
        last_row = data[counter]    # I use data from the last row's dictionary
        ETo = last_row['ETo']
        Air_Temperature = last_row['Air_Temperature']
        Rel_Hum = last_row['Rel_Hum']
        row_index = last_row['index']


    # get values of the corresponding date and hour 
    for element in data:
        if (element['date'] == date) and (element['hour'] == hour):
            ETo = element['ETo']
            Air_Temperature = element['Air_Temperature']
            Rel_Hum = element['Rel_Hum']
            row_index = element['index']

            
    # in case the CIMIS does not update the data once per hour, I use last recent hour's data
    while (ETo == '--'):
        row_index -= 1 #go back to the previous row 
        for element in data:
            if (element['index'] == row_index): #search the data of the previous row's dictionary
                ETo = element['ETo']
                Air_Temperature = element['Air_Temperature']
                Rel_Hum = element['Rel_Hum']   
            
    return ETo, Rel_Hum, Air_Temperature


def irrigation(ETo):
    
    Gallons_Water_per_day = (ETo * 1 * 200 * 0.62) / 0.75
    Gallons_Water_per_hour = Gallons_Water_per_day / 24

    return Gallons_Water_per_hour

    
                                        
PCF8574_address = 0x27 # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F # I2C address of the PCF8574A chip.
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


if __name__ == '__main__':
    print ('Program is starting ... ')

    sumCnt = 0 #number of reading times

    temperature = [] #list stores values of temperature
    humidity = [] #list stores values of humidity 

    mcp.output(3,1) #turn on LCD backlight
    lcd.begin(16,2) #set number of LCD lines and columns

    
    while True:
        try:
            hum, temp = read_Sensor()
            if (hum != -999.00) or (temp != -999.00):
                humidity.append(hum)
                temperature.append(temp)

            destroy()
            #lcd.clear()
            lcd.setCursor(0,0) # set cursor position

            hum = '{:.2f}'.format(hum)
            temp = '{:.2f}'.format(temp)
              
            lcd.message( 'H: ' + hum + ' %\n' ) #display the humidity
            lcd.message( 'T: ' + temp + ' C' ) #display temperature 
            
            sumCnt += 1 
            if sumCnt == 60:   # use 5 for testing

                time.sleep(2)
                
                avg_hum, avg_temp = get_Avg(humidity, temperature)
                print("Avg Humidity : ", avg_temp, "   Avg Temperature : ", avg_hum, '\n') 

                Date = (date.today()).strftime('%m/%d/%Y')    #get current date                
                Hour = (datetime.now().time()).strftime("%H") #get current hour
                
                #lcd.clear()
                destroy()
                lcd.setCursor(0,0) # set cursor position

                x =  '{:.2f}'.format(avg_hum)
                y =  '{:.2f}'.format(avg_temp)

                lcd.message( 'AVG H: ' + x + ' %\n' )# display average humidity
                lcd.message( 'AVG T: ' + y + ' C') # display the average temperature 
                
                #modify the date format
                Date = Date.split('/')
                Date.insert(1,'/')
                Date.insert(3,'/')

                for i in range(len(Date)):
                    if Date[i][0] == '0':
                        Date[i] = Date[i][1:]

                Date = ''.join(Date)

                #modify the hour format
                if Hour == '00':
                    Hour = '2400'
                else:
                    Hour = Hour + '00'

                print("Current date is : ", Date, "   Current hour is : ", Hour, '\n')
                               
                ETo_CIMIS, CIMIS_Hum, CIMIS_Temperature = CIMIS_data(Date, Hour)

                print("ETo_CIMIS : ",ETo_CIMIS, "    CIMIS_Hum : ", CIMIS_Hum, "    CIMIS_Temperature : ", CIMIS_Temperature, '\n')
      
                time.sleep(2)

                #lcd.clear()
                destroy()
                lcd.setCursor(0,0) # set cursor position
    
                lcd.message( 'CIMIS H: ' + CIMIS_Hum + ' %\n' ) #display the CIMIS humidity
                lcd.message( 'CIMIS T: ' + CIMIS_Temperature + ' F') #display the CIMIS temperature
                
                #convert string to float
                ETo_CIMIS = float(ETo_CIMIS)
                CIMIS_Hum = float(CIMIS_Hum)
                CIMIS_Temperature = float(CIMIS_Temperature)

                #convert F to C
                CIMIS_Temperature = (CIMIS_Temperature - 32) * (5/9)

                #calculate local ETo
                ETo_Local = ETo_CIMIS * (avg_temp/CIMIS_Temperature) * (avg_hum/CIMIS_Hum)
                print("ETo_Local : ", ETo_Local, '\n')

                time.sleep(2)

                #lcd.clear()
                destroy()
                lcd.setCursor(0,0) # set cursor position

                x =  '{:.2f}'.format(ETo_CIMIS)
                y =  '{:.2f}'.format(ETo_Local)
                
                lcd.message( 'CIMIS ETo: ' + x + '\n' ) #display the ETo_CIMIS
                lcd.message( 'Local ETo: ' + y) #display the ETo_Local

                result = irrigation( ETo_Local)                
              
                sumCnt = 0  #reset number of reading times
                
                temperature.clear() #clear the temperature list
                humidity.clear() #clear the humidity list
                
            time.sleep(60) #sleep for 60 seconds to get value every minute, use 3 for testing 
            
                    
        except KeyboardInterrupt:
            destroy()
            GPIO.cleanup()
            exit()  
