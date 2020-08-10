#ad_file_save.py
#
#This script samples signals off of ADC over SPI and saves the data with classification labels to csv file 
#
#Enables SPI through spidev on spi0.0 (see all available SPI devices at /dev/)
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
#       -Parametrize the file location, maybe write a script to automate the updating of file names for data collection purposes
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
import sys #Enables keyboard interrupt for safe early exit
#from ext_print import print_samp
from multiprocessing import Process, Queue

int_pin = 29 #define external interrupt pin
filepath = "/home/mindmap/Desktop/mindmap_final/sample_data.csv" #define filepath for data storage
samples = 0
pqueue = Queue()

spi = spidev.SpiDev() #create spi interface instance

#Converts value from fifo to proper 12-bit representation and returns int representation
def fifo_conv(t):
    tot_val = 0 #start with zero
    for n in t: #for each 8-bit value in the list of collected ADC values
        tot_val = (tot_val << 8) + n #shift the current total to the right by 8 bits and add the current iteration value
    tot_val >> 4 #once all 16 bits are added up, shift right by 4 to drop the 4 LSB's
    #print(tot_val)
    return tot_val #return the converted value

#On interrupt, reads two values off of the FIFO
def fifo_read(z):
    curTime = time.time()
    r1 = spi.xfer2([0b11100000, 0b00000000]) #Issues FIFO read command
    v1 = fifo_conv(r1) #convert the collected values
    r2 = spi.xfer2([0b11100000, 0b00000000])#Issues FIFO read command
    v2 = fifo_conv(r2) #convert the collected values
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
    a = spi.xfer2([0b10100000, 0b00000000]) #Write all 0 to CFR
    time.sleep(1)
    x = spi.xfer2([0b10100000, 0b11111011]) #write configuration value to CFR
    time.sleep(.1)
    #countSamp = 0
    for sam in range(0, 832):
        t_start = time.time()
        y = spi.xfer2([0b00010000, 0b00000000, 0b00000000, 0b000000])#Write arbitrary channel command with padding for conversion time
        time.sleep(.0001) 
        y = spi.xfer2([0b00010000, 0b00000000, 0b00000000, 0b000000])#Write arbitrary channel command with padding for conversion time
        time.sleep(.005) #Wait for INT signal to toggle (adjust this value to increase sampling rate)
        r1 = spi.xfer2([0b11100000, 0b00000000]) #Issues FIFO read command
        v1 = fifo_conv(r1) #convert the collected values
        r2 = spi.xfer2([0b11100000, 0b00000000])#Issues FIFO read command
        v2 = fifo_conv(r2) #convert the collected values
        if(sam > 415): #If we have reached 2.5s into the sample, we want the user to move their arm so we set the label variable to 1
            samples = 1
        else: #Else we expect the user to not be moving so the label should be 0
            samples = 0
        print_str = str(v1) + ',' + str(v2) + ',' + str(samples) + '\n' #creates comma-separated value string
        f = open(filepath, "a") #open the data file in append mode
        f.write(print_str) #write the comma-separated value string to the file
        f.close() #close the file
        #queue.put([v1, v2])
        #print(time.time() - t_start)
    #finally: #once complete
    #    gpio.cleanup() #clean up all gpio assignments

try: #Try starting the main function
    #pqueue = Queue()
    #print_p = Process(target=print_samp, args=((pqueue), ))
    #print_p.daemon = True
    #print_p.start()
    main(pqueue) #call main
except KeyboardInterrupt: #On keypress
    print("Ended") 
    #pqueue.put("DONE")
    time.sleep(1) #Wait to allow script to properly end
    #print_p.join()
    spi.close() #close the spi interface
    #gpio.cleanup()
    sys.exit() #End the script

