![alt text](https://raw.githubusercontent.com/robintwhite/NXCT/master/MemSeg/Lib/Images/MemSeg.png) 
# MemSeg
# Read Me
#### Code to perform segmentation of membrane by using boundaries of cathode and anode layers.

### Final result
![alt text](https://raw.githubusercontent.com/robintwhite/NXCT/master/TutorialImgs/MemSegOut.png)

### Installation
Head to https://www.anaconda.com/download/ and download version Python 3.6

During installation, you will see this, make sure both are selected
![alt text](https://raw.githubusercontent.com/robintwhite/NXCT/master/TutorialImgs/AnacondaInstall.png)

Follow the rest of the installation.

After this is complete, download the NXCT repo as .zip and unpack to a easily accessible location. Here, I'm just assuming the desktop. Open windows command prompt (type command prompt in windows search), and navigate to this folder.

More specifically, from opening command prompt, type:

`cd desktop\NXCT-master\MemSeg`

If you can't navigate to the folder location, a simple google search will be able to help you get there.

After you are in the MemSeg folder type:

`conda env create --file MemSeg.yml`

Here MemSeg is the name of the environment, and MemSeg.yml should be in your current location directory. It should ask if you want to install a long list of packages, hit y

If everything goes smoothly you should be able to then activate your new environment by typing:

`activate MemSeg`

You should now see a bracketed (MemSeg) next to your path in command prompt. You will need to type activate MemSeg everytime to start your environment. This is what you should have now:

![alt text](https://raw.githubusercontent.com/robintwhite/NXCT/master/TutorialImgs/MemSegEnv.PNG)

In the event that the packages don't install properly, you can try and run requirements-forge.txt instead by

`conda create -n MemSeg -c conda-forge --file requirements-forge.txt`

this is less explicit and may allow for conda to find active package locations. If worse comes to worst, packages may have to be installed manually.

Once the environment is ready and activated, now type:

`python main.py`

MemSeg window should pop-up.

![alt text](https://raw.githubusercontent.com/robintwhite/NXCT/master/TutorialImgs/MemSeg_popup.png)
