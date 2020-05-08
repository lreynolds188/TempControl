import os
import glob
import time
import datetime
import csv
import matplotlib.pyplot as plt
import matplotlib.animation as animation
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
    
    def print_temps(self):
        print('-'*90)
        for t, n, c in self.rows:
            print(f'Sensor: {n}  C={c:,.3f}  DateTime: {t}')
       
    def log_csv(self):
        with open('logs.csv','a+') as log:
            writer = csv.writer(log)
            writer.writerows(self.rows)
        with open('log.csv', 'a+') as log:
            writer = csv.writer(log)
            writer.writerows(self.temps)

    def clear_rows(self):
        self.rows.clear()
        self.temps.clear()

class Z6528:
    def __init__(self):
        style.use('fivethirtyeight')
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(1,1,1)

    def animate(self, i):
        graph_data = open('log.csv', 'r').read()
        lines = graph_data.split('\n')
        xs = []
        ys = []
        for line in lines:
            if len(line) > 1:
                x, y = line.split(',')
                xs.append(x)
                ys.append(y)
        self.ax1.clear()
        self.ax1.plot(xs, ys)


thermometer = DS18B20()
thermometer.find_sensors()
display = Z6528()
ani = animation.FuncAnimation(display.fig, display.animate, interval=1000)
plt.show()

while True:
    thermometer.read_temp()
    thermometer.print_temps()
    thermometer.log_csv()
    thermometer.clear_rows()