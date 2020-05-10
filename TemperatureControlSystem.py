#!/usr/bin/python3

import os
import glob
import time
import datetime
import csv
import matplotlib.pyplot as plt
import numpy as np
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

    def find_sensors(self):
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
                self.temps.append((tstamp.strftime('%H:%M:%S'), self.strip_string(temp)))
                time.sleep(2)
            else:
                time.sleep(0.2)
        return self.strip_string(temp)
    
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

class Z6528:
    def live_plotter(self,x_vec,y1_data,line1,identifier='',pause_time=0.1):
        if line1==[]:
            # this is the call to matplotlib that allows dynamic plotting
            plt.ion()
            fig = plt.figure(figsize=(13,6))
            ax = fig.add_subplot(111)
            # create a variable for the line so we can later update it
            line1, = ax.plot(x_vec,y1_data,'-o',alpha=0.8)        
            #update plot label/title
            plt.ylabel('Y Label')
            plt.title('Title: {}'.format(identifier))
            plt.show()
        
        # after the figure, axis, and line are created, we only need to update the y-data
        line1.set_ydata(y1_data)
        # adjust limits if new data goes beyond bounds
        if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
            plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])
        # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
        plt.pause(pause_time)
        
        # return line so we can update it again in the next iteration
        return line1


thermometer = DS18B20()
thermometer.find_sensors()
display = Z6528()
plt.style.use('ggplot')
size = 100
x_vec = np.linspace(0,1,size+1)[0:-1]
y_vec = np.random.randn(len(x_vec))
line1 = []

while True:
    y_vec[-1] = thermometer.read_temp()
    thermometer.print_temps()
    thermometer.log_csv()
    thermometer.clear_rows()
    line1 = display.live_plotter(x_vec, y_vec, line1)
    y_vec = np.append(y_vec[1:],0.0)
