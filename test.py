#libraries
import RPi.GPIO as GPIO
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from threading import Thread
import matplotlib.pyplot as plot


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
#TRIG_M =12
#ECHO_M = 10
#RIGHT
TRIG_R = 3
ECHO_R = 2

#set GPIO direction (in/ out)
stack=[]
leftStack=[]
middleStack=[]
rightStack = []
left =[]
middle = [] 
right = []


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
            left.append(distance)    
        elif(ID=="R"):
            rightStack.append(time.time())
            right.append(distance)    
    #elif(ID=="M"):
        #middleStack.append(time.time())
       # middle.append(distance)    

def detectIR():
    v = (mcp.read_adc(0) / 1023.0) * 3.3
    dist = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 301.439
    if(dist < 100):
        middleStack.append(time.time())
        middle.append(dist)
    
def startThreads():
    leftThread = Thread(target=detect, args=[TRIG_L, ECHO_L, "L"])
    middleThread = Thread(target=detectIR, args=())
    rightThread = Thread(target=detect, args=[TRIG_R, ECHO_R, "R"])
        
    leftThread.start()
    middleThread.start()
    rightThread.start()
    
def clearStack():
    leftStack=[]
    #middleStack=[]
    rightStack=[]
def getDirection():
    if(len(leftStack) >0 and len(rightStack) >0 and len(middleStack) >0):
        leftTime = leftStack.pop()
        middleTime= middleStack.pop()
        rightTime = rightStack.pop()
    else:
        leftTime = 0
        middleTime= 0
        rightTime = 0
    if(leftTime<middleTime and middleTime<rightTime):
        return "Swipe to the right"
    elif(leftTime>middleTime and middleTime>rightTime):
        return "Swipe to the left"
    else:
        return "no gesture"
if __name__ == '__main__':
    try:
        #startThreads()
        for x in range(100):
            startThreads()
        plot.plot(leftStack, left, label="left")
        plot.plot(middleStack, middle,label="IR")
        plot.plot(rightStack, right, label="right")
        #plot.plot(rightStack, right, label="Right")
        plot.xlabel('TIME')
        plot.ylabel('DISTANCE (cm)')
        plot.legend()
        plot.show()
           
        
    except KeyboardInterrupt:
        print("terminated by user")
        GPIO.cleanup()
        
