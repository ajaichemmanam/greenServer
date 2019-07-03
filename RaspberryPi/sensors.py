#!/usr/bin/env python

import smbus
import time
import os
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BCM)

def setupMotor():
        GPIO.setmode(GPIO.BCM)
        INT1_RELAY=26
        GPIO.setup(INT1_RELAY,GPIO.OUT)
        GPIO.output(INT1_RELAY, False) #On By Default
        return INT1_RELAY
	
def setupTempSensor():
    for i in os.listdir('/sys/bus/w1/devices'):
        if i != 'w1_bus_master1':
            ds18b20 = i
    return ds18b20

def setupLexSensor():
    # Get I2C bus
    bus = smbus.SMBus(1)
    # TSL2561 address, 0x39(57)
    # Select control register, 0x00(00) with command register, 0x80(128)
    #		0x03(03)	Power ON mode
    bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
    # TSL2561 address, 0x39(57)
    # Select timing register, 0x01(01) with command register, 0x80(128)
    #		0x02(02)	Nominal integration time = 402ms
    bus.write_byte_data(0x39, 0x01 | 0x80, 0x02)
    time.sleep(0.5)
    return bus

def setupLight():
    GPIO.setmode(GPIO.BCM)
    LightPWM=21
    GPIO.setup(LightPWM,GPIO.OUT)
    p = GPIO.PWM(LightPWM, 100)
    p.start(0)
    return p

def setupUltrasonicSensor():
    GPIO.setmode(GPIO.BCM)
    TRIG = 23
    ECHO = 24
    GPIO.setup(TRIG,GPIO.OUT)
    GPIO.setup(ECHO,GPIO.IN)
    GPIO.output(TRIG, False)
    time.sleep(2)
    return TRIG, ECHO

def setLightIntensity(pwmPort, dutycycle):
    pwmPort.ChangeDutyCycle(dutycycle)

def motorOn(motorPort):
        GPIO.output(motorPort, False)

def motorOff(motorPort):
	GPIO.output(motorPort, True)

def getTemperature(ds18b20):
    location = '/sys/bus/w1/devices/' + ds18b20 + '/w1_slave'
    tfile = open(location)
    text = tfile.read()
    tfile.close()
    secondline = text.split("\n")[1]
    temperaturedata = secondline.split(" ")[9]
    temperature = float(temperaturedata[2:])
    celsius = round(temperature / 1000,2)
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
    ch0 = data[1] * 256 + data[0] #Full Range
    ch1 = data1[1] * 256 + data1[0] #IR

    return ch1, ch0-ch1

def getWaterLevel(TRIG, ECHO):
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    pulse_start=0
    pulse_end=0
    try:
        while GPIO.input(ECHO)==0:
            pulse_start = time.time()
        
        while GPIO.input(ECHO)==1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        print("Pulse", pulse_start, pulse_end)

        distance = pulse_duration * 17150  
        #distance = round(distance, 2)
        # print("Distance", distance)

        waterTankHeight=30 #Change 30cm as needed
        waterLevel = round(((waterTankHeight-distance)/waterTankHeight)*100,2)
        
        if waterLevel < 0:
            return 0.01
        elif waterLevel>=100:
            return 0.01
        else:
            return waterLevel
    except Exception as e:
        print(e)
        return 0.01

def kill():
    GPIO.cleanup()
    quit()

if __name__ == '__main__':
    # Get I2C bus
    # i2cbus = smbus.SMBus(1)
    i2cbus  = setupLexSensor()
    serialNum = setupTempSensor()
    TRIG, ECHO = setupUltrasonicSensor()
    try:

        while(True):
            luxIR, luxVisible = getLightIntensity(i2cbus)
            print("Light Intensity: IR=",luxIR," Visible=",luxVisible)
            waterTempC, waterTempF = getTemperature(serialNum)
            if waterTempC != None:
                print("Water Temperature: ", waterTempC, "C ", waterTempF, "F")
            waterLevel = getWaterLevel(TRIG,ECHO)
            print("waterLevel: ", waterLevel)
            time.sleep(1)
    except KeyboardInterrupt:
        kill()

