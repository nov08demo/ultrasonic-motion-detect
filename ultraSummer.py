import RPi.GPIO as GPIO
import time
import sys
import os
from dotenv import load_dotenv
load_dotenv()
from threading import Thread
import socketio
from cloudwatch_logger import CloudwatchLogger
sio = socketio.Client()
sio.connect('http://summer-development-env-dev002.us-east-1.elasticbeanstalk.com')

GPIO.setmode(GPIO.BOARD)
TRIG_3 = 12
ECHO_3 = 10
TRIG_2 =11 #11 #5
ECHO_2 =7 #7 #3
TRIG_1 =5
ECHO_1 =3
DISTANCE = 30
maxTime = 0.04
log = CloudwatchLogger(os.getenv('LOG_GROUP'), os.getenv('LOG_STREAM'), __file__)
GPIO.setwarnings(True)
log.info('Listening for socket...')
def getDistance(TRIG, ECHO):
    GPIO.setup(TRIG,GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    #set trigger to high
    GPIO.output(TRIG,True)

    #set tigger to low after 0.01ms
    time.sleep(0.001)
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
    #log.info("Measured distance = %.1f cm" % distance)
      
    time.sleep(0.0003)
    
    return distance, stop

def mainLooping(TRIG, ECHO):
    num = 0
    while True:
        dist = getDistance(TRIG, ECHO)
        if(dist<10):
            num += 1
            log.info("Measured distance = %.1f cm" % dist)
            sys.stdout.flush()
        time.sleep(0.1)         

def sendMessage(direction):
    sio.emit('vision.swipeRight', {'direction': direction})

def useThreeUltrasonics(TRIG_1, ECHO_1, TRIG_2, ECHO_2, TRIG_3, ECHO_3):
    log.info("start gesture...")
    rightUltraTimeDistance = (0,0)
    leftUltraTimeDistane = (0,0)
    middleUltraTimeDistance = (0,0)
    global run
    while run:
        tempRight = getDistance(TRIG_1,ECHO_1)
        tempLeft = getDistance(TRIG_2,ECHO_2)
        tempMiddle = getDistance(TRIG_3, ECHO_3)
        if(tempLeft[0] < DISTANCE):
             leftUltraTimeDistane = tempLeft
            
        if(tempRight[0] < DISTANCE):
            rightUltraTimeDistance = tempRight
        
        if(tempMiddle[0] < DISTANCE):
            middleUltraTimeDistance = tempMiddle
        
        
        firstPass = rightUltraTimeDistance[1] - middleUltraTimeDistance[1]
        secondPass = middleUltraTimeDistance[1] - leftUltraTimeDistane[1]
        fullPass = rightUltraTimeDistance[1] - leftUltraTimeDistane[1]
        allPassLeft = firstPass < 0 and secondPass < 0
        allPassRight = firstPass > 0 and secondPass > 0
        
        onlyEndsPassLeft = fullPass < 0 and fullPass > -1
        onlyEndsPassRight = fullPass > 0 and fullPass < 1.2
        
        if(allPassRight or onlyEndsPassRight):
            sendMessage('right')
            log.info("left to right detected")
            rightUltraTimeDistance = (0,0)
            leftUltraTimeDistane = (0,0)
            middleUltraTimeDistance = (0,0)
            time.sleep(1)
        elif(allPassLeft or onlyEndsPassLeft):
            sendMessage('left')
            log.info("right to left detected")
            rightUltraTimeDistance = (0,0)
            leftUltraTimeDistane = (0,0)
            middleUltraTimeDistance = (0,0)
            time.sleep(1)

@sio.on('edge.startEdge')
def start(data):
    global run
    run = True
    GPIO.setmode(GPIO.BOARD)
    mainThread = Thread(target=useThreeUltrasonics, args=[TRIG_1, ECHO_1, TRIG_2, ECHO_2, TRIG_3, ECHO_3])
    mainThread.daemon = True
    mainThread.start()
    log.info('Starting...')
    sio.emit('edge.startSuccessful')
    
@sio.on('edge.stopEdge')
def stop(data):
    global run
    run = False
    log.info('Stopping...')
    sio.emit('edge.stopSuccessful')
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        while True:
            continue
    except Exception as exc:
        log.info("Stop by user or error",exc)
        GPIO.cleanup()
