#!/usr/bin/python3

"""
Temperature control system designed for a chemical reactor

author: Luke Reynolds
email: luke@reynolds.com
website: http://github.com/lreynolds188
license: GPL
"""

import os
import csv
import time
import datetime
import subprocess
import RPi.GPIO as GPIO
import tkinter as tk
import matplotlib
import matplotlib.animation as animation
import matplotlib.dates as dts
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style
from tkinter import *
from w1thermsensor import W1ThermSensor

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def pump_on():
    subprocess.call("Outlet1On.sh")
    print("Outlet 1 (Pump): ON")
    logger.log_csv_input("Outlet 1 (Pump): ON")

def pump_off():
    subprocess.call("Outlet1Off.sh")
    print("Outlet 1 (Pump): OFF")
    logger.log_csv_input("Outlet 1 (Pump): OFF")

def heater_on():
    subprocess.call("Outlet2On.sh")
    print("Outlet 2 (Heater): ON")
    logger.log_csv_input("Outlet 2 (Heater): ON")

def heater_off():
    subprocess.call("Outlet2Off.sh")
    print("Outlet 2 (Heater): OFF")
    logger.log_csv_input("Outlet 2 (Heater): OFF")

def compressor_acu_on():
    subprocess.call("Outlet3On.sh")
    print("Outlet 3: ON")
    logger.log_csv_input("Outlet 3 (ACU): ON")

def compressor_acu_off():
    subprocess.call("Outlet3Off.sh")
    print("Outlet 3 (ACU): OFF")
    logger.log_csv_input("Outlet 3 (ACU): OFF")

def start():
    running = 1
    pump_on()
    heater_on()
    compressor_acu_on()
    
def stop():
    running = 0
    heater_off()
    compressor_acu_off()    
    
def pump():
    pump_on()
    heater_off()
    compressor_acu_off()

def updateText():
    if temp < 65:
        lbl_temp.config(text=str(temp)+'°C', fg="blue")
    elif temp < 78:
        lbl_temp.config(text=str(temp)+'°C', fg="yellow")
    elif temp < 82:
        lbl_temp.config(text=str(temp)+'°C', fg="green")
    elif temp < 86:
        lbl_temp.config(text=str(temp)+'°C', fg="orange")
    else:
        lbl_temp.config(text=str(temp)+'°C', fg="red")

def animate(i):
    ax.clear()
    ax.plot(counts, temps)
    plt.xlabel('Time Elapsed (Seconds)', size=10)
    plt.ylabel('Temp (°C)', size=10)
 
class CR05:
    def __init__(self):
        self.openPowerRelayPin = 6
        self.openGroundRelayPin = 13
        self.openedSignalPin = 19
        self.closePowerRelayPin = 5
        self.closeGroundRelayPin = 12
        self.closedSignalPin = 16
        self.sleeptime = 0.0304

    def setup(self):
        global valve_position
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
        while not self.valve_closed():
            self.close_valve()
        self.stop_valve()    
        valve_position = 0

    def valve_opened(self):
        return not GPIO.input(self.openedSignalPin)

    def valve_closed(self):
        return not GPIO.input(self.closedSignalPin)

    def open_valve(self):
        global valve_position
        if not self.valve_opened():
            GPIO.output(self.closePowerRelayPin, GPIO.LOW)
            GPIO.output(self.closeGroundRelayPin, GPIO.LOW)
            GPIO.output(self.openPowerRelayPin, GPIO.HIGH)
            GPIO.output(self.openGroundRelayPin, GPIO.HIGH)
            valve_position += 1
            time.sleep(self.sleeptime)
        else:
            self.stop_valve()

    def close_valve(self):
        global valve_position
        if not self.valve_closed():
            GPIO.output(self.openPowerRelayPin, GPIO.LOW)
            GPIO.output(self.openGroundRelayPin, GPIO.LOW)
            GPIO.output(self.closePowerRelayPin, GPIO.HIGH)
            GPIO.output(self.closeGroundRelayPin, GPIO.HIGH)
            valve_position -= 1
            time.sleep(self.sleeptime)
        else:
            self.stop_valve()

    def stop_valve(self):
        GPIO.output(self.openPowerRelayPin, GPIO.LOW)
        GPIO.output(self.openGroundRelayPin, GPIO.LOW)
        GPIO.output(self.closePowerRelayPin, GPIO.LOW)
        GPIO.output(self.closeGroundRelayPin, GPIO.LOW)

