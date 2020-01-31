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


sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('connected to the brain')

#sio.connect('http://summer-dev.us-east-1.elasticbeanstalk.com')


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
    #middleStack=[]
    rightStack=[]
    
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
    
#plotting processed data
def dataPlotting(n):
    for x in range(400):
        startThreads(n)
    for y in range(len(left)):
        if(y<len(right) and y< len(irLeftBin)):
            diff.append(left[y] -irLeftBin[y]-right[y]+1)
            diffStack.append(leftStack[y])
    plot.plot(diffStack, diff, label="processed")
    plot.xlabel('TIME')
    plot.ylabel('DISTANCE (cm)')
    plot.legend()
    plot.show()

def check(test, val):
    if(val == test):
        return 1
    else:
        return 0


def swipeDetect( maxD, delay, timeout):
    #flags 
    flagPos = False
    flagNeg =False
    flagDetect = False

    flagDetect = False
    startTime = 0
    checkTime=0
    while True:
                 
        startThreads(maxD)
        if(len(left) >0 and len(right) >0 and len(irLeftBin) >0 ):
            l = left.pop()
            m = irLeftBin.pop()
            r = right.pop()
                    
            if(l==0 and r==0 and m ==0):
                delta=0
            else:
                delta = l - m-r+1
        else:
            delta=0
                #set flags
                
        diff.append(delta)
        diffStack.append(time.time())
        if(flagNeg==False and flagDetect ==False and delta==1):
            flagPos = True
            startTime = time.time()
        if(flagPos==False and flagDetect ==False and delta==-1):
            flagNeg = True
            startTime = time.time()
        checkTime= time.time()
        elapsed = checkTime-startTime
                
                #if no gesture detected within 1 seconds set the flags down 
        if elapsed > timeout:
            flagNeg =False
            flagPos =False
            flagDetect = False  
                #once gesture detected set flags down to sense next one
        if(flagDetect ==True and delta==0):
            flagDetect = False
            flagNeg = False
            flagPos = False
        if(flagNeg==True and delta==1):
            
            flagDetect = True
            sio.emit('edge.swipe', data={'type': 'right'})
            print("---->")
            time.sleep(delay)
        if(flagPos==True and delta==-1):
            
            flagDetect = True
            sio.emit('edge.swipe', data={'type': 'left'})
            print("<----")
            time.sleep(delay)


def swipeDetectTest(maxD, delay, timeout, timeoutTest, n):
        #flags 
    flagPos = False
    flagNeg =False
    flagDetect = False

    flagDetect = False
    total = 0
    startTime = 0
    checkTime=0
    for i in range(n):
        sensed = False
        x=randint(0,1)
        print(testSequence[x])
        startTime2 = time.time()
        while sensed == False:
                
            startThreads(maxD)
            if(len(left) >0 and len(right) >0 and len(irLeftBin) >0 ):
                l = left.pop()
                m = irLeftBin.pop()
                r = right.pop()
                if(l==0 and r==0 and m ==0):
                    delta=0
                else:
                    delta = l - m-r+1
            else:
                delta=0
                #set flags
                
            diff.append(delta)
            diffStack.append(time.time())
            if(flagNeg==False and flagDetect ==False and delta==1):
                flagPos = True
                startTime = time.time()
            if(flagPos==False and flagDetect ==False and delta==-1):
                flagNeg = True
                startTime = time.time()
            checkTime= time.time()
            elapsed = checkTime-startTime
            elapsed2 =  checkTime - startTime2
                

            if elapsed2 > timeoutTest:
                sensed = True
                #once gesture detected set flags down to sense next one
                    #if no gesture detected within 1 seconds set the flags down 
            if elapsed > timeout:
                flagNeg =False
                flagPos =False
                flagDetect = False
                    
                    #once gesture detected set flags down to sense next one
            if(flagDetect ==True and delta==0):
                flagDetect = False
                flagNeg = False
                flagPos = False
            if(flagNeg==True and delta==1):
                flagDetect = True
                total = total + check(testSequence[x], "swipe right")
                print("---->")
                sensed = True
                time.sleep(delay)
            if(flagPos==True and delta==-1):
                flagDetect = True
                print("<----")
                total = total + check(testSequence[x], "swipe left")
                sensed = True
                time.sleep(delay)
    
    print(total, "/",n)    
    plot.plot(diffStack, diff, label="processed")
    plot.xlabel('TIME')
    plot.ylabel('DISTANCE (cm)')
    plot.show()
  
if __name__ == '__main__':
    try:

#        rawPlot(50) 
#        dataPlotting(50)
        swipeDetectTest(50,0.5,0.3,5,10)
#        swipeDetect(50,0.5,0.3) 
        
    except KeyboardInterrupt:
        sio.disconnect()
        print("terminated by user")
        GPIO.cleanup()