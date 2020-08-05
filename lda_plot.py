#lda_plot.py
#
#This script pulls training data from the specified filepath, cleans the extra data, and balances the data using downsampling of the majority class.
#Then, that data is appended to the running total list of all other training data which has been downsampled, and the current set of data is fitted to the model, and the accuracy score is calculated for the test data set.
#Once this has been done for all training data, the accuracy data is plotted against the number of samples which have been fitted.
#
#Model used: Linear Discriminant analysis
#
#Improvements to make
#   -Parametrize the filepath argument (make it a command line arg?)
#   -Collect real-world data for our desired case and train
#
import numpy as np #requirement for scipy, matplotlib, and sklearn
import matplotlib.pyplot as plt #used to plot data and format plot
import scipy.io as sio
import pandas as pd #used for dataframe structure for multidimensional arrays of data
from glob import glob #used to search for subset of files in training data
from sklearn.pipeline import Pipeline
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis #import LDA model framework
from sklearn.utils import resample #import functions to enable resampling to balance training data
from sklearn.model_selection import ShuffleSplit, cross_val_score
from joblib import dump#used to dump trained model

fpath = "/home/mindmap/Desktop/sklearn_train/train" #training data filepath

#Function used to extract data and events from file, cleans unnecessary data and trims off extra classification labels
def extract_data(fname):
    data = pd.read_csv(fname) #read eeg data csv file specified in function arg

    events_fname = fname.replace('_data', '_events') #replace data with events to open events data file

    labels = pd.read_csv(events_fname) #read event csv file that corresponds to file specified in the function arg 
    clean = data.drop(['id'], axis=1) #drop id labels for each row in eeg data
    labels = labels.drop(['id'], axis=1) #drop id labels for each row in event data
    label = labels.drop(labels.iloc[:, 1:].columns, axis=1) #drop all but first classification label
    return clean, label #return cleaned data and labels

subjects = range(1, 13) #there are 13 subjects in the training data
clf = LinearDiscriminantAnalysis() #create instance of LDA model
test_x = [] #will hold eeg data for test dataset
test_y = [] #will hold event data for test dataset
sumVal = 0
sampVal = 0
combined_x = pd.DataFrame() #will hold the eeg data of the combined dataset
combined_y = [] #will hold the label data of the combined dataset
acc_data = [] #will hold the accuracy value at each testpoint
for s in subjects: #for each subject
    epochs_tot = []
    fnames = glob(fpath + '/subj%d_series*_data.csv' % (s)) #generate list of files which fit the pattern specified
    #print(s)
    #print('\n')

    for i, fname in enumerate(fnames): #for each file in the generated list
        #print(i)
        raw, lab = extract_data(fname) #extract the desired data
        X = raw
        Y = lab
        if (s == 1 and i == 0): #if we have opened the first dataset
            #Score the data
            #print(clf.score(X, Y))
            test_x = X #store the data and labels as our test dataset
            test_y = Y
            continue #skip rest of loop for this iteration
        X.insert(32, 'HandStart', Y['HandStart'].tolist()) #Add training labels as 33rd column in eeg data
        count_class_0, count_class_1 = X.HandStart.value_counts() #count the number of rows which areclassified as either 0 or 1

        X_zer = X[X['HandStart'] == 0] #extract subset of data which is classified as 0
        X_one = X[X['HandStart'] == 1] #extract subset of data which is classified as 1

        if count_class_0 == count_class_1: #if the number data points in each class is equal
            data_resamp = pd.concat([X_zer, X_one], axis=0) #recombine the data
        elif count_class_0 > count_class_1: #if class 0 has more samples than 1
            X_min = X_zer.sample(count_class_1, replace=True) #downsample class 0 to be the same size as class 1
            data_resamp = pd.concat([X_one, X_min], axis=0) #recombine the resampled data
        else: #else class 1 is larger than class 0
            X_min = X_one.sample(count_class_0, replace=True) #resample class 1 to be the same size as class 0
            data_resamp = pd.concat([X_min, X_zer], axis=0) #recombine the resampled data

        data_resamp_val = data_resamp.iloc[:, :32] #extract the eeg data from the resampled data
        data_resamp_labels = data_resamp.iloc[:, 32] #extract the labels from the resampled data
        combined_x = combined_x.append(data_resamp_val) #append the resampled eeg data to the combined dataset
        combined_y.extend(data_resamp_labels) #append the resampled labels to the combined dataset
        #print(combined_x.shape)
        #print(len(combined_y))
        clf.fit(combined_x, combined_y) #fit the current combined dataset
        #print(clf.score(test_x, test_y))
        acc_data.append(clf.score(test_x, test_y)) #generate the accuracy score and append it to the list of accuracy scores
        #sumVal += clf.score(test_x, test_y)
        #sampVal += 1
        #print(sumVal/sampVal)

#dump(clf, '/home/mindmap/Desktop/spi_test/trained_mod.joblib')
samp = range(1, len(acc_data) + 1) #generate list of successive ints which show how many samples were fitted each time
plt.plot(samp, acc_data) #plot the accuracy data vs the number of samples fitted
plt.xlabel('Samples fitted') #add x-axis label
plt.ylabel('Accuracy score') #add y-axis label
plt.title('Accuracy vs samples fitted') #add plot title
plt.grid(True) #add grid to plot
plt.ylim(0, 1) #specify the limits on the y-axis
plt.show()#show the plot