class Controller:
    def update(self):
        global running, temp, valve
        if temp < 65 and running == 0:
            pump_off()
            running = -1
        if temp < 70:
            while not valve.valve_closed():
                valve.close_valve()
            valve.stop_valve()
        elif temp < 75:
            while valve.position < 25:
                valve.open_valve()
            while valve.position > 26:
                valve.close_valve()
            valve.stop_valve() 
        elif temp < 80:
            while valve.position < 50:
                valve.open_valve()
            while valve.position > 51:
                valve.close_valve()
            valve.stop_valve()
        elif temp < 85:
            while valve.position < 75:
                valve.open_valve()
            while valve.position > 76:
                valve.close_valve()
            valve.stop_valve() 
        else:
            while not valve.valve_opened():
                valve.open_valve()
            valve.stop_valve()

class Logger:
    def __init__(self):
        tstamp = datetime.datetime.now().strftime('%c')
        log = open('log.csv','a+')
        log.write(f'\n\n\n{tstamp}\n')

    def update(self):
        self.print_status()
        self.log_csv()

    def print_status(self):
        print(f'Time: {stamps[len(stamps)-1]}    Temp: {temps[len(temps)-1]:.2f}°C    Valve Pos: {valve_position}% ')

    def log_csv(self):
        log = open('log.csv','a+')
        log.write(f'Time: {stamps[len(stamps)-1]}    Temp: {temps[len(temps)-1]:.2f}°C    Valve Pos: {valve_position}% \n')
    
    def log_csv_input(self, text):
        log = open('log.csv','a+')
        log.write(f'{text} \n')

try:
    # Global variables
    temp = 0 # I refuse to explain this variable's use
    valve_position = 0 # The position of the valve 0: Closed - 100: Open
    count = 0 # Counts the number of temperatures stored
    running = -1 # -1: Stopped, 0: Stopping, 1: Running
    temps = [] # Stores temperature's to display on screen
    counts = [] # Stores temperature's ID for logging
    stamps = [] # Stores temperature's timestamp for logging

    # Matplotlib init
    matplotlib.use("TkAgg")
    style.use('ggplot')
    fig = plt.figure(figsize=(8,3), dpi=100)
    ax = fig.add_subplot(111)

    # Sensors Init
    therm = W1ThermSensor()
    valve = CR05()
    valve.setup()

    # Controller Init
    controller = Controller()
    logger = Logger()

    # GUI Init
    gui = tk.Tk(className='Temperature Controller', )
    gui.geometry("800x460+0+-5")

    # GUI Contents
    canvas = FigureCanvasTkAgg(fig, gui)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    btn_pump_in = tk.Button(gui, height=3, width=10, text="Pump In", bg='orange', activebackground='#FFC87C', command=pump)
    btn_pump_in.pack(side=tk.LEFT)
    btn_start = tk.Button(gui, height=3, width=10, text="Start", bg='green', activebackground='#90EE90', command=start)
    btn_start.pack(side=tk.LEFT)
    btn_pump_out = tk.Button(gui, height=3, width=10, text="Pump Out", bg='yellow', activebackground='#FFFF80', command=pump)
    btn_pump_out.pack(side=tk.RIGHT)
    btn_stop = tk.Button(gui, height=3, width=10, text="Stop", bg='red', activebackground='#FF6347', command=stop)
    btn_stop.pack(side=tk.RIGHT) 
    lbl_temp = tk.Label(gui, text = "0°C") 
    lbl_temp.config(font=("Arial", 40))
    lbl_temp.pack(side=tk.BOTTOM)        

    # Animate the Matplotlib graph
    ani = animation.FuncAnimation(fig, animate, interval=1000)
    startTime = time.time()

    # Main loop
    while True:
        gui.update_idletasks()
        gui.update()
        endTime = time.time()
        if (endTime - startTime >= 1):
            startTime = time.time()
            temp = therm.get_temperature()
            counts.append(count) 
            stamps.append(datetime.datetime.now().strftime('%H:%M:%S'))
            temps.append(temp)
            if len(temps) >= 300:
                    stamps.pop(0)
                    counts.pop(0)
                    temps.pop(0)
            count += 1
            updateText()
            logger.update()
        controller.update()

except KeyboardInterrupt:
    print("An error has occurred\n")

finally:
    GPIO.cleanup()
