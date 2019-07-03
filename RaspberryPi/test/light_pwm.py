import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
LightPWM=21
GPIO.setup(LightPWM,GPIO.OUT)
p = GPIO.PWM(LightPWM, 100)
p.start(0)

while True:
	duty = input("Enter Duty Cycle")
	try:
		val = int(duty)
		if(val<=100):
			p.ChangeDutyCycle(val)
		else:
			print("Value Greater than 100")
	
	except:
		print("Enter integer value")
	