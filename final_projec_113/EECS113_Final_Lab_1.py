



import RPi.GPIO as GPIO
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
import time
from time import sleep

import Freenove_DHT as DHT
from datetime import datetime
from threading import *
from requests.exceptions import HTTPError
import io

import requests
import json


RelayPin = 7  # define the ledPin
sensorPin = 29    # define the sensorPin
DHTPin = 11     #define the pin of DHT11

PrevS = False  # False for OFF, True for ON
CurrS = False


result_hum = 0              # sum for humidity and temperature
result_temp = 0
cnt_hum = 0
cnt_temp = 0
cnt_hour = 0
hourtemp_val = 0
hourhum_val= 0
data = None

text = ''
watertime = 0

class HT_sensor(Thread):

  
    def setup(self):
        
        # motion sensor & Relay
        GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
        GPIO.setup(RelayPin, GPIO.OUT)   # Set ledPin's mode is output
        GPIO.setup(sensorPin, GPIO.IN)    # Set sensorPin's mode is input


    def loop(self):
        
        global text
        global watertime
        
        global hourhum_val
        global hourtemp_val
        global cnt_hour
        global result_hum
        global result_temp
        global cnt_hum
        global cnt_temp
        
        #print(date+"(inside loop)")
        
        dht = DHT.DHT(DHTPin)   #create a DHT class object
        sumCnt = 0              #number of reading times
        

        hourhum_val = hourtemp_val = cnt_hour = 0
        cimis_tmp = None
        
        for cnt_hour in range (60):
            if(cimis_tmp == None):
                try:
                    global data
                    data=requests.get(self.url).json()
                except HTTPError as http_err:
                    print("HTTP error occurred:",http_err)
                except Exception as err:
                    print("Other error occurred:",err)
                else:
                    cimis_tmp=data['Data']['Providers'][0]['Records'][self.now.hour-2]['HlyAirTmp']['Value']
                    print("cimis success")
                    
                
            for i in range(60):
                sumCnt += 1         #counting number of reading times
                chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
                print ("The sumCnt is : %d, \t chk    : %d"%(sumCnt,chk))
                if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
                    print("DHT11,OK!")
                    result_hum += dht.humidity
                    result_temp += dht.temperature*1.8+32 #dht.temp in Celsius
                    cnt_hum+=1
                    cnt_temp+=1
                elif(chk is dht.DHTLIB_ERROR_CHECKSUM): #data check has errors
                    print("DHTLIB_ERROR_CHECKSUM!!")
                elif(chk is dht.DHTLIB_ERROR_TIMEOUT):  #reading DHT times out
                    print("DHTLIB_ERROR_TIMEOUT!")
                else:               #other errors
                    print("Other error!")
                    
                print("Humidity : %.2f, \t Temperature : %.2f \n"%(dht.humidity,dht.temperature*1.8+32)) # dht.temp in Celsius
                
                
                
                sleep(1)
                self.lcd.DisplayLeft()
                
                i+=1
                
            print("%.2f "%(result_temp/cnt_temp))
            print("%.2f "%(result_hum/cnt_hum))
            self.lcd.setCursor(0,0)
            self.lcd.message("%.2f "%(result_temp/cnt_temp))
            self.lcd.setCursor(0,1)
            self.lcd.message("%.2f "%(result_hum/cnt_hum))
            
            
            hourtemp_val  += result_temp/cnt_temp
            hourhum_val += result_hum/cnt_hum  
            cnt_hour +=1


        
        
            
    def destroy(self):
        self.lcd.clear()
        GPIO.cleanup()
        
    def run(self):

        PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
        PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.

        global result_hum
        global result_temp
        global cnt_hum
        global cnt_temp
        global cnt_hour
        global hourtemp_val
        global hourhum_val
        global data

        # Create PCF8574 GPIO adapter.
        try:
            # self.lcd
            try:
                    mcp = PCF8574_GPIO(PCF8574_address)
            except:
                    try:
                            mcp = PCF8574_GPIO(PCF8574A_address)
                    except:
                            print ('I2C Address Error for HT_sensor!')
                            exit(1)
            
            
            
            # Create self.lcd, passing in MCP GPIO adapter.
            self.lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)
            mcp.output(3,1)     # turn on LCD backlight
            self.lcd.begin(16,2)     # set number of LCD lines and columns
            self.lcd.setCursor(0,0)  # set cursor position
            self.lcd.clear()
            self.lcd.message("Weather Station\n") #display  main title of progra
            self.lcd.message("sampling data..\n")
            
            self.setup()
            
            header ="Date\t\tHour\tLocalHum\tLocalTmp\tLocalEto\tCIMISHum\tCIMISTmp\tCIMISEto\n"
            if not open("file.txt").readlines():
                print("empty file, write header")
                open("file.txt","w").write(header)
            else:
                print("file not empty")
                print(open("file.txt").readlines())
            
            
                    
            
            while(True):
                
                self.now = datetime.now()
                if self.now.hour == 0 or self.now.hour == 1 or self.now.hour == 2:
                    self.now_list = [str(self.now.year), str(self.now.month), str(self.now.day-1)]
                    hour = self.now.hour+22
                else:
                    self.now_list = [str(self.now.year), str(self.now.month), str(self.now.day)]
                    hour = self.now.hour-2
                #self.now_list = [str(self.now.year), str(self.now.month), str(self.now.day)]
                date = self.now_list[0]+"-"+self.now_list[1]+"-"+self.now_list[2]
                print(date)
                print(hour)
                self.url = "http://et.water.ca.gov/api/data?appKey=55a1b0c5-298b-4fd5-9c42-2576c839580d&targets=75&startDate="+date+"&endDate="+date+"&unitOfMeasure=E&dataItems=hly-eto,hly-air-tmp,hly-rel-hum"
                
                self.loop()
                                
                print("Humidity : %.2f, \t Temperature : %.2f \n"%(result_hum/cnt_hum, result_temp/cnt_temp)) 
                
                
        #        self.now = datetime.now()
        #        if self.now.hour == 0 or self.now.hour == 1 or self.now.hour == 2:
        #            self.now_list = [str(self.now.year), str(self.now.month), str(self.now.day-1)]
        #            hour = self.now.hour+22
        #        else:
        #            self.now_list = [str(self.now.year), str(self.now.month), str(self.now.day)]
        #            hour = self.now.hour-2
        #            
        #        #self.now_list = [str(self.now.year), str(self.now.month), str(self.now.day)]
        #        date = self.now_list[0]+"-"+self.now_list[1]+"-"+self.now_list[2]
        #        print(date)
        #        print(hour)
        #    
        #        
        #        #self.url = "http://et.water.ca.gov/api/data?appKey=55a1b0c5-298b-4fd5-9c42-2576c839580d&targets=75&startDate="+self.now.strftime("%Y-%m-%d")+"&endDate="+self.now.strftime("%Y-%m-%d")+"&unitOfMeasure=M&dataItems=hly-eto,hly-air-tmp,hly-rel-hum"
        #        #self.url = "http://et.water.ca.gov/api/data?appKey=55a1b0c5-298b-4fd5-9c42-2576c839580d&targets=75&startDate=2019-6-12&endDate=2019-6-12&unitOfMeasure=M&dataItems=hly-eto,hly-air-tmp,hly-rel-hum"
        #        self.url = "http://et.water.ca.gov/api/data?appKey=55a1b0c5-298b-4fd5-9c42-2576c839580d&targets=75&startDate="+date+"&endDate="+date+"&unitOfMeasure=E&dataItems=hly-eto,hly-air-tmp,hly-rel-hum"

        #        data=requests.get(self.url).json()
                for index in range( 0, len(data['Data']['Providers'][0]['Records'])):
                    if index == hour:
                        #print(index)
                        cimis_hour = data['Data']['Providers'][0]['Records'][index]['Hour']
                        print('Hour= ', cimis_hour)
                        cimis_eto = float(data['Data']['Providers'][0]['Records'][index]['HlyEto']['Value'])
                        cimis_hum = float(data['Data']['Providers'][0]['Records'][index]['HlyRelHum']['Value'])
                        cimis_tmp = float(data['Data']['Providers'][0]['Records'][index]['HlyAirTmp']['Value'])
                        #print('Hour= ', cimis_hour)
                        print ('Eto = ', cimis_eto)
                        print ('RelHum= ',cimis_hum)
                        print ('AirTemp= ',cimis_tmp)
        #

