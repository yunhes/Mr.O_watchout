import time
import json
import urllib.error
import urllib.response

from lib.adafruit import DHT11 as DHT  # used for testing this file
from lib.cimis import cimis

#from matplotlib import pyplot as plt

#
SF = 200 # square feet
CONST = 0.62 # constant value used for conversion
IE = 0.75 # irrigation efficiency
PF = 1 # plant factor, range [0,1]  
secondsInMinute = 60 # testing
secondsInHour = 3600 # number of seconds in an hour

global_length = 0


### get Data from the CIMIS Database 
###     - Depends on cimis.py found in lib/cimis
###     - param format 'MM-DD-YYYY'
def extractData(start = '06-14-2019', end = '06-14-2019'):
    appKey = '7a16bfa5-c9ea-48fd-9142-4ba8e038c2d2' # Updated appKey with my account - Justin 

    sites = [75]  #query single site or multiple

    ## will need to change this depending on the path 
    xls_path = 'CIMIS_query_new.xlsx' # TODO: make this dep on stations/query date
    interval ='hourly' #options are:    default, daily, hourly

    #get the data as a list of data frames; one dataframe for each site
    while(True):
        try:
            print("Attempting to obtain CIMIS data.")
            site_names, cimis_data = cimis.run_query(appKey, sites, interval, start=start, end=end)
            break
        except json.JSONDecodeError:
            print("-- Error: JSON decoding error has occurred.")
            continue
        except urllib.error.HTTPError:
            print("-- Error: HTTP error has occurred.")
            continue
        except urllib.request.URLError:
            print("-- Error: HTTP request error occurred.")
            continue
        except ConnectionResetError:
            print("-- Error: connection has reset or timed out")
            continue
        finally: 
            print("Will attempt to obtain CIMIS data every minute.")
            time.sleep(60) # sleep for a minute, try again

    #write queried data to excel file
    cimis.write_output_file(xls_path, cimis_data, site_names)
    print(" CIMIS Data was obtained.")
    return cimis_data

def getCimisData(cimis_data, param='HlyEto', param1 = 'HlyRelHum', param2 = 'HlyAirTmp'):
    # Grab the amount of entries currently recorded within days chosen
    global global_length
    length = (int) (cimis_data[0][param].describe().loc['count'])

    eto_data = cimis_data[0][param]
    rh_data = cimis_data[0][param1]
    temp_data = cimis_data[0][param2]

    cimis_eto_hrly = eto_data[0]
    cimis_rh_hrly = rh_data[0]
    cimis_temp_hrly = temp_data[0]

    ### If station has been updated within the past hour
    if (length-global_length == 1) :
        cimis_eto_hrly = eto_data[length-1]
        cimis_rh_hrly = rh_data[length-1]
        cimis_temp_hrly = temp_data[length-1]
    ### If station hasn't been updated over an hour (aka if station is down)
    else:
        # Obtain the average of the hours missed
        count = length - global_length
        print("Data has not been obtained for a while. Obtaining averages for " + str(count) + " hours.")
        for i in range(global_length, length):
            cimis_eto_hrly += eto_data[i]
            cimis_rh_hrly = rh_data[i]
            cimis_temp_hrly = temp_data[i] 

        cimis_eto_hrly /= count
        cimis_rh_hrly /= count
        cimis_temp_hrly /= count

    global_length = length
    return cimis_eto_hrly, cimis_rh_hrly, cimis_temp_hrly

    
### Calculate Derating Factors to help convert local ETH
def getDeratingFactors(cimisT, cimisRH, localT, localRH):
    dfT= localT / cimisT
    dfRH = cimisRH / localRH
    print("Derating factors: dft(" + str(dfT) + ")   dfRH(" + str(dfRH) + ")")
    return dfT, dfRH

### Calculating how much water to obtain for the day
def getWateringInformation(local_et):
    # (ET0 x PF x SF x 0.62 ) / IE = Gallons of Water per day
    # Time needed for watering: gallons of water per day/water debit
    gallons_of_water = (local_et * PF * SF * 0.62) / IE
    print("Gallons of water: " + str(gallons_of_water))
    return gallons_of_water


### -----------------  Testing  -----------------
def cimisTestThread(checkRunTime = secondsInHour):
    print("---- CIMIS Thread is called  ----")
    
    # initial CIMIS call
    print("Getting initial CIMIS Data")
    while(True):
        try:
            cimis_data = extractData()
            print("Received initial CIMIS Data")
            break
        except json.decoder.JSONDecodeError:
            print("JSON Decode error! Trying again...")


    #get initial CIMIS length
    length = (int) (cimis_data[0]['HlyEto'].describe().loc['count']) 
    print("Initial CIMIS data retrieved length: " + str(length))
    #test = cimis_data[0]['HlyEto']
    #print(test[length-1])

    # get initial time for while loop
    initialTime = time.time()
    while(True):
        # Running for time checkRunTime. 
        if (time.time() - initialTime > checkRunTime):
            print("If-Statement Iteration.")
            initialTime = time.time()

            # Poll for new data at checkRunTime (in seconds)
            # noticing that JSON sometimes gets corrupted or something. This helps but isnt ideal
            while(True): 
                try:
                    cimis_data = extractData()
                    print("Received initial CIMIS Data")
                    break
                except json.decoder.JSONDecodeError:
                    print("JSON Decode error! Trying again...")

            # Checking if new data:
            newLength = (int) (cimis_data[0]['HlyEto'].describe().loc['count']) # get length of new data
            if(newLength > length):
                print("[SUCCESS] New Entry added in CIMIS data! Data Length: "+ str(newLength))
                length = newLength # Update length 
                

if __name__ == "__main__":
    # Write code here 
    print("---- Testing cimis_extract.py ----")
    try:
        cimisTestThread(60)
    except KeyboardInterrupt:
        print(" Exiting Test")
