# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 15:54:54 2017
    Optimization method test.
@author: Robin
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import pickle
from scipy.optimize import minimize

##Max density from porosity calculation to show constraint boundary
##Implement constraint in optimization search and COBYLA

##Uses SVR model obtained by collecting data from NIST for variation in 
##Carbon loading and Pt loading at energy of 32.5keV

model_filename = 'SVR_model_Ion.sav'

##------------Initialization-------------##
global C_scale
C_scale = 0 #Percent loss ie 0.7 loss, 70% less, 30% remaining in CCL from CO2 measurements

#Thickness Calibration 49.6um 2^16 - 1 from 16bitGS to thickness value
#calib = 49.6/((2**16)-1)

# load the SVR model from disk
loaded_model = pickle.load(open(model_filename, 'rb'))

#Pixel size um
pix = 1.53

#Calibration curve
mcal = 887.46 #Max
bcal = 13398

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

#Array initialization
C_load = 0.0
Pt_load = 0.0
Ion_load = 0.0
Density = 0.0

expGS = 20500
thickness = 11.5

#Volume cm^3
vox = (pix**3)*0.000000000001

def sigmoid(z, a):
    s = 1.0 / (1.0 + np.exp(a - z))
    return s
       
def myFun(x):
    myFun.load_C = (1-C_scale)*x[1]
    myFun.load_Pt = x[1]
    myFun.load_Ion = x[2]
    myFun.load_CL = myFun.load_C + myFun.load_Pt + myFun.load_Ion
    
    #Normalize for Mass atten model
    norm = myFun.load_C+myFun.load_Pt+myFun.load_Ion
    Xnorm = np.array([myFun.load_C/norm, myFun.load_Pt/norm, myFun.load_Ion/norm])
    #Reshape data
    X = np.array(Xnorm).reshape((-1,3))
    #Calculate Mass attenuation from SVR model previously determined and loaded
    myFun.MA_calc = loaded_model.predict(X)
    #Density 0-->3 C,Pt,I,CL
    myFun.density = myFun.load_CL/(thickness*0.1)
    myFun.calcGS = myFun.MA_calc*myFun.density*mcal + bcal   
    return np.asscalar(abs(myFun.calcGS-expGS))
            
def reporter(p): #Capture intermediate values of search
    global ps
    ps.append(p)

def porC(x):
    density = ((1-C_scale)*x[1] + x[1] + x[2])/(thickness*0.1)
    CwtP = (1-C_scale)*x[1]/((1-C_scale)*x[1] + x[1] + x[2])
    Cvol = CwtP*density*vox/Cp
    PtwtP = x[1]/((1-C_scale)*x[1] + x[1] + x[2])
    Ptvol = PtwtP*density*vox/Ptp
    IwtP = x[2]/((1-C_scale)*x[1] + x[1] + x[2])
    Ivol = IwtP*density*vox/Ip
    Tvol = Cvol + Ptvol + Ivol
#                
    #Density 0-->3 C,Pt,I,CL
    return np.asscalar((vox-Tvol)/vox)

x0 = np.array([0.4, 0.4, 0.24]) #Initial guess Ionomer/Pt loading typical 0.23/0.4
ps = [x0]

#bnds = ((0.02, 4.0),(0.02, 4.0),(0.02, 4.0)) #constraints. Must be positive, can have higher ionomer
#res = minimize(myFun, x0, method = 'TNC', bounds = bnds, callback = reporter,
#           options = {'xtol': 1e-8, 'disp': False})
##method = 'powell' 

cons = ({'type': 'ineq', 'fun': lambda x: x - 0.001}, #correction for using x = 0 and dividing by 0
        {'type': 'ineq', 'fun': lambda x: 1 - porC(x)},
        {'type': 'ineq', 'fun': lambda x: porC(x)}) #constraint g(x) >= 0

#res = minimize(myFun, x0, method = 'COBYLA', constraints = cons,
#           options = {'disp': False,'rhobeg':0.05})
res = minimize(myFun, x0, method = 'SLSQP', constraints = cons, callback=reporter)

C_load = (1-C_scale)*res.x[1]
Pt_load = res.x[1]#/myFun.load_CL
print('Pt = {:f} mg cm-2'.format(Pt_load))
Ion_load = res.x[2]#/myFun.load_CL
print('Ion = {:f} mg cm-2'.format(Ion_load))
 #Normalize for Mass atten model
