#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 14:20:43 2016

Updated 26/5/17
@author: robin
"""
##Extends NISTScrape.py and SVRtest.py

import numpy as np
import matplotlib.pyplot as plt
import pickle
from scipy.optimize import minimize
from scipy import misc
from PIL import Image
from datetime import datetime

##Uses SVR model obtained by collecting data from NIST for variation in 
##Carbon loading and Pt loading at energy of 32.5keV

model_filename = 'SVR_model_Ion.sav'

#Base directory
global C_scale
C_scale = 0 #Percent loss ie 0.7 loss, 70% less, 30% remaining in CCL from CO2 measurements
cyclenum = "BOL"

baseDir = r"E:\processed\Cell29\CL_Analysis\\" + cyclenum + "\\"
#Output filenames
IonImage = cyclenum + "_I_Load.tif"
PtImage = cyclenum + "_Pt_Load.tif"
CImage = cyclenum + "_C_Load.tif"
DensityImage = cyclenum + "_Density.tif"
TotalLoadImage = cyclenum + "_TotalLoad.tif"
MattenImage = cyclenum + "_Matten.tif"
PorosityImage = cyclenum + "_Porosity.tif"

##------------Initialization-------------##

#Load images
Timage = misc.imread(baseDir + cyclenum + "_thickness.tif") #Thickness_map16
Gimage = misc.imread(baseDir + cyclenum + "_MAX.tif") #BOL_avg_flat

#Pixel size um
pix = 1.53

#Sub of area if necessary
T = Timage#[400:500, 400:500] #Timage
G = Gimage#[400:500, 400:500] #Gimage
#Cmap = Cmapimage[400:500, 400:500]
#Ptmap = Ptmapimage[400:500, 400:500]
#Imap = Imapimage[400:500, 400:500]
#Thickness Calibration 49.6um 2^16 - 1 from 16bitGS to thickness value
#calib = 49.6/((2**16)-1)

# load the SVR model from disk
loaded_model = pickle.load(open(model_filename, 'rb'))

#Calibration curve for GSV calc only ##Updated for MAX GSV
mcal = 2390.5 #Max
bcal = 22974


#BOL expected values for 50/50 C/Pt 23wt% Ionomer
wt_exp_Ion = 23
wt_exp_Pt = (100-wt_exp_Ion)*0.5
wt_exp_C = 100 - wt_exp_Ion - wt_exp_Pt

load_exp_C = 0.4
load_exp_Pt = 0.4
load_exp_Ion = (wt_exp_Ion/wt_exp_Pt)*load_exp_Pt

#Molar masses
M_C = 12
M_Pt = 195
M_Ion = 544
M_water = 18
MM = np.array([M_C,M_Pt,M_Ion,1])

#Density of particles
Cp = 2.266
Ptp = 21.45
Ip = 1.8

#Volume cm^3
vox = (pix**3)*0.000000000001

#Array initialization
Matten_array = np.zeros((T.shape[0],T.shape[1]), dtype=float)
C_load_array = np.zeros((T.shape[0],T.shape[1]), dtype=float)
Pt_load_array = np.zeros((T.shape[0],T.shape[1]), dtype=float)
Ion_load_array = np.zeros((T.shape[0],T.shape[1]), dtype=float)
Density_array = np.zeros((T.shape[0],T.shape[1]), dtype=float)
TotalLoad_array = np.zeros((T.shape[0],T.shape[1]), dtype=float)
Porosity_array = np.zeros((T.shape[0],T.shape[1]), dtype=float)
#result_array = np.zeros_like(Pt_load_array)

#Time start
t0 = datetime.now()

def sigmoid(z, a):
    s = 1.0 / (1.0 + np.exp(a - z))
    return s

mu_T = 8.5*pix#np.mean(T) #Needs to not include 0s

count = 0
## Loop
for i in range(T.shape[0]): #up and down 0<=i<dimension in X
    for j in range(T.shape[1]): #left to right
        count += 1
        if count%int(T.shape[0]*T.shape[1]/20) == 0:
            print('{0}'.format("% complete: "), '{:.2f}'.format(count/(T.shape[0]*T.shape[1])))
            t = datetime.now() - t0
            print(t)
        
        #Thickness
        thickness = T[i, j]*pix
        #Check non-zero thickness
        if thickness <= pix:
            C_load_array[i,j] = 0
            Pt_load_array[i,j] = 0
            Ion_load_array[i,j] = 0
            Density_array[i,j] = 0
            TotalLoad_array[i,j] = 0
            Porosity_array[i,j] = 1            
            #print('flag thickness')
            
            
        else:
        #experimental GSV
            expGS = G[i, j]
            
            def myFun(x):
                 #loading calculation
                myFun.load_C = abs(x[0])
                myFun.load_Pt = abs(x[1])
                myFun.load_Ion = abs(x[2]) #Ionomer not to vary for other than BOL
                myFun.load_CL = myFun.load_C + myFun.load_Pt + myFun.load_Ion
                
                #Normalize for Mass atten model
                norm = myFun.load_C + myFun.load_Pt + myFun.load_Ion
                Xnorm = np.array([myFun.load_C/norm, myFun.load_Pt/norm, myFun.load_Ion/norm])
                #Reshape data
                X = np.array(Xnorm).reshape((-1,3))
                #Calculate Mass attenuation from SVR model previously determined and loaded
                myFun.MA_calc = loaded_model.predict(X)
                #Density 0-->3 C,Pt,I,CL
                myFun.density = myFun.load_CL/(thickness*0.1)
                myFun.calcGS = myFun.MA_calc*myFun.density*mcal + bcal
                return np.asscalar(abs(myFun.calcGS-expGS))
            
            #density calc
            def denC(x):
                denC.load_C = abs(x[0])
                denC.load_Pt = abs(x[1])
                denC.load_Ion = abs(x[2])
                denC.load_CL = denC.load_C + denC.load_Pt + denC.load_Ion
#                
                #Density 0-->3 C,Pt,I,CL
                return np.asscalar(denC.load_CL/(thickness*0.1))
            
            #porosity calc
            def porC(x):
                density = (abs(x[0]) + abs(x[1]) + abs(x[2]))/(thickness*0.1)
                CwtP = abs(x[0])/(abs(x[0]) + abs(x[1]) + abs(x[2]))
                Cvol = CwtP*density*vox/Cp
                PtwtP = abs(x[1])/(abs(x[0]) + abs(x[1]) + abs(x[2]))
                Ptvol = PtwtP*density*vox/Ptp
                IwtP = abs(x[2])/(abs(x[0]) + abs(x[1]) + abs(x[2]))
                Ivol = IwtP*density*vox/Ip
                Tvol = Cvol + Ptvol + Ivol                
                #Density 0-->3 C,Pt,I,CL
                return np.asscalar((vox-Tvol)/vox) #Porosity
            
            def valC(x):
                C1 = abs(x[0])
                P1 = abs(x[1])
                return (C1-P1)*(P1-C1)
            #Initial guess Ionomer/Pt loading typical 0.23/0.4
            x0 = np.array([0.4, 0.4, 0.23 + sigmoid(thickness, 2.0*mu_T)]) 
# + sigmoid(thickness, 2.0*mu_T)
                           
#            bnds = ((None, None),(None, None),(None, None)) #bounds. Must be positive, can have higher ionomer
            cons = ({'type': 'ineq', 'fun': lambda x: x - 0.001}, #correction for using x = 0 and dividing by 0
                    {'type': 'ineq', 'fun': lambda x: valC(x)},
                    {'type': 'ineq', 'fun': lambda x: 1 - porC(x)},
                    {'type': 'ineq', 'fun': lambda x: porC(x)}) #constraint g(x) >= 0
            
            res = minimize(myFun, x0, method = 'COBYLA', constraints = cons,
                       options = {'disp': False}).x
#            res = minimize(myFun, x0, method = 'SLSQP', bounds = bnds, constraints = cons,
#                       options = {'disp': False}).x
            #res = minimize(myFun, x0, method = 'TNC', bounds = bnds, 
            #           options = {'xtol': 1e-8, 'disp': False})
            #method = 'powell' 
            
            Matten_array[i,j] = myFun.MA_calc
            Pt_load_array[i,j] = myFun.load_Pt
            Ion_load_array[i,j] = myFun.load_Ion
            C_load_array[i,j] = myFun.load_C
            Density_array[i,j] = (myFun.load_C + myFun.load_Pt + myFun.load_Ion)/(thickness*0.1)
            TotalLoad_array[i,j] = myFun.load_CL
            
            CwtP = myFun.load_C/(myFun.load_C + myFun.load_Pt + myFun.load_Ion)
            Cvol = CwtP*Density_array[i,j]*vox/Cp
            PtwtP = myFun.load_Pt/(myFun.load_C + myFun.load_Pt + myFun.load_Ion)
            Ptvol = PtwtP*Density_array[i,j]*vox/Ptp
            IwtP = myFun.load_Ion/(myFun.load_C + myFun.load_Pt + myFun.load_Ion)
            Ivol = IwtP*Density_array[i,j]*vox/Ip
            Tvol = Cvol + Ptvol + Ivol
            Airvol = vox-Tvol
            Porosity_array[i,j] = Airvol/vox

#Time end
t = datetime.now() - t0
print(t)    
  
plt.imshow(Density_array)
im1 = Image.fromarray(Ion_load_array)
im2 = Image.fromarray(Pt_load_array)
im3 = Image.fromarray(C_load_array)
im4 = Image.fromarray(Density_array)
im5 = Image.fromarray(TotalLoad_array)
im6 = Image.fromarray(Matten_array)
im7 = Image.fromarray(Porosity_array)

im1.save(baseDir + IonImage)
im2.save(baseDir + PtImage)
im3.save(baseDir + CImage)
im4.save(baseDir + DensityImage)
im5.save(baseDir + TotalLoadImage)
im6.save(baseDir + MattenImage)
im7.save(baseDir + PorosityImage)
#print(res.x)
#print(loaded_model.predict(res.x))
#print('calcGSV:', myFun.calcGS)