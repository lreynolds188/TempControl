#!/usr/bin/python3

"""
Temperature control system designed for a chemical reactor

author: Luke Reynolds
email: luke@reynolds.com
website: http://github.com/lreynolds188
license: GPL
"""

import os
import glob
import time
import datetime
import csv
import RPi.GPIO as GPIO
import tkinter as tk
import matplotlib
import matplotlib.animation as animation
import matplotlib.dates as dts
import matplotlib.pyplot as plt
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style
matplotlib.use("TkAgg")
style.use('ggplot')
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

fig = plt.figure(figsize=(8,3), dpi=100)
ax = fig.add_subplot(111)

temps = []
counts = []
stamps = []
        
def animate(i):
    ax.clear()
    ax.plot(counts, temps)
    plt.xlabel('Time Elapsed (Seconds)', size=10)
    plt.ylabel('Temp (°C)', size=10)
    

class DS18B20:
    def __init__(self):
        self.base_dir = r'/sys/bus/w1/devices/28*'
        self.sensor_path = []        
        self.sensor_name = []
        self.count = 0
        
    def setup(self):
        self.sensor_path = glob.glob(self.base_dir)
        self.sensor_name = [path.split('/')[-1] for path in self.sensor_path]

    def strip_string(self, temp_str):
        i = temp_str.index('t=')
        if i != -1:
            t = temp_str[i+2:]
            temp_c = float(t)/1000.0
        return temp_c

    def read_temp(self):
        global counts
        global temps
        global stamps
        tstamp = datetime.datetime.now().strftime('%H:%M:%S')
        for sensor, path in zip(self.sensor_name, self.sensor_path):
            with open(path + '/w1_slave','r') as f:
                valid, temp = f.readlines()
            if 'YES' in valid:
                temp = round(self.strip_string(temp), 2)
                counts.append(self.count) 
                stamps.append(tstamp)
                temps.append(temp)
                if len(temps) >= 300:
                    stamps.pop(0)
                    counts.pop(0)
                    temps.pop(0)
                self.count += 1
        return (tstamp, temp)

 
class CR05:
    def __init__(self):
        self.openPowerRelayPin = 6
        self.openGroundRelayPin = 13
        self.openedSignalPin = 19
        self.closePowerRelayPin = 5
        self.closeGroundRelayPin = 12
        self.closedSignalPin = 16
        self.sleeptime = 0.0304
        self.position = 0

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
        while not self.valve_closed():
            self.close_valve()
        self.stop_valve()    
        self.position = 0

    def valve_opened(self):
        return not GPIO.input(self.openedSignalPin)

    def valve_closed(self):
        return not GPIO.input(self.closedSignalPin)

    def open_valve(self):
        if not self.valve_opened():
            GPIO.output(self.closePowerRelayPin, GPIO.LOW)
            GPIO.output(self.closeGroundRelayPin, GPIO.LOW)
            GPIO.output(self.openPowerRelayPin, GPIO.HIGH)
            GPIO.output(self.openGroundRelayPin, GPIO.HIGH)
            self.position += 1
            time.sleep(self.sleeptime)
        else:
            self.stop_valve()

    def close_valve(self):
        if not self.valve_closed():
            GPIO.output(self.openPowerRelayPin, GPIO.LOW)
            GPIO.output(self.openGroundRelayPin, GPIO.LOW)
            GPIO.output(self.closePowerRelayPin, GPIO.HIGH)
            GPIO.output(self.closeGroundRelayPin, GPIO.HIGH)
            self.position -= 1
            time.sleep(self.sleeptime)
        else:
            self.stop_valve()

    def stop_valve(self):
        GPIO.output(self.openPowerRelayPin, GPIO.LOW)
        GPIO.output(self.openGroundRelayPin, GPIO.LOW)
        GPIO.output(self.closePowerRelayPin, GPIO.LOW)
        GPIO.output(self.closeGroundRelayPin, GPIO.LOW)


class GUI(Tk):
    def __init__(self):
        super().__init__()
        self.title("Temperature Controller")
        self.geometry('800x460+0+-5') 

        self.canvas = FigureCanvasTkAgg(fig, self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.btn_pump_in = tk.Button(self, height=3, width=10, text="Pump In", bg='orange', activebackground='#FFC87C', command=lambda: controller.show_frame(GUI))
        self.btn_pump_in.pack(side=tk.LEFT)

        self.btn_start = tk.Button(self, height=3, width=10, text="Start", bg='green', activebackground='#90EE90', command=lambda: controller.show_frame(GUI))
        self.btn_start.pack(side=tk.LEFT)

        self.btn_pump_out = tk.Button(self, height=3, width=10, text="Pump Out", bg='yellow', activebackground='#FFFF80', command=lambda: controller.show_frame(GUI))
        self.btn_pump_out.pack(side=tk.RIGHT)
 
        self.btn_stop = tk.Button(self, height=3, width=10, text="Stop", bg='red', activebackground='#FF6347', command=lambda: controller.show_frame(GUI))
        self.btn_stop.pack(side=tk.RIGHT) 

        self.lbl_temp = tk.Label(self, text = "0°C") 
        self.lbl_temp.config(font=("Arial", 40))
        self.lbl_temp.pack(side=tk.BOTTOM)

    def updateText(self, temp):
        
        if temp < 65:
            self.lbl_temp.config(text=str(temp)+'°C', fg="blue")
        elif temp < 78:
            self.lbl_temp.config(text=str(temp)+'°C', fg="yellow")
        elif temp < 82:
            self.lbl_temp.config(text=str(temp)+'°C', fg="green")
        elif temp < 86:
            self.lbl_temp.config(text=str(temp)+'°C', fg="orange")
        else:
            self.lbl_temp.config(text=str(temp)+'°C', fg="red")

class Controller:
    def update(self, temp, valve, gui):
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
        log.write(f'\n\n{tstamp}\n')

    def update(self, valve):
        self.print_status(valve)
        self.log_csv()

    def print_status(self, valve):
        print(f'Time: {stamps[len(stamps)-1]}    Temp: {temps[len(temps)-1]:.2f}°C    Valve Pos: {valve.position}% ')

    def log_csv(self):
        log = open('log.csv','a+')
        log.write(f'Time: {stamps[len(stamps)-1]}    Temp: {temps[len(temps)-1]:.2f}°C    Valve Pos: {valve.position}% \n')


try:
    therm = DS18B20()
    therm.setup()
    valve = CR05()
    valve.setup()
    controller = Controller()
    logger = Logger()
    gui = GUI()
    ani = animation.FuncAnimation(fig, animate, interval=10000)
    temp = 0
    startTime = time.time()
    endTime =  time.time()
    while True:
        gui.update_idletasks()
        gui.update() 
        endTime = time.time()
        if (endTime - startTime >= 1):
            startTime = time.time()
            temp = therm.read_temp()[1]
            gui.updateText(temp)
            logger.update(valve)
        controller.update(temp, valve, gui)
        

except KeyboardInterrupt:
    print("\n")

finally:
    GPIO.cleanup()     
