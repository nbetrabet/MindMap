#plot_data.py
#
#Utility to plot a slice of 100 samples from collected EEG data
#
#Improvements to make
#   -Parametrize the filepath values
#   -parametrize the number of channels being sampled
#   -parametrize time step value based on sampling period
#
#
import matplotlib.pyplot as plt #Allows us to plot values and format the plot
import numpy as np #Allows better mathematic programming

ch0 = [] #channel 0 value list
ch2 = [] #channel 2 value list

with open('/home/mindmap/Desktop/spi_test/sample_data_1.csv') as f: #Open data csv file
    for line in f: #For each line in the file
        #print(line)
        l1 = line.split(',') #split the line at the comma
        map_obj = map(int, l1) #map the list of strings returned by the split to integer values
        int_list = list(map_obj) #create a list using the values in the map
        if(int_list[0] == 0 and int_list[1] == 0): #if both values are 0, ignore
            continue
        ch0.append((int_list[0]/65535) * 5) #convert the ADC step value to voltage
        ch2.append((int_list[1]/65535) * 5)

f.close() #close the file

sliceVal = ch0[500:601] #Take a slice of the channel 0 values
#y = range(0, len(ch0))
#y = range(500*, len(sliceVal))
startTime = 500 * .006 #time stamp for first sample in slice (given that the first sample in file is at 0 seconds)
endTime = 600 * .006 #time stamp for last sample in slice
y = np.arange(startTime, endTime, .006).tolist() #generate a list of numbers between the timestamp values with step size equal to sampling period

plt.plot(y, sliceVal) #plot the EEG value
#plt.plot(y, ch2)
plt.title('Sampled EEG signal') #Specify plot title
plt.xlabel('time(s)') #specify x-axis label
plt.ylabel('Voltage(V)') #specify y-axis label
plt.ylim(0, 5) #specify the y-axis limits
plt.show() #show the plot
