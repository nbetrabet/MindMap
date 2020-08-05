#ad_pred.py
#
#This script samples signals off of ADC over SPI and pipes the sensor data to the ML model for prediction 
#
#Enables SPI through spidev on spi0.0 (see all available SPI devices at /dev/)
#
#Utilizes multiprocessing queue as pipe between ADC process and ML prediction process, with the ADC process being the master which starts the ML prediction process
#
#See datasheet for TLV2548 for timing diagrams for stages of communication
#Overview:
#   -Write all 0 to CFR
#   -Write desired configuration to CFR
#   -Issue any channel select command with a 30bit long message to allow for short conversion
#       -repeat this command for however many samples are configured to be held in the FIFO
#   -Once all desired samples are taken, wait for a few SCLK cycles and then begin to issue FIFO read commands, samples values are output of the xfer command as tx and rx happen at the same time
#   -Convert each channel's sample value
#   -Append the tuple, with the classification label to csv file
#   -Repeat steps for 5s with 2.5s window for motion
#
#Improvements to make:
#   -make this script more adjustable and dynamic
#       -parametrize delay between samples and FIFO read
#       -parametrize number of samples which are going to be stored in FIFO, then use loop for sampling commands
#       -Parametrize configuration value
#       -Add improvements to ensure safe exit of ML prediction process, some kind of flow limiter on queue.put() (buffer in this process?)
#
#Essential command formats (see TLV2548 documentation for more details)
#   -Write to CFR - 0xAXXX (Last 12 bits correspond to specific configuration parameters)
#       -bit11: 0-External reference | 1-Internal reference
#       -bit10: 0-Internal reference 4V | 1-Internal reference 2V (don't care if b11 = 0)
#       -bit9: 0-Short sample (12clk) | 1-Long sample (24clk)
#       -bit8-7: 00-internal osc for conv | 01-SCLK | 10-SCLK/4 | 11-SCLK/2
#       -bit6-5: 00-single conv mode | 01-single repeat conv | 10-sweep mode | 11-repeat sweep mode
#       -bit4-3: see documentation for channel sweep sequence values
#       -bit2: 0-use pin as INT | 1-use pin as EOC
#       -bit1-0: 00-Full FIFO trigger | 01-Trigger FIFO at 6 values | 10-Trigger at 4 values | 11-Trigger at 2 values
#
import Jetson.GPIO as gpio #Imports gpio functionality for the Jetson
import spidev #enables spi interface functions
import time #enables us to delay commands
import csv
import sys #Enables safe script exit
#from ext_print import print_samp
from par_inference import predThread #imports ML prediction function for multiprocessing
from multiprocessing import Process, Queue #enables multiprocessing and piping through queue

int_pin = 29 #define external interrupt pin
filepath = "/home/mindmap/Desktop/spi_test/sample_data_1.csv" #define filepath for data storage
samples = 0
pqueue = Queue() #creates empty queue for multiprocessing

spi = spidev.SpiDev() #create spi interface instance
#conf = [0b10100000, 0b11111011]
conf = [0b10100000, 0b11111011] #CFR configuration value
read = [0b1001000000000000]
fifo = [0b11100000, 0b00000000]
ch0 = [0b00010000, 0b00000000]

#Converts value from fifo to proper 12-bit representation and returns int representation
def fifo_conv(t):
    #print(t)
    tot_val = 0 #start with zero
    for n in t: #for each 8-bit value in the list of collected ADC values
        tot_val = (tot_val << 8) + n #shift the current total to the right by 8 bits and add the current iteration value
    tot_val >> 4 #once all 16 bits are added up, shift right by 4 to drop the 4 LSB's
    #print(tot_val)
    return tot_val #return the converted value

#On interrupt, reads two values off of the FIFO
def fifo_read(z):
    print("interrupted")
    curTime = time.time()
    r1 = spi.xfer2([0b11100000, 0b00000000]) #Issues FIFO read command
    v1 = fifo_conv(r1) #convert the collected values
    print(v1)
    r2 = spi.xfer2([0b11100000, 0b00000000])#Issues FIFO read command
    v2 = fifo_conv(r2) #convert the collected values
    print(v2)
    print_str = str(v1) + ',' + str(v2) + '\n' #creates comma-separated value string
    f = open(filepath, "a") #open the data file in append mode
    f.write(print_str) #write the comma-separated value string to the file
    f.close() #close the file
    print(time.time() - curTime)

#Main function which establishes all interface pins and defines the external interrupt
def main(queue):
    samples = 0
    spi.open(0, 0) #open spi0.0
    spi.max_speed_hz = 4000000 #set the SPI interface to 4MHz
    spi.bits_per_word = 8 #set each word to be transmitted to be 8 bits long
    spi.mode = 0b00 #Set SPI interface mode
    gpio.setmode(gpio.BOARD) #set the gpio addressing mode to that of the Jetson board
    gpio.setup(int_pin, gpio.IN) #Set the interrupt pin as an input
    #gpio.add_event_detect(int_pin, gpio.RISING, callback=fifo_read, bouncetime=0) #confgure the external interrupt to depend on the interrupt pin, look for a rising edge, on interrupt call the fifo_read function with no bounce delay
    try: #continuously try this look
        x = spi.xfer2([0b10100000, 0b11111011]) #write configuration value to CFR
        print(x)
        time.sleep(.1)
        countSamp = 0
        while True:
            t_start = time.time()
            y = spi.xfer2([0b00010000, 0b00000000, 0b00000000, 0b000000])#Write arbitrary channel command with padding for conversion time
            time.sleep(.0001) 
            y = spi.xfer2([0b00010000, 0b00000000, 0b00000000, 0b000000])#Write arbitrary channel command with padding for conversion time
            time.sleep(.005) 
            r1 = spi.xfer2([0b11100000, 0b00000000]) #Issues FIFO read command
            v1 = fifo_conv(r1) #convert the collected values
            #print(v1)
            r2 = spi.xfer2([0b11100000, 0b00000000])#Issues FIFO read command
            v2 = fifo_conv(r2) #convert the collected values
            #print(v2)
            print_str = str(v1) + ',' + str(v2) + '\n' #creates comma-separated value string
            #f = open(filepath, "a") #open the data file in append mode
            #f.write(print_str) #write the comma-separated value string to the file
            #f.close() #close the file
            queue.put([v1, v2]) #put the current sensor data into shared queue
            #print(time.time() - t_start)
    finally: #once complete
        gpio.cleanup() #clean up all gpio assignments

try:
    pqueue = Queue() #create empty queue
    print_p = Process(target=predThread, args=((pqueue), )) #create process which will run our prediction function and pass the queue as the only argument
    print_p.daemon = True #Set daemon to true, prevent prediction process from spawning its own child processes
    print_p.start() #start the parallel process
    main(pqueue) #call main
except KeyboardInterrupt:
    print("Ended")
    #pqueue.put("DONE")
    time.sleep(1)
    print_p.join() #force end the ML prediction process
    spi.close() #close the spi interface
    #gpio.cleanup()
    sys.exit() #end the script

