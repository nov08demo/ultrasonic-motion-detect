import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import matplotlib.pyplot as plot


CLK = 18
MISO = 23
MOSI = 24
CS = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK,cs =CS, miso=MISO, mosi=MOSI)
t = [] #time data
d = [] #distance data
t2=[]
d2=[]
 
    
if __name__ == '__main__':
    try:
        for x in range(100):
            v = (mcp.read_adc(0) / 1023.0) * 3.3
            v2 = (mcp.read_adc(1)/1023.0)*3.3
            dist = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 301.439
            dist2 = 16.2537 * v2**4 - 129.893 * v2**3 + 382.268 * v2**2 - 512.611 * v2 + 301.439
            d.append(dist)
            d2.append(dist2)
            print(dist)
            print(dist2)
            tData = time.time()
            
            t.append(tData)
            t2.append(tData)

        plot.plot(t2,d2,label="left")
        
        plot.xlabel('TIME')
        plot.ylabel('DISTANCE (cm)')
        plot.legend()
        plot.show()
           
        
    except KeyboardInterrupt:
        print("terminated by user")
        GPIO.cleanup()
        

