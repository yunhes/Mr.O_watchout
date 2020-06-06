#!/usr/bin/python
#Assignment4#
#Liyuan Zhao
#43307320


###import pthon modules###
import threading
import RPi.GPIO as GPIO
from time import sleep, time
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

###  Set GPIO pins and all setups needed  ###
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #green button
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #red button
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #yellow button
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #blue button

GPIO.setup(29,GPIO.OUT) #green led
GPIO.setup(31,GPIO.OUT) #red led
GPIO.setup(32,GPIO.OUT) #yellow led
GPIO.setup(33,GPIO.OUT) #blue led


### LEDs are off initially
GPIO.output(29, True)
GPIO.output(31, True)
GPIO.output(32, True)
GPIO.output(33, True)

#dictionary
btn2led = {22:29, 12:31, 13:32, 15:33}
### Define a function based on assignment description ###

#if  red and green in blinking, blink_on = true
global blink_on
blink_on = False
#if yellow is pressed before blue, yellow_on = true
global yellow_on
yellow_on = False
#if blue... yellow, blue_on = true
global blue_on
blue_on = False

def handle(pin):
    global blink_on
    global yellow_on
    global blue_on
    print("exec"+str(pin))
    # light corresponding LED when pushbutton of color is pressed
    # btn2led is a dictionary which saves information regarding each pushbuttopn
    # and its corresponding LED which needs to be defined at start of your code
    GPIO.output(btn2led[pin], not GPIO.input(pin))

    #yellow
    if pin == 13:
        if GPIO.input(13):
        #yellow button
            if (blue_on == True):
                 blue_on = False
                 blink_on = False
                 print("yellow pressed, blue off")
                 GPIO.output(32, False)
                 sleep(0.1)
                 GPIO.output(32, True)

            else:
                 yellow_on = True # yellow is used for activating the blink mode
                 print("yellow pressed, yellow on")
                 blink_on = True # activate the blink mode
                 print("blue off, yellow on, activate blink mode")
                 GPIO.output(32, False)
                 sleep(0.1)
                 GPIO.output(32, True)


    if pin == 15:
        ###yellow button###
        if GPIO.input(15):
            if (yellow_on == True): # yellow is used for activating blink mode
                 yellow_on = False  # set yellow not used
                 blink_on = False # exit the blink mode
                 print("yellow on, blue off, exit blink mode")
                 GPIO.output(33, False)
                 sleep(0.1)
                 GPIO.output(33, True)


            else: # yellow is not used for activating the blink mode
                 blue_on = True # blue is used for activating the blink mode
                 blink_on = True # activate the blink mode
                 print("yellow off, blue on, activate blink mode")
                 GPIO.output(33, False)
                 sleep(0.1)
                 GPIO.output(33, True)



    t = None
    if (pin == 22 or pin == 12) and(blink_on == True):
        #when green and red pressed simultaneously, enter blink mode
        if (GPIO.input(22) )and (GPIO.input(12)):
            #print "starting thread"
            t = threading.Thread(target = blink_thread)
            t.daemon = True
            t.start()
        elif GPIO.input(22): # only press green
            GPIO.output(29, False)
            sleep(0.1)
            GPIO.output(29, True)
        elif GPIO.input (12): # only press red
            GPIO.output(31, False)
            sleep(0.1)
            GPIO.output(31, True)
    elif(pin == 22) and (blink_on == False ): # only press green when blink is not activated
        if GPIO.input(22):
            GPIO.output(29, False)
            sleep(0.1)
            GPIO.output(29, True)
    elif(pin == 12) and (blink_on == False): # only press red when blink is not activated
        if GPIO.input (12):
            GPIO.output(31, False)
            sleep(0.1)
            GPIO.output(31, True)

### Tell GPIO library to look out for an event on pushbutton and pass handle ###
### function to be run for each pushbutton detection ###

#funtion for blink mode
def blink_thread():
    global blink_on
    global yellow_on
    global blue_on

    t_end = time() + 10

    while time() < t_end:

        if  blink_on == 0:
            GPIO.output(31, True) #turn off RED LED
            GPIO.output(29, True) #turn off Green LED
            print("stop blinking manually!")
            break

        else:
            print("blink!")
            GPIO.output(31, False) #turn on RED LED
            GPIO.output(29, False) #turn on Green LED
            sleep(0.1) # Sleep for 1 second
            GPIO.output(31, True) #turn off RED LED
            GPIO.output(29, True) #turn off Green LED
            sleep(0.1) # Sleep for 1 second

    blink_on = 0
    yellow_on = 0
    blue_on = 0



#set button event
GPIO.add_event_detect(22, GPIO.RISING, bouncetime=1000)
GPIO.add_event_callback(22, handle)
GPIO.add_event_detect(12, GPIO.RISING, bouncetime=1000)
GPIO.add_event_callback(12, handle)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=1000)
GPIO.add_event_callback(13, handle)
GPIO.add_event_detect(15, GPIO.RISING, bouncetime=1000)
GPIO.add_event_callback(15, handle)

while True:
    pass