#                cimis_tmp = 78
#                cimis_hum = 63
#                cimis_eto = 0.01
                local_hum = hourhum_val/60
                local_tmp = hourtemp_val/60
                local_eto = cimis_eto*(local_tmp/cimis_tmp)*(cimis_hum/local_hum)
                print("%.2f"%(local_eto))
                waters = (local_eto*1.0*200*0.62)/0.75
                watertime = waters/1020*60*60
#                waterdiff = waters/((cimis_eto*1.0*200*0.62)/0.75)    # we cannot calculate the waterdiff when cimis_eto is 0
                
#                watertime = 30 # for test
                
                text = 'Local: Hum:' + "%.2f "%(local_hum) + 'Temp:' + "%.2f "%(local_tmp) + 'Eto:' + "%.2f "%(local_eto) + 'wa:' + "%.2f"%(waters)+'\n' + 'CIMIS: Hum:' + "%.2f "%(cimis_hum) + 'Temp:' + "%.2f "%(cimis_tmp) + 'Eto:' + "%.2f "%(cimis_eto) + "%.2f"%(waterdiff)+ '\n'
                self.lcd.setCursor(6,0)
                self.lcd.message( 'L: H:' + "%.2f "%(local_hum) + 'T:' + "%.2f "%(local_tmp) + 'Eto:' + "%.2f "%(local_eto) + 'wa:' + "%.2f"%(waters))
                self.lcd.setCursor(6,1)
                self.lcd.message( 'C: H:' + "%.2f "%(cimis_hum) + 'T:' + "%.2f "%(cimis_tmp) + 'Eto:' + "%.2f "%(cimis_eto) + 'wd:' + "%.2f"%(waterdiff))
                #output = date+'\t'+self.now.hour+':00\t'+local_hum+'\t'+local_tmp+'\t'+repr(local_eto)+'\t'+cimis_hum+'\t'+cimis_tmp+'\t'+cimis_eto+'\n'
                output = "{}\t{}\t{}\t\t{}\t\t{}\t\t{}\t\t{}\t\t{}\n".format(date,cimis_hour,"%.2f"%(local_hum),"%.2f"%(local_tmp),"%.2f"%(local_eto),cimis_hum,cimis_tmp,cimis_eto)
                
                print(output)
                open("file.txt","a").write(output)

                   
                result_hum = result_temp = cnt_hum = cnt_temp = 0

        except KeyboardInterrupt:
            self.destroy()
            exit()  

