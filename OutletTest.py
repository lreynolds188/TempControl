#!/usr/bin/python3

"""
Temperature control system designed for a chemical reactor

author: Luke Reynolds
email: luke@reynolds.com
website: http://github.com/lreynolds188
license: GPL
"""

import time
import subprocess

subprocess.call("Outlet1On.sh")
print("Outlet 1: ON")
time.sleep(2)
subprocess.call("Outlet1Off.sh")
print("Outlet 1: OFF")
time.sleep(2)
subprocess.call("Outlet2On.sh")
print("Outlet 2: ON")
time.sleep(2)
subprocess.call("Outlet2Off.sh")
print("Outlet 2: OFF")
time.sleep(2)
subprocess.call("Outlet3On.sh")
print("Outlet 3: ON")
time.sleep(2)
subprocess.call("Outlet3Off.sh")
print("Outlet 3: OFF")
time.sleep(2)
