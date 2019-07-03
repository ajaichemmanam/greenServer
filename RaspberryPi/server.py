# from flask_socketio import SocketIO, emit
from flask_socketio import SocketIO, emit
from flask import Flask, request
from flask_cors import CORS
from random import random
from threading import Thread, Event
from time import sleep
# Logging
import logging 

# Improves Performance
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
# Import Raspberrypi Control and Monitoring Functions
from sensors import setupTempSensor, setupLexSensor, setupUltrasonicSensor, setupLight, setLightIntensity, getTemperature, getLightIntensity, getWaterLevel, kill
from sensors import setupMotor, motorOff, motorOn

#Create and configure logger 
logging.basicConfig(filename="serverLogs.log", 
                    format='%(asctime)s %(message)s', 
                    filemode='w') 
#Initialise
logger=logging.getLogger() 
#Setting the threshold of logger to DEBUG 
logger.setLevel(logging.DEBUG) 

# Start Main Program
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
CORS(app)
# Server functionality for receiving and storing data from elsewhere, not related to the websocket
#Data Generator Thread
thread = Thread()
thread_stop_event = Event()
operatingMode="Automatic"
ip = "0.0.0.0"
lightPwm=0
pumpState="Off"
class DataThread(Thread):
    def __init__(self):
        self.delay = 1
        super(DataThread, self).__init__()
    def dataGenerator(self):
        print("Initialising")
        i2cbus = setupLexSensor()
        serialNum = setupTempSensor()
        TRIG, ECHO = setupUltrasonicSensor()
        lightPwmPort= setupLight()
        motorPort= setupMotor()
        try:
            while not thread_stop_event.isSet():
                luxIR, luxVisible = getLightIntensity(i2cbus)
                print("Light Intensity: IR=",luxIR," Visible=",luxVisible)
                logger.info("Light Intensity: IR="+str(luxIR)+" Visible="+str(luxVisible))
                waterTempC, waterTempF = getTemperature(serialNum)
                if waterTempC != None:
                    print("Water Temperature: ", waterTempC, "C ", waterTempF, "F")
                    logger.info("Water Temperature: "+ str(waterTempC)+ "C "+ str(waterTempF)+ "F")
                else:
                    print("Error Fetching Water Temperature")
                    logger.error("Error Fetching Water Temperature")
                waterLevel = getWaterLevel(TRIG,ECHO)
                print("waterLevel: ", waterLevel)
                logger.info("waterLevel: "+ str(waterLevel))
                if(operatingMode=="Automatic"):
                    logger.info("Operating Mode: Automatic")
                    lightRequired = (2000-luxVisible)/2000
                    lightPerc = int(lightRequired*100)
                    logger.info("AUTOMATIC MODE: LED Duty Cycle: " + str(lightPerc))
                    if lightPerc>100:
                        setLightIntensity(lightPwmPort, 100)
                    elif lightPerc<10:
                        setLightIntensity(lightPwmPort, 10)
                    else:
                        setLightIntensity(lightPwmPort, lightPerc)
                        print('LED Brightness',lightPerc)
                    if waterLevel<5:
                        motorOff(motorPort)
                        print('Motor Off')
                        logger.info("AUTOMATIC MODE: Water Pump: Off ")
                    else:
                        motorOn(motorPort)
                        print('Motor On')
                        logger.info("AUTOMATIC MODE: Water Pump: On ")
                elif(operatingMode=="Manual"):
                    if lightPwm>100:
                        setLightIntensity(lightPwmPort, 100)
                    elif lightPwm<0:
                        setLightIntensity(lightPwmPort, 0)
                    else:
                        setLightIntensity(lightPwmPort, lightPwm)
                    print("Light Intensity", lightPwm)
                    logger.info("MANUAL MODE: LED Duty Cycle"+str(lightPwm))
                    if(pumpState=="On"):
                        motorOn(motorPort)
                        print("Motor On")
                        logger.info("MANUAL MODE: Water Pump: On" )
                    elif(pumpState=="Off"):
                        motorOff(motorPort)
                        print("Motor Off")
                        logger.info("MANUAL MODE: Water Pump: Off" )
                    else:
                        print("Unknown Motor Pump State")
                else:
                    print("Unknown Mode Of Operation")
                    logger.error("Unknown Mode Of Operation")

                # socketio.emit('responseMessage', {'waterTemperature': waterTempC, 'waterTemperatureF': waterTempF, 'airTemperature': round(random()*10, 3), 'humidity': round(random()*10, 3),'pH': round(random()+ 7, 3), 'lux':luxVisible, 'luxIR':luxIR, 'waterLevel':waterLevel}, namespace='/devices')
                socketio.emit('responseMessage', {'waterTemperatureC': waterTempC, 'waterTemperatureF': waterTempF, 'conductivity':round(random()*10, 3), 'salinity':round(random()*10, 3), 'luxVisible':luxVisible, 'luxIR':luxIR, 'waterLevel':waterLevel})
                sleep(self.delay)
        except KeyboardInterrupt:
            logger.error("Keyboard Interrupt")
            kill()
        # while not thread_stop_event.isSet():
            # socketio.emit('responseMessage', {'temperature': round(random()*10, 3), 'humidity': round(random()*10, 3),'pH': round(random()+ 7, 3), 'lux':round(random()*10, 3)}, namespace='/devices')
            # sleep(self.delay)
    def run(self):
        self.dataGenerator()
