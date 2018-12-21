# Membrane Crack Analysis Version 0.9

#### Author List

Tylynn Haddow  
Robin T. White

#### Purpose
The objective of this program is to provide quantitative information about cracks or snake-like objects for a binary, segmented input image.
  
Outputs include overall crack area, number of cracks, individual crack area, crack lengths, crack widths, orientation, and location.

#### Running the program

In the command prompt:

* cd to the crack analysis GUI folder location
* type `python main.py` and press enter

The GUI will pop up. In the GUI:

* Navigate to the Crack Analysis tab
* Input your binary segmented membrane tiff file. Cracks should have a value of 1 (white) and membrane should have a value of 0 (black)
* Input a valid save location
* Input the known pixel size from the imaging
* To remove small objects, set the Minimum Object Size. This parameter can be modified as needed. 10 to 15 is sufficient for removing noise speckle.
* Ensure save data is checked if you would like an output CSV with the data for each individua crack
* Click Start Analysis

In addition to the csv file, the analysis will display overall crack area and number of cracks in the Output field. The input image and histograms of the lengths and widths will be displayed in the image field

#### Installation

To install on your computer, 
copy the installation steps for anaconda and python in the membrane segmentation README 
https://github.com/robintwhite/NXCT/tree/master/MembraneSegmentation
with a few key differences:

* cd into the crack analysis GUI folder location `cd desktop\NXCT\CrackAnalysisGUI`
* use `conda create -n CrackGUI --file requirements.txt` to give your environment a relevant name
* you should then be able to activate the environment using `activate CrackGUI`

#### Current Issues

* The segmentation part of the program is not complete.
* The save visuals and analyze shape/ orientation functionalities currently have not yet been implemented.
