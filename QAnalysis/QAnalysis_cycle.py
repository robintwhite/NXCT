#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 14:20:43 2016

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


######Check values against BOL values

#%%
model_filename = 'SVR_model_Ion.sav'

#Base directory
global C_scale
C_scale = 0
cyclenum = "750"

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
Gimage = misc.imread(baseDir + cyclenum + "_MAX.tif") 
#Map to read in values from BOL
Cmapimage = misc.imread(r"E:\processed\Cell29\CL_Analysis\550\\550_C_Load.tif") 
Ptmapimage = misc.imread(r"E:\processed\Cell29\CL_Analysis\550\\550_Pt_Load.tif") 
Imapimage = misc.imread(r"E:\processed\Cell29\CL_Analysis\550\\550_I_Load.tif") 

#Pixel size um
pix = 1.53

#Sub of area if necessary
T = Timage#[400:500, 400:500] #Timage
G = Gimage#[400:500, 400:500] #Gimage
Cmap = Cmapimage#[400:500, 400:500]
Ptmap = Ptmapimage#[400:500, 400:500]
Imap = Imapimage#[400:500, 400:500]

# load the SVR model from disk
loaded_model = pickle.load(open(model_filename, 'rb'))

#%%
#Calibration curve for GSV calc only ##Updated for MAX GSV
mcal = 2390.5 #Max
bcal = 22974
#mcal = 655.19 #average
#bcal = 13455

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

#%%
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

