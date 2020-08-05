#lda_dump.py
#
#This script pulls training data from the specified filepath, cleans the extra data, and balances the data using downsampling of the majority class.
#Then, that data is appended to the running total list of all other training data which has been downsampled, and the current set of data is fitted to the model, and the accuracy score is calculated for the test data set.
#Once this has been done for all training data, the model is dumped to a joblib file which can be loaded and used for prediction.
#
#Model used: Linear Discriminant analysis
#
#Improvements to make
#   -Parametrize the filepath argument (make it a command line arg?)
#   -Collect real-world data for our desired case and train
#

import numpy as np #requirement for scipy, matplotlib, and sklearn
import scipy.io as sio
import pandas as pd #Used for dataframe structure for multidimensional arrays of data
from glob import glob #Used to search for subset of files in training data
from sklearn.pipeline import Pipeline
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis #Import framework for LDA model
from sklearn.utils import resample #Import functions to enable resampling of training data to balance dataset
from sklearn.model_selection import ShuffleSplit, cross_val_score
from joblib import dump #Used to dump trained model to joblib file for loading later

fpath = "/home/mindmap/Desktop/sklearn_train/train" #Filepath to training data


#Function used to extract data and events for each trial, cleans unnecessary data and trims off extra classification label
def extract_data(fname):
    data = pd.read_csv(fname) #read the csv file specified in the function call

    events_fname = fname.replace('_data', '_events') #replace data with events in file name to open the events data file

    labels = pd.read_csv(events_fname) #read the event data from the csv
    clean = data.drop(['id'], axis=1) #drop id column from the data
    labels = labels.drop(['id'], axis=1) #drop the id column from the labels
    label = labels.drop(labels.iloc[:, 1:].columns, axis=1) #drop all but the first label column to give us binary classification labels
    return clean, label #return our cleaned data and labels

subjects = range(1, 13) #there are 13 subjects in the dataset
clf = LinearDiscriminantAnalysis() #create an instance of an LDA model
test_x = [] #will hold our single test dataset signal data
test_y = [] #will hold our single test dataset class labels
combined_x = pd.DataFrame() #Will hold the combined dataset of the individual training data files which have been resampled
combined_y = [] #Will hold the classification labels of the combined dataset
for s in subjects: #for each of the subjects
    fnames = glob(fpath + '/subj%d_series*_data.csv' % (s)) #Generate a list of all the files which match the specified file name

    for i, fname in enumerate(fnames): #for each of the files in the generated list
        raw, lab = extract_data(fname) #extract the data from the single file
        X = raw
        Y = lab
        if (s == 1 and i == 0): #if we are on the first file for the first subject
            test_x = X #save its data for use as test data
            test_y = Y
            continue #continue to next iteration of loop
        X.insert(32, 'HandStart', Y['HandStart'].tolist()) #Add training labels as last column on the right of the signal dataframe
        count_class_0, count_class_1 = X.HandStart.value_counts() #Determine the number of samples in the data which have class 0 and class 1

        X_zer = X[X['HandStart'] == 0] #generate list of all samples in the dataset which have a classification of 0
        X_one = X[X['HandStart'] == 1] #generate list of all samples in the dataset which have a classification of 1

        if count_class_0 == count_class_1: #if the number of class 0 equals the number of class 1
            data_resamp = pd.concat([X_zer, X_one], axis=0) #recombine the data
        elif count_class_0 > count_class_1: #else if class 0 is the majority
            X_min = X_zer.sample(count_class_1, replace=True) #downsample the class 0 data to match the number of samples of class 1
            data_resamp = pd.concat([X_one, X_min], axis=0) #create the resampled dataset
        else: #else if class 1 is the majority
            X_min = X_one.sample(count_class_0, replace=True) #downsample the class 1 data to match the number of samples of class 0 
            data_resamp = pd.concat([X_min, X_zer], axis=0) #create the resampled dataset

        data_resamp_val = data_resamp.iloc[:, :32] #extract the signal data from the resampled data
        data_resamp_labels = data_resamp.iloc[:, 32] #extract the labels from the resampled data
        combined_x = combined_x.append(data_resamp_val) #append the resampled data to the combined dataset
        combined_y.extend(data_resamp_labels) #append the resampled labels to the combined dataset
        clf.fit(combined_x, combined_y) #fit the current combined dataset
        print(clf.score(test_x, test_y)) #print the accuracy score of the model using the test data

dump(clf, '/home/mindmap/Desktop/spi_test/trained_mod_final.joblib') #Once training is complete, dump the model to the following file location
