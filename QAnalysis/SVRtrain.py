#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 28 19:45:01 2016
    Train regression model to be used for calculated mass attenuation coefficients
    to be used in quantitative optimization model
    Save trained model using pickle
@author: robin
"""

#print(__doc__)

import pandas as pd
import numpy as np
from sklearn.svm import SVR
#from sklearn.kernel_ridge import KernelRidge
from IPython.display import display
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
from datetime import datetime
from matplotlib import cm
import pickle

#Read in data
data = pd.read_csv('MAttenDataCPtIonNorm.csv', sep='\t')
#data = data.loc[data['Thickness']==10] #Selecting only certain thickness values
#data = data.reset_index(drop=True)
#display(data)

X = data.iloc[:,2:-2].copy()
Xsub = X[['Loading C','Loading Pt','Loading Ion']].copy()
Xtrain = Xsub#[:-10].copy()
Xtrain1 = np.array(Xtrain).reshape((len(Xtrain),3))
y = data['Mass atten.'].copy() #Previous had error with two sets of [] as above with Xsub asks for 1D array
ytrain = y#[:-10].copy()
GS = data['calc. GSV'].copy()
GStrain = GS#[:-10].copy()

XtrainC = Xtrain['Loading C']
XtrainC = XtrainC.as_matrix()
XtrainPt = Xtrain['Loading Pt']
XtrainPt = XtrainPt.as_matrix()
XtrainI = Xtrain['Loading Ion']
XtrainI = XtrainI.as_matrix()
ytrainM = ytrain.as_matrix()
GStrainM = GStrain.as_matrix()
#display(ytrainM)

Xtest = Xsub.loc[len(Xsub.index)-1]
display(Xtest)
Xtest = np.array(Xtest).reshape((1,3))
ytest = y.loc[len(y.index)-1]
#display(XtrainPt)

#scaler = preprocessing.MinMaxScaler()
#Xtrain_scaled = pd.DataFrame(scaler.fit_transform(Xtrain), columns=Xtrain.columns)
#display(Xtrain_scaled)
#
#Fit regression model
#http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
svr_rbf = SVR(kernel='rbf', C=1000, gamma='auto')
svr_lin = SVR(kernel='linear', C=1000)
#clf = KernelRidge(alpha=0.05)
#svr_poly = SVR(kernel='poly', C=1000, degree=2)

t0 = datetime.now()
y_rbf = svr_rbf.fit(Xtrain1, ytrain)
t_rbf = datetime.now() - t0
#KR = clf.fit(Xtrain1, ytrain)
#y_lin = svr_lin.fit(Xtrain, ytrain)
#t_lin = datetime.now() - t0
#y_poly = svr_poly.fit(Xtrain, ytrain)
#t_poly = datetime.now() - t0

#Prediction
y_rbf_predict = y_rbf.predict(Xtest)
#KR_predict = KR.predict(Xtest)
#y_lin_predict = y_lin.predict(Xtest)
#y_poly_predict = y_poly.predict(Xtest)

#Print
#RBF shown to have best acuracy of the three
print('Time rbf:', t_rbf)
#print('Time lin:', t_lin)
#print('Time poly:', t_poly)
print('Prediction rbf:', y_rbf_predict)
#print('Prediction KR:', KR_predict)
#print('Prediction poly:', y_poly_predict)
print('Actual:', ytest)
print('% error', abs(ytest - y_rbf_predict)*100/ytest)
#print('% error', abs(ytest - KR_predict)*100/ytest)
#print('% error', abs(ytest - y_poly_predict)*100/ytest)

##Take thickness and calculate GSV from loading and Mass atten
##(Need to calculate density and multiply with Mass atten)
##Loading is input from genetic algorithm to find best inputs that yield
##closest GSV to experimental given calculated Mass atten from model

# save the model to disk
filename = 'SVR_model_Ion.sav'
pickle.dump(svr_rbf, open(filename, 'wb'))


