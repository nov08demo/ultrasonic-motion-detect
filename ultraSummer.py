import RPi.GPIO as GPIO
import time
import sys
import os
from dotenv import load_dotenv
load_dotenv()
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from threading import Thread
import matplotlib.pyplot as plot
import socketio
from cloudwatch_logger import CloudwatchLogger
from matplotlib.animation import FuncAnimation
from random import randint
global startEdge
startEdge = False

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('connected to the brain')


    
@sio.on('edge.startEdge')
def on_startEdge(data):
    print('------START EDGE RECEIVED------')
    global startEdge
    startEdge = True
    
@sio.on('edge.stopEdge')
def on_stopEdge(data):
    print('------STOP EDGE RECEIVED------')
    global startEdge
    startEdge = False



sio.connect('http://summer-dev.us-east-1.elasticbeanstalk.com/')

GPIO.setmode(GPIO.BCM)


GPIO.setmode(GPIO.BCM)
CLK = 18
MISO = 23
MOSI = 24
CS = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK,cs =CS, miso=MISO, mosi=MOSI)
t = [] #time data
d = [] #distance data

#GPIO mode (BOARD/ BOM)


#set GPIO pins
#LEFT 
TRIG_L =17
ECHO_L = 4
#MIDDLE

#RIGHT
TRIG_R = 3
ECHO_R = 2

#set GPIO direction (in/ out)

testSequence = ["swipe left", "swipe right"]
leftStack=[]
left =[]
leftDist=[]

irStackLeft=[]
irLeft = []
irLeftBin = []

irStackRight=[]
irRight = []
irRightBin = []

rightStack = []
right = []
rightDist = []

diffStack = []
diff = []








#log = CloudwatchLogger(os.getenv('LOG_GROUP'), os.getenv('LOG_STREAM'), __file__)
GPIO.setwarnings(True)
#log.info('Listening for socket...')


    

    
#calculating and processing distance for ultrasonic sensors    
def detect(TRIG, ECHO, ID, maxDist):
    
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    #set trigger high
    GPIO.output(TRIG, True)
    
    #set trigger after 0.01 s to low
    time.sleep(0.00001)
    GPIO.output(TRIG,False)
    
    StartTime = time.time()
    StopTime =time.time()
    
    #save Starttime
    while GPIO.input(ECHO) == 0:
        StartTime = time.time()
        
    #save time of arrival
    while GPIO.input(ECHO) == 1:
        StopTime = time.time()
    
    #time difference
    TimeElapsed = StopTime - StartTime
    
    #distance = speed* time
    #d = 34300*t/2 --> time for there and back so divide by 2
    distance = (TimeElapsed *34300)/2
    val=1
    if(distance < 100):
        if(ID=="L"):
            leftStack.append(time.time())
            leftDist.append(distance)
            
            if(distance <maxDist):
                left.append(0)
            else:
                left.append(1)
        elif(ID=="R"):
            rightStack.append(time.time())
            rightDist.append(distance)

            if(distance <maxDist):
                right.append(0)
            else:
                right.append(1)
        return True
    else:
        return False
 
#calculating and processing distance for infrared sensors 
def detectIR(channel, maxDist):
    v = (mcp.read_adc(channel) / 1023.0) * 3.3
    dist = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 301.439
    
    if(channel==1):
        irStackLeft.append(time.time())
        irLeft.append(dist)
        if(dist <maxDist):
            irLeftBin.append(0)
        else:
            irLeftBin.append(1)
    elif(channel==0):
        irStackRight.append(time.time())
        irRight.append(dist)
        
        if(dist <maxDist):
            irRightBin.append(0)
        else:
            irRightBin.append(1)
    
def startThreads(n):
    #n is the max distance
    leftThread = Thread(target=detect, args=[TRIG_L, ECHO_L, "L", n])
    irleftThread = Thread(target=detectIR, args=[1, n])
    irRightThread = Thread(target=detectIR, args=[0, n])
    rightThread = Thread(target=detect, args=[TRIG_R, ECHO_R, "R", n])
        
    leftThread.start()
    irleftThread.start()
#    irRightThread.start()
    rightThread.start()



def clearStack():
    leftStack=[]
    leftDist = []
    #middleStack=[]
    rightStack=[]
    rightDist =[]
# plotting distance data from all sensors
def rawPlot(n):
    #n is max distance
    for x in range(500):
        startThreads(n)
    plot.plot(leftStack, leftDist, label="left")
    plot.plot(irStackLeft, irLeft,label="IR left")
    plot.plot(irStackRight, irRight,label="IR right")
    plot.plot(rightStack, rightDist, label="right")
    plot.xlabel('TIME')
    plot.ylabel('DISTANCE (cm)')
    plot.legend()
    plot.show()
    



global startBool    
startBool = True

    

@sio.on('edge.startGame')
def startGame(data):
    global startBool
    startBool= True
    
@sio.on('edge.stopGame')
def stopGame(data):
    global startBool
    startBool = False
    
def hover(dist, delay, en):
    flagLeft = False
    flagRight =False
    flagSelect = False
    while True:
        startThreads(dist)
        if(len(leftDist)>0):
            l = leftDist.pop()
        else:
            l = 100
        if(len(rightDist)>0):
            r = rightDist.pop()
        else:
            r = 100
        
        if(startBool and startEdge):
            if( l< dist):
                sio.emit('edge.select')
                
                print('<----')
                if en== True:
                    time.sleep(delay*(l/10))
                else:
                    time.sleep(delay)
            elif(r< dist):
                sio.emit('edge.scroll')
                
                print('---->')
                if en== True:
                    time.sleep(delay*(l/10))
                else:
                    time.sleep(delay)
            else:
                sio.emit('edge.unselect')
               

if __name__ == '__main__':
    try:

#        rawPlot(50) 
#        swipeDetectTest(50,0.5,0.3,5,10)

#        swipeDetect(50,0.5,0.3)

         hover(50,0.5,False)#0.5 delay 


    except KeyboardInterrupt:
        sio.disconnect()
        print("terminated by user")
        clearStack()

        GPIO.cleanup()
        


