import RPi.GPIO as GPIO
import time
import sys
import threading
import socketio

sio = socketio.Client()
sio.connect('http://summer-development-env-dev002.us-east-1.elasticbeanstalk.com')

GPIO.setmode(GPIO.BOARD)

TRIG_2 =11 #11 #5
ECHO_2 =7 #7 #3
TRIG_1 =5
ECHO_1 =3
DISTANCE = 20
maxTime = 0.04

GPIO.setwarnings(True)

print("start meare...")

def getDistance(TRIG, ECHO):
    GPIO.setup(TRIG,GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    #set trigger to high
    GPIO.output(TRIG,True)

    #set tigger to low after 0.01ms
    time.sleep(0.01)
    GPIO.output(TRIG,0)
    time.sleep(0.00001)
    
    start = time.time()
    timeout = start + maxTime
    while GPIO.input(ECHO) == 0 and start < timeout:
        start = time.time()
    
    stop = time.time()
    timeout = stop + maxTime
    while GPIO.input(ECHO) == 1 and stop < timeout:
         stop = time.time()
  
    distance = ((stop-start)*34300)/2
    #if(distance<10):
    #print("Measured distance = %.1f cm" % distance)
      
    time.sleep(0.0003)
>>>>>>> 5a7854c18dd4a2393aa3ae2850aa6e974a27a86f
    
    return distance, stop

def mainLooping(TRIG, ECHO):
    num = 0
    while True:
        dist = getDistance(TRIG, ECHO)
        if(dist<10):
            num += 1
            print("Measured distance = %.1f cm" % dist)
            sys.stdout.flush()
        time.sleep(0.1)         

def sendMessage(direction):
    sio.emit('vision.swipeRight', {'direction': direction})

def useTwoUltrasonics(TRIG_1, ECHO_1, TRIG_2, ECHO_2):
    rightUltraTimeDistance = (0,0)
    leftUltraTimeDistane = (0,0)
    while True:
        tempRight = getDistance(TRIG_1,ECHO_1)
        tempLeft = getDistance(TRIG_2,ECHO_2)
        
        if(tempLeft[0] < DISTANCE):
             leftUltraTimeDistane = tempLeft
            
        if(tempRight[0] < DISTANCE):
            rightUltraTimeDistance = tempRight

           
        term = rightUltraTimeDistance[1]-leftUltraTimeDistane[1]
        it calulated last detected time. it mean rightUltra detect hands ahead of leftUltra
        if (term < 0 and term > -1):
            sendMessage('left')
            print("right to left detected")
            rightUltraTimeDistance = (0,0)
            leftUltraTimeDistane = (0,0)
          
        elif (term > 0 and term < 1.2):
            sendMessage('right')
            print("left to right detected")
            rightUltraTimeDistance = (0,0)
            leftUltraTimeDistane = (0,0)
           
if __name__ == '__main__':
    try:
        useTwoUltrasonics(TRIG_1, ECHO_1, TRIG_2, ECHO_2)
    except Exception as exc:
        print("Stop by user or error",exc)
        GPIO.cleanup()