class Motor(Thread):
    

    
    def setup(self):
        #print ('Program is starting...')
        GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
        GPIO.setup(RelayPin, GPIO.OUT)   # Set ledPin's mode is output
        GPIO.setup(sensorPin, GPIO.IN)    # Set sensorPin's mode is input
        GPIO.output(RelayPin, True)

    def loop(self):
        global PrevS
        global CurrS
        global text
        global watertime
        
        for i in range(watertime):
            i+=1
            GPIO.output(RelayPin,False)
                    
            detect = GPIO.input(sensorPin)
            if (detect == 1):
                CurrS = False
                if CurrS != PrevS:
                    PrevS = CurrS
                    print('Motion detected')
                    print('Relay close: Sprinkler Off')
                    self.lcd.clear()
                    self.lcd.message('Motion detected. \n'+'Sprinkler Off.')
                    sleep(0.7)
                    self.lcd.clear()
                    print(text)
                    self.lcd.message(text)
                    GPIO.setup(RelayPin, GPIO.IN)
                    time.sleep(3);
                                           
            elif (detect == 0):
                CurrS = True
                if CurrS != PrevS:
                    PrevS = CurrS
                    print('No motion')
                    print('Relay open: Sprinkler On')
                    self.lcd.clear()
                    self.lcd.setCursor(0,0)
                    self.lcd.message('No motion. \n'+'Sprinkler On.')
                    sleep(1)
                    self.lcd.clear()
                    print(text)
                    self.lcd.message(text)
                    GPIO.setup(RelayPin, GPIO.OUT)
                    GPIO.output(RelayPin, GPIO.LOW)
                        
            GPIO.setup(RelayPin, GPIO.OUT)
            sleep(1)
        GPIO.cleanup()
                    

    def destroy(self):
        GPIO.cleanup()                     # Release resource
        self.lcd.clear()

    def run(self):
        PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
        PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
        try:
            try:                
                mcp = PCF8574_GPIO(PCF8574_address)
            except:
                try:
                    mcp = PCF8574_GPIO(PCF8574A_address)
                except:
                    print ('I2C Address Error for motion sensor!')
                    exit(1)
            self.setup()
            self.lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)
            mcp.output(3,1)     # turn on LCD backlight
            self.lcd.begin(16,2)     # set number of LCD lines and columns
            self.lcd.setCursor(0,0)  # set cursor position
            self.loop()
        except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
            self.destroy()


PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.

t1 = HT_sensor()
t2 = Motor()



try:
    try:
        mcp = PCF8574_GPIO(PCF8574_address)
    except:
        try:
            mcp = PCF8574_GPIO(PCF8574A_address)
        except:
            print ('I2C Address Error for HT_sensor!')
            exit(1)

    # Create LCD, passing in MCP GPIO adapter.
    t1.lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)
    mcp.output(3,1)     # turn on LCD backlight
    t1.lcd.begin(16,2)     # set number of LCD lines and columns
    t1.lcd.setCursor(0,0)  # set cursor position
    t2.lcd = t1.lcd
    
    t1.start()
    sleep(3600)  # the first hour of the day, we don't need to irrigate
    t2.start()

    t1.join()
    t2.join()

except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
    t1.destroy()
    t2.destroy()
    exit(1)


