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
import datetime
import time
import csv
import matplotlib.dates as dts
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
from matplotlib import style

#these tow lines mount the device:
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

class DS18B20:
    def __init__(self):
        self.base_dir = r'/sys/bus/w1/devices/28*'
        self.sensor_path = []        
        self.sensor_name = []
        self.temps = []
        self.rows = []

    def update(self):
        thermometer.print_temps()
        thermometer.log_csv()
        thermometer.clear_rows()

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
        tstamp = datetime.datetime.now()
        for sensor, path in zip(self.sensor_name, self.sensor_path):
            # open sensor file and read data
            with open(path + '/w1_slave','r') as f:
                valid, temp = f.readlines()
            # check validity of data
            if 'YES' in valid:
                self.rows.append((tstamp, sensor, self.strip_string(temp)))
                time.sleep(1)
            else:
                time.sleep(0.2)
        return (tstamp.strftime('%H:%M:%S'), self.strip_string(temp))
    
    def print_temps(self):
        print('-'*90)
        for t, n, c in self.rows:
            print(f'Sensor: {n}  C={c:,.3f}  DateTime: {t}')
       
    def log_csv(self):
        with open('logs.csv','a+') as log:
            writer = csv.writer(log)
            writer.writerows(self.rows)

    def clear_rows(self):
        self.rows.clear()
        self.temps.clear()

        
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


class Z6528:
    def __init__(self):
        plt.style.use('ggplot')
        plt.ion()
        self.fig = plt.figure(figsize=(13,6))
        self.ax = self.fig.add_subplot(111)
        self.size = 100
        self.x_vec = np.linspace(0,1,self.size+1)[0:-1]
        self.y_vec = np.random.randn(len(self.x_vec))
        self.line = []

    def update(self, temp):
        self.y_vec[-1] = temp
        self.line = self.live_plotter(self.x_vec, self.y_vec, self.line)
        self.y_vec = np.append(self.y_vec[1:],0.0)

    def live_plotter(self,x1_data,y1_data,line,identifier='',pause_time=0.1):
        if line==[]:
            # create a variable for the line so we can later update it
            line, = self.ax.plot(x1_data,y1_data,alpha=0.8,color='red')  

            #update plot label/title
            plt.ylabel('Temp (°C)')
            plt.title('Temp Control System {}'.format(identifier))
            plt.show()
        
        # after the figure, axis, and line are created, we only need to update the y-data
        line.set_ydata(y1_data)

        # adjust limits if new data goes beyond bounds
        if np.min(y1_data)<=line.axes.get_ylim()[0] or np.max(y1_data)>=line.axes.get_ylim()[1]:
            plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])
        
        # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
        plt.pause(pause_time)

        # return line so we can update it again in the next iteration
        return line

class Controller:
    def update(self, temp, valve):
        # close valve
        if temp <= 70:
            while not valve.valve_closed():
                valve.close_valve()
            valve.stop_valve()
        # open valve 1/8
        elif temp <= 75:
            while valve.position < 20:
                valve.open_valve()
            while valve.position > 21:
                valve.close_valve()
            valve.stop_valve()
        # open valve 1/4    
        elif temp <= 80:
            while valve.position < 35:
                valve.open_valve()
            while valve.position > 36:
                valve.close_valve()
            valve.stop_valve()
        # open valve 1/2
        elif temp <= 85:
            while valve.position < 50:
                valve.open_valve()
            while valve.position > 51:
                valve.close_valve()
            valve.stop_valve()
        # open valve fully, sound alarm, turn off heat   
        elif temp > 85:
            while not valve.valve_opened():
                valve.open_valve()
            valve.stop_valve()
    
try:
    thermometer = DS18B20()
    thermometer.setup()
    valve = CR05()
    valve.setup()
    display = Z6528()
    controller = Controller()

    while True:
        temp = thermometer.read_temp()[1]
        thermometer.update()
        controller.update(temp, valve)
        display.update(temp)

except KeyboardInterrupt:
    print("\n")

finally:
    GPIO.cleanup()
