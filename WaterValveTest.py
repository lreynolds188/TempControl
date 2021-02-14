#!/usr/bin/python3
import os
import glob
import datetime
import time
import csv
import matplotlib.dates as dts
import matplotlib.pyplot as plt
import numpy as np
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from matplotlib import style

#these tow lines mount the device:
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
        
class CR05:
    def __init__(self):
        self.openPowerRelayPin = 6
        self.openGroundRelayPin = 13
        self.openedSignalPin = 19
        self.closePowerRelayPin = 5
        self.closeGroundRelayPin = 12
        self.closedSignalPin = 16
        self.position = 0
        self.sleeptime = 0.0304

    def setup(self):
        GPIO.setup(self.closePowerRelayPin, GPIO.OUT)
        GPIO.output(self.closePowerRelayPin, GPIO.LOW)
        GPIO.setup(self.openPowerRelayPin, GPIO.OUT)
        GPIO.output(self.openPowerRelayPin, GPIO.LOW)
        GPIO.setup(self.closeGroundRelayPin, GPIO.OUT)
        GPIO.output(self.closeGroundRelayPin, GPIO.LOW)
        GPIO.setup(self.openGroundRelayPin, GPIO.OUT)
        GPIO.output(self.openGroundRelayPin, GPIO.LOW)
        GPIO.setup(self.closedSignalPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.openedSignalPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

    def valve_opened(self):
        return not GPIO.input(self.openedSignalPin)

    def valve_closed(self):
        return not GPIO.input(self.closedSignalPin)

    def valve_position(self):
        return self.position

    def open_valve(self, increment):
        if not self.valve_opened():
            GPIO.output(self.closePowerRelayPin, GPIO.LOW)
            GPIO.output(self.closeGroundRelayPin, GPIO.LOW)
            GPIO.output(self.openPowerRelayPin, GPIO.HIGH)
            GPIO.output(self.openGroundRelayPin, GPIO.HIGH)
            adjustment = self.sleeptime * increment
            self.position += adjustment
            time.sleep(adjustment)
        else:
            self.stop_valve()

    def close_valve(self, increment):
        if not self.valve_closed():
            GPIO.output(self.openPowerRelayPin, GPIO.LOW)
            GPIO.output(self.openGroundRelayPin, GPIO.LOW)
            GPIO.output(self.closePowerRelayPin, GPIO.HIGH)
            GPIO.output(self.closeGroundRelayPin, GPIO.HIGH)
            adjustment = self.sleeptime * increment
            self.position -= adjustment
            time.sleep(adjustment)
        else:
            self.stop_valve()

    def stop_valve(self):
        GPIO.output(self.openPowerRelayPin, GPIO.LOW)
        GPIO.output(self.openGroundRelayPin, GPIO.LOW)
        GPIO.output(self.closePowerRelayPin, GPIO.LOW)
        GPIO.output(self.closeGroundRelayPin, GPIO.LOW)

class Controller:
    def update(self, temp, valve):
        # close valve
        if temp <= 70:
            valve.close_valve(1)
        # open valve 1/8
        elif temp <= 75:
            if valve.position < 12:
                valve.open_valve(12 - valve.position)
        # open valve 1/4    
        elif temp <= 80:
            if valve.position < 25:
                valve.open_valve(25 - valve.position)
        # open valve 1/2
        elif temp <= 85:
            if valve.position < 50:
                valve.open_valve(50 - valve.position)
        # open valve fully, sound alarm, turn off heat   
        elif temp > 85:
            if valve.position < 100:
                valve.open_valve(100 - valve.position)
    

valve = CR05()
valve.setup()
controller = Controller()

old_time = datetime.datetime.now()
while not valve.valve_opened():
    valve.open_valve(1)
new_time = datetime.datetime.now()
print(new_time - old_time)
while not valve.valve_closed():
    valve.close_valve(1)
valve.stop_valve()

GPIO.cleanup()

    