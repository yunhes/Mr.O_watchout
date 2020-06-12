#!/usr/bin/env python3
########################################################################
# Filename    : DHT.py
# Description : Use the DHT to get local humidity and temperature data
#               Use this data to calculate irrigation time
# Author      : Sienna Ballot
# modification: 6/3/19
########################################################################

import threading
import time
import RPi.GPIO as GPIO
import Freenove_DHT as DHT
import Relay
import csv
import CIMIS

thermoPin = 11
localHourly = []
localHumidity = 0.0
localTemp = 0.0
irrigationTime = 0.0
sqft = 200          # 200 square feet to be irrigated
pf = 1.0            # plant factor for lawn
conversion = 0.62   # constant conversion factor
IE = 0.75           # irrigation efficiency (suggested to use 0.75)
systemRate = 17     # 17 gallons per minute = 1020 gallons per hour
ET0 = 0             # variable for calculated ET0
cimisHumidity = 0   # variables to store the pulled CIMIS data
cimisTemp = 0
cimisET = 0
additionalWater = 0
waterSaved = 0

display = False     # to control LCD display
displaycimis = False

def getIrrigationTime():
    global irrigationTime
    global ET0
    global cimisET
    global cimisHumidity
    global cimisTemp
    global localHumidity
    global localTemp
    global displaycimis
    
    # get current date and time info
    result = time.localtime(time.time())
    
    # get ET, humidity, and temp from CIMIS
    # check if CIMIS site has been update for first hour in list
    CIMIS.getcimisdata(localHourly[0][0], localHourly[0][1])#result.tm_hour, date)

    # if CIMIS has not been update for first hour in list
    # skip irrigation and wait for data updates
    if ((cimisET == None) or (cimisHumidity == None) or (cimisTemp == None)):
        cimisET = None
        cimisHumidity = None
        cimisTemp = None
        currH = None
        currT = None
        gallons = None
        irrigationTime = None
        additionalWater = 0
        waterSaved = 1020
    # otherwise, get data from CIMIS for all hours in list that have been updated
    # and get ET0 and irrigation time to turn on motor
    else:
        displaycimis = True
        while True:
            # if list empty then break
            if (len(localHourly) == 0):
                break
            
            # get cimis data for the next hour in the list
            CIMIS.getHourData(localHourly[0][0], localHourly[0][1])
            
            # if the cimis has not been updated for that hour then break
            if (cimisET == None):
                break
        
            # get derating factors for the hour in the list to derate ET0
            humidityDerate = cimisHumidity / localHourly[0][2]
            tempDerate = localHourly[0][3] / cimisTemp
            currT = cimisTemp
            currH = cimisHumidity
            currET = cimisET * (tempDerate * humidityDerate)        # get the ET0 for the current time to calculate additional water used for that hour
            ET0 = ET0 + (cimisET * (tempDerate * humidityDerate))   # add derated ET0 to find total ET0 for all hours whose data has been updated
            localHourly.pop(0)                                      # remove hour from list if data has been used

        print("ET0: ", ET0)

        # get total gallons of water needed per hour for total ET0 (using gallons needed per day formula divided by 24)
        gallons = ((ET0 * pf * sqft * conversion) / IE) / 24
        print("Gallons Total Needed: ", gallons)

        # get gallons of water needed only for the ET0 of the current hour
        galHour = ((currET * pf * sqft * conversion) / IE) / 24
        print("Gallons for only this hour: ", galHour)

        # additional water is the total water needed minus the required water for that hour 
        additionalWater = gallons - galHour
        print("Additional Water: ", additionalWater)

        # water saved is the rate of water per hour minus the total water used
        waterSaved = 1020 - gallons
        print("Water Saved: ", waterSaved)

        # get time to run irrigation in minutes
        # gallons needed / (gallons per min) = minutes needed to run 
        irrigationTime = gallons / systemRate
        print("Irrigation Time (min): ", irrigationTime)

        # signal relay to turn on and start relay thread
        Relay.systemState = True
        t = None
        print("starting Relay/Motor thread")
        t = threading.Thread(target=Relay.loop)
        t.daemon = True
        t.start()

    # open output file to store information for the hour
    date = str(result.tm_mon)+'/'+str(result.tm_mday)+'/'+str(result.tm_year)
    row = [date, str(result.tm_hour), str(ET0), str(localHumidity), str(localTemp), str(cimisET), str(currH), str(currT), str(gallons), str(irrigationTime), str(additionalWater), str(waterSaved)]

    with open('output.csv', mode='a') as outputFile:
        outputWriter = csv.writer(outputFile)
        outputWriter.writerow(row)

    outputFile.close()

    currET = 0
    ET0 = 0
    cimisHumidity = 0
    cimisTemp = 0


def loop():
    global localHumidity
    global localTemp
    global display

    # intialize output file and write headers to the file
    row = ['Date (MM/DD/YYYY)','Hour','Local ET0', 'Local Humidity', 'Local Temp(F)', 'CIMIS ET0', 'CIMIS Humidity', 'CIMIS Temp (F)', 'Gallons Needed (gal/hr)', 'Time Needed (min)', 'Additional Water (per hour)', 'Water Saved (per hour)']

    with open('output.csv', mode='a') as outputFile:
        outputWriter = csv.writer(outputFile)
        outputWriter.writerow(row)

    outputFile.close()

    dht = DHT.DHT(thermoPin)        # creates DHT class object
    count = 0                       # initialize minute count for an hour

    while(True):
        chk = dht.readDHT11()
        print("Check DHT: ", chk)

        # CONVERT CELSIUS TO FAHRENHEIT
        if (chk is dht.DHTLIB_OK):
            # if the start of an hour, do not need to average 2 values
            if (localHumidity == 0 and localTemp == 0):
                localHumidity = dht.humidity
                localTemp = 32 + (1.8*dht.temperature)
            # otherwise avergae the new data with the past averages of the hour
            else:
                localHumidity = (localHumidity + dht.humidity)/2
                localTemp = (localTemp + (32+(1.8*dht.temperature)))/2
        
        count += 1
        print("Local Humidity: ", localHumidity)
        print("Local Temperature: ", localTemp)
        
        # check CIMIS for new data
        # if there is new data for the hour
        result = time.localtime(time.time())
        if (count >= 60 or result.tm_min == 59):
            # format month for date string
            if (result.tm_mon/10 == 0):                 
                month = '0'+str(result.tm_mon)
            else:
                month = str(result.tm_mon)
            # format day for date string
            if (result.tm_mday/10 == 0):                
                day = '0'+str(result.tm_mday)
            else:
                day = str(result.tm_mday)
            # formulate date string and send as argument to CIMIS function
            date = str(result.tm_year)+'-'+month+'-'+day
            
            # make a list containing the date and local data for the current hour
            # and append this data to the localHourly list
            data = [result.tm_hour, date, localHumidity, localTemp]
            localHourly.append(data)

            getIrrigationTime()

            # reset variables to calculate new data for the new hour
            localHumidity = 0
            localTemp = 0
            count = 0
        
        # sleep for 1 minute  
        display = True #enable LCD to display
        time.sleep(60)
        display = False #disable LCD to display
        time.sleep(0.5)

