import numpy as np
from PIL import Image
import scipy.ndimage.measurements as ndm
import skimage.morphology as morph
import matplotlib.pyplot as plt
import skimage.measure as meas
import pandas as pd
import os
#The purpose of this script is to:
#1. Analyze the cracks and classify them based on...
    #orientation, shape, width, area, location, number of branches, and length
#2. Analyze the overall number and area fraction of cracks
# Written by Tylynn Haddow and Robin White.
# Revision 3
# Last updated 10/9/2017

## Initialize input variables
#Specify the input and output information (This will be an input field on the GUI)
#input_image_file, save_vis, save_data, save_loc, save_name, px_size, area_open, shape_orient
def runCrackAnalysis(imageIn, pxSz, areaOpen, shapeOrient):
    #imageIn = 'C:\Users\tylyn_000\Desktop\Tylynn\membrane\Yadvinder\Y_2200_final.tif'

    #Specify analysis variables (All GUI inputs)
    branchInfo = False
    lowerLimAngle = 45
    upperLimAngle = 135
    axisRatioLim = 0.5 #Minor / Major (always <= 1)
    largest = 7 #Set x to display or save the x largest cracks

    ## Read in the image
    im = Image.open(imageIn)
    imarray = np.array(im)

    ## Image Size: width (horizontal), height (vertical)
    width, height = im.size

    ## Remove small objects
    lb1 = morph.label(imarray, connectivity=2)
    CC = morph.remove_small_objects(lb1, areaOpen, connectivity=2)

    ## Get number of objects
    lb,num = morph.label(CC, return_num=True, connectivity=2)
    #print("Number of objects: " + str(num))

    ## Region Props to get orientation, label, area, and centroid
    props = meas.regionprops(lb, cache=False)
    orientation = [(r.orientation * 180 / 3.14159) for r in props]
    label = [r.label for r in props]
    area = [r.area for r in props]
    centroid_x = np.empty(num, dtype=float)
    centroid_y = np.empty(num, dtype=float)
    i=0
    for r in props:
        centroid_x[i], centroid_y[i] = r.centroid
        i+=1

    ## Calculate Percent Area Fraction
    xy = width * height
    totalAreaFrac = (np.sum(area)/ xy) * 100
    #print("Percent Area Fraction: " + str(total_area_frac))
    areaFrac = (np.asarray(area) / xy) * 100 #individual area fractions

    ## Despur the cracks (Remove spurious edges)
    despurred = morph.thin(lb) # may need more steps for more complicated cracks

    ## Calculate crack widths (2 * centermost distance ridge value * pixel size)
    # Get the skeleton and the distance ridge values
    skel,dist = morph.medial_axis(lb, return_distance=True)
    widths = np.empty(num, dtype=float)
    for k in range (1, num+1):
        ind = np.where(lb == k)
        DRmasked = dist[ind]
        widths[k-1] = "{0:.3f}".format(2 * pxSz * np.amax(DRmasked))

    ## Calculate Crack Lengths (area of despurred crack)
    lengths = np.empty(num, dtype=float)
    for k in range (1, num+1):
        ind = np.where(lb == k)
        despurMasked = despurred[ind]
        lengths[k-1] = "{0:.3f}".format(pxSz * np.sum(despurMasked))

    #create panda data frame
    raw_data = {
        'Label': label,
        'Centroid_x': centroid_x,
        'Centroid_y': centroid_y,
        'Percent_Crack_Area': areaFrac,
        'Width_(um)': widths,
        'Length_(um)': lengths,
        'Orientation': orientation,
    }
    df = pd.DataFrame(raw_data, columns = ['Label', 'Centroid_x', 'Centroid_y', 'Percent_Crack_Area', 'Width_(um)', 'Length_(um)', 'Orientation'])

    return num, totalAreaFrac, widths, lengths, df