Optnorm = C_load+Pt_load+Ion_load
OptXnorm = np.array([C_load/Optnorm, Pt_load/Optnorm, Ion_load/Optnorm])
#Reshape data
OptX = np.array(OptXnorm).reshape((-1,3))
#Calculate Mass attenuation from SVR model previously determined and loaded
temp = loaded_model.predict(OptX)
OptMA = temp[0]
OptDensity = (res.x[0] + res.x[1] + res.x[2])/(thickness*0.1)
print('Density = {:f} g cm-3'.format(OptDensity))
B = [res.x[1],res.x[1],res.x[2]]
print('Porosity = {} '.format(porC(B))) 

xx = np.arange(0.02, 4.0, 0.05) #range x
xy = np.arange(0.02, 4.0, 0.05) #range y
Ax, Ay = np.meshgrid(xx, xy, sparse=False, indexing='ij')
MA = np.zeros((len(xx),len(xy)), dtype=float)
z = np.zeros((len(xx),len(xy)), dtype=float)
p = np.zeros((len(xx),len(xy)), dtype=float)
pplot = np.zeros((len(xx),len(xy)), dtype=float)
density = np.zeros((len(xx),len(xy)), dtype=float)

for i in range(len(xx)):
    for j in range(len(xy)):        
        A = [Ax[i,j], Ax[i,j], Ay[i,j]]
        z[i,j] = myFun(A)
        MA[i,j] = myFun.MA_calc#myFun(A)
        density[i,j] = myFun.density#(2*A[1] + A[2])/(thickness*0.1)
        p[i,j] = porC(A)        
        if (0.0 <= p[i,j] <= 1.0):
            pplot[i,j] = 1
        else:
            pplot[i,j] = -1
#            z[i,j] = float('nan')
#            MA[i,j] = float('nan')
#            density[i,j] = float('nan')

#Optimization search
pr = np.array(ps)
MA_search = np.zeros(len(pr), dtype=float)
Dens_search = np.zeros(len(pr), dtype=float)

for i in range(len(pr)):
    Searchnorm = pr[i][0]+pr[i][1]+pr[i][2]
    SearchXnorm = np.array([pr[i][0]/Searchnorm, pr[i][1]/Searchnorm, pr[i][2]/Searchnorm])
    Y = np.array(SearchXnorm).reshape((-1,3))
    MA_search[i] = loaded_model.predict(Y)
    Dens_search[i] = (pr[i][0] + pr[i][1] + pr[i][2])/(thickness*0.1)

       
from matplotlib import cm
fig = plt.figure()
#ax = fig.gca(projection='3d')
#ax.plot_surface(Ax, Ay, z, rstride=8, cstride=8, alpha=0.3)
#cset = ax.contourf(Ax, Ay, density, 256, zdir='z', offset=0, cmap=cm.coolwarm)
#ax.set_xlabel('Ion')
#ax.set_xlim(0, 4)
#ax.set_ylabel('Pt')
#ax.set_ylim(0, 2)
#ax.set_zlabel('Density')
#ax.set_zlim(0, 166000)
#fig.colorbar(cset)

#p = ax.plot(ps[:,0], ps[:,1], '-wo')
cset = plt.contourf(Ax, Ay, z, 256)
pset = plt.contour(Ax, Ay, pplot, 2, colors = 'k', )
plt.plot(Pt_load, Ion_load, 'wo')
plt.title('Difference between calculated and experimental GSV')
plt.xlabel('Pt loading mgcm-2')
plt.ylabel('Ionomer loading mgcm-2')
xl = '{:0.2f}'.format(Pt_load)
xr = '{:0.2f}'.format(Ion_load)
plt.text(Pt_load + 0.1, Ion_load+0.05, xl + ', ' + xr, fontsize=12, color='gray')
#plt.savefig('optimTestLoading.png', bbox_inches='tight')
fig.colorbar(cset)
plt.show()

fig = plt.figure()       
cset = plt.contourf(MA, density, z, 256)
pset = plt.contour(MA, density, pplot, 2, colors = 'k', )
plt.plot(OptMA, OptDensity, 'wo')
plt.plot(MA_search, Dens_search, '-.')
plt.title('Difference between calculated and experimental GSV')
plt.xlabel('Mass atten. cm^2 / g')
plt.ylabel('Density g/cm3')
xl = '{:0.2f}'.format(OptMA)
xr = '{:0.2f}'.format(OptDensity)
plt.text(OptMA + 0.01, OptDensity+0.01, xl + ', ' + xr, fontsize=12, color='gray')
#plt.savefig('optimTestMADensity.png', bbox_inches='tight')
fig.colorbar(cset)
plt.show()
