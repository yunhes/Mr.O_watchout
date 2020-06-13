#!/usr/bin/python
import adafruit_dht
import board
import adafruit_character_lcd.character_lcd as characterlcd
import digitalio
import os
from time import sleep

# Kill libgpiod_pulsei to avoid DHT bug
os.system("killall libgpiod_pulsei")

lcd_rs = digitalio.DigitalInOut(board.D26)
lcd_en = digitalio.DigitalInOut(board.D19)
lcd_d7 = digitalio.DigitalInOut(board.D11)
lcd_d6 = digitalio.DigitalInOut(board.D5)
lcd_d5 = digitalio.DigitalInOut(board.D6)
lcd_d4 = digitalio.DigitalInOut(board.D13)
pir = digitalio.DigitalInOut(board.D17)
pir.direction = digitalio.Direction.INPUT

dht_device = adafruit_dht.DHT11(board.D4)

lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, 16, 2)

try:
    while True:
        try:
            temperature_c, humidity = dht_device.temperature, dht_device.humidity

            lcd.message = "PIR: {}\nTemp:{} hum:{}".format("High" if pir.value else "Low", temperature_c, humidity)
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print("[ERROR] ", error.args[0])
            lcd.message = "PIR: {}\nRead Error".format("High" if pir.value else "Low")

        sleep(0.3)
except KeyboardInterrupt as error:
    lcd.message = "Fucking off"