# Handle the webapp connecting to the websocket
@socketio.on('connect')
def connect():
    global ip
    if not request.headers.getlist("X-Forwarded-For"):
        ip = request.remote_addr
    else:
        ip = request.headers.getlist("X-Forwarded-For")[0]
    print("IP"+ ip)
    logger.debug('Client Connected: '+ip)
    emit('responseMessage', {'data': 'Connected'})
    # need visibility of the global thread object
    global thread
    if not thread.isAlive():
        print("Starting Thread")
        logger.debug('Starting Thread')
        thread = DataThread()
        thread.start()

@socketio.on('disconnect')
def test_disconnect():
    global ip
    if not request.headers.getlist("X-Forwarded-For"):
        ip = request.remote_addr
    else:
        ip = request.headers.getlist("X-Forwarded-For")[0]
    print('Client Disconnected :'+ip)
    logger.debug('Client Disconnected :'+ip)

# Handle the webapp connecting to the websocket, including namespace for testing
@socketio.on('connect', namespace='/devices')
def test_connect2():
    logger.debug('someone connected to websocket with namespace devices')
    emit('responseMessage', {'data': 'Connected devices'})
    # need visibility of the global thread object
    # global thread
    # if not thread.isAlive():
    #     print("Starting Thread")
    #     thread = DataThread()
    #     thread.start()
    

# Handle the webapp sending a message to the websocket
@socketio.on('message')
def handle_message(message):
    global thread
    # global thread_stop_event
    global operatingMode
    global lightPwm
    global pumpState
    logger.debug('Message Recieved')
    try:
        if (message["mode"]=="Manual"):
            operatingMode="Manual"
            print("Setting Manual Mode")
            logger.debug("Setting Manual Mode")
            # lightPwmPort= setupLight()
            # motorPort= setupMotor()

            lightPwm = int(message["lightIntensity"])
            pumpState = message["pumpState"]            
        elif (message["mode"]=="Automatic"):
            operatingMode="Automatic"
            if not thread.isAlive():
                thread_stop_event.clear()
                logger.debug("Starting Thread")
                print("Starting Thread")
                thread = DataThread()
                thread.start()
        else:
            print("Unknown Mode Of Operation")
            logger.error("Unknown Mode Of Operation")
    except Exception as e:
        global ip
        if not request.headers.getlist("X-Forwarded-For"):
            ip = request.remote_addr
        else:
            ip = request.headers.getlist("X-Forwarded-For")[0]
        logger.error("Error in Message Recieved from" + ip)
        print(e)
        logger.error("Error"+e)


# Handle the webapp sending a message to the websocket, including namespace for testing
@socketio.on('message', namespace='/devices')
def handle_message2():
    logger.debug('Message Recieved in devices namesapce')
    print('someone sent to the websocket!')


@socketio.on_error_default  # handles all namespaces without an explicit error handler
def default_error_handler(e):
    print('An error occured:')
    print(e)
    logger.error("ERROR : "+e)

if __name__ == '__main__':
    # socketio.run(app, debug=False, host='0.0.0.0')
    http_server = WSGIServer(('',5000), app, handler_class=WebSocketHandler)
    http_server.serve_forever()
