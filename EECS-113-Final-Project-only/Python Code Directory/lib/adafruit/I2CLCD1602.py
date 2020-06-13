#!/usr/bin/env python3
########################################################################
# Filename    : I2CLCD1602.py
# Description : Use the LCD display data
# Author      : freenove
# modification: 2018/08/03
########################################################################
from lib.adafruit.PCF8574 import PCF8574_GPIO
from lib.adafruit.Adafruit_LCD1602 import Adafruit_CharLCD
from time import sleep, strftime
from datetime import datetime

def scroll(lcd,msg):
    lcd.clear()
    lcd.setCursor(0,0)
    lcd.message(msg)
    sleep(1)

    try:
        while True:
            for x in range(0,16):
                lcd.leftToRight()
                sleep(0.1)
            sleep(2)
    except KeyboardInterrupt:
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
#lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

if __name__ == '__main__':
    print ('Program is starting ... ')
    try:
        lcd_scroll("Program is starting...")
    except KeyboardInterrupt:
        destroy()

