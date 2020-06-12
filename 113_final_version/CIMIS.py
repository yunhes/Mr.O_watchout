import requests
import datetime
import csv
import pprint
import DHT
import time

hour_entries = {}

# getting cimis data for provided date and hour without accessing site
def getHourData(hour, date):
    hour_str = None
    hour += 1
    if hour < 10:
        hour_str = '0' + str(hour)
    else:
        hour_str = str(hour)
    hour_str = hour_str + '00'
    print("CIMIS hour: ", hour_str)
    #pprint.pprint("Hour String")
    #pprint.pprint(hour_str)
    for i in hour_entries:
        if hour_entries[i]['Hour'] == hour_str and hour_entries[i]['Date'] == date:
            if hour_entries[hour]['HlyAirTmp']['Value'] != None:
                DHT.cimisTemp = float(hour_entries[hour]['HlyAirTmp']['Value'])
                DHT.cimisET = float(hour_entries[hour]['HlyEto']['Value'])
                DHT.cimisHumidity = float(hour_entries[hour]['HlyRelHum']['Value'])
                print("Value Found")
                return
            else:
                DHT.cimisTemp = None
                DHT.cimisET = None 
                DHT.cimisHumidity = None 
                print("Value not updated")
        #else:
            #print("At " + hour_entries[i]['Hour'])
    
def getcimisdata(hour, date):
    #appKey = 'a28ddf14-568e-45b8-8050-6925a8ff77e1'  # cimis appKey
    #appKey = '3cae5dfd-ef01-49e4-b6f4-0441a144c5e5'
    #appKey = '952d594c-ff2e-4011-b1d9-8d62e6300ec8'
    #appKey = 'fe36cc18-4506-4cca-8ba9-c903131fde2f'
    appKey = 'a5550049-e0d5-438b-99e1-949f85c4d82b'
    # list of CIMIS station ID's from which to query data
    sites = [75]  # uncomment to query single site
    sites = [str(i) for i in sites]  # convert list of ints to strings
    ItemInterval = 'hourly'
    # start date fomat in YYYY-MM-DD
    start = date
    # end date fomat in YYYY-MM-DD
    # e.g. pull all data from start until today
    end = datetime.datetime.now().strftime("%Y-%m-%d")

    station = sites[0]
    dataItems_list = ['hly-air-tmp',
                      'hly-eto',
                      'hly-asce-eto',
                      'hly-asce-etr',
                      'hly-precip',
                      'hly-rel-hum',
                      'hly-res-wind']
    dataItems = ','.join(dataItems_list)
    url = ('http://et.water.ca.gov/api/data?appKey=' + appKey + '&targets='
        + str(station) + '&startDate=' + start + '&endDate=' + end +
        '&dataItems=' + dataItems +'&unitOfMeasure=E')

#    test = requests.head(url)    
    
#    if test.status_code == 302:
#        print("error 302")
#        time.sleep(60)
#    else:
#        print("200")

    print(url)

    #r0 = requests.get(url, timeout = 10)
    
    try:
        r0 = requests.get(url, timeout = 10)
        if test.status_code == 302:
            print("error 302")
            return
    except Exception:
        print("Timed out...")
        DHT.cimisTemp = None
        DHT.cimisET = None
        DHT.cimisHumidity = None
        return

    r = requests.get(url).json()
    #print(type(r)) #dict
    #pprint.pprint(r)

    #data = r['Data']
    currdata = {}
    for key in r:
        currdata = r[key]
    #print(type(currdata)) #dict
    #pprint.pprint(currdata)

    #for key in r:
    #    data = currdata[key]
    #data = currdata['Data']
    #print(type(data)) #dict
    #pprint.pprint(data)

    #for key in r:
    providers = currdata['Providers']
    #now a list and access using providers[int]
    #print(type(providers))
    #pprint.pprint(providers)
    
    access_list = providers[0]
    #print(type(access_list))
    #pprint.pprint(access_list)

    records_list = access_list['Records']
    #print(type(records_list))
    #pprint.pprint(records_list)

    #moved hour_entries dictionary

    for i,val in enumerate(records_list):
        hour_entries[i] = val

    #print(type(hour_entries))
    #pprint.pprint(hour_entries)
    
    targ_tmp = hour_entries[0]['HlyAirTmp']['Value']
    targ_eto = hour_entries[0]['HlyEto']['Value']
    targ_hum = hour_entries[0]['HlyRelHum']['Value']
    print(targ_tmp)
    print(targ_eto)
    print(targ_hum)
    if ((hour_entries[hour]['HlyEto']['Value'] == None) or (hour_entries[hour]['HlyAirTmp']['Value'] == None) or (hour_entries[hour]['HlyRelHum']['Value'] == None)):
        DHT.cimisTemp = hour_entries[hour]['HlyAirTmp']['Value']
        DHT.cimisET = hour_entries[hour]['HlyEto']['Value']
        DHT.cimisHumidity = hour_entries[hour]['HlyRelHum']['Value']
        return 

    DHT.cimisTemp = float(hour_entries[hour]['HlyAirTmp']['Value'])
    DHT.cimisET = float(hour_entries[hour]['HlyEto']['Value'])
    DHT.cimisHumidity = float(hour_entries[hour]['HlyRelHum']['Value'])
    print(type(DHT.cimisTemp))
    print(type(DHT.cimisET))
    print(type(DHT.cimisHumidity))
    return

if __name__ == "__main__":
        #xls_path = 'CIMIS_query_irvine_hourly.xlsx'
        #site_names, cimis_data = main()
        #write_output_file(xls_path, cimis_data, site_names)
        getcimisdata(11, '2019-06-03')
        getHourData(4, '2019-06-03')