# Print iterations progress
def printProgressBar (iteration, total, time_passed, prefix = '', suffix = '', decimals = 1, length = 100, fill = "!"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    t = ("{}").format(time_passed)
    #print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    print('\r%s |%s| %s %s' % (prefix, bar, t, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()


def sigmoid(z, a):
    s = 1.0 / (1.0 + np.exp(a - z))
    return s
mu_T = np.mean(T) # Needs to not include 0s when calculating mean thickness


#Density function
def denC(x):
    denC.load_C = abs(x[0])
    denC.load_Pt = abs(x[1])
    denC.load_Ion = abs(x[2])
    denC.load_CL = denC.load_C + denC.load_Pt + denC.load_Ion
#                
    #Density 0-->3 C,Pt,I,CL
    return np.asscalar(denC.load_CL/(thickness*0.1))

#Porosity function
def porC(x):
    density = (abs(x[0]) + abs(x[1]) + abs(x[2]))/(thickness*0.1)
    CwtP = abs(x[0])/(abs(x[0]) + abs(x[1]) + abs(x[2]))
    Cvol = CwtP*density*vox/Cp
    PtwtP = abs(x[1])/(abs(x[0]) + abs(x[1]) + abs(x[2]))
    Ptvol = PtwtP*density*vox/Ptp
    IwtP = abs(x[2])/(abs(x[0]) + abs(x[1]) + abs(x[2]))
    Ivol = IwtP*density*vox/Ip
    Tvol = Cvol + Ptvol + Ivol
#                
    #Density 0-->3 C,Pt,I,CL
    return np.asscalar((vox-Tvol)/vox) #Porosity

def maxValC(x):
    C1 = abs(x[0])                
    return (C0 - C1)#*(abs(x[1]) - C1)#*(C1 - (1-C_scale)*C0)
def maxValPt(x):
    Pt1 = abs(x[1])                
    return (Pt0 - Pt1)*(Pt1 - abs(x[0]))
def maxValI(x):
    I1 = abs(x[2])                
    return (I1 - I0)*(I0 - I1)#Ionomer not to vary other than BOL

#%%
count = 0
l = T.shape[0]*T.shape[1]
## Loop
for i in range(T.shape[0]): #up and down 0<=i<dimension in X
    for j in range(T.shape[1]): #left to right
        count += 1
#        if count%int(T.shape[0]*T.shape[1]/20) == 0:
#            print('{0}'.format("% complete: "), '{:.2f}'.format(count/(T.shape[0]*T.shape[1])))
#            t = datetime.now() - t0
#            print(t)
        
        diff = datetime.now() - t0
        t = divmod(diff.days * 86400 + diff.seconds, 60)
        printProgressBar(count, l, t[0], prefix = 'Progress:', suffix = 'Minutes', length = 50)    
        #Thickness
        thickness = T[i, j]*pix
        #initial values for cycles from BOL
        C0 = Cmap[i,j]
        Pt0 = Ptmap[i,j]
        I0 = Imap[i,j]
        
        #Check non-zero thickness
        if thickness <= 1*pix:
            C_load_array[i,j] = 0
            Pt_load_array[i,j] = 0
            Ion_load_array[i,j] = 0
            Density_array[i,j] = 0
            TotalLoad_array[i,j] = 0
            Porosity_array[i,j] = 1            
            #print('flag thickness')
        
        elif C0 <= 0.001 or Pt0 <= 0.001 or I0 <= 0.001:
            C_load_array[i,j] = 0
            Pt_load_array[i,j] = 0
            Ion_load_array[i,j] = 0
            Density_array[i,j] = 0
            TotalLoad_array[i,j] = 0
            Porosity_array[i,j] = 1            
            
        else:
        #experimental GSV
            expGS = G[i, j]
        
            
            def myFun(x):
                
                ##Check for invalid values
                if np.any(np.isinf(x)):
                    print(x)
#                    x = np.array([C0, Pt0, I0])
                    print(i,j)
                    
                    
                 #loading calculation
                myFun.load_C = abs(x[0])
                myFun.load_Pt = abs(x[1])
                myFun.load_Ion = abs(x[2]) 
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
            
            x0 = np.array([(1-C_scale)*C0, 0.4, 0.24]) #Initial guess Ionomer/Pt loading typical 0.23/0.4  
            #Use -0.1 since search is initialted with 0.05
            #x0 = np.array([C0,Pt0,I0])
            #x0 = np.array([0.23, 0.2])
                           
        #            bnds = ((None, None),(None, None),(None, None)) #bounds. Must be positive, can have higher ionomer
            cons = ({'type': 'ineq', 'fun': lambda x: x - 0.001}, #correction for using x = 0 and dividing by 0                    
                    {'type': 'ineq', 'fun': lambda x: 1 - porC(x)},
                    {'type': 'ineq', 'fun': lambda x: porC(x)},
                    {'type': 'ineq', 'fun': lambda x: maxValPt(x)},
                    {'type': 'ineq', 'fun': lambda x: maxValI(x)},
                    {'type': 'ineq', 'fun': lambda x: maxValC(x)}) #constraint g(x) >= 0) #constraint h(x) = 0
                    
            res = minimize(myFun, x0, method = 'COBYLA', constraints = cons,
                       options = {'disp': False, 'rhobeg':0.05}).x
#            res = minimize(myFun, x0, method = 'SLSQP', constraints = cons,
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
            
#            if Porosity_array[i,j] < 0:
#                Porosity_array[i,j] = 0
#End loop

#Time end
t = datetime.now() - t0
print(t)    

#%%Plot
fig = plt.figure()
a = fig.add_subplot(1, 1, 1)  
plt.imshow(Porosity_array)
plt.colorbar(orientation='horizontal')
plt.show()
#%%
im1 = Image.fromarray(Ion_load_array)
im2 = Image.fromarray(Pt_load_array)
im3 = Image.fromarray(C_load_array)
im4 = Image.fromarray(Density_array)
im5 = Image.fromarray(TotalLoad_array)
im6 = Image.fromarray(Matten_array)
im7 = Image.fromarray(Porosity_array)

im1.save(baseDir + IonImage) # "\\Pt_loss\\" +
im2.save(baseDir + PtImage)
im3.save(baseDir + CImage)
im4.save(baseDir + DensityImage)
im5.save(baseDir + TotalLoadImage)
im6.save(baseDir + MattenImage)
im7.save(baseDir + PorosityImage)
#print(res.x)
#print(loaded_model.predict(res.x))
#print('calcGSV:', myFun.calcGS)