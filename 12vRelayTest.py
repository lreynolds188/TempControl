#!/usr/bin/python3
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

pinList = [5, 6, 12, 13, 16, 19, 20, 26]

for i in pinList:
    GPIO.setup(i, GPIO.OUT)
    GPIO.output(i, GPIO.LOW)

SleepTimeL = 1

try:
  GPIO.output(5, GPIO.HIGH)
  print ("ONE:ON")
  time.sleep(SleepTimeL);
  GPIO.output(5, GPIO.LOW)
  print ("ONE:OFF")
  time.sleep(SleepTimeL);
  GPIO.output(6, GPIO.HIGH)
  print ("TWO:ON")
  time.sleep(SleepTimeL);
  GPIO.output(6, GPIO.LOW)
  print ("TWO:OFF")
  time.sleep(SleepTimeL);
  GPIO.output(12, GPIO.HIGH)
  print ("THREE:ON")
  time.sleep(SleepTimeL);
  GPIO.output(12, GPIO.LOW)
  print ("THREE:OFF")
  time.sleep(SleepTimeL);
  GPIO.output(13, GPIO.HIGH)
  print ("FOUR:ON")
  time.sleep(SleepTimeL);

except KeyboardInterrupt:
  print ("... Quit")
  GPIO.cleanup()

GPIO.cleanup()
