###
### By Tylynn Haddow and Robin T. White
### Version 0.9
###

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
import sys
import os
import membraneCrackGUI #the design file generated from qt designer
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import random
import numpy as np
from PIL import Image
import pandas as pd
import time
import membraneCrackAnalysis

#All functions defined in App class
class AnalysisApp(QtWidgets.QMainWindow, membraneCrackGUI.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)
        
        #Initialize click objects
        self.btn_startSeg.clicked.connect(self.segmentation)
        self.btn_startAn.clicked.connect(self.analysis)
        self.btn_left.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.btn_right.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.btn_helpAn.clicked.connect(self.anHelpApp) #See code below for popup
        
        #Default text box values
        self.le_segInput.setText(os.getcwd())
        self.le_input.setText("C:\\Users\\tylyn_000\\Documents\\Tylynn\\membrane\\Yadvinder\\Y_2200_final.tif")
        self.le_saveLoc.setText(os.getcwd())
        self.le_saveName.setText(time.strftime("%Y%m%d-%H%M%S")+'output.csv')
    
    #Save file function to handle seperate exception
    def save_file_toCSV(self, data, filename):
        try:
            data.to_csv(filename)
            #print(filename)
        except(PermissionError, AttributeError, FileNotFoundError, OSError):
            self.output.append("{0}".format('Please input a valid save name and location'))

    def save_hist(self, filename):
        try:
            #remove the filetype
            s = filename.rsplit('.', 1)
            imagename = s[0]
            self.canvas_2.canvas.fig.savefig(imagename + '.png')
            #print(filename)
        except(PermissionError, AttributeError, FileNotFoundError, OSError):
            self.output.append("{0}".format('in save_hist - Please input a valid save name and location'))     
    
    def segmentation(self):
        #Segmentation function to be run when startSegBtn is pressed
        #Incomplete - This will be where it will take the centermost pixels of the membrane from the 3D segmentation to obtain a 2D image
        #Maybe add a small console output in this tab just for communication to the user
        input_image_file = self.le_segInput.text()
        try:
            self.seg_output.append("{0}".format('This section is under construction'))           
            img = Image.open(input_image_file)
            imarray = np.array(img)
            self.stackedWidget.widget_2.canvas.ax = self.widget_2.canvas.fig.add_subplot(111)
            self.widget_2.canvas.ax.imshow(imarray)
            self.widget_2.canvas.fig.tight_layout()
            self.widget_2.canvas.draw()
        except (PermissionError, AttributeError, FileNotFoundError): 
            self.seg_output.append("{0}".format('Please input a valid image'))           
    
    def analysis(self):
        #Analysis to be run when start analysis button pressed
        input_image_file = self.le_input.text()
        save_vis = self.cb_saveVis.isChecked()
        save_data = self.cb_saveData.isChecked()
        save_loc = self.le_saveLoc.text()
        save_name = self.le_saveName.text()
        px_size = self.le_pxSz.text()
        area_open = self.sb_areaOpen.value()
        shape_orient = self.cb_ShapeOrient.isChecked()
        #Will need some check if the image can be found and if all inputs are satisfied

        try:
            if(px_size == ''):
                self.output.append("{0}".format('Please input the pixel size (um)'))
                px_size = 1.0
            else:
                px_size = float(px_size)
                #show image
                img = Image.open(input_image_file)
                imarray = np.array(img)
                self.canvas_1.canvas.ax = self.canvas_1.canvas.fig.add_subplot(111)
                self.canvas_1.canvas.ax.imshow(imarray) #clear axes
                self.canvas_1.canvas.ax.set_title('Input Image')
                self.canvas_1.canvas.fig.tight_layout()
                self.canvas_1.canvas.draw()

                num, percent_area_frac, widths, lengths, df = membraneCrackAnalysis.runCrackAnalysis(input_image_file, px_size, area_open, shape_orient)
                #Output to console
                #Must be string type
                self.output.append("{0}".format('Number of Cracks: '+ str(num) + '\n' + 'Percent Area Fraction: ' + str(percent_area_frac)))

                #Plot widths
                wh_list, wc_list, w_width = self.histPlot(widths)
                self.canvas_2.canvas.ax = self.canvas_2.canvas.fig.add_subplot(211)
                self.canvas_2.canvas.ax.cla() #clear axes for each plot
                self.canvas_2.canvas.ax.bar(wc_list, wh_list, w_width, color='xkcd:teal')
                self.canvas_2.canvas.ax.set_title('Widths [um]')
                self.canvas_2.canvas.ax.set_ylabel('Normalized Counts')
                self.canvas_2.canvas.ax.set_xticks(wc_list)
                #Plot lengths
                lh_list, lc_list, l_width = self.histPlot(lengths)
                self.canvas_2.canvas.ax = self.canvas_2.canvas.fig.add_subplot(212)
                self.canvas_2.canvas.ax.cla()
                self.canvas_2.canvas.ax.bar(lc_list, lh_list, l_width, color='xkcd:azure')
                self.canvas_2.canvas.ax.set_title('Lengths [um]')
                self.canvas_2.canvas.ax.set_ylabel('Normalized Counts')
                self.canvas_2.canvas.ax.set_xticks(lc_list)
                self.canvas_2.canvas.fig.tight_layout()
                self.canvas_2.canvas.draw()

                if (save_data):
                    #save data frame to csv
                    self.save_file_toCSV(df, os.path.join(save_loc,save_name))
                if (save_vis):
                    #save histograms
                    self.save_hist(os.path.join(save_loc,save_name))

        #Errors for image input       
        except (PermissionError, AttributeError, FileNotFoundError, OSError) as e:
            self.output.append("{0}".format('Please input a valid image'))
            #print(e)
            #print('mpl error')
        except (ValueError) as e:
            self.output.append("{0}".format('Please input a valid pixel size (number)'))
            #print(e)

    def histPlot(self, data):
        min = int(np.amin(data))
        max = np.ceil(np.amax(data))
        step = int((max-min)/10)
        bins = np.arange(min,max+step,step)
        hist, bin_e = np.histogram(data, bins=bins) 
        center = (bin_e[:-1] + bin_e[1:]) / 2
        width = 0.7 * (bin_e[1] - bin_e[0])

        h_norm = (hist-np.amin(hist))/(np.amax(hist)-np.amin(hist))

        h_list = h_norm.tolist()
        c_list = center.tolist()
        #plt.savefig(mstDir+data+'_fracChngFig.pdf', bbox_inches='tight')
        return h_list, c_list, width  
            
    def anHelpApp(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowTitle(self.tr("Help"))
        msgBox.setText("<br>"+
                       "<b>{0}</b><br><br>".format('Membrane Crack Analysis Help') +
                       "{0}<br><br>".format('The purpose of this application is to provide quantitiative crack information.')+
                       "<b>{0}</b><br>{1}<br><br>".format('Input Image', 'The input image should be a binary, segmented image of a membrane in through-plane view. The membrane should have a value of 1 and the cracks should have a value of 0. Currently, only 2D images are accepted.')+
                       "<b>{0}</b><br>{1}<br><br><br>".format('Output', 'If save data is checked, the application output is a csv file including the individual crack data. Overall crack area and overall number of cracks are displayed in the application Output. Histograms of crack lengths and widths will also be displayed in the application.')+
                       "&copy;2017<br>")
        msgBox.setInformativeText("If your problem is not resolved, please see the README or submit an issue via https://github.com/robintwhite/NXCT")

        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)

        msgBox.exec_() 
        

def main():
    app = QtWidgets.QApplication(sys.argv)
    form = AnalysisApp()
    form.show()
    app.exec_()
    
if __name__ == '__main__':
    main()