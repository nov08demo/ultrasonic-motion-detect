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
#sio = socketio.Client()
#sio.connect('http://summer-development-env-dev002.us-east-1.elasticbeanstalk.com')

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



DISTANCE = 30
maxTime = 0.04

flagPos = False
flagNeg =False
flagComplete = False
#log = CloudwatchLogger(os.getenv('LOG_GROUP'), os.getenv('LOG_STREAM'), __file__)
GPIO.setwarnings(True)
#log.info('Listening for socket...')




def sendMessage(direction):
    sio.emit('vision.swipeRight', {'direction': direction})


#@sio.on('edge.startEdge')
def start(data):
    global run
    run = True
    GPIO.setmode(GPIO.BOARD)
    mainThread = Thread(target=useThreeUltrasonics, args=[TRIG_1, ECHO_1, TRIG_2, ECHO_2, TRIG_3, ECHO_3])
    mainThread.daemon = True
    mainThread.start()
    log.info('Starting...')
    sio.emit('edge.startSuccessful')
    
#@sio.on('edge.stopEdge')
def stop(data):
    global run
    run = False
    log.info('Stopping...')
    sio.emit('edge.stopSuccessful')
    GPIO.cleanup()
    
    
def detect(TRIG, ECHO, ID):
    
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
            if(distance <30):
                left.append(0)
            else:
                left.append(1)
        elif(ID=="R"):
            rightStack.append(time.time())
            rightDist.append(distance)
            if(distance <30):
                right.append(0)
            else:
                right.append(1)
        return True
    else:
        return False
 

def detectIR(channel):
    v = (mcp.read_adc(channel) / 1023.0) * 3.3
    dist = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 301.439
    if(dist < 100):
        if(channel==1):
            irStackLeft.append(time.time())
            irLeft.append(dist)
            if(dist <30):
                irLeftBin.append(0)
            else:
                irLeftBin.append(1)
        elif(channel==0):
            irStackRight.append(time.time())
            irRight.append(dist)
            if(dist <30):
                irRightBin.append(0)
            else:
                irRightBin.append(1)
    
def startThreads():
    leftThread = Thread(target=detect, args=[TRIG_L, ECHO_L, "L"])
    irleftThread = Thread(target=detectIR, args=[1])
    irRightThread = Thread(target=detectIR, args=[0])
    rightThread = Thread(target=detect, args=[TRIG_R, ECHO_R, "R"])
        
    leftThread.start()
    irleftThread.start()
#    irRightThread.start()
    rightThread.start()
    
def clearStack():
    leftStack=[]
    #middleStack=[]
    rightStack=[]
def rawPlot():
    for x in range(200):
        startThreads()
    plot.plot(leftStack, leftDist, label="left")
    plot.plot(irStackLeft, irLeft,label="IR left")
    plot.plot(irStackRight, irRight,label="IR right")
    plot.plot(rightStack, rightDist, label="right")
    plot.xlabel('TIME')
    plot.ylabel('DISTANCE (cm)')
    plot.legend()
    plot.show()
def dataPlotting():
    for x in range(400):
        startThreads()
    for y in range(len(left)):
        if(y<len(right) and y< len(irLeftBin)):
            diff.append(left[y] -irLeftBin[y]-right[y])
            diffStack.append(leftStack[y])
    plot.plot(diffStack, diff, label="processed")
    plot.xlabel('TIME')
    plot.ylabel('DISTANCE (cm)')
    plot.legend()
    plot.show()

def getDirectionCurve(flagNeg, flagPos):
    if(len(left) >0 and len(right) >0 ):
        x = left.pop()
        y = right.pop()
        delta = x-y
    else:
        delta=0
    #set flags
    
    if(flagNeg==False and delta==1):
        flagPos = True
        timeStart = time.time()
    if(flagPos==False and delta==-1):
        flagNeg = True
        timeStart = time.time()
    #check for change in sign: i.e., diff => -1 to 1 =>RTL
    #also will time out if no gesture detected
    while flagNeg==True:
        timeEnd = time.time()
        if(delta==1):
            print("---->")
            flagNeg = False
        elif((timeEnd-timeStart)>2):
            flagNeg = False
    while flagPos==True:
        timeEnd = time.time()
        if(delta==-1):
            flagPos = False
            print("<----")
        elif (timeEnd-timeStart)>2:
            flagPos = False
def getDirection():
    if(len(leftStack) >0 and len(rightStack) >0 ):
        leftTime = leftStack.pop()
        rightTime = rightStack.pop()
    else:
        leftTime = 0
        rightTime = 0
    diff = leftTime -rightTime
    if(diff < 0):
        return "right"
    elif(diff> 0):
        return "left"
  
if __name__ == '__main__':
    try:
        
        #startThreads()
        #rawPlot() 
        #dataPlotting()
        
        #semi functional ultrasonic solution
    
        startTime=0
        checkTime=0
        while True:
            startThreads()
            if(len(left) >0 and len(right) >0 and len(irLeftBin)):
                l = left.pop()
                m = irLeftBin.pop()
                r = right.pop()
                
                delta = l-m -r +1
            else:
                delta=0
            #set flags
            
            diff.append(delta)
            diffStack.append(time.time())
            if(flagNeg==False and delta==1):
                flagPos = True
                startTime = time.time()
            if(flagPos==False and delta==-1):
                flagNeg = True
                startTime = time.time()
            checkTime= time.time()
            timeout = checkTime-startTime
            #if no gesture detected within 1 seconds set the flags down 
            if (timeout) > 1:
                flagNeg =False
                flagPos =False
            
            if(flagNeg==True and delta==1):
                flagNeg =False
                print("---->")
                time.sleep(0.05)
            if(flagPos==True and delta==-1):
                flagPos = False
                print("<----")
                time.sleep(0.05)
            #gesture =getDirection()
            #printMessage(gesture)
            #clearStack()
            
        plot.plot(diffStack, diff, label="processed")
        plot.xlabel('TIME')
        plot.ylabel('DISTANCE (cm)')
        plot.show()
    
        
    except KeyboardInterrupt:
        print("terminated by user")
        GPIO.cleanup()