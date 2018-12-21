#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 12:35:38 2016

@author: robinwhite
"""
##From varying loading of C and Pt calculate molecular formula and get 
## Mass attenuation from NIST website. Interpolate for 32.5keV energy

#Get data for compound from http://physics.nist.gov/PhysRefData/FFast/html/form.html
#example url
#http://physics.nist.gov/cgi-bin/ffast/ffast.pl?Formula=C211H3F51O15S3Pt14&gtype=3&range=S&lower=30&upper=35&density=

#import webbrowser
from datetime import datetime
import math
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
from IPython.display import display


##Majority of this code is not needed here. Can be stripped down to simple scrape data script
##------------Initialization-------------##
startTime = datetime.now()
#output Filename
filename = 'MAttenDataCPtIonNorm.csv'

#Pixel size um
pix = 1.5

#Calibration curve for GSV calc only
mcal = 1027.3
bcal = 11728

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

urlbase = 'http://physics.nist.gov'

C_load_list = []
Pt_load_list = []
Ion_load_list = []
Thickness_list = []
Density_list = []
MAtten_list = []
calcGSV_list = []

load_rangeI = int(math.ceil((1.0-0.01)/0.1))
load_rangePt = int(math.ceil((1.0-0.01)/0.1))
load_rangeC = int(math.ceil((1.0-0.01)/0.1))
##------------Loop-------------##
for i in range(load_rangeI):
    x = round(i*0.1 + 0.01 ,2) #Plus start value if other than 0
    print(int(i/(load_rangeI)*100),'%')
    
    for j in range(load_rangePt):
        y = round(j*0.1 +0.01 ,2)
        
        for k in range(load_rangeC):
            z = round(k*0.1 +0.01 ,2)
        
            #Progress
            print(datetime.now() - startTime)
            
            #loading calculation
            load_C = round(z/(x + y + z),3) #x
            load_Pt = round(y/(x + y +z),3)
            load_Ion = round(x/(x + y + z),3) #load_exp_Ion #For C load variation
            load_CL = load_C + load_Pt + load_Ion
            load = np.array([load_C, load_Pt, load_Ion, load_CL])
            
#            ## If loading value already collected, skip
#            if ((round(C_load_list,2) == load_C) & 
#                       (round(data_to_append['Loading Ion'],2) == x) & 
#                       (round(data_to_append['Loading Pt'],2) == y) ).any() == False:
            #Thickness does not affect mass attenuation value. Can use arbitrary thickness
            #And recalculate later
            
        #for k in range(1,35,5):
            t = 15
            #Thickness variation
            thickness = t
            
            #Density index 0-->3 C,Pt,I,CL
            density = load/(thickness*0.1)
            
            #Molar density index 0-->2 C, Pt, I
            M_density = density/MM
            
            #Voxel density index 0-->2 C, Pt, I
            V_density = M_density * (pix**3) * (1*10**(-12))
            
            
            C = int((9*(V_density[2]/V_density[2])+(V_density[0]/V_density[2]))*3)
            H = int((V_density[2]/V_density[2])*3)
            F = int(17*(V_density[2]/V_density[2])*3)
            O = int(5*(V_density[2]/V_density[2])*3)
            S = int((V_density[2]/V_density[2])*3)
            Pt = int((V_density[1]/V_density[2])*3)
            
            
            if Pt != 0:
                Formula = 'C'+ str(C) + 'H' + str(H) + 'F' + str(F) + 'O' + str(O) + 'S' + str(S) + 'Pt' + str(Pt)
            else:
                Formula = 'C'+ str(C) + 'H' + str(H) + 'F' + str(F) + 'O' + str(O) + 'S' + str(S)
                
            gtype = '3' #Mass attenuation coeff
            lower = '30' #lower energy range
            upper = '35' #upper energy range
            suffix1 = '/cgi-bin/ffast/ffast.pl?' + 'Formula=' + Formula + '&' + 'gtype=' + gtype + '&' + 'range=S' + '&' + 'lower=' + lower + '&' + 'upper=' + upper + '&' + 'denisty='
            
            # Scrape data
            r = requests.get(urlbase+suffix1)
            r.raise_for_status()
            
            #webbrowser.open(url)
            # Read main webpage as "lxml"
            page = BeautifulSoup(r.content, "lxml")
            
            # Get the source (URL) of the 3rd frame which contains the data we need
            # Note: this assumes layout of webpage is always the same
            suffix2 = page.find_all('frame')[2].get('src')
            
            # Read URL of page with the data needed
            r = requests.get(urlbase+suffix2)
            r.raise_for_status()
            
            table = BeautifulSoup(r.content, "lxml")
            # Data is after the only <a> tag
            data = table.a.nextSibling
            # data read as a list of characters
            #print('Raw data as list of chars: ', data)
            
            energy = []
            atten = []
            
            values = data.split()
            
            for i in range(int(len(values)/2)):
                energy.append(float(values[2*i]))
                atten.append(float(values[2*i+1]))
            
            #Linear regression for attenuation A at E_eff = 32.5keV
            E_eff = 32.5
            m = (atten[2]-atten[1])/(energy[2]-energy[1])
            b = atten[1]-energy[1]*m
            MA_eff = E_eff*m + b
            
            
            #Store data for each calcuation in loop to lists
            C_load_list.append(load[0])
            Pt_load_list.append(load[1])
            Ion_load_list.append(load[2])
            Thickness_list.append(thickness)
            Density_list.append(density[3])
            MAtten_list.append(MA_eff)
            calcGSV_list.append(MA_eff*density[3]*mcal + bcal)

##------------Data structuring-------------##
names = ['Loading C','Loading Pt','Loading Ion','Thickness','Density','Mass atten.','calc. GSV']

datatable = {names[0] : pd.Series(C_load_list),
             names[1] : pd.Series(Pt_load_list),
             names[2] : pd.Series(Ion_load_list),
             names[3] : pd.Series(Thickness_list),
             names[4] : pd.Series(Density_list),
             names[5] : pd.Series(MAtten_list),
             names[6] : pd.Series(calcGSV_list)}
 
d = pd.DataFrame(datatable)
 
display(d)

d.to_csv(filename, sep='\t')