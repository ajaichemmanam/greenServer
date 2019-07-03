#!/usr/bin/env python

import smbus
import time
import os
import RPi.GPIO as GPIO

def setupTempSensor():
    for i in os.listdir('/sys/bus/w1/devices'):
        if i != 'w1_bus_master1':
            ds18b20 = i
    return ds18b20

def setupLexSensor(bus):
    # TSL2561 address, 0x39(57)
    # Select control register, 0x00(00) with command register, 0x80(128)
    #		0x03(03)	Power ON mode
    bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
    # TSL2561 address, 0x39(57)
    # Select timing register, 0x01(01) with command register, 0x80(128)
    #		0x02(02)	Nominal integration time = 402ms
    bus.write_byte_data(0x39, 0x01 | 0x80, 0x02)

    time.sleep(0.5)

def setupUltrasonicSensor():
    GPIO.setmode(GPIO.BCM)
    TRIG = 23
    ECHO = 24
    GPIO.setup(TRIG,GPIO.OUT)
    GPIO.setup(ECHO,GPIO.IN)
    GPIO.output(TRIG, False)
    time.sleep(2)
    return TRIG, ECHO

def getTemperature(ds18b20):
    location = '/sys/bus/w1/devices/' + ds18b20 + '/w1_slave'
    tfile = open(location)
    text = tfile.read()
    tfile.close()
    secondline = text.split("\n")[1]
    temperaturedata = secondline.split(" ")[9]
    temperature = float(temperaturedata[2:])
    celsius = temperature / 1000
    farenheit = (celsius * 1.8) + 32
    return celsius, farenheit

def getLightIntensity(bus):

    # Read data back from 0x0C(12) with command register, 0x80(128), 2 bytes
    # ch0 LSB, ch0 MSB
    data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)

    # Read data back from 0x0E(14) with command register, 0x80(128), 2 bytes
    # ch1 LSB, ch1 MSB
    data1 = bus.read_i2c_block_data(0x39, 0x0E | 0x80, 2)

    # Convert the data
    ch0 = data[1] * 256 + data[0]
    ch1 = data1[1] * 256 + data1[0]

    return ch0, ch1, ch0-ch1

def getWaterLevel(TRIG, ECHO):
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    pulse_start=0
    pulse_end=0
    while GPIO.input(ECHO)==0:
        pulse_start = time.time()
    
    while GPIO.input(ECHO)==1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start

    distance = pulse_duration * 17150  
    distance = round(distance, 2)
    return distance

def kill():
    GPIO.cleanup()
    quit()

if __name__ == '__main__':
    # Get I2C bus
    bus = smbus.SMBus(1)
    setupLexSensor(bus)
    serialNum = setupTempSensor()
    TRIG, ECHO = setupUltrasonicSensor()
    try:

        while(True):
            FullRange, IR, Visible = getLightIntensity(bus)
            print("Light Intensity: Full=",FullRange," IR=",IR," Visible=",Visible)
            celsius, farenheit = getTemperature(serialNum)
            if celsius != None:
                print("Water Temperature: ", celsius, "C ", farenheit, "F")
            distance = getWaterLevel(TRIG,ECHO)
            print("Distance: ", distance)
            time.sleep(1)
    except KeyboardInterrupt:
        kill()


