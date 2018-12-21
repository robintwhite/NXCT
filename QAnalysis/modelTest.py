# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 08:02:38 2017

@author: Robin
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from IPython.display import display
import pickle

model_filename = 'SVR_model_Ion.sav'
loaded_model = pickle.load(open(model_filename, 'rb'))

#Read in data
data = pd.read_csv('MAttenDataCPtIonNorm.csv', sep='\t')
#data = data.loc[data['Thickness']==10] #Selecting only certain thickness values
#data = data.reset_index(drop=True)
#display(data)


X = data.ix[:,2:-2].copy()
Xsub = X[['Loading C','Loading Pt','Loading Ion']].copy() 
y = data.ix[:, 5].copy()

###Constant C plot
#for i in np.where(X.ix[:,0] == 0.42): #Where C loading is 0.42
#    Xsub = X.ix[i, 0:3].copy() #Get C Ion loading and Pt loadng
#    y = data.ix[i, 5].copy()

   
Xtrain = np.array(Xsub).reshape((len(Xsub),3))
ytrain = np.array(y).reshape((len(y),1))


#XtrainC = np.full(Xtrain['Loading C'].shape,0.42)
#XtrainC = np.asmatrix(XtrainC) #XtrainC.as_matrix()
XtrainC = Xtrain[:,0]
XtrainCM =  np.asmatrix(XtrainC)
XtrainPt = Xtrain[:,1]
XtrainPtM =  np.asmatrix(XtrainPt)
XtrainI = Xtrain[:,2]
XtrainIM =  np.asmatrix(XtrainI)
ytrainM = np.asmatrix(ytrain)

#XtestC=0.15
#XtestPt=0.4
#XtestIon=0.24
#norm = XtestC + XtestPt + XtestIon
Xtest = Xtrain[50,:] #len(Xsub.index)-500
#Xtest = np.array([XtestC/norm,XtestPt/norm,XtestIon/norm])
ytest = ytrainM[50] #len(y.index)-500

Xtest = np.array(Xtest).reshape((1,3))
display(Xtest)

#Predict
Z = loaded_model.predict(Xtrain)
y_predict = loaded_model.predict(Xtest)

#Prediction accuracy
print('Prediction rbf:', y_predict)
#print('Prediction lin:', y_lin_predict)
#print('Prediction poly:', y_poly_predict)
print('Actual:', ytest)
print('% error', abs(ytest - y_predict)*100/ytest)


# Max error
y_predict_err_perc = np.zeros(shape = (len(Xsub),1))
y_predict_err_abs = np.zeros(shape = (len(Xsub),1))
error_perc = 0
error_abs = 0
temp = 0

for i in range(len(Xsub)):
    Xtest = Xtrain[i,:]
    Xtest = np.array(Xtest).reshape((1,3))
    ytest = ytrainM[i]
    y_predict = loaded_model.predict(Xtest)
    error_perc = abs(ytest - y_predict)*100/ytest
    error_abs = abs(ytest - y_predict)
    y_predict_err_perc[i] = error_perc
    y_predict_err_abs[i] = error_abs
    if y_predict_err_perc[i] > temp:
        X_max = Xtest
        i_max = i
        y_predict_max =  error_perc#y_predict
        temp = error_perc
        
print('Max error:', max(y_predict_err_perc))
print('Max predict:', max(y_predict_max))
print('Max error loading:{}, index:{}'.format(X_max,i_max))
print('Avg error %:{}'.format(np.mean(y_predict_err_perc)))
print('Avg error:{}'.format(np.mean(y_predict_err_abs)))
fig = plt.figure()
ax = fig.gca()
#plt.scatter(range(len(Xsub)), y_predict_err_perc)
plt.scatter(range(len(Xsub)), y_predict_err_abs)
ax.set_xlabel('Training data')
ax.set_ylabel('Error')
plt.show()
#Plot

fig = plt.figure()
#ax = fig.add_subplot(111, projection='3d')
ax = fig.gca(projection='3d')
lw = 2
ax.scatter(XtrainPt, XtrainI, ytrain, s=2, cmap=cm.jet, label='data')
#ax.plot(XtrainPt, XtrainC, y_rbf_predict, c='navy', alpha = 0.5, lw=lw, label='RBF model')
#ax.plot(XtrainPt, XtrainC, y_lin_predict, c='c', lw=lw, label='Linear model')
#ax.plot(XtrainPt, XtrainC, y_poly_predict, c='cornflowerblue', lw=lw, label='Polynomial model')
#
ax.plot_trisurf(XtrainPt, XtrainI, Z, cmap=cm.jet, alpha = 0.5, linewidth=0.2, label='RBF model')
ax.set_xlabel('Wt % Pt')
ax.set_ylabel('Wt % Ion')
ax.set_zlabel('Mass atten')
ax.view_init(20, 135)
plt.title('Support Vector Regression')
#plt.legend()
plt.show()

plt.figure()
plt.scatter(XtrainPt, ytrain)
#plt.plot(XtrainPt, Z)
#plt.xlim(0, 0.9)
#plt.ylim(0, 0.9)
plt.title('Plot Pt')
plt.show()

plt.figure()
plt.scatter(XtrainC, ytrain)
#plt.plot(XtrainPt, Z)
#plt.xlim(0, 0.9)
#plt.ylim(0, 0.9)
plt.title('Plot Carbon')
plt.show()

plt.figure()
plt.scatter(XtrainI, ytrain)
#plt.plot(XtrainPt, Z)
#plt.xlim(0, 0.9)
#plt.ylim(0, 0.9)
plt.title('Plot Ionomer')
plt.show()