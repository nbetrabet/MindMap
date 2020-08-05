import numpy as np
import scipy.io as sio
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from joblib import load
from multiprocessing import Queue

def predThread(queue):
    clf = load('/home/mindmap/Desktop/spi_test/trained_mod_final.joblib')
    while True:
        if(not queue.empty()):
            val = queue.get()
            finalList = [val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1], val[0], val[1]]
            df = pd.DataFrame([finalList])
            pred = clf.predict_proba(df)
            #print(clf.predict_proba(df))
            listProb = pred[0]
            print(listProb)
            if listProb[0] >= listProb[1]:
                print("No movement")
            else:
                print("Movement")
