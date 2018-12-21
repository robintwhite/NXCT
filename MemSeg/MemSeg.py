# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 11:49:27 2017

@author: Robin
"""


import numpy as np
from skimage.external import tifffile
from scipy import interpolate, ndimage
import os
import gui
from PyQt5 import QtWidgets
#import matplotlib.pyplot as plt

def GetBoundary(progress_callback, input_dir, im_list, elec_list, boundary_list, filter_size):
    """
    Obtains boundaries from original thresholded images.
    Also performs interpolation to smooth and fill gaps.

    Arguments:
    progress_callback -- signal for GUI update
    input_dir -- string, location for input/output files
    im_list -- list, names of images to read in
    elec_list -- list, electrode naming for output
    boundary_list -- list, order of boundary location (top vs bottom)
    filter_size -- scalar, input for smoothing of uniform_filter


    Returns:
    boundaries -- dictionary of boundary locations for anode and cathode
    """

    baseDir = input_dir
    im_name = im_list#["CathodeRemoved.tif","AnodeRemoved.tif"]
    electrode = elec_list#['anode','cathode']
    keep_pixels = boundary_list#['bottom','top']
    filter_size = filter_size #convolution box size (square)
    interp_method = 'nearest' #nearest, linear or cubic

    l = len(im_name)
    boundaries = {}

    progress_callback.emit(10, 'Collecting boundary')

    try:
        for p in np.arange(l):
            cat_outline_im = tifffile.imread(os.path.join(baseDir,im_name[p]))
            dims = cat_outline_im.shape

            blank_im = np.zeros(dims, dtype=np.uint8)
            flag = np.zeros((dims[1], dims[2]), dtype=np.uint8)
            temp = np.zeros((dims[1], dims[2]), dtype=np.uint8)
            logical_mask = np.zeros((dims[1], dims[2]), dtype=np.uint8)

            #Get Boundary pixels
            if keep_pixels[p] == 'top':
                #Top boundary
                for slc in range(0, dims[0]): #top boundary because of order
                    a = np.where(cat_outline_im[slc] == 255)
                    if any(a[0]): #must have x and y location, just check one
                        if any(flag[a[0],a[1]]) == 1: #If already found boundary
                            flag[a[0],a[1]] = 1 #update for new boundary location additions in plane
                            logical_mask = np.logical_xor(flag,temp) #check previous step over full plane
                            #if anlready have boundary (1,1) = 0, don't update draw
                            b = np.where(logical_mask == True) #New locations
                            temp[a[0],a[1]] = 1 #update this step
                            if any(b[0]):
                                blank_im[slc,b[0],b[1]] = 255 #draw boundary
                        else: #First time finding boundary
                            flag[a[0],a[1]] = 1
                            temp[a[0],a[1]] = 1 #update this step
                            blank_im[slc,a[0],a[1]] = 255 #draw boundary

            elif keep_pixels[p] == 'bottom':
                #Bottom boundary
                for slc in range(dims[0] - 1, -1, -1):
                    a = np.where(cat_outline_im[slc] == 255)
                    if any(a[0]):
                        if any(flag[a[0],a[1]]) == 1:
                            flag[a[0],a[1]] = 1 #update
                            logical_mask = np.logical_xor(flag,temp) #check
                            b = np.where(logical_mask == True)
                            temp[a[0],a[1]] = 1
                            if any(b[0]):
                                blank_im[slc,b[0],b[1]] = 255 #draw boundary
                        else:
                            flag[a[0],a[1]] = 1
                            temp[a[0],a[1]] = 1 #update this step
                            blank_im[slc,a[0],a[1]] = 255 #draw boundary

            else:
                raise NameError('Must choose either top or bottom')

            #clear
            flag = None
            temp = None
            logical_mask = None
            cat_outline_im = None

            interp_im = np.zeros(dims, dtype=np.uint8)
            ny = np.linspace(0, dims[1]-1, dims[1], int)
            nx = np.linspace(0, dims[2]-1, dims[2], int)
            [xx,yy] = np.meshgrid(nx,ny) #grid to fit interpolation values

            r = np.where(blank_im[:,:,:] == 255) #locations of non-zero pixels
            blank_im = None

            rz = r[0] #slice number values
            ry = r[1]
            rx = r[2]
            ry = np.ndarray.tolist(ry)
            rx = np.ndarray.tolist(rx)
            X = np.column_stack((ry, rx)) #(y,x location values)

            #clear
            ry = None
            rx = None

            interp = interpolate.griddata(X, rz, (yy, xx), method=interp_method)
            #ZI = signal.medfilt(interp, [med_k,med_k]) #smooth
            ZI = ndimage.uniform_filter(interp, size=filter_size, mode='nearest')
            ##indexing issue ZI is 2D matrix
            interp_im[ZI[yy.astype(int),xx.astype(int)].astype(int), yy.astype(int), xx.astype(int)] = 255
            boundaries[electrode[p]] = interp_im

    except (FileNotFoundError, UnboundLocalError, AttributeError, KeyError):
        progress_callback.emit(0, 'Image not found')
        return boundaries
    interp_im = None
    return boundaries

def DynamicSlice(progress_callback, elec_list, boundary_list, boundaries, gs_im, height_vec, num_steps, dyn_range = [0.0,1.0]):
    """
    Fills region of empty image with values 255 for volume between boundaries,
    and area of dynamic slice.

    Arguments:
    progress_callback -- signal for GUI update
    input_dir -- string, location for input/output files
    elec_list -- list, electrode naming for output
    boundary_list -- list, order of boundary location (top vs bottom)
    boundaries -- dictionary of boundary locations for anode and cathode
    height_vec -- array, height of boundaries at x,y locations


    Returns:
    blank_im -- 8bit binary (0 and 255) image stack of volume between boundaries
    slice_im -- 8bit binary image stack of area of dynamic slice location
    """
    dyn_slc = []

    progress_callback.emit(80, 'Creating full dynamic slice')
    try:
        top_boundary = boundaries[elec_list[boundary_list.index('bottom')]]
        dims = top_boundary.shape

        top_pix_arr = np.nonzero(top_boundary)

        arz = top_pix_arr[0]
        arz = np.ndarray.tolist(arz)
        ary = top_pix_arr[1]
        ary = np.ndarray.tolist(ary)
        arx = top_pix_arr[2]
        arx = np.ndarray.tolist(arx)
        ars = list(zip(ary,arx,arz))
        ar_sort = sorted(ars, key=lambda x: x[0])
        ary2, arx2, arz2 = list(zip(*ar_sort))

        #clear
        arz = None
        ary = None
        arx = None

        #Have range selection 0,1 for full, 0.2,0.8 etc..
        height_min_rng = np.multiply(height_vec, dyn_range[0])
        arz2 = [arz2[i] + int(height_min_rng[ary2[i]][arx2[i]]) + 1 for i in range(len(ary2))]

        height = np.reshape(height_vec, height_vec.shape[0]*height_vec.shape[1]) - 1
        height_max_rng = np.multiply(height, dyn_range[1]-dyn_range[0])
        max_height = int(np.max(height_max_rng))

        if num_steps == 0:
            num_steps = max_height

        dyn_slc = np.zeros((num_steps, dims[1], dims[2]))
        step_size = np.divide(height_max_rng, num_steps)
        for i in np.arange(0,num_steps, dtype=np.uint8):
            dyn_slc[i,ary2,arx2] = gs_im[(arz2 + np.floor((i+1)*step_size).astype(np.uint8)),ary2,arx2]

    except (FileNotFoundError, UnboundLocalError, AttributeError, KeyError):
        progress_callback.emit(0, 'No boundary images')
        return

    return dyn_slc

def BoundaryFill(progress_callback, elec_list, boundary_list, boundaries, slc_loc):
    """
    Fills region of empty image with values 255 for volume between boundaries,
    and area of dynamic slice.

    Arguments:
    progress_callback -- signal for GUI update
    input_dir -- string, location for input/output files
    elec_list -- list, electrode naming for output
    boundary_list -- list, order of boundary location (top vs bottom)
    boundaries -- dictionary of boundary locations for anode and cathode
    slc_loc -- scalar, fraction of membrane thickness to create dynamic slice


    Returns:
    blank_im -- 8bit binary (0 and 255) image stack of volume between boundaries
    slice_im -- 8bit binary image stack of area of dynamic slice location
    """
    blank_im = []
    slc_im = []
    slc_boundary = []
    progress_callback.emit(50, 'Filling boundary')

    try:
        top_outline_im = boundaries[elec_list[boundary_list.index('bottom')]]
        bot_outline_im = boundaries[elec_list[boundary_list.index('top')]]
        dims = top_outline_im.shape

        top_pix_arr = np.nonzero(top_outline_im)
        bot_pix_arr = np.nonzero(bot_outline_im)

        arz = top_pix_arr[0]
        arz = np.ndarray.tolist(arz)
        ary = top_pix_arr[1]
        ary = np.ndarray.tolist(ary)
        arx = top_pix_arr[2]
        arx = np.ndarray.tolist(arx)
        ars = list(zip(ary,arx,arz))
        ar_sort = sorted(ars, key=lambda x: x[0])
        ary2, arx2, arz2 = list(zip(*ar_sort))

        #clear
        arz = None
        ary = None
        arx = None
        ar_sort = None

        crz = bot_pix_arr[0]
        crz = np.ndarray.tolist(crz)
        cry = bot_pix_arr[1]
        cry = np.ndarray.tolist(cry)
        crx = top_pix_arr[2]
        crx = np.ndarray.tolist(crx)
        crs = list(zip(cry,crx,crz))
        cr_sort = sorted(crs, key=lambda x: x[0])
        cry2, crx2, crz2 = list(zip(*cr_sort))

        #clear
        crz = None
        cry = None
        crx = None
        cr_sort = None

        h = [j-k for k, j in zip(arz2, crz2)] #Height

        #If height is zero
        if any(w == 0 for w in h):
            indices = [idx for idx, v in enumerate(h) if v == 0]
            for d in indices:
                h[d] = 1 #set to 1

        a_h = np.array([arz2]) #Top z location
        l = [range(p) for p in h] #length values
        q = a_h+[np.array(list(s)) for s in l]#locations to be made 255 to fill membrane area

        blank_im = np.zeros(dims, dtype=np.uint8)
        slc_im = np.zeros(dims, dtype=np.uint8)

        #Print pixels to blank image
        slc_boundary = a_h + np.multiply(h,slc_loc).astype(int) + 1
        slc_im[slc_boundary[0],ary2,arx2] = 255

        #for m in range(0, len(q[0])):
        flat_list = [item for sublist in q for item in sublist]
        for i in range(len(flat_list)):
            blank_im[flat_list[i],ary2[i],arx2[i]] = 255

    except (ValueError):
        progress_callback.emit(0, 'Incorrect image alignment')
        return blank_im, slc_im

    except (FileNotFoundError, UnboundLocalError, AttributeError, KeyError):
        progress_callback.emit(0, 'No boundary images')
        return blank_im, slc_im

    return blank_im, slc_im

def MaskMem(progress_callback, mem_mask, slc_mask, input_dir, gs_im):
    """
    Creates mask of greyscale from binary image stacks.

    Arguments:
    progress_callback -- signal for GUI update
    input_dir -- string, location for input/output files
    mem_mask -- image array, 8-bit binary stack of membrane location
    slc_mask -- image array, 8-bit binary stack of slice location
    gs_im_name -- string, image name to be read in


    Returns:
    masked_gs -- greyscale values of original image stack between boundaries
    masked_slc -- greyscale values of original image stack at slice location
    """
    masked_gs = []
    masked_slc = []
    progress_callback.emit(50, 'Creating mask')

    masked_gs = gs_im*mem_mask.clip(max=1)
    masked_slc = gs_im*slc_mask.clip(max=1)
    progress_callback.emit(100, 'Done.')

    return masked_gs, masked_slc
