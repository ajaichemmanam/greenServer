import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

INT1_RELAY=26
GPIO.setup(INT1_RELAY,GPIO.OUT)

while True:
	switchRelay = input("Enter y to turn on and n to turn off")
	if(switchRelay.lower()=='y'):
		GPIO.output(INT1_RELAY, False)
		time.sleep(3)
	elif (switchRelay.lower()=='n'):
		GPIO.output(INT1_RELAY, True)
		time.sleep(3)
	else:
		print('Invalid Input, Enter y to turn on and n to turn off')

GPIO.cleanup()